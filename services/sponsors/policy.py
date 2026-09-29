"""Sponsorship policy.

The single place that decides whether a sponsorship may exist, be activated,
and be served in a given location. Every other module consults this file rather
than re-implementing the rules, so a placement guard in the frontend and a
check in the admin API cannot disagree.

Why the rules are this strict
-----------------------------
The project's own evidence base argues against advertising on a smallholder
advisory surface. Independent research found that tool-type applications are
the least tolerant category of forced ad formats, and that organisations
holding non-profit status are penalised harder than commercial firms when
users perceive a trust breach. The floor for this platform is therefore
behaviour, not severity: the guidance is that an intrusive, targeted format
costs more trust than it earns.

So the design is a *labelled sponsor*, never an ad:
* no ad network, no third-party SDK, no impression field, no user targeting;
* contextual placement only, derived from the page, never from the reader;
* a permanent, unremovable disclosure string;
* no placement on any surface that produces an agronomic recommendation.
"""

from __future__ import annotations

#: Sectors the project will not accept money from. This is a hard exclusion,
#: not a review criterion: a sponsor in one of these categories is rejected at
#: activation regardless of the money offered.
#:
#: The petrochemical, synthetic-fertiliser and pesticide entries are not
#: arbitrary. They are the categories a pastoralist-facing advisory surface
#: would be least credible carrying, and a sponsor on that surface damages
#: the product's central claim rather than its reputation.
FORBIDDEN_CATEGORIES: frozenset[str] = frozenset(
    {
        "fossil_fuel",
        "petrochemical",
        "synthetic_fertilizer",
        "pesticide",
        "extractive_industry",
        "tobacco",
        "alcohol",
        "gambling",
        "adult",
        "weapons",
        "data_extraction",
        "surveillance_sales",
        "predatory_lending",
        "binary_options",
    }
)

#: Route prefixes that may never carry a sponsor slot.
#:
#: The two groups have different reasons. The first is agronomic: these are
#: the surfaces that produce a recommendation a farmer acts on, and contaminating
#: them would void the project's central claim. The second is transactional:
#: money-handling and settlement surfaces. The third is sensory: low-bandwidth
#: channels where any slot is an intrusion.
FORBIDDEN_PLACEMENT_PREFIXES: tuple[str, ...] = (
    # Agronomic recommendation surfaces
    "/hydroma",
    "/virtual-lab",
    "/simulator",
    "/simulators",
    "/models",
    "/advisor",
    # Transactional and settlement surfaces
    "/checkout",
    "/wallet",
    "/escrow",
    "/orders",
    # Account surfaces
    "/settings",
    "/profile",
    "/admin",
    # Low-bandwidth channels: a slot here is an intrusion, not a placement
    "/telecom",
    "/ussd",
    "/voice",
    "/simple",
    "/offline",
)

#: Directives that may not be added without changing policy first.
FORBIDDEN_PLACEMENTS: tuple[str, ...] = FORBIDDEN_PLACEMENT_PREFIXES

#: Visual budget. A sponsor slot must never be able to out-shout content.
MAX_VISUAL_WEIGHT_PCT = 12
#: At most one sponsor per placement. A rotation would turn the slot into
#: advertising, which is the thing this design exists to avoid.
MAX_SPONSORS_PER_PLACEMENT = 1
#: Platform share ceiling, as a fraction of the annual sponsorship amount.
#: A per-slot service fee above this starts to look like a markup on farmer
#: inputs, and the pricing module enforces the same ceiling.
MAX_PLATFORM_SHARE = 0.08

#: Sponsors are re-screened on this cadence. Aligns with the quarterly green
#: claims attestation in the sustainability plan.
REVIEW_INTERVAL_DAYS = 90

#: A sponsorship that ends is removed from the slot on this day. Serving an
#: expired sponsor is the most likely silent failure, so the service refuses
#: rather than relying on a scheduled job.
EXPIRY_GRACE_DAYS = 0


class PolicyViolation(PermissionError):
    """Raised when a sponsorship breaks a rule that cannot be waived."""


def assert_placement_allowed(pathname: str) -> None:
    """Refuse a slot on a protected surface.

    Called from the API when a placement is registered, and mirrored by a
    Vitest guard that scans the frontend tree, so neither side can drift.
    """
    clean = pathname.rstrip("/") or "/"
    for prefix in FORBIDDEN_PLACEMENT_PREFIXES:
        if clean == prefix or clean.startswith(f"{prefix}/"):
            raise PolicyViolation(
                f"a sponsor slot is not permitted on {pathname!r}: it is under "
                f"the protected prefix {prefix!r}. See "
                f"services/sponsors/policy.py for why."
            )


def assert_category_allowed(sponsor_category: str | None) -> None:
    """Refuse a forbidden sector outright."""
    if sponsor_category is None:
        return
    key = sponsor_category.strip().lower()
    if key in FORBIDDEN_CATEGORIES:
        raise PolicyViolation(
            f"sponsor category {sponsor_category!r} is excluded from this "
            f"project. See services/sponsors/policy.py FORBIDDEN_CATEGORIES."
        )


def assert_platform_share_ok(share: float) -> None:
    """A sponsor fee above the ceiling is a markup on farmer-facing services."""
    if not 0.0 <= share <= MAX_PLATFORM_SHARE:
        raise PolicyViolation(
            f"platform share {share!r} is outside 0.0-{MAX_PLATFORM_SHARE}. "
            f"A higher share makes the instrument a markup on farmer inputs."
        )


def disclosure_key(sponsor_name: str) -> str:
    """The i18n key for the disclosure string, per locale.

    Kept here so the API and the component cannot produce different wording,
    which is exactly the kind of drift that turns a labelled sponsorship back
    into a hidden ad.
    """
    return f"sponsors.slot.disclosure::{sponsor_name}"
