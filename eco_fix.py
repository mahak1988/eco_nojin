#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v8 — async DB wiring (prove-then-commit).

Usage:
    python eco_fix.py              # verify + patch + proof + commit + push
    python eco_fix.py verify
    python eco_fix.py patch-async
    python eco_fix.py recon-conftest
"""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

GIT_EXE = None
for _c in (r"C:\Program Files\Git\cmd\git.exe",
           r"C:\Program Files (x86)\Git\cmd\git.exe",
           r"C:\Program Files\Git\bin\git.exe"):
    if Path(_c).exists():
        GIT_EXE = _c
        break

LINE = "=" * 62

def out(*a, **kw): print(*a, flush=True, **kw)
def ok(m): out(f"[ OK ] {m}")
def warn(m): out(f"[WARN] {m}")
def fail(m): out(f"[FAIL] {m}")

def sh(cmd, timeout=900, input=None):
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, input=input)

def git(*a, **kw):
    if GIT_EXE is None:
        raise RuntimeError("git.exe not found")
    return sh([GIT_EXE, *a], **kw)

def read_text(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    return raw, crlf, raw.replace("\r\n", "\n")

def write_text(p, text, crlf):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", "\r\n") if crlf else text)

# ---------------------------------------------------------------- verify ---
def verify():
    out(LINE, "STEP 0 — verify", LINE, sep="\n")
    git("fetch", "origin", timeout=300)
    r = git("log", "--oneline", "origin/main..main")
    if [l for l in r.stdout.splitlines() if l.strip()]:
        warn("unpushed commits — pushing ...")
        git("push", "origin", "main")
    else:
        ok("everything pushed to origin/main")
    out(git("log", "--oneline", "-3").stdout)
    return True

# ------------------------------------------------------------- hub patch ---
HUB = ROOT / "database" / "hub" / "hub.py"

HUB_IMPORTS = [
    ("from typing import Optional, Any, Generator",
     "from typing import Optional, Any, AsyncGenerator, Generator"),
    ("from contextlib import contextmanager",
     "from contextlib import asynccontextmanager, contextmanager"),
]
HUB_INIT_ANCHOR = "        self._session_factory = None"
HUB_INIT_ADD = ("        self._async_engine = None\n"
                "        self._async_session_factory = None")
HUB_METHOD_ANCHOR = '    def get_duckdb(self, database: str = "master") -> Any:'

HUB_METHODS = '''    def get_async_engine(self) -> Any:
        """Get async SQLAlchemy engine (additive — sync paths untouched)."""
        if getattr(self, "_async_engine", None) is None:
            from sqlalchemy.ext.asyncio import create_async_engine

            database_url = os.environ.get(
                "DATABASE_URL",
                f"sqlite:///{self.main_sqlite}",
            )

            # translate sync driver scheme -> async driver
            if database_url.startswith("sqlite:///"):
                async_url = database_url.replace(
                    "sqlite:///", "sqlite+aiosqlite:///", 1)
            elif database_url.startswith("postgresql://"):
                async_url = database_url.replace(
                    "postgresql://", "postgresql+psycopg://", 1)
            elif database_url.startswith("postgres://"):
                async_url = database_url.replace(
                    "postgres://", "postgresql+psycopg://", 1)
            else:
                async_url = database_url  # assume async-capable already

            self._async_engine = create_async_engine(
                async_url,
                echo=False,
                pool_pre_ping=True,
            )
            logger.info(f"Async SQLAlchemy engine created: {async_url}")

        return self._async_engine

    def get_async_session_factory(self) -> Any:
        """Get async session factory."""
        if getattr(self, "_async_session_factory", None) is None:
            from sqlalchemy.ext.asyncio import async_sessionmaker

            engine = self.get_async_engine()
            self._async_session_factory = async_sessionmaker(
                bind=engine,
                expire_on_commit=False,
                autoflush=False,
            )
            logger.info("Async session factory created")

        return self._async_session_factory

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[Any, None]:
        """
        Get an async session with automatic transaction management.

        Usage:
            async with hub.get_async_session() as session:
                result = await session.execute(select(User))
        """
        factory = self.get_async_session_factory()
        session = factory()

        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async transaction failed: {e}")
            raise
        finally:
            await session.close()

'''

# --------------------------------------------------------- reporting patch -
RPT = ROOT / "services" / "reporting" / "api" / "__init__.py"
RPT_IMPORT_OLD = "from typing import List, Optional"
RPT_IMPORT_NEW = "from typing import AsyncGenerator, List, Optional"
RPT_GETDB_OLD = ("def get_db():\n"
                 "    with hub.get_session() as session:\n"
                 "        yield session")
RPT_GETDB_NEW = ("async def get_db() -> AsyncGenerator[AsyncSession, None]:\n"
                 "    async with hub.get_async_session() as session:\n"
                 "        yield session")

# ------------------------------------------------------------ proof file ---
PROOF = ROOT / "eco_proof_tmp.py"
PROOF_CODE = '''import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
tmpdb = ROOT / "_proof_v8.db"
os.environ["DATABASE_URL"] = "sqlite:///" + tmpdb.as_posix()

from database.hub import hub  # noqa: E402
from services.reporting.models import Report  # noqa: E402
from services.reporting.repository import ReportingRepository  # noqa: E402


async def main() -> None:
    engine = hub.get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda c: Report.__table__.create(c, checkfirst=True))

    async with hub.get_async_session() as db:
        repo = ReportingRepository(db)
        rep = Report(report_type="sales", title="probe",
                     parameters={}, generated_by="probe",
                     status="pending")
        repo.db.add(rep)
        await repo.db.commit()
        await repo.db.refresh(rep)
        rid = rep.id

    async with hub.get_async_session() as db:
        repo = ReportingRepository(db)
        got = await repo.get_report(str(rid))
        assert got is not None and got.title == "probe", "read-back failed"
        print(f"ASYNC-OK id={rid}")

    await engine.dispose()

    from sqlalchemy import text
    with hub.get_session() as s:
        assert s.execute(text("SELECT 1")).scalar() == 1
    print("SYNC-STILL-OK")


try:
    asyncio.run(main())
except Exception as e:
    print(f"ASYNC-FAIL: {type(e).__name__}: {e}")
    sys.exit(1)
finally:
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(ROOT / "_proof_v8.db") + suffix)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
'''

# --------------------------------------------------------------- patch ----
def patch_async():
    out(LINE, "STEP 1 — async wiring (prove-then-commit)", LINE, sep="\n")

    # ---- read originals (kept for rollback) ----
    hub_raw, hub_crlf, hub_text = read_text(HUB)
    rpt_raw, rpt_crlf, rpt_text = read_text(RPT)

    # ---- apply hub patch ----
    if "get_async_engine" in hub_text:
        ok("hub.py already patched")
    else:
        for old, new in HUB_IMPORTS:
            if old not in hub_text:
                fail(f"hub anchor missing: {old!r}")
                return False
            hub_text = hub_text.replace(old, new, 1)
        if HUB_INIT_ANCHOR not in hub_text:
            fail("hub init anchor missing")
            return False
        hub_text = hub_text.replace(
            HUB_INIT_ANCHOR, HUB_INIT_ANCHOR + "\n" + HUB_INIT_ADD, 1)
        if HUB_METHOD_ANCHOR not in hub_text:
            fail("hub method anchor missing")
            return False
        hub_text = hub_text.replace(
            HUB_METHOD_ANCHOR, HUB_METHODS + HUB_METHOD_ANCHOR, 1)
        ok("hub.py: imports + init attrs + 3 async methods staged")

    # ---- apply reporting patch ----
    if "async def get_db" in rpt_text:
        ok("reporting get_db already async")
    else:
        if RPT_IMPORT_OLD not in rpt_text:
            fail("reporting import anchor missing")
            return False
        rpt_text = rpt_text.replace(RPT_IMPORT_OLD, RPT_IMPORT_NEW, 1)
        if RPT_GETDB_OLD not in rpt_text:
            fail("reporting get_db anchor missing")
            return False
        rpt_text = rpt_text.replace(RPT_GETDB_OLD, RPT_GETDB_NEW, 1)
        ok("reporting: async get_db dependency staged")

    # ---- parse gates ----
    for name, text in (("hub", hub_text), ("reporting", rpt_text)):
        try:
            ast.parse(text)
            ok(f"{name}: parses cleanly")
        except SyntaxError as e:
            fail(f"{name}: parse error line {e.lineno}: {e.msg} — aborting")
            return False

    # ---- write to disk (rollback possible) ----
    write_text(HUB, hub_text, hub_crlf)
    write_text(RPT, rpt_text, rpt_crlf)
    ok("patches written to disk")

    # ---- runtime proof in a fresh process ----
    PROOF.write_text(PROOF_CODE, encoding="utf-8", newline="\n")
    out("\nrunning runtime proof (fresh process) ...")
    r = sh([sys.executable, str(PROOF)], timeout=300)
    out((r.stdout or "") + ((r.stderr or "")[-600:] if (r.stderr or "").strip() else ""))

    if "ASYNC-OK" not in r.stdout:
        fail("PROOF FAILED — rolling back patches, nothing committed")
        write_text(HUB, hub_raw.replace("\r\n", "\n") if hub_crlf else hub_raw, hub_crlf)
        write_text(RPT, rpt_raw.replace("\r\n", "\n") if rpt_crlf else rpt_raw, rpt_crlf)
        ok("original files restored")
        PROOF.unlink(missing_ok=True)
        return False
    ok("proof green — committing")

    # ---- commits ----
    git("add", "--", "database/hub/hub.py")
    r = git("commit", "-m",
            "feat(database): additive async engine/session support in DataHub")
    ok("hub commit") if r.returncode == 0 else \
        warn("hub commit: " + (r.stdout + r.stderr)[-300:])

    git("add", "--", "services/reporting/api/__init__.py")
    r = git("commit", "-m",
            "fix(reporting): wire get_db to hub.get_async_session (async dependency)")
    ok("reporting commit") if r.returncode == 0 else \
        warn("reporting commit: " + (r.stdout + r.stderr)[-300:])

    PROOF.unlink(missing_ok=True)

    git("add", "--", "eco_fix.py")
    r = git("commit", "-m", "chore: update automation script")
    if r.returncode == 0:
        ok("script commit")
    r = git("push", "origin", "main")
    ok("pushed origin/main") if r.returncode == 0 else \
        warn("push failed — run: python eco_fix.py verify")

    out("\n" + git("log", "--oneline", "-4").stdout)
    return True

# -------------------------------------------------------- recon conftest ---
def recon_conftest():
    out(LINE, "STEP 2 — services/conftest.py (existing async pattern)", LINE, sep="\n")
    p = ROOT / "services" / "conftest.py"
    if not p.exists():
        warn("not found"); return True
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    out(f"({len(lines)} lines, showing 1-130)")
    for i, ln in enumerate(lines[:130], 1):
        out(f"{i:4d}| {ln}")
    return True

# ------------------------------------------------------------------ main ---
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"verify": verify, "patch-async": patch_async,
             "recon-conftest": recon_conftest}
    if cmd == "all":
        for name in ("verify", "patch-async", "recon-conftest"):
            try:
                steps[name]()
            except Exception as e:
                fail(f"{name} crashed: {e!r}")
    elif cmd in steps:
        try:
            steps[cmd]()
        except Exception as e:
            fail(f"{cmd} crashed: {e!r}")
    else:
        out(__doc__)

if __name__ == "__main__":
    main()