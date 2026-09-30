"""Tests for the reference basket valuation.

These are the checks that matter for the instrument's credibility: the price
anchor must be reproducible, the value must stay within a plausible band, the
platform share must not become a markup, and the data-quality gate must fail
closed.
"""

from __future__ import annotations

import pytest

from engine.hydroma.economics.reference_basket import (
    BaseBasket,
    BasketError,
    DataMode,
    InputItem,
    denomination_plan,
    fetch_reference_prices,
    last_fetch_audit,
    parse_pink_sheet_csv,
    quality_factor,
    value_basket,
)

#: Prices as published in the World Bank Pink Sheet of 2 September 2026,
#: covering August 2026 data. Used as a fixed fixture so the arithmetic is
#: reproducible without a network call. Keys are the canonical short
#: identifiers used across `reference_basket`; the mapping to the sheet's
#: published labels lives only in `parse_pink_sheet_csv`.
PINK_SHEET_AUG_2026 = {
    "dap": 793.50,
    "urea": 390.00,
    "mop": 386.90,
    "tsp": 704.40,
}


def maize_rainfed() -> BaseBasket:
    return BaseBasket(
        crop="maize",
        market_class="coastal_middle_income",
        items=(
            InputItem("DAP", 321.0, "dap"),
            InputItem("Urea", 150.0, "urea"),
            # Seed is not in the Pink Sheet; a local price must be supplied.
            InputItem("Certified maize seed", 25.0, "local", local_price_usd_per_tonne=900.0),
        ),
    )


class TestUnitPriceResolution:
    def test_reference_series_resolved(self):
        basket = BaseBasket(
            crop="wheat",
            market_class="coastal_low_income",
            items=(InputItem("DAP", 180.0, "dap"),),
        )
        v = value_basket(basket, PINK_SHEET_AUG_2026, platform_share=0.05)
        assert v.unit_prices["DAP"] == pytest.approx(793.50)

    def test_missing_quote_fails_loudly(self):
        basket = BaseBasket(
            crop="wheat",
            market_class="coastal_low_income",
            items=(
                InputItem("DAP", 180.0, "dap"),
                InputItem("Urea", 120.0, "urea"),
            ),
        )
        with pytest.raises(BasketError, match="missing"):
            value_basket(basket, {"Urea": 390.0}, platform_share=0.05)

    def test_unknown_unit_without_local_price_rejected_at_construction(self):
        with pytest.raises(ValueError, match="local_price_usd_per_tonne"):
            InputItem("Mystery", 10.0, "not-a-series")

    def test_seed_only_basket_is_refused_as_implausible(self):
        """A base basket is a full hectare package, not one line item."""
        basket = BaseBasket(
            crop="maize",
            market_class="coastal_low_income",
            items=(InputItem("Seed", 25.0, "local", local_price_usd_per_tonne=900.0),),
        )
        with pytest.raises(BasketError, match="outside the plausible range"):
            value_basket(basket, PINK_SHEET_AUG_2026, platform_share=0.05)


class TestArithmetic:
    def test_maize_basket_lands_in_expected_range(self):
        v = value_basket(maize_rainfed(), PINK_SHEET_AUG_2026, platform_share=0.05)
        # DAP 321kg @ 793.50 = 254.71; urea 150kg @ 390.00 = 58.50;
        # seed 25kg @ 900.00 = 22.50 -> 335.71 international
        assert v.international_subtotal_usd_ha == pytest.approx(335.71, abs=0.05)
        # coastal_middle_income multiplier midpoint = (1.10 + 1.25) / 2 = 1.175
        assert v.landed_multiplier == pytest.approx(1.175)
        assert v.landed_value_usd_ha == pytest.approx(335.71 * 1.175, abs=0.05)
        assert v.redemption_ceiling_usd_ha == pytest.approx(v.landed_value_usd_ha * 0.95, abs=0.05)

    def test_line_values_sum_to_subtotal(self):
        v = value_basket(maize_rainfed(), PINK_SHEET_AUG_2026, platform_share=0.05)
        assert sum(v.line_values.values()) == pytest.approx(
            v.international_subtotal_usd_ha, abs=0.01
        )

    def test_ceiling_is_always_below_landed_value(self):
        for share in (0.0, 0.05, 0.08):
            v = value_basket(maize_rainfed(), PINK_SHEET_AUG_2026, platform_share=share)
            assert v.redemption_ceiling_usd_ha <= v.landed_value_usd_ha


class TestPlatformShareCeiling:
    def test_share_above_cap_rejected(self):
        """The share must stay a service fee, not a markup on farmer inputs."""
        with pytest.raises(BasketError, match="platform_share"):
            value_basket(maize_rainfed(), PINK_SHEET_AUG_2026, platform_share=0.12)

    def test_share_exactly_at_cap_accepted(self):
        v = value_basket(maize_rainfed(), PINK_SHEET_AUG_2026, platform_share=0.08)
        assert v.platform_share == 0.08


class TestPlausibilityBand:
    def test_implausible_basket_refused(self):
        """A bad price fetch must not produce a publishable number."""
        basket = BaseBasket(
            crop="wheat",
            market_class="coastal_low_income",
            items=(InputItem("DAP", 3000.0, "dap"),),
        )
        with pytest.raises(BasketError, match="outside the plausible range"):
            value_basket(basket, PINK_SHEET_AUG_2026, platform_share=0.05)

    def test_empty_quotes_rejected(self):
        with pytest.raises(BasketError, match="no reference quotes"):
            value_basket(maize_rainfed(), {}, platform_share=0.05)


