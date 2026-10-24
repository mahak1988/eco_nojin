"""Export the gateway's OpenAPI document (the public HTTP contract).

The typed/api-client consumers are generated from the live document, and CI
fails when a checked-in copy drifts. This tool writes it:

    python tools/export_openapi.py [--out docs/openapi.json]

It boots the real app (no server needed) and serialises ``app.openapi()``.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def export(out_path: Path) -> int:
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    from services.api_gateway.main import app

    schema = app.openapi()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths = len(schema.get("paths", {}))
    print(f"wrote {out_path} ({paths} paths)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(PROJECT_ROOT / "docs" / "openapi.json"),
    )
    args = parser.parse_args()
    return export(Path(args.out))


if __name__ == "__main__":
    raise SystemExit(main())
