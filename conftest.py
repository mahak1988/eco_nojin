"""Root conftest: session-level setup that must run before anything imports the hub.

The one thing that lives here is per-worker database isolation, because it has
to happen before ``database.hub`` is first instantiated (it reads
``DATABASE_URL`` at construction time) and because it applies to every test
tree — ``services/``, ``engine/``, ``testing_lab/`` and ``tests/`` — while a
conftest inside any one of those directories would only cover that tree.
"""

from __future__ import annotations

import os
from pathlib import Path


def _use_per_worker_database() -> None:
    """Give each xdist worker its own SQLite file.

    Without this, every worker opens the same ``data/econojin.db``. The
    ``clean_db`` fixture calls ``reset_database()``, which **drops every
    table** and recreates it, so a worker entering a test destroys the schema
    another worker's in-flight request is using. The visible symptoms were
    ``no such table: users``, ``no such table: refresh_tokens`` and bare
    ``401`` responses from requests that should have succeeded — which read
    like product bugs and are not.

    The effect was that no database-backed test could be trusted in a
    parallel run, which is how several dozen failures ended up being
    attributed to unrelated changes.

    A non-SQLite ``DATABASE_URL`` is left alone: the PostgreSQL lane points at
    a real server and manages its own isolation.
    """
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if not worker or worker == "master":
        return

    configured = os.environ.get("DATABASE_URL", "")
    if configured and not configured.startswith("sqlite"):
        return

    root = Path(__file__).resolve().parent
    target = root / "data" / "pytest"
    target.mkdir(parents=True, exist_ok=True)
    db_path = target / f"{worker}.sqlite"

    # Start from empty so a stale schema or row from a previous run cannot be
    # inherited. A previous process may still hold the file open, so this is
    # best-effort: an unlink failure must not abort the hook, because that would
    # leave DATABASE_URL unset and silently restore the shared-database bug.
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(db_path) + suffix)
        try:
            if candidate.exists():
                candidate.unlink()
        except OSError:
            pass

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"


# Executed at import time, deliberately.
#
# ``tests/conftest.py`` does ``from database.hub import hub`` at module level, and
# ``DataHub.__init__`` captures DATABASE_URL once, at construction. pytest
# imports all initial conftests *before* it calls ``pytest_configure``, so an
# override placed in that hook runs too late: the hub already points at the
# shared database. This file is the first conftest imported (it sits at
# rootdir), so doing the work here is the earliest point that still lands before
# the hub exists.
_use_per_worker_database()


def pytest_configure(config: object) -> None:
    """No-op: the database is already isolated at import time. See above."""
    return


def pytest_report_header(config: object) -> list[str]:
    worker = os.environ.get("PYTEST_XDIST_WORKER", "")
    if not worker or worker == "master":
        return []
    return [f"database: per-worker sqlite ({worker}) -> {os.environ.get('DATABASE_URL')}"]


try:
    import pytest

    @pytest.fixture(scope="session", autouse=True)
    def _per_worker_schema() -> None:
        """Create the schema in this worker's database.

        Must not run in ``pytest_configure``: at that point no test module has
        been imported, so ``Base.metadata`` is still empty and ``create_all``
        would create nothing. That is why the first attempt left 0-byte worker
        databases and every test then failed with "no such table: users".
        """
        if not os.environ.get("PYTEST_XDIST_WORKER"):
            return
        from database.config import init_db

        init_db()

except ImportError:  # pragma: no cover - pytest always present in practice
    pass
