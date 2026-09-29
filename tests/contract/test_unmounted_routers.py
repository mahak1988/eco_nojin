"""Phase 5 — a router that is defined but never included is a router that does
not exist, and the gap was invisible.

Three routers could be imported cleanly and none of them appeared in any
``include_router`` call, so no request could ever reach them. The failure mode
is not a crash: a defined ``APIRouter`` is silently inert, which means a whole
security surface, a carbon audit queue and a lineage API all read as
"implemented" in any code search while serving nothing.

The three did not deserve the same fate, and the evidence decided it rather
than taste:

  * ``security_router`` — three real handlers over live state, no conflicting
    path. Mounted.
  * ``audit`` — five real handlers driving SECURITY DEFINER RPCs whose SQL
    ships in ``supabase/migrations/0006_audit_credits.sql``. Mounted.
  * ``provenance`` — left unmounted, and asserted here so the decision is
    recorded rather than left ambiguous. See
    ``TestProvenanceStaysUnmounted``.

Mounting ``security_router`` also exposed a lie. Its ``/status`` payload
declared ``"csp": "self + free data providers"``, which describes the policy in
``services/security/headers.py`` — a middleware that is *not* mounted. The
middleware that is mounted declares no Content-Security-Policy at all, so the
endpoint asserted a header the gateway never sent. The field is now read from
the mounted class, and ``TestSecurityStatusDoesNotLie`` pins it to the wire.
"""

from __future__ import annotations

import ast
import collections
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
SECURITY_ROUTER_SRC = ROOT / "services" / "api_gateway" / "routers" / "security_router.py"
PROVENANCE_ROUTER_SRC = ROOT / "services" / "provenance" / "router.py"

CSP_HEADER = "content-security-policy"

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}

#: The shape of a real CSP policy value, as opposed to a header name. Matching
#: a directive is what distinguishes a hardcoded policy from the lookup key.
_CSP_DIRECTIVE = re.compile(
    r"default-src|script-src|style-src|frame-ancestors|unsafe-inline", re.IGNORECASE
)

#: Node types that open a docstring.
_DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _code_strings(tree: ast.Module) -> list[ast.Constant]:
    """Every string constant that is *not* a docstring.

    Docstrings are excluded deliberately: this file and ``security_router.py``
    both quote the old hardcoded policy while explaining that it was removed,
    and a guard that matched prose would fail on its own documentation.
    """
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, _DOCSTRING_OWNERS):
            continue
        body = getattr(node, "body", None)
        if (
            isinstance(body, list)
            and body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            docstrings.add(id(body[0].value))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


@pytest.fixture(scope="module")
def app():
    from services.api_gateway.main import app as fastapi_app

    return fastapi_app


@pytest.fixture(scope="module")
def paths(app) -> dict:
    """The served path table.

    Read from the OpenAPI schema rather than ``app.routes``: this FastAPI
    version represents an included router as a single lazy ``_IncludedRouter``
    wrapper, so ``app.routes`` shows 84 entries for an app serving 497 paths
    and cannot answer "is this router mounted" on its own.
    """
    return app.openapi()["paths"]


class TestSecurityRouterIsMounted:
    def test_all_three_paths_are_served(self, paths):
        served = set(paths)
        for path in (
            "/api/v1/security/status",
            "/api/v1/security/anti-phishing",
            "/api/v1/security/events",
        ):
            assert path in served, (
                f"{path} is defined in security_router.py but not served. A router "
                f"that is never included is not a weaker feature, it is no feature."
            )

    def test_it_does_not_shadow_the_passkey_routes(self, paths):
        """``passkey_router`` already owns part of this prefix.

        Mounting beside it is only safe because neither router declares a
        catch-all under ``/api/v1/security/``. If one ever does, the earlier
        include wins and the later endpoint becomes unreachable — which is the
        exact defect that blocks the provenance router below.
        """
        served = set(paths)
        for path in (
            "/api/v1/security/passkeys",
            "/api/v1/security/step-up/methods",
        ):
            assert path in served, f"mounting security_router displaced {path}"


class TestAuditRouterIsMounted:
    def test_all_paths_are_served(self, paths):
        served = set(paths)
        for path in (
            "/api/v1/audit/queue",
            "/api/v1/audit/vote",
            "/api/v1/audit/credits",
            "/api/v1/audit/certificate/{project_id}",
        ):
            assert path in served, (
                f"{path} is defined in audit.py but not served; the RPCs it calls "
                f"already exist in supabase/migrations/0006_audit_credits.sql"
            )

    def test_it_ships_no_route_without_an_implementation(self):
        """No handler may return a hardcoded body.

        The router's value is entirely in the Supabase round trip; a stub that
        answered with static JSON would look mounted and be worth nothing.
        """
        source = (ROOT / "services" / "api_gateway" / "routers" / "audit.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        handlers = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(
                isinstance(d, ast.Call)
                and getattr(d.func, "attr", None) in {"get", "post", "put", "delete"}
                for d in node.decorator_list
            )
        ]
        assert len(handlers) == 5, (
            f"expected audit.py's 5 routed handlers, found {len(handlers)}; if the "
            f"router was reworked, re-check the mount assertions above"
        )
        for handler in handlers:
            for node in ast.walk(handler):
                if not (isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)):
                    continue
                values = node.value.values
                assert not all(isinstance(v, ast.Constant) for v in values), (
                    f"{handler.name}() returns a fully constant dict; the handler would "
                    f"be a stub dressed as a feature"
                )


