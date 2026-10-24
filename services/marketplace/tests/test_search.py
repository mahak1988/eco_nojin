"""Tests for the marketplace product full-text index.

Everything here runs offline: the index is a SQLite/FTS5 database opened
in-process through the standard library's ``sqlite3`` module, and the ORM
round-trip tests build their own in-memory engine from the shared
``database.base`` metadata — no network and no external services.

The Persian strings are real product names/descriptions ("کود زیستی",
"گندم ارگانیک", ...) so tokenisation, the Arabic-script normalisation and
snippetting are exercised on the text the marketplace actually stores.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

import services.marketplace.search as search_module
from database.base import Base
from services.marketplace.models import (
    MarketplaceProduct,
    MarketplaceProductStatus,
    MarketplaceSeller,
)
from services.marketplace.search import (
    FTS_SCHEMA,
    FTS_TABLE,
    FTS5UnavailableError,
    MarketplaceSearchService,
    fts5_available,
    get_search_service,
    normalize_text,
    reset_search_service,
)


class _Product:
    """Duck-typed stand-in for a ``MarketplaceProduct`` row.

    The search index reads ``id``, ``name``, ``description``, ``village_id``,
    ``category``, ``price`` and ``status``, which is exactly what the ORM
    row and the legacy catalog dataclass expose.
    """

    def __init__(
        self,
        product_id: str,
        name: str,
        description: str = "",
        *,
        village_id: str = "v-a",
        category: str = "other",
        price: float = 0.0,
        status: str = "active",
    ) -> None:
        self.id = product_id
        self.name = name
        self.description = description
        self.village_id = village_id
        self.category = category
        self.price = price
        self.status = status


@pytest.fixture(autouse=True)
def _clean_search_singleton():
    """Keep the process-wide singleton from leaking between tests."""
    reset_search_service()
    yield
    reset_search_service()


@pytest.fixture
def index() -> MarketplaceSearchService:
    """A fresh in-memory index."""
    return MarketplaceSearchService()


@pytest.fixture
def sync_session():
    """A synchronous in-memory ORM session over the shared metadata."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    yield session
    session.close()
    engine.dispose()


