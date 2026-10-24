"""Shared data files and the generators that project them into other backends.

``soil_vg_table.csv`` is the single source of the van Genuchten parameter table
that the whole engine reads. It is loaded by
:mod:`engine.hydroma.soil.parameters`, so the file is load-bearing rather than
incidental, and it is listed in ``package-data`` for that reason.

``generate_cpp_table`` projects the same rows into ``cpp_core/src/soil.cpp``,
which cannot read a CSV at run time. Run it with ``--check`` in CI so that a
hand edit to the generated block fails the build instead of quietly becoming a
fifth copy of the table.
"""