class TestProvenanceStaysUnmounted:
    """Recorded decision, not an oversight.

    Mounting this router would ship ten endpoints that cannot work, and the two
    things that would make them work both live outside the files this change is
    allowed to touch.
    """

    def test_it_is_not_served(self, paths):
        served = {p for p in paths if p.startswith("/api/v1/provenance")}
        assert not served, (
            f"the provenance router is now served: {sorted(served)}. That is allowed "
            f"only once its route ordering is fixed and its tables are migrated."
        )

    def test_the_router_module_still_exists_for_review(self):
        assert PROVENANCE_ROUTER_SRC.exists(), (
            "the provenance router was deleted. If that was deliberate, delete the "
            "test above with it; do not leave a passing assertion about a file that "
            "is gone."
        )

    def test_its_model_list_endpoint_is_shadowed(self):
        """The concrete defect: ``GET /models`` can never run.

        ``/{provenance_id}`` is declared at line 48, ahead of ``/models`` at
        line 140, and Starlette matches in declaration order. A request for the
        model list therefore reaches ``get_provenance`` with
        ``provenance_id="models"`` and 404s. Reordering the decorators in
        ``services/provenance/router.py`` is the fix, and that file is outside
        the allow-list for this change.
        """
        from services.provenance.router import router

        def first_full_match(path: str, method: str) -> str | None:
            scope = {
                "type": "http",
                "path": path,
                "method": method,
                "root_path": "",
                "headers": [],
                "query_string": b"",
                "scheme": "http",
                "server": ("test", 80),
                "client": ("test", 1),
                "http_version": "1.1",
            }
            for route in router.routes:
                match, _ = route.matches(scope)
                if str(match) == "Match.FULL":
                    return route.name
            return None

        winner = first_full_match("/api/v1/provenance/models", "GET")
        assert winner == "get_provenance", (
            f"GET /api/v1/provenance/models is now captured by {winner!r} rather than "
            f"by /{{provenance_id}}. The route-ordering defect is fixed; the remaining "
            f"blockers are the missing migration and the init_db import, both asserted "
            f"below. When those land too, delete this class and mount the router."
        )

    def test_its_tables_are_created_by_nothing(self):
        """``init_db()`` never imports the provenance models.

        ``Base.metadata.create_all`` only creates tables whose models were
        imported, and ``init_db`` imports four model modules that are not this
        one. So on a fresh database all ten endpoints raise "no such table".
        Creating them needs an Alembic revision; ``create_all`` is not a schema
        source of record in this repo.
        """
        main_src = (ROOT / "services" / "api_gateway" / "main.py").read_text(encoding="utf-8")
        init_db = main_src.split("def init_db():", 1)[1].split("\ndef ", 1)[0]
        assert "provenance" not in init_db, (
            "init_db() now imports the provenance models. If an Alembic revision was "
            "added for provenance_records / model_versions / data_lineage, the router "
            "can be mounted and TestProvenanceStaysUnmounted should be replaced with a "
            "mount assertion."
        )

    def test_no_migration_exists_for_its_tables(self):
        versions = list((ROOT / "alembic" / "versions").glob("*.py"))
        blob = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in versions)
        for table in ("provenance_records", "model_versions", "data_lineage"):
            assert table not in blob, (
                f"{table} is now migrated. Combined with the route-ordering fix and an "
                f"init_db import, the provenance router becomes mountable."
            )


