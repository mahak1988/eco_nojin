from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import os

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "cpp_nojin",  # Name of the Python module
        sources=[
            "bindings.cpp",
            "nojin_calculator.cpp",
            # Add other .cpp files here as needed
        ],
        include_dirs=[
            # Path to pybind11 headers
            get_cmake_dir(),
            # Path to local headers
            ".",
        ],
        language='c++',
        cxx_std=14, # Specify C++ standard
    ),
]

setup(
    name="cpp_nojin",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
)