@pytest_asyncio.fixture
async def async_session():
    """The project's own async ORM session over the shared metadata."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


# --- capability & normalisation -------------------------------------------


class TestFTS5Capability:
    """The index must declare itself honestly, never silently degrade."""

    def test_fts5_is_available_in_this_build(self):
        assert fts5_available() is True

    def test_service_refuses_to_build_without_fts5(self, monkeypatch):
        monkeypatch.setattr(search_module, "fts5_available", lambda: False)
        with pytest.raises(FTS5UnavailableError, match="FTS5"):
            MarketplaceSearchService()

    def test_schema_declares_the_virtual_table(self):
        assert "USING fts5" in FTS_SCHEMA
        assert FTS_TABLE in FTS_SCHEMA


class TestNormalization:
    """Persian-aware normalisation is applied on both sides of the index."""

    def test_arabic_spelling_variants_fold_to_persian(self):
        assert normalize_text("كود زيستي") == "کود زیستی"

    def test_zwnj_compound_becomes_separate_tokens(self):
        assert normalize_text("کود‌زیستی") == "کود زیستی"

    def test_harakat_and_case_are_folded(self):
        # harakat are combining marks, Latin casing is folded
        assert normalize_text("کَدَ ZooDiAC") == "کد zoodiac"


# --- indexing and basic search --------------------------------------------


class TestIndexAndSearch:
    def test_index_and_exact_title_search(self, index):
        index.index_product(_Product("p-1", "کود زیستی ارگانیک"))
        hits = index.search("کود زیستی ارگانیک")
        assert len(hits) == 1
        hit = hits[0]
        assert hit["product_id"] == "p-1"
        assert hit["title"] == "کود زیستی ارگانیک"
        assert isinstance(hit["rank"], float)
        assert hit["snippet"]

    def test_partial_word_search(self, index):
        index.index_product(_Product("p-1", "Organic Wheat"))
        index.index_product(_Product("p-2", "Basmati Rice"))
        assert [h["product_id"] for h in index.search("Whea")] == ["p-1"]

    def test_partial_word_search_persian(self, index):
        index.index_product(_Product("p-1", "کود زیستی ارگانیک"))
        assert [h["product_id"] for h in index.search("زیست")] == ["p-1"]

    def test_multi_word_search_requires_every_term(self, index):
        index.index_product(_Product("p-1", "کود زیستی ارگانیک", "برای مزارع"))
        index.index_product(_Product("p-2", "کود کشاورزی", "بدون واژه تخصصی"))
        hits = index.search("کود زیستی")
        assert [h["product_id"] for h in hits] == ["p-1"]
        # the single surviving term still finds both products
        assert len(index.search("کود")) == 2

    def test_persian_text_search(self, index):
        index.index_product(
            _Product(
                "p-fa",
                "کود زیستی ارگانیک",
                "کود طبیعی و زیستی برای مزارع روستایی",
                village_id="v-a",
            )
        )
        hits = index.search("کود زیستی")
        assert [h["product_id"] for h in hits] == ["p-fa"]
        assert "زیستی" in hits[0]["snippet"]

    def test_persian_query_finds_arabic_spelling(self, index):
        index.index_product(_Product("p-ar", "كود زيستي", "Arabic spelling"))
        index.index_product(_Product("p-zwnj", "کود‌زیستی", "ZWNJ compound"))
        assert sorted(h["product_id"] for h in index.search("کود زیستی")) == ["p-ar", "p-zwnj"]

    def test_search_matches_the_description_body(self, index):
        index.index_product(_Product("p-1", "Plain Title", "Saffron from Khorasan"))
        assert [h["product_id"] for h in index.search("saffron")] == ["p-1"]

    def test_empty_and_operator_only_queries_return_empty(self, index):
        index.index_product(_Product("p-1", "کود زیستی"))
        assert index.search("") == []
        assert index.search("   ") == []
        assert index.search("AND OR NOT ( ) *") == []

    def test_query_with_fts_punctuation_never_raises(self, index):
        index.index_product(_Product("p-1", "کود زیستی"))
        for raw in ['"کود"', "کود^2", 'کود AND "زیستی"', "کود:", "کود*"]:
            assert isinstance(index.search(raw), list)

    def test_indexing_a_product_without_id_is_rejected(self, index):
        class NoId:
            name = "کود زیستی"

        with pytest.raises(ValueError, match="without an id"):
            index.index_product(NoId())


# --- filters ----------------------------------------------------------------


class TestFilters:
    """Filters are SQL predicates on the FTS table, not Python post-filtering."""

    @pytest.fixture
    def index(self, index):
        index.index_product(
            _Product(
                "p-1",
                "کود زیستی",
                "برای مزارع",
                village_id="v-a",
                category="fertilizer",
                price=150000.0,
            )
        )
        index.index_product(
            _Product(
                "p-2",
                "کود کشاورزی",
                "برای باغ",
                village_id="v-b",
                category="fertilizer",
                price=40.0,
            )
        )
        index.index_product(
            _Product(
                "p-3",
                "کود ارگانیک",
                "بدون واژه زیستی",
                village_id="v-a",
                category="chemical",
                price=10.0,
            )
        )
        return index

    def test_village_filter(self, index):
        assert [h["product_id"] for h in index.search("کود", village_id="v-a")] == ["p-1", "p-3"]

    def test_category_filter(self, index):
        assert [h["product_id"] for h in index.search("کود", category="chemical")] == ["p-3"]

    def test_max_price_filter(self, index):
        assert [h["product_id"] for h in index.search("کود", max_price=50.0)] == ["p-2", "p-3"]

    def test_price_filter_excludes_null_prices(self, index):
        index.index_product(_Product("p-4", "کود بی‌قیمت", price=None))
        ids = [h["product_id"] for h in index.search("کود", max_price=200000.0)]
        assert "p-4" not in ids
        assert "p-1" in ids

    def test_filters_combine(self, index):
        hits = index.search("کود", village_id="v-a", category="fertilizer", max_price=200000.0)
        assert [h["product_id"] for h in hits] == ["p-1"]

    def test_filter_that_matches_nothing_returns_empty(self, index):
        assert index.search("کود", village_id="v-zzz") == []

    def test_filters_are_sql_predicates(self, index):
        """The generated statement must bind the filters as predicates."""
        sql, params = MarketplaceSearchService._build_sql(
            '"کود"*',
            village_id="v-a",
            category="fertilizer",
            max_price=200000.0,
            limit=5,
        )
        assert "WHERE products_fts MATCH ?" in sql
        assert "AND village_id = ?" in sql
        assert "AND category = ?" in sql
        assert "AND price <= ?" in sql
        assert "ORDER BY rank" in sql
        # every value is bound, never interpolated
        assert '"کود"*' not in sql
        assert "v-a" not in sql
        assert params[-4:] == ["v-a", "fertilizer", 200000.0, 5]

    def test_unfiltered_query_has_no_extra_predicates(self):
        sql, params = MarketplaceSearchService._build_sql(
            '"x"*', village_id=None, category=None, max_price=None, limit=20
        )
        assert "village_id = ?" not in sql
        assert "price <= ?" not in sql
        assert params[-1] == 20


# --- ranking ----------------------------------------------------------------


class TestRanking:
    def test_title_match_outranks_body_match(self, index):
        index.index_product(_Product("p-title", "Super Widget", "Unrelated body text here"))
        index.index_product(_Product("p-body", "Plain Thing", "Super Widget inside the body"))
        hits = index.search("super widget")
        assert [h["product_id"] for h in hits] == ["p-title", "p-body"]
        assert hits[0]["rank"] < hits[1]["rank"]

    def test_rank_is_a_negative_bm25_score(self, index):
        index.index_product(_Product("p-1", "Organic Wheat", "Golestan farms"))
        hit = index.search("organic wheat")[0]
        assert hit["rank"] < 0

    def test_ordering_is_best_first(self, index):
        index.index_product(_Product("p-1", "Super Widget", "Super Widget body"))
        index.index_product(_Product("p-2", "Plain Thing", "super widget inside"))
        ranks = [h["rank"] for h in index.search("super widget")]
        assert ranks == sorted(ranks)


# --- result shape -----------------------------------------------------------


class TestResultShape:
    def test_results_carry_the_filter_fields(self, index):
        index.index_product(
            _Product(
                "p-1",
                "کود زیستی ارگانیک",
                "body",
                village_id="v-a",
                category="fertilizer",
                price=Decimal("150000.00"),
                status="active",
            )
        )
        hit = index.search("کود")[0]
        assert hit == {
            "product_id": "p-1",
            "title": "کود زیستی ارگانیک",
            "rank": hit["rank"],
            "snippet": hit["snippet"],
            "village_id": "v-a",
            "category": "fertilizer",
            "price": 150000.0,
            "status": "active",
        }

    def test_title_keeps_its_original_spelling(self, index):
        index.index_product(_Product("p-1", "Organic Wheat"))
        assert index.search("wheat")[0]["title"] == "Organic Wheat"

    def test_limit_controls_the_result_count(self, index):
        for i in range(5):
            index.index_product(_Product(f"p-{i}", f"کود زیستی شماره {i}"))
        assert len(index.search("کود", limit=2)) == 2
        assert len(index.search("کود", limit=100)) == 5


class TestSnippet:
    def test_snippet_highlights_the_body_when_the_match_is_there(self, index):
        index.index_product(_Product("p-1", "Plain", "Saffron from Khorasan fields"))
        snippet = index.search("saffron")[0]["snippet"]
        assert "<mark>saffron</mark>" in snippet

    def test_snippet_falls_back_to_the_title(self, index):
        index.index_product(_Product("p-1", "Basmati Rice", "Long grain white rice"))
        snippet = index.search("basmati")[0]["snippet"]
        # the snippet highlights the normalised (indexed) title text
        assert "<mark>basmati</mark>" in snippet
        assert "rice" in snippet

    def test_snippet_marks_every_term_of_a_persian_query(self, index):
        index.index_product(_Product("p-1", "کود زیستی", "محصول مزرعه"))
        snippet = index.search("کود زیستی")[0]["snippet"]
        assert snippet.count("<mark>") == 2
        assert "کود" in snippet and "زیستی" in snippet


# --- index maintenance ------------------------------------------------------


class TestIndexMaintenance:
    def test_remove_product_drops_the_row(self, index):
        index.index_product(_Product("p-1", "کود زیستی", "برای مزارع"))
        index.remove_product("p-1")
        assert index.search("کود") == []

    def test_remove_of_unknown_product_is_a_no_op(self, index):
        index.index_product(_Product("p-1", "کود زیستی"))
        index.remove_product("never-existed")
        assert [h["product_id"] for h in index.search("کود")] == ["p-1"]

    def test_re_indexing_replaces_the_row(self, index):
        index.index_product(_Product("p-1", "کود زیستی", "توضیح قدیمی"))
        index.index_product(_Product("p-1", "گندم کامل", "توضیح تازه"))
        assert index.count() == 1
        assert index.search("کود") == []
        assert [h["product_id"] for h in index.search("گندم")] == ["p-1"]

    def test_rebuild_replaces_everything(self, index):
        index.index_product(_Product("p-1", "کود زیستی", "برای مزارع"))
        index.index_product(_Product("p-2", "Organic Wheat", "Golestan"))
        assert index.rebuild([_Product("p-3", "گندم کامل", "گندم ارگانیک")]) == 1
        assert index.count() == 1
        assert index.search("کود") == []
        assert [h["product_id"] for h in index.search("گندم")] == ["p-3"]

    def test_rebuild_from_empty_database(self, index):
        index.index_product(_Product("p-1", "کود زیستی"))
        assert index.rebuild([]) == 0
        assert index.search("کود") == []


class TestRebuildFromSession:
    """The index must be cold-startable from the ORM table itself."""

    @staticmethod
    def _products(seller_id: Any) -> list[MarketplaceProduct]:
        return [
            MarketplaceProduct(
                id="orm-1",
                seller_id=seller_id,
                name="کود زیستی ارگانیک",
                slug="kooad-zisti-organic",
                description="کود طبیعی و زیستی برای مزارع روستایی",
                category="fertilizer_organic",
                price=Decimal("150000.00"),
                village_id="v-a",
                status=MarketplaceProductStatus.ACTIVE,
            ),
            MarketplaceProduct(
                id="orm-2",
                seller_id=seller_id,
                name="گندم ارگانیک",
                slug="gandom-organic",
                description="گندم کامل از مزارع گلستان",
                category="grains",
                price=Decimal("250000.00"),
                village_id="v-b",
                status=MarketplaceProductStatus.ACTIVE,
            ),
            MarketplaceProduct(
                id="orm-3",
                seller_id=seller_id,
                name="برنج هاشمی",
                slug="berenj-hashemi",
                description="برنج ده‌دانه شمال",
                category="grains",
                price=Decimal("900000.00"),
                village_id="v-a",
                status=MarketplaceProductStatus.DRAFT,
            ),
        ]

    @staticmethod
    async def _seed_async(db_session) -> str:
        seller = MarketplaceSeller(village_id="v-a", user_id="u-1", shop_name="فروشگاه روستایی")
        db_session.add(seller)
        await db_session.commit()
        for product in TestRebuildFromSession._products(seller.id):
            db_session.add(product)
        await db_session.commit()
        return str(seller.id)

    @staticmethod
    def _seed_sync(db_session) -> str:
        seller = MarketplaceSeller(village_id="v-a", user_id="u-1", shop_name="فروشگاه روستایی")
        db_session.add(seller)
        db_session.commit()
        for product in TestRebuildFromSession._products(seller.id):
            db_session.add(product)
        db_session.commit()
        return str(seller.id)

    async def test_round_trip_from_an_async_session(self, async_session):
        await self._seed_async(async_session)

        index = MarketplaceSearchService()
        assert await index.rebuild_from_session(async_session) == 3
        assert index.count() == 3

        hits = index.search("کود زیستی")
        assert [h["product_id"] for h in hits] == ["orm-1"]
        assert hits[0]["village_id"] == "v-a"
        assert hits[0]["category"] == "fertilizer_organic"
        assert hits[0]["price"] == 150000.0
        assert hits[0]["status"] == "active"

        # the filters survive the round trip too
        assert [h["product_id"] for h in index.search("گندم", village_id="v-a")] == []
        assert [h["product_id"] for h in index.search("گندم", village_id="v-b")] == ["orm-2"]

        # a draft product is indexed and surfaced — status policy belongs to
        # the caller, never to the index
        assert [h["product_id"] for h in index.search("برنج")] == ["orm-3"]

    async def test_round_trip_from_a_sync_session(self, sync_session):
        self._seed_sync(sync_session)

        index = MarketplaceSearchService()
        assert await index.rebuild_from_session(sync_session) == 3

        hits = index.search("کود زیستی")
        assert [h["product_id"] for h in hits] == ["orm-1"]
        assert index.search("گندم", category="grains")[0]["product_id"] == "orm-2"


# --- singleton & persistence ------------------------------------------------


class TestSingletonAndPersistence:
    def test_get_search_service_returns_one_in_memory_index(self):
        first = get_search_service()
        second = get_search_service()
        assert first is second
        assert first.path == ":memory:"
        first.index_product(_Product("p-1", "کود زیستی"))
        assert [h["product_id"] for h in second.search("کود")] == ["p-1"]

    def test_persistent_index_survives_a_reopen(self, tmp_path):
        path = tmp_path / "marketplace" / "products_fts.db"
        writer = MarketplaceSearchService(path=str(path))
        try:
            writer.index_product(_Product("p-1", "Persistent Honey", "عسل طبیعی"))
            assert writer.count() == 1
        finally:
            writer.close()

        reader = MarketplaceSearchService(path=str(path))
        try:
            assert reader.count() == 1
            assert [h["title"] for h in reader.search("honey")] == ["Persistent Honey"]
        finally:
            reader.close()

    def test_reset_clears_the_singleton(self):
        first = get_search_service()
        reset_search_service()
        assert get_search_service() is not first
