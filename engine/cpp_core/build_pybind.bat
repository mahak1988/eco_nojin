@echo off
REM ---------------------------------------------------------------------------
REM Build the hydroma_core pybind11 module from a clean checkout.
REM
REM CMake is not required. This compiles the same sources listed in
REM engine/cpp_core/CMakeLists.txt with cl directly, so the native module is
REM reproducible from a clean tree without an extra toolchain dependency.
REM
REM   build_pybind.bat  [out_dir]
REM
REM Produces <out_dir>\hydroma_core.pyd
REM
REM Requires: MSVC Build Tools (vcvars64.bat on PATH via the call below) and
REM pybind11 importable by the active interpreter:
REM   .venv\Scripts\python.exe -m pip install -e ".[dev]"
REM ---------------------------------------------------------------------------

setlocal enabledelayedexpansion
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 (
  echo [build_pybind] vcvars64.bat not found or failed
  exit /b 1
)

for %%I in ("%~dp0") do set "CPP=%%~fI"
for %%I in ("%CPP%\..\..") do set "ROOT=%%~fI"
set "PYEXE=%ROOT%\.venv\Scripts\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

REM Resolve the pybind11 and Python include directories into a file first.
REM `for /f` over a command containing a quoted executable path is fragile in
REM cmd, whereas reading a plain file has no quoting problem at all.
set "PATHS=%TEMP%\hydroma_build_paths.txt"
"%PYEXE%" -c "import sysconfig, pathlib, sys; p=pathlib.Path(sysconfig.get_paths()['include']); lib=pathlib.Path(sysconfig.get_config_var('LIBDIR') or pathlib.Path(sys.base_prefix,'libs')); import pybind11; pathlib.Path(r'%PATHS%').write_text(str(pybind11.get_include()) + '\n' + str(p) + '\n' + str(lib))"
if errorlevel 1 (
  echo [build_pybind] could not query include paths via "%PYEXE%"
  echo [build_pybind] run: .venv\Scripts\python.exe -m pip install -e ".[dev]"
  exit /b 1
)
set /a _n=0
for /f "usebackq delims=" %%I in ("%PATHS%") do (
  set /a _n+=1
  if !_n! EQU 1 (set "PYBIND_INC=%%I") else (if !_n! EQU 2 (set "PY_INC=%%I") else (set "PY_LIB=%%I"))
)
if not defined PYBIND_INC goto :nopaths
if not defined PY_INC goto :nopaths
if not defined PY_LIB goto :nopaths

set "OUT=%~1"
if not defined OUT set "OUT=%CPP%\build"
if not exist "%OUT%" mkdir "%OUT%"

echo [build_pybind] cpp:       %CPP%
echo [build_pybind] pybind11:  %PYBIND_INC%
echo [build_pybind] python:    %PY_INC%
echo [build_pybind] pylib:     %PY_LIB%
echo [build_pybind] out:       %OUT%
echo [build_pybind] sources:   11 kernels + nojin_calculator + bindings, /openmp:llvm

cl /nologo /std:c++20 /EHsc /W3 /O2 /openmp:llvm /LD ^
   /I"%CPP%\include" /I"%PYBIND_INC%" /I"%PY_INC%" ^
   "%CPP%\src\climate.cpp" "%CPP%\src\crop_water.cpp" "%CPP%\src\erosion.cpp" ^
   "%CPP%\src\hydrology.cpp" "%CPP%\src\indices.cpp" "%CPP%\src\nojin_calculator.cpp" ^
   "%CPP%\src\richards.cpp" "%CPP%\src\saint_venant.cpp" "%CPP%\src\sampling.cpp" ^
   "%CPP%\src\sediment.cpp" "%CPP%\src\soil.cpp" ^
   "%CPP%\bindings\bindings.cpp" ^
   /Fe:"%OUT%\hydroma_core.pyd" ^
   /link /LIBPATH:"%PY_LIB%"

if errorlevel 1 (
  echo [build_pybind] FAILED
  exit /b 1
)
echo [build_pybind] OK
exit /b 0

:nopaths
echo [build_pybind] could not resolve pybind11 / Python include directories
exit /b 1


