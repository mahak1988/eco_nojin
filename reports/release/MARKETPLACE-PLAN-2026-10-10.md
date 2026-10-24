# Marketplace completion plan — 2026-10-10

Conflict-free by construction: every file has exactly one owner, and the only
shared file (`services/api_gateway/main.py`) is touched by exactly one agent
with an additive router mount.

| id | gap it closes | files owned (exclusive) | mounts to main.py? |
|---|---|---|---|
| **SA-T** | no product search | NEW `services/marketplace/search.py`, NEW `services/marketplace/tests/test_search.py` | no |
| **SA-U** | `international` gateway undeclared | `services/marketplace/payments_service.py`, NEW `services/marketplace/tests/test_international_gateway.py` | no |
| **SA-V** | no buyer ratings/reviews | NEW `services/marketplace/models/marketplace_review.py`, `services/marketplace/models/__init__.py`, NEW `services/marketplace/reviews.py`, NEW `services/api_gateway/routers/marketplace_reviews.py` | **yes (only agent that does)** |
| **SA-W** | no reference-price feed for commission | NEW `engine/hydroma/data_pipeline/connectors/market_price_connector.py`, `engine/hydroma/data_pipeline/pipeline.py` (registration only), NEW `engine/hydroma/data_pipeline/tests/test_market_price_connector.py` | no |

## Shared rules for every agent

* Environment: `$env:PYTHONPATH="D:\HyDroMA;D:\eco_nojin"; $env:SECRET_KEY="test-secret-key"`; python `D:\eco_nojin\.venv\Scripts\python.exe`.
* Test gate after every batch: `pytest services/ -q -p no:cacheprovider` (baseline
  **3784 passed engine+services combined / 0 failed**) and, for SA-W,
  `pytest engine/ -q -p no:cacheprovider`.
* `python tools/detect_imports.py --root .` must stay **PASS, 0 violations**
  (services still reach the engine only via `services/_gateway_facade.py`).
* No fabrication: a source that cannot be reached raises a typed error naming
  what is missing; a feature that cannot run says so instead of pretending.
* No commits. No changes outside the owned files. Ruff/mypy clean on every
  touched file (mypy currently: **Success — no issues found in 393 source
  files**; that must stay true).

## Acceptance

* Every new service/model/connector is unit-tested against the project's own
  primitives (no new third-party dependency — see the offline notes below).
* The marketplace's existing 83 endpoints and 3784-test baseline stay green.
* Each agent reports: files changed, tests added, and the gap's before/after
  state.

## Offline constraint

No network for installs (`pip` is unreachable from this box), so:
* SA-T uses **SQLite FTS5**, which ships inside Python's `sqlite3` — no
  dependency, no server, and it is the same database backend the project
  already uses (`database/config.py`).
* SA-U declares the gateway with the project's existing typed-unavailable
  pattern (`ConnectorUnavailable`-style) when `STRIPE_API_KEY` is absent, and
  the real REST call when it is present — mirroring the ZarinPal branch that
  already exists.
* SA-W reads the World Bank Pink Sheet CSV over HTTP with the connector
  pattern already used by the CDS/ERA5 connectors, and raises a typed error
  naming the URL when the network is absent (the tests use fixtures).