class TestSecurityStatusDoesNotLie:
    def test_the_reported_csp_matches_the_headers_actually_sent(self, app):
        """The regression this file exists to prevent.

        ``/status`` used to hardcode ``"csp": "self + free data providers"``,
        describing the policy in ``services/security/headers.py``. That
        middleware is not mounted. The mounted one — from
        ``services.api_gateway.security`` — declares no CSP, so the endpoint
        claimed a header the gateway never sent.
        """
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/security/status")
        assert response.status_code == 200, response.text

        csp = response.json()["layers"]["headers"]["csp"]
        sent = response.headers.get(CSP_HEADER)

        assert csp["enforced"] is (sent is not None), (
            f"/status reports csp.enforced={csp['enforced']!r} but the response "
            f"carries Content-Security-Policy={sent!r}. The endpoint is describing a "
            f"middleware that is not the one serving this request."
        )
        if sent is not None:
            assert csp["policy"] == sent, (
                f"/status reports the policy {csp['policy']!r}; the response carries {sent!r}"
            )

    def test_the_mounted_layer_is_named(self, app):
        """A layer that is not mounted must not be reported as active."""
        client = TestClient(app, raise_server_exceptions=False)
        layers = client.get("/api/v1/security/status").json()["layers"]
        assert layers["headers"]["csp"]["source"] == (
            "services.api_gateway.security.SecurityHeadersMiddleware"
        ), (
            "the CSP source should name the mounted middleware class. If the header "
            "layer moved, this assertion is what catches the stale report."
        )

    def test_no_hardcoded_csp_policy_remains_in_the_source(self):
        """Belt and braces on the source itself.

        A derived value can still be undermined by someone re-adding a literal
        next to it, and the literal is what this endpoint shipped before. The
        guard looks for a *policy* — the ``default-src 'self'; ...`` shape — and
        not for the header name, which has to be spelled out somewhere. Only
        code is inspected: both files quote the old policy while explaining that
        it was removed, and a text search would fail on its own documentation.
        """
        offenders = [
            node.value
            for node in _code_strings(ast.parse(SECURITY_ROUTER_SRC.read_text(encoding="utf-8")))
            if _CSP_DIRECTIVE.search(node.value)
        ]
        assert not offenders, (
            f"security_router.py hardcodes a CSP policy: {offenders}. The policy must be "
            f"read from the mounted middleware class, never asserted here."
        )

    def test_the_header_name_is_a_named_constant(self):
        """The name is a lookup key, so it belongs in one place."""
        source = SECURITY_ROUTER_SRC.read_text(encoding="utf-8")
        assert '_CSP_HEADER = "Content-Security-Policy"' in source, (
            "the header name should be the module constant _CSP_HEADER so the "
            "lookup and the report cannot drift apart"
        )

    def test_the_csp_field_calls_the_derived_helper(self):
        source = SECURITY_ROUTER_SRC.read_text(encoding="utf-8")
        assert '"csp": _csp_report(request)' in source, (
            "the csp field must call the derived helper, not a literal"
        )


class TestNoRouteIsServedTwice:
    def test_no_duplicate_path_and_method_pairs(self, paths):
        """Mounting more routers makes silent shadowing the likely next break."""
        seen: collections.Counter = collections.Counter()
        for path, operations in paths.items():
            for method in operations:
                if method in HTTP_METHODS:
                    seen[(path, method)] += 1
        duplicates = [key for key, count in seen.items() if count > 1]
        assert not duplicates, (
            f"{len(duplicates)} (path, method) pairs are served more than once; the "
            f"first include wins at runtime and the other is unreachable: {duplicates[:5]}"
        )
