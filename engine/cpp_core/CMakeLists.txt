cmake_minimum_required(VERSION 3.22)

project(hydroma_core VERSION 2.0.0 LANGUAGES CXX)

# -----------------------------------------------------------------------------
# Basic C++20 Configuration
# -----------------------------------------------------------------------------
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Default build type
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# -----------------------------------------------------------------------------
# Platform-specific settings
# -----------------------------------------------------------------------------
if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
  # Windows: use multithreaded DLL runtime
  if(MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
    add_compile_options(
      /W4
      /permissive-
      /EHsc
      /bigobj
    )
  endif()
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  # Linux: GCC/Clang
  add_compile_options(
    -Wall
    -Wextra
    -Wpedantic
    -fPIC
  )
  if(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    add_compile_options(-Wno-unknown-warning-option)
  endif()
endif()

# -----------------------------------------------------------------------------
# Find dependencies
# -----------------------------------------------------------------------------
# OpenMP for parallel processing
find_package(OpenMP REQUIRED)
if(NOT OpenMP_FOUND)
  message(FATAL_ERROR "OpenMP is required but not found!")
endif()

# Python for pybind11
find_package(Python COMPONENTS Interpreter Development.Module QUIET)

# pybind11 - try find_package first, then fallback to FetchContent
set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG QUIET)

if(NOT pybind11_FOUND)
  # Fetch pybind11 from GitHub if not found
  include(FetchContent)
  FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG v2.13.6
  )
  FetchContent_MakeAvailable(pybind11)
  message(STATUS "pybind11 fetched from GitHub")
else()
  message(STATUS "pybind11 found via find_package")
endif()

# -----------------------------------------------------------------------------
# Build options
# -----------------------------------------------------------------------------
option(HYDROMA_BUILD_TESTS "Build the self-contained test executables" ON)
option(HYDROMA_BUILD_PYTHON_BINDINGS "Build the pybind11 Python module" ON)
option(HYDROMA_BUILD_BENCHMARKS "Build benchmark executables" OFF)
option(HYDROMA_ENABLE_SANITIZERS "Enable Address/Thread/Undefined sanitizers (Linux only)" OFF)

# -----------------------------------------------------------------------------
# Static library: hydroma_core
# -----------------------------------------------------------------------------
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
  src/nojin_calculator.cpp
)

