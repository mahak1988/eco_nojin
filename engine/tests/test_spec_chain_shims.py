"""Spec §3.1 chain shims: additive half of remediation item A-4.

Five packages mirror the spec §3.1 chain as re-export shims:

``engine.indicators``, ``engine.knowledge``, ``engine.decision``,
``engine.scenario`` and ``engine.numerical``. Each re-exports the
TODAY-correct modules so the chain is navigable; module migration into them
happens later, behind a mandate, one family at a time and behind a parity
test. These tests pin the two properties an additive shim must hold:

1. it imports, and every name it advertises in ``__all__`` is really there;
2. it duplicates no logic — a shim that starts computing has stopped being a
   shim, and the AST assertion below is what keeps that true;
3. the high-traffic indicator names are the *same objects* as the originals,
   so a caller cannot silently end up on a second copy of a kernel.

``engine/knowledge`` is deliberately not in the AST-checked set. It already
exists as a real engine package — ``KnowledgeEngine`` and its ``Fact`` /
``Rule`` / ``Claim`` vocabulary live there — so it is the spec §3.1 knowledge
node rather than a shim this change created, and its own legitimately numeric
code must not be held to a shim ceiling. The test that follows states that
explicitly instead of leaving it implicit.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
from types import ModuleType

#: The five spec §3.1 chain nodes, in chain order. Every one must import and
#: every name each advertises must resolve.
SHIM_MODULES = (
    "engine.indicators",
    "engine.knowledge",
    "engine.decision",
    "engine.scenario",
    "engine.numerical",
)

#: The shims this mandate created: pure re-export layers, so their bodies must
#: contain no computation of their own. ``engine.knowledge`` is excluded and
#: asserted separately (see the module docstring).
CREATED_SHIM_MODULES = (
    "engine.indicators",
    "engine.decision",
    "engine.scenario",
    "engine.numerical",
)


def _module(name: str) -> ModuleType:
    return importlib.import_module(name)


def _source_path(module: ModuleType) -> Path:
    source = inspect.getsourcefile(module)
    assert source is not None, f"{module.__name__} has no source file"
    return Path(source)


def _numeric_return_lines(tree: ast.AST) -> list[int]:
    """Line numbers of ``return <numeric literal>`` statements in *tree*.

    ``bool`` is a subclass of ``int`` in Python, so the boolean check has to
    come first or every ``return True`` would read as a numeric constant.
    """
    offenders: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Constant):
            continue
        value = node.value.value
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float, complex)):
            offenders.append(node.lineno)
    return offenders


def test_every_shim_imports() -> None:
    """Every spec §3.1 chain node imports and resolves its own ``__all__``."""
    missing: list[str] = []
    empty: list[str] = []
    for name in SHIM_MODULES:
        module = _module(name)
        advertised = list(getattr(module, "__all__", []))
        if not advertised:
            empty.append(name)
        for public in advertised:
            if not hasattr(module, public):
                missing.append(f"{name}.{public}")
    assert empty == [], f"shim modules advertising nothing: {empty}"
    assert missing == [], f"names advertised in __all__ but not importable: {missing}"


def test_shims_do_not_duplicate_logic() -> None:
    """A shim holds no computation: no ``return`` of a numeric literal.

    Asserted by AST over each created shim's source. The placeholders the
    mandate allows (the documented ``NotImplementedError``-raising stand-ins
    for modules that could not be imported) raise, so they are compatible with
    the ceiling by construction. ``engine.knowledge`` is out of scope on
    purpose — see the module docstring and the test below.
    """
    offenders: list[str] = []
    for name in CREATED_SHIM_MODULES:
        tree = ast.parse(_source_path(_module(name)).read_text(encoding="utf-8"))
        for lineno in _numeric_return_lines(tree):
            offenders.append(f"{name}:{lineno}")
    assert offenders == [], f"shim bodies contain numeric returns: {offenders}"


def test_indicators_shim_exposes_the_priority_ones() -> None:
    """The A-4 priority trio is callable here and is the original object."""
    shim = _module("engine.indicators")

    for name in ("calculate_spi", "water_balance", "water_productivity"):
        assert callable(getattr(shim, name)), f"engine.indicators.{name} is not callable"

    assert shim.calculate_spi is _module("engine.hydroma.spi_calculator").calculate_spi
    assert shim.water_balance is _module("engine.hydroma.water_balance").water_balance
    water_productivity = _module("engine.hydroma.water_productivity")
    assert shim.water_productivity is water_productivity.water_productivity


def test_knowledge_node_is_the_existing_engine_package() -> None:
    """Why ``engine.knowledge`` is a chain node but not a created shim.

    The path is already taken by the Knowledge Engine itself, and this mandate
    is additive and touches no existing file. Stating it as an assertion keeps
    the exclusion in :func:`test_shims_do_not_duplicate_logic` visible instead
    of leaving a reader to wonder why one of the five nodes is missing.
    """
    knowledge = _module("engine.knowledge")
    assert knowledge.KnowledgeEngine.__module__ == "engine.knowledge"
    assert "KnowledgeEngine" in knowledge.__all__
    assert knowledge.__name__ not in CREATED_SHIM_MODULES