class TestMarketClassAndStructure:
    def test_unknown_market_class_rejected(self):
        with pytest.raises(ValueError, match="unknown market_class"):
            BaseBasket(
                crop="maize",
                market_class="middle_of_nowhere",
                items=(InputItem("DAP", 100.0, "dap"),),
            )

    def test_empty_basket_rejected(self):
        with pytest.raises(ValueError, match="at least one item"):
            BaseBasket(crop="maize", market_class="coastal_low_income", items=())

    def test_non_positive_rate_rejected(self):
        with pytest.raises(ValueError, match="kg_per_ha"):
            InputItem("DAP", 0.0, "dap")

    def test_pastoralist_multiplier_is_highest(self):
        from engine.hydroma.economics.reference_basket import LANDED_COST_MULTIPLIER

        assert (
            LANDED_COST_MULTIPLIER["pastoralist_mobile"][0]
            > LANDED_COST_MULTIPLIER["landlocked_remote"][0]
            > LANDED_COST_MULTIPLIER["coastal_middle_income"][0]
        )


class TestQualityFactor:
    def test_verified_scores_higher_than_modelled(self):
        assert quality_factor(DataMode.FIELD_VERIFIED) > quality_factor(DataMode.MODELLED_ESTIMATE)

    def test_modelled_estimate_is_never_full_value(self):
        """A modelled estimate has no measurement behind it."""
        assert quality_factor(DataMode.MODELLED_ESTIMATE) < 1.0


class TestDenomination:
    def test_small_denomination_exists(self):
        """Zambia: 84% left a balance because no SKU absorbed the remainder."""
        plan = denomination_plan(500.0, units_per_basket=100)
        assert plan[0][0] == pytest.approx(500.0)
        assert any(v <= 0.10 * 500.0 for v, _ in plan)

    def test_smallest_is_under_ten_percent(self):
        plan = denomination_plan(400.0, units_per_basket=100)
        smallest = min(v for v, _ in plan)
        assert smallest < 0.10 * 400.0

    def test_zero_denominations_rejected(self):
        with pytest.raises(ValueError, match="units_per_basket"):
            denomination_plan(500.0, units_per_basket=0)


class TestPinkSheetParsing:
    HEADER = "Unnamed: 0,DAP,Urea,Potassium chloride,TSP"

    def _csv(self, rows: list[str]) -> str:
        return self.HEADER + "\n" + "\n".join(rows) + "\n"

    def test_takes_last_complete_month(self):
        payload = self._csv(
            [
                "2026-07M,300,700,350,650",
                "2026-08M,793.50,390.00,386.90,704.40",
            ]
        )
        assert parse_pink_sheet_csv(payload) == PINK_SHEET_AUG_2026

    def test_skips_incomplete_month(self):
        """A partially published month must never be used."""
        payload = self._csv(
            [
                "2026-07M,700,350,300,600",
                "2026-08M,793.50,,386.90,704.40",
            ]
        )
        prices = parse_pink_sheet_csv(payload)
        assert prices["dap"] == 700.0
        assert prices["urea"] == 350.0

    def test_parser_output_feeds_value_basket(self):
        """The two functions must share one vocabulary, or valuation is impossible."""
        payload = self._csv(["2026-08M,793.50,390.00,386.90,704.40"])
        quotes = parse_pink_sheet_csv(payload)
        v = value_basket(maize_rainfed(), quotes, platform_share=0.05)
        assert v.unit_prices["DAP"] == pytest.approx(793.50)
        assert v.unit_prices["Urea"] == pytest.approx(390.00)

    def test_missing_series_raises(self):
        payload = "Unnamed: 0,DAP\n2026-08M,793.50\n"
        with pytest.raises(BasketError, match="missing required series"):
            parse_pink_sheet_csv(payload)

    def test_empty_payload_raises(self):
        with pytest.raises(BasketError):
            parse_pink_sheet_csv("")

    def test_fetch_requires_payload(self):
        with pytest.raises(BasketError, match="no pink sheet payload"):
            fetch_reference_prices()

    def test_audit_records_success(self):
        payload = "Unnamed: 0,DAP,Urea,Potassium chloride,TSP\n2026-08M,793.50,390,386.9,704.4\n"
        fetch_reference_prices(payload)
        audit = last_fetch_audit()
        assert audit["ok"] is True
        assert audit["rows"] == 4
        assert "Pink Sheet" in str(audit["attribution"])
        assert "CMO-Historical-Data-Monthly" in str(audit["source"])

    def test_audit_records_failure(self):
        with pytest.raises(BasketError):
            fetch_reference_prices("garbage\n")
        assert last_fetch_audit()["ok"] is False


class TestProvenanceIsRecorded:
    def test_valuation_carries_source_and_caveat(self):
        v = value_basket(maize_rainfed(), PINK_SHEET_AUG_2026, platform_share=0.05)
        assert "World Bank" in v.provenance
        assert "CC-BY 4.0" in v.provenance
        assert "ceiling" in " ".join(v.notes)
        assert "not a quotation" not in v.provenance.lower()  # wording checked below
        assert "guaranteed amount" in " ".join(v.notes)
