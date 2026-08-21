@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "%~dp0"
cl /nologo /std:c++20 /EHsc /W4 /O2 /Iinclude ^
  src\hydrology.cpp src\soil.cpp src\erosion.cpp src\climate.cpp src\indices.cpp ^
  src\richards.cpp src\saint_venant.cpp src\crop_water.cpp src\sediment.cpp src\sampling.cpp ^
  tests\test_hydroma.cpp /Fe:hydroma_tests.exe
