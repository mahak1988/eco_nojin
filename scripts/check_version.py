import json
import sys
import tomllib
from pathlib import Path

version = Path("VERSION").read_text(encoding="utf-8").strip()
package = json.loads(Path("package.json").read_text(encoding="utf-8"))["version"]
project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
if not version or version != package or version != project:
    print(
        f"version mismatch: VERSION={version} package={package} pyproject={project}",
        file=sys.stderr,
    )
    raise SystemExit(1)
print(f"version aligned: {version}")
