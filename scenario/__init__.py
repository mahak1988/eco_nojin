"""Eco Nojin scenario-definition layer (ECO-12).

Root-level home for versioned scenario *definitions* and the tooling that
reads, validates and compares them. This package exists because the engine
stub at ``engine/hydroma/scenario/__init__.py`` is a one-line empty placeholder
and is deliberately left untouched: the spec-shaped ECO-12 path is built here
instead of by editing engine code.

Nothing in this package executes anything. See ``scenario/engine/
baseline_manager.py`` for what is implemented (definition, versioning,
diff) and what is explicitly not (phase 2 execution).
"""
