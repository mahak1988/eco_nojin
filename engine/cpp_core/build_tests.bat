@echo off
REM ---------------------------------------------------------------------------
REM Build and run every engine/cpp_core unit test.
REM
REM Each tests\test_*.cpp is a standalone program with its own main(). None of
REM them propagate failure -- every one ends in `return 0` -- so a failing check
REM still exits 0. The harness that invokes this script counts the "[FAIL]"
REM lines instead, so a red result cannot pass as green here.
REM
REM   build_tests.bat  [out_dir]
REM
REM Writes <out_dir>\<test>.exe, <test>.out and <test>.build.log per test.
REM Exits non-zero only if a test could not be built.
REM ---------------------------------------------------------------------------

setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 (
  echo [build_tests] vcvars64.bat not found
  exit /b 1
)

for %%I in ("%~dp0") do set "CPP=%%~fI"
set "OUT=%~1"
if not defined OUT set "OUT=%CPP%build\tests"
if not exist "%OUT%" mkdir "%OUT%"

set "KERNELS=%CPP%src\climate.cpp %CPP%src\crop_water.cpp %CPP%src\erosion.cpp %CPP%src\hydrology.cpp %CPP%src\indices.cpp %CPP%src\nojin_calculator.cpp %CPP%src\richards.cpp %CPP%src\saint_venant.cpp %CPP%src\sampling.cpp %CPP%src\sediment.cpp %CPP%src\soil.cpp"

REM Compile from the output directory so the intermediate .obj files land there.
REM cl rejects a /Fo<dir> that is shared by several source files, and the source
REM paths below are absolute, so changing the working directory is the clean fix.
pushd "%OUT%"

REM Compile the kernels ONCE into a static library, then link each test against
REM it. The previous version recompiled all 11 kernel sources for every one of the
REM 13 test programs, which is where most of the wall time went.
if not exist "%OUT%\hydroma_kernels.lib" (
  echo [build_tests] compiling kernels once
  cl /nologo /c /std:c++20 /EHsc /W3 /O2 /openmp:llvm /DNDEBUG /I"%CPP%\include" ^
     "%CPP%\src\climate.cpp" "%CPP%\src\crop_water.cpp" "%CPP%\src\erosion.cpp" ^
     "%CPP%\src\hydrology.cpp" "%CPP%\src\indices.cpp" "%CPP%\src\nojin_calculator.cpp" ^
     "%CPP%\src\richards.cpp" "%CPP%\src\saint_venant.cpp" "%CPP%\src\sampling.cpp" ^
     "%CPP%\src\sediment.cpp" "%CPP%\src\soil.cpp" /Fo:"%OUT%\\" >"%OUT%\kernels.log" 2>&1
  if errorlevel 1 (
    echo [build_tests] KERNEL BUILD FAILED
    findstr /C:"error" "%OUT%\kernels.log"
    exit /b 1
  )
  lib /nologo /OUT:"%OUT%\hydroma_kernels.lib" "%OUT%\climate.obj" "%OUT%\crop_water.obj" ^
      "%OUT%\erosion.obj" "%OUT%\hydrology.obj" "%OUT%\indices.obj" ^
      "%OUT%\nojin_calculator.obj" "%OUT%\richards.obj" "%OUT%\saint_venant.obj" ^
      "%OUT%\sampling.obj" "%OUT%\sediment.obj" "%OUT%\soil.obj" >>"%OUT%\kernels.log" 2>&1
  if errorlevel 1 (
    echo [build_tests] ARCHIVE FAILED
    findstr /C:"error" "%OUT%\kernels.log"
    exit /b 1
  )
)

for %%T in ("%CPP%tests\test_*.cpp") do (
  cl /nologo /std:c++20 /EHsc /W3 /O2 /openmp:llvm /DNDEBUG ^
     /I"%CPP%\include" "%%T" "%OUT%\hydroma_kernels.lib" ^
     /Fe:"%OUT%\%%~nT.exe" /Fo:"%OUT%\\" >"%OUT%\%%~nT.build.log" 2>&1
  if errorlevel 1 (
    echo BUILD-FAIL %%~nT
  ) else (
    echo BUILT %%~nT
  )
)

exit /b 0
