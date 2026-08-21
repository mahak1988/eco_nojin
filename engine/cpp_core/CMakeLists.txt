cmake_minimum_required(VERSION 3.22)

project(hydroma_core VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# Find OpenMP for parallel processing
find_package(OpenMP REQUIRED)

if(NOT OpenMP_FOUND)
  message(FATAL_ERROR "OpenMP is required but not found!")
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
# Add OpenMP to the hydroma_core library
target_link_libraries(hydroma_core PUBLIC OpenMP::OpenMP_CXX)
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

  # --- Added by Implementation Plan ---
  add_executable(test_soil_unit tests/test_soil_unit.cpp)
  target_link_libraries(test_soil_unit PRIVATE hydroma_core)
  add_test(NAME test_soil_unit COMMAND test_soil_unit)

  add_executable(benchmark_soil tests/benchmark_soil.cpp)
  target_link_libraries(benchmark_soil PRIVATE hydroma_core)

  add_executable(test_richards_unit tests/test_richards_unit.cpp)
  target_link_libraries(test_richards_unit PRIVATE hydroma_core)

  add_executable(benchmark_richards tests/benchmark_richards.cpp)
  target_link_libraries(benchmark_richards PRIVATE hydroma_core)

  add_executable(test_hydrology_unit tests/test_hydrology_unit.cpp)
  target_link_libraries(test_hydrology_unit PRIVATE hydroma_core)

  add_executable(benchmark_hydrology tests/benchmark_hydrology.cpp)
  target_link_libraries(benchmark_hydrology PRIVATE hydroma_core)

  add_executable(test_indices_unit tests/test_indices_unit.cpp)
  target_link_libraries(test_indices_unit PRIVATE hydroma_core)

  add_executable(benchmark_indices tests/benchmark_indices.cpp)
  target_link_libraries(benchmark_indices PRIVATE hydroma_core)

  add_executable(benchmark_soil_extended tests/benchmark_soil_extended.cpp)
  target_link_libraries(benchmark_soil_extended PRIVATE hydroma_core)

  add_executable(test_erosion_unit tests/test_erosion_unit.cpp)
  target_link_libraries(test_erosion_unit PRIVATE hydroma_core)

  add_executable(benchmark_erosion tests/benchmark_erosion.cpp)
  target_link_libraries(benchmark_erosion PRIVATE hydroma_core)

  add_executable(test_climate_unit tests/test_climate_unit.cpp)
  target_link_libraries(test_climate_unit PRIVATE hydroma_core)

  add_executable(benchmark_climate tests/benchmark_climate.cpp)
  target_link_libraries(benchmark_climate PRIVATE hydroma_core)

  add_executable(test_crop_water_unit tests/test_crop_water_unit.cpp)
  target_link_libraries(test_crop_water_unit PRIVATE hydroma_core)

  add_executable(benchmark_crop_water tests/benchmark_crop_water.cpp)
  target_link_libraries(benchmark_crop_water PRIVATE hydroma_core)

  add_executable(test_sediment_unit tests/test_sediment_unit.cpp)
  target_link_libraries(test_sediment_unit PRIVATE hydroma_core)

  add_executable(benchmark_sediment tests/benchmark_sediment.cpp)
  target_link_libraries(benchmark_sediment PRIVATE hydroma_core)

  add_executable(test_saint_venant_unit tests/test_saint_venant_unit.cpp)
  target_link_libraries(test_saint_venant_unit PRIVATE hydroma_core)

  add_executable(benchmark_saint_venant tests/benchmark_saint_venant.cpp)
  target_link_libraries(benchmark_saint_venant PRIVATE hydroma_core)

  add_executable(test_sampling_unit tests/test_sampling_unit.cpp)
  target_link_libraries(test_sampling_unit PRIVATE hydroma_core)

  add_executable(benchmark_sampling tests/benchmark_sampling.cpp)
  target_link_libraries(benchmark_sampling PRIVATE hydroma_core)
  # ------------------------------------

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