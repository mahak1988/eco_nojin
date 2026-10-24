"""The money-write boundary: one scanner, shared by every guard that enforces it.

This module is the single source of truth for **which packages may write the
money/balance tables**. It was extracted because the boundary was enforced
twice, from two copies of the same table map, and the copies had drifted --
one of them was scanning a directory that does not exist, so the guard had
never once looked at the repository
(see ``docs/project/SECTOR-TECH-DEBT-REMEDIATION-2026-10-20.md``, FR-01/FR-02).

Two rules keep the guard honest:

1. **The scanner must be able to fail.** :func:`scan_money_writers` is a plain
   function over a root, so a guard can point it at a synthetic tree that
   contains an offender and assert that it *is* flagged. A guard that cannot
   fail proves nothing.
2. **The allow-list is a reviewed decision, not an accident.** Every sanctioned
   package carries the reason it is sanctioned.

Run it standalone to see the current boundary::

    python tools/money_boundary.py --root .
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

#: Tables that hold money/balance state, and the packages allowed to write them.
#:
#: Every entry below is a reviewed decision, not an accident:
#:
#: * ``services.finance``     -- the canonical money owner (D-09/D-11).
#: * ``services.api_gateway`` -- writes the wallet through the finance service.
#: * ``services.ecowallet``   -- creates the wallet ROW (balance zero) in
#:                               ``service.py``; it never mutates a balance.
#: * ``services.auth_legacy`` -- creates the wallet ROW at user bootstrap.
#: * ``services.inventory``   -- ``_post_journal`` is a documented, balanced,
#:                               transaction-joining journal writer: it must land
#:                               in the caller's transaction so the stock mutation
#:                               and its journal commit together.
#: * ``services.wallet``      -- the eco-balance plane; the module moved here
#:                               from ``services/ecosystem/``.
#: * ``services.ledger``      -- the single-entry ledger service.
#:
#: ``services.ecosystem`` was on this list before FR-01 and has been removed: it
#: touches none of these tables (the module that did moved to ``services/wallet/``).
MONEY_TABLES: dict[str, set[str]] = {
    "EcoWallet": {
        "services.finance",
        "services.api_gateway",
        "services.ecowallet",
        "services.auth_legacy",
    },
    "FinJournalEntry": {"services.finance", "services.inventory"},
    "FinJournalBatch": {"services.finance", "services.inventory"},
    "LedgerEntry": {"services.finance", "services.ledger"},
    "EcoBalanceAccount": {"services.finance", "services.wallet"},
    "EcoBalanceEntry": {"services.finance", "services.wallet"},
}

#: Write-verbs whose call sites count as a write to a table's ORM class.
#:
#: ``execute`` is deliberately NOT here: ``db.execute(select(...))`` is a READ,
#: and including it made the guard flag ``services/finance/cross_ledger_report.py``
#: -- a reader -- as an offender. DML that does not go through ``add`` is caught
#: by :data:`DML_CALL` below.
WRITE_CALL = re.compile(
    r"\.(?:add|add_all|merge|delete|bulk_save_objects)\s*\(", re.MULTILINE
)

#: SQLAlchemy Core DML (``insert(Model)`` / ``update(Model)`` / ``delete(Model)``)
#: and raw SQL DML. The Core pattern requires a CamelCase model argument so that
#: the ubiquitous ``dict.update(...)`` is not mistaken for a write.
DML_CALL = re.compile(
    r"\b(?:insert|update|delete)\s*\(\s*[A-Z][\w]*"
    r"|\b(?:INSERT\s+INTO|UPDATE\s+[A-Za-z_\"][\w.\"]*\s+SET|DELETE\s+FROM)\b",
    re.IGNORECASE,
)


def module_owner(path: Path, root: Path) -> str:
    """The package a file belongs to, e.g. ``services.marketplace``."""
    parts = path.relative_to(root).parts
    if len(parts) >= 2 and parts[0] == "services":
        return f"services.{parts[1]}"
    return ".".join(parts[:2])


def scan_money_writers(
    root: Path,
    tables: dict[str, set[str]] | None = None,
) -> dict[str, set[str]]:
    """Map every money table to the packages that write it outside its owner.

    ``root`` is the *repo* root -- the directory that contains ``services/``.
    """
    table_map = MONEY_TABLES if tables is None else tables
    offenders: dict[str, set[str]] = {}
    services_root = root / "services"
    for table, allowed in table_map.items():
        for path in services_root.rglob("*.py"):
            if "__pycache__" in path.parts or "/tests/" in str(path).replace("\\", "/"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if table not in text:
                continue
            if WRITE_CALL.search(text) is None and DML_CALL.search(text) is None:
                continue  # imports the model but never writes through it here
            owner = module_owner(path, root)
            if owner not in allowed:
                offenders.setdefault(table, set()).add(owner)
    return offenders


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repo root (contains services/)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    offenders = scan_money_writers(root)
    if not offenders:
        print("money-write boundary: OK (no unauthorized writer)")
        return 0
    print("money-write boundary: VIOLATIONS")
    for table, owners in sorted(offenders.items()):
        for owner in sorted(owners):
            print(f"  {table}: {owner}")
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
