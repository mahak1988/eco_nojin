# API Contract v1 — Eco Nojin / HyDroMA

* **Status:** Ratified contract page · **Version:** v1.0 · **Ratified:** 2026-10-11 (P2, A02)
* **Enforced by:** `services/api_gateway/tests/test_api_contract_v1.py` — every clause below that
  carries a §Clause tag is pinned by a test; a behavior change requires a new contract version
  (v2), never a silent edit.
* **Scope:** every HTTP surface the gateway serves (113 registered routes / 630 documented paths).

## 1. Error body contract

Every error response is a JSON object. Three shapes exist, and routers must not invent a fourth.

| Shape | When | Body |
|---|---|---|
| Domain error | `EcoNojinException` (and its 6 subclasses) raised anywhere | `{"detail": <message>, "code": <stable code>, "path": <request path>}` at the exception's `status_code` |
| Unhandled failure | any other exception | `{"detail": "Internal server error", "error_id": <id>, "path": <path>}` + `X-Request-ID` header; `error_type` is added **only** when `settings.debug` is explicitly on |
| Route not found | unmatched path | `{"detail": "Endpoint not found: <path>", "hint": "Check /docs for available endpoints"}` |

Rules:
* **No internal exposure.** A handler must never embed `str(exc)`, class names, stack text, or SQL
  in an error body (eco.md §48; `services/api_gateway/errors.py::safe_error_detail` is the only
  sanctioned generic-detail helper). The `error_id`/`X-Request-ID` pair is the correlation channel.
* **`code` is a stable vocabulary**, not a message. Domain codes come from
  `EcoNojinException.code`; gateway errors use the 13-code engine vocabulary via
  `GatewayCallError.spec_error_code` (`services/api_gateway/errors_gateway.py`).
* `access_error_status` maps authorization failures by exception *type/attribute*
  (`exc.access_denied`), never by parsing Persian text out of a message.

## 2. Idempotency contract (§Clause 2)

* Header: **`Idempotency-Key`** — required on every route in
  `middleware/idempotency.py::IDEMPOTENT_EXACT_ROUTES` / `IDEMPOTENT_PARAM_ROUTES` (money- and
  order-moving paths: ecowallet, ledger entries, marketplace orders/payments incl. the 6-step
  purchase flow, finance wallet/payment intent).
* Format: **SHA256-hex (64 chars) or UUID v4**. A SHA256 key is additionally verified against
  `SHA256(X-Client-Secret + path + body)` when `X-Client-Secret` is sent.
* Storage: `fin_idempotency_keys` keyed by `(user_id, key)`, TTL **24 h**; the scope is the
  authenticated subject (pepper-salted peer digest when anonymous) so two clients can never read
  each other's cached response.
* Responses:
  * missing header → **400** `code=IDEMPOTENCY_KEY_REQUIRED`;
  * bad format / SHA mismatch → **400** `code=INVALID_IDEMPOTENCY_KEY`;
  * same key, **different** body → **422** `code=IDEMPOTENCY_KEY_REUSE` (a client bug, not a retry);
  * same key, in flight → **409** `code=IDEMPOTENCY_KEY_IN_PROGRESS`;
  * same key, completed → **replay of the stored response** (`response_code` + `response_body`).
* New mutating money routes **must** be added to the route tables above in the same change; an
  unlisted money route is a contract violation (§Clause 2 gate in the test).

## 3. Money contract

* **Internal:** every amount, balance, fee and rate is `decimal.Decimal` — never `float`.
  (`services/finance/*`, wallet/ledger services, tax and fee calculators; the repo's property-based
  money tests pin this.)
* **Wire format:** JSON numbers carrying the exact decimal value
  (`Decimal("10.50")` → `10.5`). Clients parsing money MUST parse into a decimal type
  (Python `Decimal`, JS `decimal.js`/string round-trip): a binary-float client silently loses exact
  cent-level equality at large magnitudes. This is the known, documented limitation of v1; a
  string-amount wire format is a **v2 additive option**, decided only with the frontend contract
  (D-01) — never mixed within one response.
* Balances and posted journals stay balanced at their call sites; a batch that does not balance is
  rejected, never rounded into agreement.

## 4. Pagination contract

* List endpoints use **`page`** (≥1, default 1) and **`page_size`** (1–100, default 20) query
  parameters — the convention already implemented by the alerting/jobs/oracle routers. Offset
  math is `offset((page-1)*page_size).limit(page_size)`.
* Response bodies expose the page's items plus the total count (`total`) so clients can paginate
  without a second count request. New list endpoints follow this shape; divergent shapes are
  grandfathered and listed in the endpoint inventory, not silently added to.

## 5. Rate limiting & headers

* Every response carries **`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`**;
  a throttled request adds **`Retry-After`** and returns **429**.
* Auth routes (`/api/v1/auth/login|token|refresh|register`) carry a second, per-IP+route
  token-bucket ceiling (`HYDROMA_AUTH_RATE_LIMIT_*`, default 60/60 s, in-process, `X-Forwarded-For`
  deliberately ignored). Disabling it is a test-only escape hatch, never a production setting.
* Every response carries the security header set from `SecurityHeadersMiddleware`; every response
  carries `X-Request-ID` (client-quotable for support).

## 6. Version status rules (for any future change)

Every API change ships one of:
1. **compatible** — additive optional field/endpoint, no client change needed;
2. **additive** — new optional field/endpoint with a default for old clients;
3. **breaking-with-version** — behavior change on an existing path, requires `/v2` or an explicit
   version negotiation + this contract page re-issued as v2;
4. **deprecated-with-migration** — removal path announced with a dated deprecation header/note and
   a migration guide before the endpoint disappears.

A change that alters error `code` values, idempotency route membership, money wire format, or the
error body shapes in §1 is **never** "compatible".
