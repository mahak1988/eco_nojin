"""Regression guard for village-hub route shadowing (P0-5).

``GET /{village_id}`` used to be the first route registered on the
``/api/v1/marketplace/villages`` router, so their global literal paths matched
it before their own handlers ever ran:

    GET .../opportunities        -> village_id="opportunities"        -> 404
    GET .../entrepreneurs        -> village_id="entrepreneurs"        -> 404
    GET .../investments          -> village_id="investments"          -> 404
    GET .../nomadic-communities  -> village_id="nomadic-communities"  -> 404

Each of those requests fell through to ``get_village_profile`` ->
``_verify_village_exists`` (a nonexistent "village") and 404'd, leaving the four
literal handlers -- most visibly the nomadic-community listing -- dead at the
API layer.

Starlette resolves routes in registration order, so the fix registers every
literal-path route before any parameterized ``/{village_id}`` route. These tests
match routes exactly as Starlette's router does (first full path+method match in
registration order) and need no database.
"""

from __future__ import annotations

import pytest

from services.api_gateway.routers import village_hub as vh

_PREFIX = vh.router.prefix  # "/api/v1/marketplace/villages"

# Global literal path suffix -> the handler that must own it.
GLOBAL_LITERALS = {
    "/opportunities": "search_opportunities",
    "/entrepreneurs": "search_entrepreneurs",
    "/investments": "get_my_investments",
    "/nomadic-communities": "list_nomadic_communities",
}


def _routes():
    return [
        r
        for r in vh.router.routes
        if hasattr(r, "path") and r.path.startswith(_PREFIX)
    ]


def _full_match_route(routes, path):
    """First route Starlette would dispatch a ``GET path`` request to.

    Mirrors the Starlette router: walk routes in registration order and return
    the first whose compiled regex matches ``path`` AND whose methods include
    GET (a full match). Path-only / wrong-method matches are ignored because
    these endpoints are all served by ``GET``.
    """
    for route in routes:
        if route.path_regex.match(path) and "GET" in getattr(route, "methods", set()):
            return route
    return None


def _suffix(route_path):
    return route_path[len(_PREFIX) :]


@pytest.mark.parametrize("suffix,expected", GLOBAL_LITERALS.items())
def test_global_literal_route_is_not_shadowed(suffix, expected):
    route = _full_match_route(_routes(), _PREFIX + suffix)
    assert route is not None, f"no GET route matches {_PREFIX}{suffix}"
    assert route.endpoint.__name__ == expected, (
        f"{_PREFIX}{suffix} resolved to {route.endpoint.__name__}, "
        f"expected the literal handler {expected}"
    )


@pytest.mark.parametrize("suffix", GLOBAL_LITERALS.keys())
def test_matched_route_is_literal_not_parameterized(suffix):
    route = _full_match_route(_routes(), _PREFIX + suffix)
    assert route is not None
    assert not _suffix(route.path).startswith("/{"), (
        f"{_PREFIX}{suffix} matched the parameterized route {route.path}"
    )


def test_nomadic_community_listing_is_reachable():
    route = _full_match_route(_routes(), _PREFIX + "/nomadic-communities")
    assert route is not None
    assert route.endpoint.__name__ == "list_nomadic_communities"
    assert route.endpoint.__name__ != "get_village_profile"


def test_dynamic_village_id_still_resolves_to_profile():
    route = _full_match_route(_routes(), _PREFIX + "/SOME-VILLAGE-ID")
    assert route is not None
    assert route.endpoint.__name__ == "get_village_profile"


def test_every_literal_route_precedes_every_parameterized_route():
    registered = _routes()
    literal_idx = [i for i, r in enumerate(registered) if not _suffix(r.path).startswith("/{")]
    param_idx = [i for i, r in enumerate(registered) if _suffix(r.path).startswith("/{")]
    assert literal_idx and param_idx, "expected both literal and parameterized routes"
    assert max(literal_idx) < min(param_idx), (
        "a literal path route is registered after a parameterized /{village_id} route"
    )


def test_total_route_count_unchanged():
    # 49 routes after the wave-1 shadowing fix, + 4 nomadic-community routes
    # (GET/PUT/DELETE /nomadic-communities/{id} and PATCH .../approve)
    # introduced by the P1-10 nomadic workflow.
    # + 2 Phase 9 B2B routes (/b2b/demands and /b2b/matches/confirm)
    assert len(_routes()) == 55
