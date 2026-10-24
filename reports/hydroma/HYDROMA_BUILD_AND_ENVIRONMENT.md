# HYDROMA Build & Environment

**Generated**: 2026-10-09  
**Scope**: `D:\HyDroMA` repository  
**Auditor**: Kilo autonomous agent  
**Classification**: Internal — Build & Environment  

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Repository path | `D:\HyDroMA` |
| OS | Windows 11 (win32) |
| Python version | 3.12.10 |
| Virtual environment | `D:\eco_nojin\.venv` |
| PYTHONPATH | `D:\HyDroMA;D:\eco_nojin` |
| Test runner | pytest 9.1.1 |
| C++ backend | Available (cp312-win_amd64.pyd) |
| Network access | Not available (no PyPI access) |

---

## 2. Python Environment

### 2.1 Virtual Environment

The project uses a virtual environment located at `D:\eco_nojin\.venv`.

```
Venv Python:    D:\eco_nojin\.venv\Scripts\python.exe
Python version: 3.12.10
```

To activate:
```powershell
. D:\eco_nojin\.venv\Scripts\Activate.ps1
```

### 2.2 PYTHONPATH

The environment requires two directories on `PYTHONPATH`:
```
PYTHONPATH="D:\HyDroMA;D:\eco_nojin"
```

- `D:\HyDroMA` — the repository root (contains `engine/`, `services/`, `database/`)
- `D:\eco_nojin` — the parent project directory (additional packages)

### 2.3 Key Dependencies

The `pyproject.toml` declares minimal dependencies:
```toml
dependencies = [
    "numpy>=1.26",
    "scipy>=1.11",
    "pandas>=2.0",
    "duckdb>=0.10",
    "supabase>=2.0",
    "requests>=2.31",
    "httpx>=0.25",
    "pydantic>=2.0",
    "loguru>=0.7",
]
```

### 2.4 Installed Packages (Key)

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | 2.3.5 | Scientific computing |
| pandas | 2.3.3 | Data manipulation |
| scipy | 1.16.3 | Scientific algorithms |
| fastapi | 0.141.1 | Web framework |
| starlette | 1.6.0 | ASGI toolkit |
| uvicorn | 0.52.4 | ASGI server |
| pydantic | 2.13.4 | Data validation |
| pydantic-settings | 2.15.0 | Settings management |
| SQLAlchemy | 2.0.52 | Database ORM |
| supabase | 2.31.0 | Supabase client |
| redis | 8.1.0 | Redis client |
| httpx | 0.28.1 | HTTP client |
| bcrypt | 4.0.1 | Password hashing |
| PyJWT | 2.13.0 | JWT handling |
| python-jose | 3.5.0 | JWT alternative |
| cryptography | 50.0.0 | Encryption |
| pytest | 9.1.1 | Testing |
| pytest-asyncio | 1.4.0 | Async tests |
| pytest-cov | 6.0.0 | Coverage |
| pytest-xdist | 3.8.0 | Parallel tests |
| pytest-benchmark | 5.3.0 | Benchmarks |
| structlog | 26.1.0 | Structured logging |
| alembic | 1.19.1 | Database migrations |
| pybind11 | 3.1.0 | C++ bindings |
| torch | 2.13.0+cpu | ML framework |
| transformers | 5.16.1 | Transformers |
| qdrant-client | 1.19.1 | Vector DB |
| web3 | 7.16.0 | Blockchain |
| postgrest | 2.31.0 | Supabase REST |
| storage3 | 2.31.0 | Supabase Storage |
| pyparsing | 3.3.2 | Parser |
| pystac | 1.15.2 | SpatioTemporal Asset Catalog |
| rioxarray | 0.23.0 | Raster I/O |
| xarray | 2026.7.0 | N-dim arrays |
| openai | 3.19.1 | OpenAI API |
| httpx2 | 2.13.1 | HTTP client v2 |
| opentelemetry-api | 1.44.0 | Observability |

Full package list available via:
```powershell
& D:\eco_nojin\.venv\Scripts\python.exe -m pip list
```

