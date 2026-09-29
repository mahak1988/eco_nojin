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
"%PYEXE%" -c "import sysconfig, pathlib, sys; p=pathlib.Path(sysconfig.get_paths()['include']); lib=pathlib.Path(sysconfig.get_config_var('LIBDIR') or pathlib.Path(sys.base_prefix,'libs')); import pybind11; pathlib.Path(r'%PATHS%').write_text(str(pybind11.get_include()) + '\n' + str(p) + '\n' + str(lib) + '\n' + sysconfig.get_config_var('EXT_SUFFIX'))"
if errorlevel 1 (
  echo [build_pybind] could not query include paths via "%PYEXE%"
  echo [build_pybind] run: .venv\Scripts\python.exe -m pip install -e ".[dev]"
  exit /b 1
)
set /a _n=0
for /f "usebackq delims=" %%I in ("%PATHS%") do (
  set /a _n+=1
  if !_n! EQU 1 (set "PYBIND_INC=%%I") else (if !_n! EQU 2 (set "PY_INC=%%I") else (if !_n! EQU 3 (set "PY_LIB=%%I") else (set "EXT_SUFFIX=%%I")))
)
if not defined PYBIND_INC goto :nopaths
if not defined PY_INC goto :nopaths
if not defined PY_LIB goto :nopaths
if not defined EXT_SUFFIX goto :nopaths

REM The output must carry the interpreter's ABI tag, e.g.
REM hydroma_core.cp312-win_amd64.pyd. An untagged hydroma_core.pyd is a real
REM hazard rather than a cosmetic one: CPython 3.12 prefers the tagged name and
REM will silently load a STALE extension that is still sitting next to it, so a
REM successful build appears to have had no effect. This is the failure recorded
REM in engine/cpp_core/README_BUILD_STATUS_FA.md, section on /Fe naming.
REM The tag is read from the interpreter rather than guessed, so a 3.11 build
REM cannot end up writing a 3.12 name.
set "MODULE=hydroma_core%EXT_SUFFIX%"

set "OUT=%~1"
if not defined OUT set "OUT=%CPP%\build"
if not exist "%OUT%" mkdir "%OUT%"

echo [build_pybind] cpp:       %CPP%
echo [build_pybind] pybind11:  %PYBIND_INC%
echo [build_pybind] python:    %PY_INC%
echo [build_pybind] pylib:     %PY_LIB%
echo [build_pybind] out:       %OUT%
echo [build_pybind] module:    %MODULE%
echo [build_pybind] sources:   11 kernels + nojin_calculator + bindings, /openmp:llvm

REM Remove a stale extension of the same name first. cl refuses to overwrite a
REM file that is loaded by another process, and leaving yesterday's binary in
REM place is how a change appears to do nothing.
if exist "%OUT%\%MODULE%" del /q "%OUT%\%MODULE%" >nul 2>&1

cl /nologo /std:c++20 /EHsc /W3 /O2 /openmp:llvm /LD ^
   /I"%CPP%\include" /I"%PYBIND_INC%" /I"%PY_INC%" ^
   "%CPP%\src\climate.cpp" "%CPP%\src\crop_water.cpp" "%CPP%\src\erosion.cpp" ^
   "%CPP%\src\hydrology.cpp" "%CPP%\src\indices.cpp" "%CPP%\src\nojin_calculator.cpp" ^
   "%CPP%\src\richards.cpp" "%CPP%\src\saint_venant.cpp" "%CPP%\src\sampling.cpp" ^
   "%CPP%\src\sediment.cpp" "%CPP%\src\soil.cpp" ^
   "%CPP%\bindings\bindings.cpp" ^
   /Fe:"%OUT%\%MODULE%" ^
   /link /LIBPATH:"%PY_LIB%"

if errorlevel 1 (
  echo [build_pybind] FAILED
  exit /b 1
)

REM cl derives the import library name from /Fe, so it now says
REM hydroma_core.cp312-win_amd64.lib rather than hydroma_core.lib. Move it to
REM the undecorated name the shipped layout expects.
for %%E in ("%OUT%\%MODULE%") do set "STEM=%%~nE"
if exist "%OUT%\%STEM%.lib" copy /y "%OUT%\%STEM%.lib" "%OUT%\hydroma_core.lib" >nul
if exist "%OUT%\%STEM%.exp" copy /y "%OUT%\%STEM%.exp" "%OUT%\hydroma_core.exp" >nul

if not exist "%OUT%\%MODULE%" (
  echo [build_pybind] FAILED -- cl reported success but %OUT%\%MODULE% is absent
  exit /b 1
)
echo [build_pybind] OK
exit /b 0

:nopaths
echo [build_pybind] could not resolve pybind11 / Python include directories
exit /b 1


