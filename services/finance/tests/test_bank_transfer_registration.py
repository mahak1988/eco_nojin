"""Registration lifecycle of the finance ``bank_transfer`` provider.

``POST /api/v1/finance/payments/intent?provider=bank_transfer`` must work
without an order flow having constructed an ``OrderService`` (the only other
writer to ``payment_registry``), so the provider is registered while
``services.finance.routers.finance`` is imported. That registration used to
resolve the hub's async engine and build an ``AsyncSession`` at *import* time,
which is an ordering hazard: the engine is bound to the event loop that happens
to be running (or to no loop at all during collection), so the session built on
it is stale for every later request, and the import itself fails when the hub
engine is not initialised yet — an intermittent full-suite collection error.

These tests pin the repaired behaviour:

* importing the module — twice, re-executed, or in a fresh process — performs no
  database side effects and cannot raise;
* the provider is registered exactly once and stays idempotent;
* an intent is created (200) and persisted as a ``ComPaymentIntent``;
* a failed intent leaves nothing behind: the next intent is still 200.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

import services.finance.routers.finance as finance_router
from database.hub import hub
from database.models import ComPaymentIntent
from services.api_gateway.auth import get_current_user
from services.finance.payment_provider import BankTransferProvider, payment_registry

#: Repository root, derived from the module under test so the subprocess below
#: imports the very same copy of ``services`` the running tests do.
_ROOT = Path(finance_router.__file__).resolve().parents[3]

_INTENT_URL = "/api/v1/finance/payments/intent"

#: Runs in a brand-new interpreter: the strongest statement that importing the
#: router resolves nothing on the database hub, that re-executing the module
#: (a reload) registers the provider exactly once, and that both happen without
#: an engine ever being built.
_IMPORT_SNIPPET = (
    "import importlib\n"
    "import database.hub as hub\n"
    "import services.finance.routers.finance as finance\n"
    "names = [p.provider_name for p in finance.payment_registry.get_all()]\n"
    "assert 'bank_transfer' in names, names\n"
    "provider = finance.payment_registry.get('bank_transfer')\n"
    "assert isinstance(provider, finance.BankTransferProvider), provider\n"
    "importlib.reload(finance)\n"
    "names = [p.provider_name for p in finance.payment_registry.get_all()]\n"
    "assert names.count('bank_transfer') == 1, names\n"
    "assert finance.payment_registry.get('bank_transfer') is provider\n"
    "assert hub._async_engine is None, 'importing the router created the async engine'\n"
    "print('ok')\n"
)


def _provider_names() -> list[str]:
    return [provider.provider_name for provider in payment_registry.get_all()]


async def _post_intent(app: FastAPI, order_id: str) -> object:
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        return await client.post(
            _INTENT_URL,
            json={
                "amount": 150000,
                "currency": "IRR",
                "order_id": order_id,
                "provider": "bank_transfer",
            },
        )


async def _read_intent(intent_id: str) -> ComPaymentIntent | None:
    async with hub.get_async_session() as session:
        return await session.get(ComPaymentIntent, intent_id)


@pytest.fixture
def finance_app() -> FastAPI:
    """Minimal app on the real router and the real hub session.

    ``get_db`` is intentionally *not* overridden: the provider resolves its own
    session per call, which is the behaviour under test, and both then land in
    the same shared-cache database.
    """
    app = FastAPI()
    app.include_router(finance_router.router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="u1", role="user")

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def _server_error_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    return app


# ===========================================================================
# (a) Import is side-effect free and cannot fail
# ===========================================================================


def test_import_in_a_fresh_process_registers_without_touching_the_engine():
    """A cold interpreter imports, registers, and never builds an engine."""
    environment = dict(os.environ)
    existing = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(_ROOT), existing) if part
    )

    completed = subprocess.run(
        [sys.executable, "-c", _IMPORT_SNIPPET],
        cwd=str(_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert completed.returncode == 0, completed.stderr
    assert "ok" in completed.stdout


def test_repeated_import_does_not_raise_or_duplicate():
    module = importlib.import_module("services.finance.routers.finance")
    before = payment_registry.get("bank_transfer")

    assert importlib.import_module("services.finance.routers.finance") is module
    # A second execution (a reload, or a fresh interpreter) re-runs the
    # registration; the registry must still hold the provider exactly once.
    finance_router._ensure_bank_transfer_registered()

    assert _provider_names().count("bank_transfer") == 1
    assert payment_registry.get("bank_transfer") is before


def test_registered_provider_is_usable_before_any_order_service():
    provider = payment_registry.get("bank_transfer")
    assert isinstance(provider, BankTransferProvider)
    assert provider.provider_name == "bank_transfer"


# ===========================================================================
# (b) Registration through the payment-intent path
# ===========================================================================


@pytest.mark.asyncio
async def test_intent_request_registers_the_provider_exactly_once(finance_app):
    """The route re-registration is a no-op once the provider is present."""
    finance_router._ensure_bank_transfer_registered()
    finance_router._ensure_bank_transfer_registered()

    response = await _post_intent(finance_app, "ord-bt-registration")

    assert response.status_code == 200, response.text
    assert _provider_names().count("bank_transfer") == 1


@pytest.mark.asyncio
async def test_payment_intent_is_created_and_persisted(finance_app):
    response = await _post_intent(finance_app, "ord-bt-persist")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["provider"] == "bank_transfer"
    assert body["status"] == "awaiting_transfer"
    assert Decimal(body["amount"]) == Decimal("150000")
    assert body["metadata"]["reference_number"].startswith("BT-")

    row = await _read_intent(body["id"])
    assert row is not None
    assert row.provider == "bank_transfer"
    assert row.status == "awaiting_transfer"
    assert row.order_id == "ord-bt-persist"
    assert Decimal(str(row.amount)) == Decimal("150000.00000000")


@pytest.mark.asyncio
async def test_failed_request_does_not_poison_the_next_intent(finance_app, monkeypatch):
    """A failure inside the provider must not leave the next intent failing."""
    original = BankTransferProvider._to_dataclass
    calls = {"n": 0}

    def _flaky_dataclass(self, payment, metadata):
        """Fail once, after the intent row has been committed."""
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated failure after commit")
        return original(self, payment, metadata)

    monkeypatch.setattr(BankTransferProvider, "_to_dataclass", _flaky_dataclass)

    failed = await _post_intent(finance_app, "ord-bt-poison-1")
    assert failed.status_code == 500, failed.text

    recovered = await _post_intent(finance_app, "ord-bt-poison-2")
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()["status"] == "awaiting_transfer"
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_failed_transaction_does_not_poison_the_provider():
    """A rolled-back statement leaves no session behind to be poisoned.

    ``payment_metadata`` is a JSON column, so a value the serializer rejects
    aborts the transaction on the first attempt; the second, valid intent must
    still be created and persisted on a fresh session.
    """
    provider = payment_registry.get("bank_transfer")

    with pytest.raises(Exception):  # noqa: B017, PT011 - the exact json/json error type varies
        await provider.create_payment_intent(
            amount=Decimal("1000"),
            currency="IRR",
            order_id="ord-bt-bad-metadata",
            metadata={"unserialisable": object()},
            idempotency_key="key-bt-bad-metadata",
        )

    intent = await provider.create_payment_intent(
        amount=Decimal("1000"),
        currency="IRR",
        order_id="ord-bt-after-failure",
        metadata={},
        idempotency_key="key-bt-after-failure",
    )

    assert intent.status == "awaiting_transfer"
    row = await _read_intent(intent.id)
    assert row is not None
    assert row.order_id == "ord-bt-after-failure"
