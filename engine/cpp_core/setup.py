from pybind11 import get_cmake_dir
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup
from pathlib import Path

# Get the directory of this setup.py
THIS_DIR = Path(__file__).resolve().parent

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "cpp_nojin",  # Name of the Python module
        sources=[
            str(THIS_DIR / "bindings.cpp"),
            str(THIS_DIR / "nojin_calculator.cpp"),
            # Add other .cpp files here as needed
        ],
        include_dirs=[
            # Path to pybind11 headers
            get_cmake_dir(),
            # Path to local headers
            str(THIS_DIR),
            str(THIS_DIR / "include"),
        ],
        language="c++",
        cxx_std=17,  # Updated to C++17 for better compatibility
        define_macros=[("VERSION_INFO", '"dev"')],
    ),
]

setup(
    name="cpp_nojin",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
    setup_requires=["pybind11>=2.10"],
    install_requires=["pybind11>=2.10"],
)
