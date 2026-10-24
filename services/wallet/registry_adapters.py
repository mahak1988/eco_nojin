"""Registry adapter interface — the plug-in point, with nothing plugged in.

From ``reports/CREDIT_VALUE_ARCHITECTURE_FA_2026-10-02.md`` layer 3. This
module exists so that choosing a carbon registry becomes a *configuration and
compliance* decision rather than an engineering one, and so that the choice is
never implicit.

**No adapter ships here.** That is the point. With nothing configured,
``resolve_attester()`` returns ``None``, ``CreditService`` issues
``SELF_REPORTED`` credits, and ``standard_code`` stays ``NULL`` — which is the
zero-legal-risk state documented in ``docs/decisions/DEC-0001_REWARD_ONLY_VALUE_INSTRUMENT_FA.md``.

Adding one is deliberately a two-part commitment so it cannot happen by accident:

1. set ``CARBON_REGISTRY_ADAPTER`` in the environment, and
2. pass ``resolve_attester()`` into ``CreditService``.

Step 1 without 2 does nothing; step 2 without 1 returns ``None``. Neither alone
can promote a self-reported credit.

Why a serial number is mandatory
--------------------------------

A registry issues a serial for every credit it issues; an attester that cannot
return one is not an attester for this table. ``CreditService`` enforces that,
because the alternative — letting a caller pass ``standard_code`` as a string —
is the exact defect this system replaced.
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Protocol

from services.wallet.credits import Attestation

#: Environment variable naming the adapter. No default: an unconfigured system
#: has no registry, which is the correct default rather than an oversight.
ENV_ADAPTER = "CARBON_REGISTRY_ADAPTER"

#: Adapters this build knows how to load. Empty by design — see the module
#: docstring. A registry is a contractual and legal relationship, not a library
#: dependency, and it cannot be selected without that relationship existing.
KNOWN_ADAPTERS: dict[str, str] = {}


class NotConfigured(RuntimeError):
    """An adapter was named that this build does not contain."""


class Adapter(Protocol):
    """What every adapter must be able to do.

    Note the shape of ``attest``: it may return ``None``. A registry that
    declines to attest a particular project is a normal outcome, and treating
    that as an error would push an adapter toward returning something it does
    not have.
    """

    name: str

    async def attest(
        self, *, project_ref: str, tonnes_co2e: Decimal, evidence_digest: str
    ) -> Attestation | None: ...


def load_adapter(name: str | None = None) -> Adapter | None:
    """Return the configured adapter, or ``None``.

    ``None`` is returned — never raised — when nothing is configured, because
    "no registry yet" is the normal operating state and callers must not need a
    try/except to do the ordinary thing.

    A *named but unknown* adapter raises, because that is a configuration error
    rather than an absence: a deployment that set ``CARBON_REGISTRY_ADAPTER`` has
    asserted something about itself that is not true, and silently downgrading
    that to self-reported would hide it.
    """
    configured = (name or os.getenv(ENV_ADAPTER, "") or "").strip()
    if not configured:
        return None
    if configured not in KNOWN_ADAPTERS:
        raise NotConfigured(
            f"{ENV_ADAPTER}={configured!r}, but this build ships no such adapter. "
            f"Known: {sorted(KNOWN_ADAPTERS) or 'none'}. Deployments without a "
            "registry relationship must leave this unset."
        )
    raise NotConfigured(  # pragma: no cover - unreachable while KNOWN_ADAPTERS is empty
        f"{configured!r} is declared but has no loader"
    )


def resolve_attester() -> Adapter | None:
    """The entry point callers pass to ``CreditService(attester=...)``."""
    return load_adapter()


# --------------------------------------------------------------------------
# Template for whoever adds a real adapter. Kept as a string, not as code, so it
# cannot be mistaken for an implementation or imported by accident.
# --------------------------------------------------------------------------

ADAPTER_TEMPLATE = '''
class {Name}Adapter:
    """{Registry} adapter. DELETE THIS DOCSTRING and state the contract you
    actually hold with them, with a date and a reference."""

    name = "{slug}"

    def __init__(self, client: "{Registry}Client") -> None:
        self._client = client

    async def attest(
        self, *, project_ref: str, tonnes_co2e: Decimal, evidence_digest: str
    ) -> Attestation | None:
        response = await self._client.issue(project_ref, tonnes_co2e)

        if response is None:
            # The registry declined. Not an error.
            return None

        return Attestation(
            serial_number=response.serial,
            standard_code="{standard_code}",
            reference=f"{registry_url}/{response.serial}",
        )
'''
