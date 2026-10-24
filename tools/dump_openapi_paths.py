"""Dump the gateway's OpenAPI paths, one per line, sorted.

Used by the frontend coverage work (frontend/API-INVENTORY.md): regenerate
the path inventory after any gateway change with::

    $env:PYTHONPATH = "D:\\HyDroMA;D:\\eco_nojin"
    $env:SECRET_KEY = "test-secret-key"
    & "D:\\eco_nojin\\.venv\\Scripts\\python.exe" tools/dump_openapi_paths.py --write

The output goes to stdout (redirect it) or to frontend/API-INVENTORY.paths
when run with ``--write``, which is the file frontend tooling reads.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "frontend" / "API-INVENTORY.paths"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    from services.api_gateway.main import app

    paths = sorted(app.openapi()["paths"].keys())
    text = "\n".join(paths) + "\n"
    if "--write" in sys.argv:
        DEFAULT_OUT.write_text(text, encoding="utf-8")
        print(f"{len(paths)} paths -> {DEFAULT_OUT}", file=sys.stderr)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())