target_link_libraries(hydroma_core PUBLIC OpenMP::OpenMP_CXX)
target_include_directories(hydroma_core PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Compile options
target_compile_options(hydroma_core PRIVATE
  $<$<CXX_COMPILER_ID:MSVC>:/W4 /permissive- /EHsc /bigobj>
  $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Wpedantic -fPIC>
)

# Sanitizers (Linux only, optional)
if(HYDROMA_ENABLE_SANITIZERS AND CMAKE_SYSTEM_NAME STREQUAL "Linux")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address,undefined -fno-omit-frame-pointer")
  set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=address,undefined")
  set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -fsanitize=address,undefined")
endif()

# -----------------------------------------------------------------------------
# Python bindings module: hydroma_core (importable as hydroma_core)
# -----------------------------------------------------------------------------
if(HYDROMA_BUILD_PYTHON_BINDINGS AND Python_Development_FOUND AND pybind11_FOUND)
  # Determine Python extension suffix
  if(WIN32)
    set(PYTHON_EXTENSION_SUFFIX ".pyd")
  else()
    set(PYTHON_EXTENSION_SUFFIX "${PYTHON_MODULE_EXTENSION}")
  endif()

  pybind11_add_module(hydroma_core_py bindings/bindings.cpp)
  
  # Output name must be "hydroma_core" to match import
  set_target_properties(hydroma_core_py PROPERTIES
    OUTPUT_NAME hydroma_core
    PREFIX ""  # Remove "lib" prefix on Linux
    SUFFIX "${PYTHON_EXTENSION_SUFFIX}"
    # On Windows, ensure .pyd extension
    # On Linux, ensure .so extension
  )

  target_link_libraries(hydroma_core_py PRIVATE hydroma_core pybind11::module)
  target_include_directories(hydroma_core_py PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

  target_compile_options(hydroma_core_py PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /permissive- /EHsc /bigobj>
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Wpedantic -fPIC>
  )

  # Install Python module
  install(TARGETS hydroma_core_py
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}/hydroma_core
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  )

  message(STATUS "Python bindings will be built as: hydroma_core${PYTHON_EXTENSION_SUFFIX}")
else()
  message(STATUS "Python bindings SKIPPED:")
  if(NOT Python_Development_FOUND)
    message(STATUS "  - Python development headers not found")
  endif()
  if(NOT pybind11_FOUND)
    message(STATUS "  - pybind11 not found")
  endif()
endif()

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
if(HYDROMA_BUILD_TESTS)
  enable_testing()
  
  # Helper function to add test executable
  function(add_hydroma_test name source)
    add_executable(${name} ${source})
    target_link_libraries(${name} PRIVATE hydroma_core)
    add_test(NAME ${name} COMMAND ${name})
    set_target_properties(${name} PROPERTIES
      RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/tests
    )
  endfunction()

  # Core tests
  add_hydroma_test(hydroma_tests tests/test_hydroma.cpp)
  add_hydroma_test(hydroma_advanced_tests tests/test_advanced.cpp)
  
  # Unit tests per module
  add_hydroma_test(test_soil_unit tests/test_soil_unit.cpp)
  add_hydroma_test(test_richards_unit tests/test_richards_unit.cpp)
  add_hydroma_test(test_hydrology_unit tests/test_hydrology_unit.cpp)
  add_hydroma_test(test_indices_unit tests/test_indices_unit.cpp)
  add_hydroma_test(test_erosion_unit tests/test_erosion_unit.cpp)
  add_hydroma_test(test_climate_unit tests/test_climate_unit.cpp)
  add_hydroma_test(test_crop_water_unit tests/test_crop_water_unit.cpp)
  add_hydroma_test(test_sediment_unit tests/test_sediment_unit.cpp)
  add_hydroma_test(test_saint_venant_unit tests/test_saint_venant_unit.cpp)
  add_hydroma_test(test_sampling_unit tests/test_sampling_unit.cpp)
  add_hydroma_test(test_nojin_calculator tests/test_nojin_calculator.cpp)

  # Benchmarks (only if enabled)
  if(HYDROMA_BUILD_BENCHMARKS)
    add_hydroma_test(benchmark_soil tests/benchmark_soil.cpp)
    add_hydroma_test(benchmark_richards tests/benchmark_richards.cpp)
    add_hydroma_test(benchmark_hydrology tests/benchmark_hydrology.cpp)
    add_hydroma_test(benchmark_indices tests/benchmark_indices.cpp)
    add_hydroma_test(benchmark_soil_extended tests/benchmark_soil_extended.cpp)
    add_hydroma_test(benchmark_erosion tests/benchmark_erosion.cpp)
    add_hydroma_test(benchmark_climate tests/benchmark_climate.cpp)
    add_hydroma_test(benchmark_crop_water tests/benchmark_crop_water.cpp)
    add_hydroma_test(benchmark_sediment tests/benchmark_sediment.cpp)
    add_hydroma_test(benchmark_saint_venant tests/benchmark_saint_venant.cpp)
    add_hydroma_test(benchmark_sampling tests/benchmark_sampling.cpp)
  endif()

  # Set test output directory
  set_property(DIRECTORY APPEND PROPERTY
    ADDITIONAL_MAKE_CLEAN_FILES "${CMAKE_CURRENT_BINARY_DIR}/tests/*.exe"
  )

endif()

# -----------------------------------------------------------------------------
# Installation
# -----------------------------------------------------------------------------
install(TARGETS hydroma_core
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(DIRECTORY include/
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/hydroma_core
  FILES_MATCHING PATTERN "*.h" PATTERN "*.hpp"
)

# -----------------------------------------------------------------------------
# Packaging (CPack)
# -----------------------------------------------------------------------------
if(HYDROMA_BUILD_PYTHON_BINDINGS)
  include(CPack)
  set(CPACK_PACKAGE_NAME "hydroma_core")
  set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
  set(CPACK_GENERATOR "TGZ;ZIP")
endif()

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
message(STATUS "=== hydroma_core Build Summary ===")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  OpenMP: ${OpenMP_FOUND}")
message(STATUS "  Python: ${Python_Development_FOUND}")
message(STATUS "  pybind11: ${pybind11_FOUND}")
message(STATUS "  Build Tests: ${HYDROMA_BUILD_TESTS}")
message(STATUS "  Build Python Bindings: ${HYDROMA_BUILD_PYTHON_BINDINGS}")
message(STATUS "  Build Benchmarks: ${HYDROMA_BUILD_BENCHMARKS}")
message(STATUS "===================================")