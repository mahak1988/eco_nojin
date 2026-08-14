cmake_minimum_required(VERSION 3.22)

project(hydroma_core VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

option(HYDROMA_BUILD_TESTS "Build the self-contained test executables" ON)
option(HYDROMA_BUILD_PYTHON_BINDINGS "Build the pybind11 Python module" ON)

add_library(hydroma_core STATIC
  src/hydrology.cpp
  src/soil.cpp
  src/erosion.cpp
  src/climate.cpp
  src/indices.cpp
  src/richards.cpp
  src/saint_venant.cpp
  src/crop_water.cpp
  src/sediment.cpp
  src/sampling.cpp
)
target_include_directories(hydroma_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_options(hydroma_core PRIVATE
  $<$<CXX_COMPILER_ID:MSVC>:/W4>
  $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra>
)

if(HYDROMA_BUILD_TESTS)
  enable_testing()
  add_executable(hydroma_tests tests/test_hydroma.cpp)
  target_link_libraries(hydroma_tests PRIVATE hydroma_core)
  add_test(NAME hydroma_tests COMMAND hydroma_tests)

  add_executable(hydroma_advanced_tests tests/test_advanced.cpp)
  target_link_libraries(hydroma_advanced_tests PRIVATE hydroma_core)
  add_test(NAME hydroma_advanced_tests COMMAND hydroma_advanced_tests)
endif()

if(HYDROMA_BUILD_PYTHON_BINDINGS)
  # pybind11 3.x: resolve Python explicitly before the pybind11 config.
  find_package(Python COMPONENTS Interpreter Development.Module QUIET)
  set(PYBIND11_FINDPYTHON ON)
  find_package(pybind11 CONFIG QUIET)
  if(pybind11_FOUND)
    pybind11_add_module(hydroma_core_py bindings/bindings.cpp)
    # .pyd must be hydroma_core (matches PYBIND11_MODULE); keep the import
    # library name distinct so it does not clash with the static lib .lib.
    set_target_properties(hydroma_core_py PROPERTIES
      OUTPUT_NAME hydroma_core
      ARCHIVE_OUTPUT_NAME hydroma_core_py
    )
    target_link_libraries(hydroma_core_py PRIVATE hydroma_core)
    target_compile_options(hydroma_core_py PRIVATE
      $<$<CXX_COMPILER_ID:MSVC>:/W4>
    )
  else()
    message(STATUS "pybind11 not found - Python bindings skipped "
                   "(install pybind11 via pip: python -m pip install pybind11)")
  endif()
endif()
