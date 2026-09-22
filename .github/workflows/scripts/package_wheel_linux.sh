#!/bin/bash
# Linux wheel packaging script
set -euo pipefail

MODULE=$(find . -name "hydroma_core*.so" | head -1)
echo "Found module: $MODULE"

mkdir -p wheel/hydroma_core
cp $MODULE wheel/hydroma_core/hydroma_core.so

cat > wheel/hydroma_core/__init__.py << 'PYEOF'
import sys
from pathlib import Path
_bridge_dir = str(Path(__file__).parent.absolute())
if _bridge_dir not in sys.path:
    sys.path.insert(0, _bridge_dir)
try:
    from .hydroma_core import *
    BACKEND = "cpp"
except ImportError as e:
    BACKEND = "python"
    import logging
    logging.getLogger("econojin.cpp_bridge").error(f"C++ hydroma_core NOT available: {e}")
PYEOF

cat > wheel/pyproject.toml << 'TOMLEOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "hydroma-core"
version = "2.0.0"
description = "Eco Nojin HyDroMa C++ Core Kernels"
readme = "README.md"
requires-python = ">=3.11"
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: POSIX :: Linux",
    "Operating System :: Microsoft :: Windows",
]
dependencies = []

[tool.setuptools.packages.find]
where = ["."]
include = ["hydroma_core*"]

[tool.setuptools.package-data]
"*" = ["*.so", "*.pyd"]
TOMLEOF

cd wheel
python -m pip install auditwheel
python -m build --wheel --no-isolation

WHEEL_FILE=$(find dist -name "*.whl" | head -1)
auditwheel repair $WHEEL_FILE -w ../dist_repaired

REPAIRED_WHEEL=$(find ../dist_repaired -name "*.whl" | head -1)
cp $REPAIRED_WHEEL ../../../../hydroma_core-${PYTHON_VERSION}-${PLATFORM}.whl

echo "Wheel created: $(basename $REPAIRED_WHEEL)"