### 2.5 Missing / Notable Absences

| Package | Impact if missing |
|---------|-------------------|
| n/a | All packages listed in §2.4 are present in the venv |

### 2.6 Environment Notes

- **No `.env` file** is present at `D:\HyDroMA\.env` — secrets must be provisioned
  from environment variables or a `.env` file created per deployment
- **No `AGENTS.md`** file exists at the repository root
- **No `conftest.py`** at the repository root (conftest files exist in
  `services/*/` subdirectories)
- **`requirements.txt` and `requirements-dev.txt`** exist but `pyproject.toml`
  is the authoritative dependency source

---

## 3. C++ Build

### 3.1 Overview

The C++ engine (`hydroma_core`) is built via CMake + MSVC with pybind11 bindings
that expose 56 C++ functions to Python. The compiled extension is loaded by
`engine/hydroma/cpp_bridge/__init__.py`.

### 3.2 Build Directory Structure

```
engine/cpp_core/
├── CMakeLists.txt          # CMake build configuration
├── bindings/
│   └── bindings.cpp        # pybind11 bindings (Python module interface)
├── include/hydroma/
│   ├── climate.hpp
│   ├── crop_water.hpp
│   ├── erosion.hpp
│   ├── hydrology.hpp
│   ├── indices.hpp
│   ├── nojin_calculator.hpp
│   ├── richards.hpp
│   ├── saint_venant.hpp
│   ├── sampling.hpp
│   ├── sediment.hpp
│   └── soil.hpp
├── src/
│   ├── climate.cpp
│   ├── crop_water.cpp
│   ├── erosion.cpp
│   ├── hydrology.cpp
│   ├── indices.cpp
│   ├── nojin_calculator.cpp
│   ├── richards.cpp
│   ├── saint_venant.cpp
│   ├── sampling.cpp
│   ├── sediment.cpp
│   └── soil.cpp
├── tests/                  # C++ test executables (source)
│   ├── test_hydroma.cpp
│   ├── test_advanced.cpp
│   ├── test_climate_unit.cpp
│   ├── test_crop_water_unit.cpp
│   ├── test_erosion_unit.cpp
│   ├── test_hydrology_unit.cpp
│   ├── test_indices_unit.cpp
│   ├── test_nojin_calculator.cpp
│   ├── test_richards_unit.cpp
│   ├── test_saint_venant_unit.cpp
│   ├── test_sampling_unit.cpp
│   ├── test_sediment_unit.cpp
│   ├── test_soil_unit.cpp
│   └── benchmark_*.cpp
├── build/                  # Build output (legacy)
│   ├── hydroma_core.pyd
│   └── tests/              # Test executables
└── build2/                 # CMake build directory (current)
    ├── hydroma_core.sln    # Visual Studio solution
    ├── hydroma_core_py.vcxproj
    ├── CMakeCache.txt
    └── Release/
        ├── hydroma_core.cp311-win_amd64.pyd
        └── hydroma_core.cp312-win_amd64.pyd
```

### 3.3 Compiled Extension

**Location**: `engine/cpp_core/build2/Release/hydroma_core.cp312-win_amd64.pyd`

The extension carries the **Python 3.12** ABI tag in its filename, ensuring
correct interpreter compatibility. A `cp311` build also exists alongside it.

### 3.4 CMake Build

**Requirements**:
- CMake ≥ 3.22
- MSVC (Visual Studio 2019 Build Tools or newer)
- pybind11 (via `find_package` or FetchContent from GitHub)
- OpenMP
- Python development headers

**Build command** (from `engine/cpp_core/`):
```powershell
cmake -S . -B build2 -DCMAKE_BUILD_TYPE=Release
cmake --build build2 --config Release
```

**Build script** (no CMake required, direct MSVC):
```powershell
.\build_pybind.bat [output_dir]
```

This compiles all 11 kernel source files + `bindings.cpp` directly with `cl.exe`,
producing `hydroma_core.cp312-win_amd64.pyd` with the correct ABI tag.

