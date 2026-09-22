#!/bin/bash
# Verify Python module loads correctly
set -euo pipefail

if [ "${RUNNER_OS}" = "Linux" ]; then
    cp hydroma_core*.so /tmp/hydroma_core.so
    python -c "import sys; sys.path.insert(0, '/tmp'); import hydroma_core; print('Module loaded:', hydroma_core.BACKEND)"
else
    cp hydroma_core*.pyd C:/tmp/hydroma_core.pyd
    python -c "import sys; sys.path.insert(0, 'C:/tmp'); import hydroma_core; print('Module loaded:', hydroma_core.BACKEND)"
fi