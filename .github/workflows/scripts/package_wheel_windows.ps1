<#
.SYNOPSIS
    Windows wheel packaging script for hydroma_core
#>

$ErrorActionPreference = "Stop"

$MODULE = Get-ChildItem -Filter "hydroma_core*.pyd" | Select-Object -First 1
Write-Host "Found module: $($MODULE.FullName)"

New-Item -ItemType Directory -Force -Path "wheel/hydroma_core" | Out-Null
Copy-Item $MODULE.FullName -Destination "wheel/hydroma_core/hydroma_core.pyd"

$initContent = @"
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
"@

Set-Content -Path "wheel/hydroma_core/__init__.py" -Value $initContent -Encoding UTF8

$tomlContent = @"
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
"@

Set-Content -Path "wheel/pyproject.toml" -Value $tomlContent -Encoding UTF8

Set-Location wheel
python -m pip install wheel
python -m build --wheel --no-isolation

$WHEEL_FILE = Get-ChildItem dist/*.whl | Select-Object -First 1
Copy-Item $WHEEL_FILE.FullName -Destination "../../../../hydroma_core-${env:PYTHON_VERSION}-${env:PLATFORM}.whl"

Write-Host "Wheel created: $($WHEEL_FILE.Name)"