### 3.5 Build Options

| Option | Default | Description |
|--------|---------|-------------|
| `HYDROMA_BUILD_TESTS` | ON | Build C++ test executables |
| `HYDROMA_BUILD_PYTHON_BINDINGS` | ON | Build pybind11 module |
| `HYDROMA_BUILD_BENCHMARKS` | OFF | Build benchmark executables |
| `HYDROMA_ENABLE_SANITIZERS` | OFF | Enable ASan/TSan/UBSan (Linux) |

### 3.6 C++ Configuration

| Setting | Value |
|---------|-------|
| C++ Standard | C++20 (`CMAKE_CXX_STANDARD 20`) |
| MSVC flags | `/W4 /permissive- /EHsc /bigobj` |
| Runtime | MultiThreadedDLL |
| Threading | OpenMP |
| Python binding | pybind11 v2.13.6 |

### 3.7 Loading in Python

**Location**: `engine/hydroma/cpp_bridge/__init__.py:55-72`

```python
try:
    import hydroma_core as _hydroma_core
    _cpp_available = True
except ImportError as e:
    _cpp_import_error = str(e)
    logger.error("C++ hydroma_core NOT available (%s). Falling back to Python kernels", e)
```

The `BACKEND` global reports `"cpp"` when the extension is loaded, `"python"`
when falling back. `backend_status()` provides full diagnostics including
import errors and telemetry counters.

---

## 4. Test Execution

### 4.1 Test Configuration

From `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["engine/tests", "engine/strict_tests", "services/*/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### 4.2 Running Tests

**All tests**:
```powershell
& D:\eco_nojin\.venv\Scripts\python.exe -m pytest
```

**With coverage**:
```powershell
& D:\eco_nojin\.venv\Scripts\python.exe -m pytest --cov=engine --cov=services --cov-report=html
```

**Specific test directory**:
```powershell
& D:\eco_nojin\.venv\Scripts\python.exe -m pytest engine/strict_tests/
```

**Parallel execution** (using pytest-xdist):
```powershell
& D:\eco_nojin\.venv\Scripts\python.exe -m pytest -n auto
```

**Security tests specifically**:
```powershell
& D:\eco_nojin\.venv\Scripts\python.exe -m pytest services/security/tests/ -v
```

### 4.3 C++ Tests

C++ test executables are built alongside the extension and located at:
`engine/cpp_core/build2/tests/test_*.exe`

Run all C++ tests via CTest:
```powershell
cd engine\cpp_core\build2
ctest --output-on-failure
```

### 4.4 Python Environment for Tests

Tests require `PYTHONPATH="D:\HyDroMA;D:\eco_nojin"` to resolve imports correctly.
The `TestSettings` class in `engine/hydroma/config/settings.py:787-852` provides
safe test defaults (no real secrets, reads no `.env`).

---

## 5. Lint & Type Check

### 5.1 Ruff (Linting)

```powershell
& D:\eco_nojin\.venv\Scripts\python.exe -m ruff check engine/ services/
```

Configuration (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4"]
```

### 5.2 Mypy (Type Checking)

```powershell
& D:\eco_nojin\.venv\Scripts\python.exe -m mypy engine/ services/ --strict
```

Configuration (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

### 5.3 Pytest Collection Stats

Based on static analysis of the repository:
- **Total Python files**: 948
- **Test files**: 90
- **Test classes**: 218
- **Test functions**: 1,451
- **Test paths**: `engine/tests`, `engine/strict_tests`, `services/*/tests`

---

## 6. Environment Constraints

### 6.1 Current Environment

| Component | Status | Detail |
|-----------|--------|--------|
| Network access | ❌ Unavailable | No PyPI access; `pip install` fails |
| C++ compiler | ❌ Not available | Cannot rebuild `.pyd` |
| CMake | ❌ Not available | — |
| Ninja | ❌ Not available | — |

### 6.2 What Works

1. ✅ Static analysis (import guards, architecture checks)
2. ✅ Code inspection and review (source files)
3. ✅ Documentation generation
4. ✅ `pip list` via venv Python
5. ✅ `python -c "import ..."` for pure-Python modules
6. ✅ Reading existing C++ compiled extension (already built)

### 6.3 What Is Blocked

1. ❌ Installing new packages (no network)
2. ❌ Rebuilding C++ extension (no compiler, no CMake)
3. ❌ Running scientific engine tests (require numpy-dependent imports)
4. ❌ Any operation requiring network access

---

## 7. Configuration & Secrets

### 7.1 Environment Variables

Settings are loaded from `.env` (if present) and environment variables via
pydantic-settings. The `.env` file does **not** exist in this repository.

### 7.2 Required for Production

| Variable | Field | Notes |
|----------|-------|-------|
| `JWT_SECRET` | `jwt_secret` | 64+ chars, not a known default |
| `SECRET_KEY` | `secret_key` | 64+ chars, not a known default |
| `DATABASE_URL` | `database_url` | Must be PostgreSQL, not SQLite |
| `REDIS_URL` | `redis_url` | Not localhost:6379 |
| `TELEGRAM_BOT_TOKEN` | `telegram_bot_token` | Not placeholder |
| `SENTRY_DSN` | `sentry_dsn` | Warning only if missing |
| `OAUTH_ENCRYPTION_KEY` | `oauth_encryption_key` | 64+ chars (KeyError if empty) |
| `PASSKEY_RP_ID` | `passkey_rp_id` | Required when WebAuthn enabled |
| `PASSKEY_ORIGIN` | `passkey_origin` | Required when WebAuthn enabled |
| `OAUTH_REDIRECT_URI` | `oauth_redirect_uri` | Required when OAuth enabled |

### 7.3 Supabase Integration

Supabase credentials (separate from app settings):
```
SUPABASE_URL               — Project URL
SUPABASE_SERVICE_ROLE_KEY  — Service role key (server-side only)
SUPABASE_ANON_KEY          — Anonymous key (client-side)
SUPABASE_ACCESS_TOKEN      — Management API token for audit logging
SUPABASE_PROJECT_REF       — Project reference
```

**Note**: `SUPABASE_PROJECT_REF` defaults to `"cpncggavcfplewlhvvnw"` in
`services/security/audit.py:38` — this is a hardcoded fallback that should be
overridden in production deployments.

### 7.4 Settings Validation

The `Settings.validate_production_settings()` validator runs 21 production rules
(`engine/hydroma/config/rules.py:285-406`). In non-production environments, a
**fail-fast** checks that `SECRET_KEY` is non-empty. The `TestSettings` subclass
provides safe test defaults with no `.env` loading.

---

## 8. Build Commands Reference

| Action | Command |
|--------|---------|
| Install (editable) | `& D:\eco_nojin\.venv\Scripts\python.exe -m pip install -e ".[dev]"` |
| Run all Python tests | `& D:\eco_nojin\.venv\Scripts\python.exe -m pytest` |
| Run C++ tests | `cd engine\cpp_core\build2; ctest --output-on-failure` |
| Lint | `& D:\eco_nojin\.venv\Scripts\python.exe -m ruff check engine/ services/` |
| Type check | `& D:\eco_nojin\.venv\Scripts\python.exe -m mypy engine/ services/ --strict` |
| Build C++ extension (CMake) | `cd engine\cpp_core; cmake -S . -B build2 -DCMAKE_BUILD_TYPE=Release; cmake --build build2 --config Release` |
| Build C++ extension (MSVC) | `cd engine\cpp_core; .\build_pybind.bat` |
| Run security scanner | `& D:\eco_nojin\.venv\Scripts\python.exe tools/check_security.py` |
| Start dev server | `& D:\eco_nojin\.venv\Scripts\python.exe -m uvicorn services.api_gateway.main:app --reload` |
| List packages | `& D:\eco_nojin\.venv\Scripts\python.exe -m pip list` |

---

*End of Build & Environment Report — Generated 2026-10-09*
