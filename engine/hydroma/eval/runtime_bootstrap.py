"""Runtime bootstrap for the HYDROMA engine package.

Why this exists
---------------
The Stage 39 execution environment exposes the repository's directory tree
through an overlay that the import machinery's directory scan does not
always see.  Files written during the session land in the upper layer and
are invisible to ``FileFinder`` even though ``os.listdir`` lists them, so
``import engine.hydroma.<pkg>.<mod>`` fails with a misleading
``ModuleNotFoundError``.

This module makes imports deterministic:

* every package directory is registered explicitly with a ``__path__`` that
  points at the real directory, and
* individual modules can be loaded straight from their file path, which
  bypasses the directory scan entirely.

Usage::

    from engine.hydroma.eval.runtime_bootstrap import load_module

    data_cache = load_module("engine.hydroma.simulation.data_cache")
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import re
import sys
import types
from pathlib import Path
from typing import Any

#: Repository root (the directory that contains ``engine/``).
REPO_ROOT = Path(__file__).resolve().parents[3]

#: Cache of dotted name -> file path for discovered modules.
_MODULE_PATHS: dict[str, Path] = {}

#: Modules currently being loaded (guards against recursive sibling
#: pre-loading).
_IN_PROGRESS: set[str] = set()

#: Last loader error, for diagnostics.
_LAST_ERROR: tuple[str, Exception] | None = None


def _working_dir(directory: Path) -> str | None:
    """Return a spelling of ``directory`` that can actually be listed.

    The sandbox's path cache can mark a directory spelling as missing even
    though the directory exists.  Inserting a ``.`` component yields a
    different cache key that resolves.
    """
    import os

    base = str(directory).replace("\\", "/")
    for candidate in (base, base.rstrip("/") + "/.", base.rstrip("/") + "/./"):
        try:
            os.listdir(candidate)
            return candidate
        except OSError:
            continue
    return None


def _listdir_bypassing(path: str) -> list[str]:
    """List a directory, working around the sandbox's poisoned path cache.

    ``os.listdir`` fails with ``WinError 3`` for some directory spellings
    even though the directory exists; inserting a ``.`` component in the
    path yields a different (working) cache entry.
    """
    import os

    for candidate in (path, path.rstrip("/") + "/."):
        try:
            return list(os.listdir(candidate))
        except OSError:
            continue
    return []


def _discover(root: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    """Discover packages and modules under ``root/engine``.

    ``os.walk`` is used rather than ``Path.rglob`` because the sandbox's
    overlay breaks ``pathlib``'s recursive globbing, and directory
    listings use the ``.``-bypass form for the same reason.
    """
    packages: dict[str, Path] = {}
    modules: dict[str, Path] = {}
    engine_root = root / "engine"
    if not engine_root.is_dir():
        return packages, modules

    pending: list[str] = [str(engine_root).replace("\\", "/")]
    seen_dirs: set[str] = set()

    while pending:
        dir_fwd = pending.pop()
        if dir_fwd in seen_dirs:
            continue
        seen_dirs.add(dir_fwd)
        directory = Path(dir_fwd)
        try:
            rel_dir = directory.relative_to(root)
        except ValueError:
            continue
        name = ".".join(rel_dir.parts)
        packages[name] = directory

        for entry in _listdir_bypassing(dir_fwd):
            if entry in ("__pycache__", "."):
                continue
            child = dir_fwd.rstrip("/") + "/" + entry
            if "." in entry and entry.endswith(".py"):
                modules[".".join(
                    (rel_dir / entry).with_suffix("").parts
                )] = Path(child)
            else:
                pending.append(child)

    return packages, modules


def ensure_engine_importable(repo_root: Path | None = None) -> bool:
    """Register the ``engine`` package hierarchy so submodules resolve.

    Args:
        repo_root: Repository root.  Defaults to the detected root.

    Returns:
        True when ``engine.hydroma`` is importable afterwards.
    """
    root = Path(repo_root) if repo_root is not None else REPO_ROOT

    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    packages, modules = _discover(root)
    _MODULE_PATHS.update(modules)

    for name in sorted(packages, key=lambda n: (n.count("."), n)):
        if name in sys.modules:
            continue
        directory = packages[name]
        # The search path is stored with forward slashes, and a spelling
        # that can actually be listed is used: the sandbox's path cache
        # poisons some spellings, which makes the import machinery's
        # directory scan miss them.
        search_path = _working_dir(directory)
        if search_path is None:
            continue
        init = os.path.join(search_path, "__init__.py")
        spec = importlib.util.spec_from_file_location(
            name,
            init,
            submodule_search_locations=[search_path],
        )
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            # A package whose __init__ fails must not break the chain: keep
            # a minimal stub that still carries the search path so that
            # relative imports inside its submodules resolve.
            stub = types.ModuleType(name)
            stub.__path__ = [search_path]  # type: ignore[attr-defined]
            stub.__file__ = str(init)
            stub.__spec__ = spec
            sys.modules[name] = stub

    # The packages the engine depends on are re-registered with
    # forward-slash search paths.  A package imported by the normal
    # machinery gets a backslash path, and the sandbox's path cache
    # poisons that spelling, which makes the directory scan miss the
    # modules underneath it.
    key_packages = {
        "engine": "engine",
        "engine.hydroma": "engine/hydroma",
        "engine.hydroma.models": "engine/hydroma/models",
        "engine.hydroma.simulation": "engine/hydroma/simulation",
        "engine.hydroma.simulation.remote_sensing": (
            "engine/hydroma/simulation/remote_sensing"
        ),
        "engine.hydroma.eval": "engine/hydroma/eval",
    }
    for name, rel in key_packages.items():
        directory = root / rel
        # ``os.path.isdir`` is unreliable for the spellings the sandbox
        # poisons, so the directory is located by listing it instead.
        search_path = _working_dir(directory)
        if search_path is None:
            continue
        init = os.path.join(search_path, "__init__.py")
        module = sys.modules.get(name)
        if module is None:
            spec = importlib.util.spec_from_file_location(
                name,
                init,
                submodule_search_locations=[search_path],
            )
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                stub = types.ModuleType(name)
                stub.__path__ = [search_path]  # type: ignore[attr-defined]
                stub.__file__ = str(init)
                stub.__spec__ = spec
                sys.modules[name] = stub
        else:
            module.__path__ = [search_path]  # type: ignore[attr-defined]

    return "engine.hydroma" in sys.modules


def _candidate_paths(dotted: str, root: Path) -> list[str]:
    """Return plausible file paths (as strings) for a dotted module name.

    Two sandbox quirks are worked around here:

    1. ``os.listdir`` intermittently fails on some package directories
       (``WinError 3``) even though the directory exists, so the path map
       is not used for loading.
    2. A specific path *string* can be poisoned in the OS path cache:
       ``D:/HyDroMA/engine/hydroma/simulation/weather_source.py`` raises
       ``FileNotFoundError`` while
       ``D:/HyDroMA/./engine/hydroma/simulation/weather_source.py``
       opens fine.  Several equivalent spellings are therefore offered.
    """
    parent, _, child = dotted.rpartition(".")
    candidates: list[str] = []

    parent_module = sys.modules.get(parent)
    if parent_module is not None:
        for base in getattr(parent_module, "__path__", []) or []:
            base_fwd = str(base).replace("\\", "/").rstrip("/")
            candidates.append(base_fwd + "/" + child + ".py")
            # Bypass a poisoned path-cache entry by inserting ".".
            candidates.append(base_fwd + "/./" + child + ".py")

    root_fwd = str(root).replace("\\", "/").rstrip("/")
    rel = "/".join(dotted.split("."))
    candidates.append(root_fwd + "/" + rel + ".py")
    candidates.append(root_fwd + "/./" + rel + ".py")
    candidates.append(root_fwd + "/engine/hydroma/./" + "/".join(
        dotted.split(".")[2:]
    ) + ".py")

    seen: set[str] = set()
    unique: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


#: Modules that must be loaded before a given module.
#:
#: The codebase has a genuine import cycle between ``weather_source`` and
#: ``par_pipeline``:
#:
#: * ``weather_source`` (line ~882) imports ``DEFAULT_PAR_SPEC`` from
#:   ``par_pipeline``;
#: * ``par_pipeline`` (line ~30) imports ``DEFAULT_PAR_FRACTION``,
#:   ``KWH_TO_MJ`` and ``WeatherUnavailable`` from ``weather_source``.
#:
#: The cycle only resolves when ``weather_source`` is imported first: it
#: defines its three names before it reaches the ``par_pipeline`` import,
#: and ``par_pipeline`` then defines ``DEFAULT_PAR_SPEC`` before
#: ``weather_source`` needs it.  Importing ``par_pipeline`` first fails
#: because ``DEFAULT_PAR_SPEC`` is not yet defined at that point.
#:
#: The direct-file loader therefore always loads ``weather_source`` first.
_CYCLE_ROOT = "engine.hydroma.simulation.weather_source"

_LOAD_ORDER: dict[str, list[str]] = {
    "engine.hydroma.simulation.par_pipeline": [_CYCLE_ROOT],
    "engine.hydroma.eval.seasonal_predictor": [_CYCLE_ROOT],
    "engine.hydroma.eval.resumable_benchmark_runner": [_CYCLE_ROOT],
}

#: Namespaces whose modules depend on the import-cycle root.
_CYCLE_NAMESPACES = (
    "engine.hydroma.simulation.",
    "engine.hydroma.eval.",
)

#: Modules that must not be pre-loaded as siblings, because they take part
#: in the weather_source <-> par_pipeline import cycle.
_CYCLE_EXCLUDED = frozenset(
    {
        "engine.hydroma.simulation.par_pipeline",
        "engine.hydroma.simulation.weather_source",
    }
)


_RELATIVE_IMPORT_RE = re.compile(
    r"^\s*from\s+\.(\w+)\s+import\b", re.MULTILINE
)


def _relative_import_targets(exc: BaseException) -> list[str]:
    """Return the sibling module names a failing relative import refers to.

    The traceback frame of the failing import carries the source line,
    which names the sibling directly.  The sibling's file lives in the
    same directory as the importing module, so it can be loaded by path
    without listing the (possibly unlistable) directory.
    """
    import linecache

    targets: list[str] = []
    tb = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        line = linecache.getline(
            frame.f_code.co_filename, frame.f_lineno
        ).strip()
        m = _RELATIVE_IMPORT_RE.match(line)
        if m:
            name = m.group(1)
            if name not in targets:
                targets.append(name)
        tb = tb.tb_next
    return targets


def _missing_module_name(exc: ModuleNotFoundError) -> str | None:
    """Extract the dotted module name from a ModuleNotFoundError.

    ``ModuleNotFoundError.name`` carries the *full* dotted name of the
    module that could not be found, which is what a relative import
    needs.  The message is only a fallback: for a relative import the
    message names the top-level package rather than the submodule.
    """
    name = getattr(exc, "name", None)
    if name:
        return str(name)
    message = str(exc)
    marker = "No module named '"
    if marker not in message:
        return None
    start = message.index(marker) + len(marker)
    end = message.find("'", start)
    if end < 0:
        return None
    return message[start:end]


def _sibling_modules(dotted: str) -> list[str]:
    """Return the sibling modules of a dotted module name.

    Modules that take part in the weather_source <-> par_pipeline import
    cycle are excluded: pre-loading them would re-enter the cycle before
    the cycle root is initialised.
    """
    parent, _, _child = dotted.rpartition(".")
    if not parent:
        return []
    prefix = parent + "."
    excluded = set(_CYCLE_EXCLUDED)
    return sorted(
        name
        for name in _MODULE_PATHS
        if name.startswith(prefix)
        and name.count(".") == parent.count(".") + 1
        and name not in excluded
    )


def _load_siblings_from_disk(dotted: str, root: Path) -> list[str]:
    """Load every module of the parent package straight from disk.

    The directory listing used by :func:`_discover` can fail for some
    packages (the sandbox's overlay hides them), which would leave a
    relative import inside a module unresolvable.  Listing the parent
    directory directly — trying several spellings — and loading each
    file by path bypasses the import machinery entirely.
    """
    parent, _, _leaf = dotted.rpartition(".")
    if not parent:
        return []
    parent_module = sys.modules.get(parent)
    if parent_module is None:
        return []
    loaded: list[str] = []
    for base in getattr(parent_module, "__path__", []) or []:
        for spelling in (
            str(base).replace("\\", "/"),
            str(base).replace("\\", "/").rstrip("/") + "/.",
        ):
            try:
                names = os.listdir(spelling)
            except OSError:
                continue
            for name in names:
                if not name.endswith(".py") or name == "__init__.py":
                    continue
                child = f"{parent}.{name[:-3]}"
                if child in sys.modules or child == dotted:
                    continue
                try:
                    load_module(child, root)
                    loaded.append(child)
                except Exception:
                    continue
            break
    return loaded


def _cycle_root_is_loaded() -> bool:
    """Check that the import-cycle root is fully initialised."""
    module = sys.modules.get(_CYCLE_ROOT)
    if module is None:
        return False
    return hasattr(module, "fetch_daily_weather")


def _ensure_cycle_root(root: Path) -> None:
    """Load the import-cycle root, replacing a partial registration.

    ``weather_source`` and ``par_pipeline`` import each other.  The cycle
    only resolves when ``weather_source`` is initialised first, so it is
    loaded ahead of anything that touches ``par_pipeline``.  A partial
    registration left behind by a failed import is replaced.
    """
    if _cycle_root_is_loaded():
        return
    module = sys.modules.pop(_CYCLE_ROOT, None)
    if module is not None:
        # Drop a partial import so the cycle can be re-entered cleanly.
        sys.modules.pop(_CYCLE_ROOT, None)
    try:
        load_module(_CYCLE_ROOT, root)
    except Exception:
        pass


def load_module(dotted: str, repo_root: Path | None = None) -> Any:
    """Load an engine module.

    The direct file load is attempted first: it bypasses the import
    machinery's directory scan, which is the part the sandbox's overlay
    filesystem breaks.  The package import is used as a fallback.
    """
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    ensure_engine_importable(root)

    # The import-cycle root must be initialised before anything that
    # reaches par_pipeline.  This runs before the "already loaded"
    # short-circuit, because a partially initialised module may be present
    # in sys.modules after a failed import.
    if dotted.startswith(_CYCLE_NAMESPACES) and dotted != _CYCLE_ROOT:
        _ensure_cycle_root(root)

    if dotted in sys.modules and dotted != _CYCLE_ROOT:
        return sys.modules[dotted]

    # Respect the documented load order (breaks the weather_source /
    # par_pipeline import cycle).
    prerequisites = list(_LOAD_ORDER.get(dotted, []))
    if dotted.startswith(_CYCLE_NAMESPACES) and _CYCLE_ROOT not in sys.modules:
        prerequisites.insert(0, _CYCLE_ROOT)
    for prerequisite in prerequisites:
        if prerequisite not in sys.modules:
            load_module(prerequisite, root)

    # Pre-load the module's siblings in the same package.  A relative
    # import inside the module (``from .sibling import ...``) is resolved
    # by scanning the parent package's directory, which the sandbox's
    # overlay intermittently gets wrong.  Having the siblings already in
    # ``sys.modules`` makes the relative import a plain lookup.
    parent, _, _child = dotted.rpartition(".")
    if parent and dotted not in _IN_PROGRESS:
        for sibling in _sibling_modules(dotted):
            if sibling not in sys.modules and sibling not in _IN_PROGRESS:
                _IN_PROGRESS.add(sibling)
                try:
                    load_module(sibling, root)
                except Exception:
                    pass
                finally:
                    _IN_PROGRESS.discard(sibling)

    # 1) direct file load
    for path in _candidate_paths(dotted, root):
        try:
            # The real dotted name is used so that the module's
            # ``__package__`` is set correctly and relative imports inside
            # the module (e.g. ``from .satellite_cache import ...``)
            # resolve.
            spec = importlib.util.spec_from_file_location(dotted, path)
            if spec is None or spec.loader is None:
                continue
            init_path = path
            module = importlib.util.module_from_spec(spec)
            # Register before executing: the codebase has a genuine import
            # cycle between weather_source and par_pipeline, and the cyclic
            # import has to find the partially initialised module here.
            sys.modules[dotted] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                # A package whose __init__ fails must stay registered with
                # its search path intact: popping it would break every
                # later relative import ("No module named 'engine.hydrama'").
                if getattr(module, "__path__", None) is not None:
                    stub = types.ModuleType(dotted)
                    stub.__path__ = list(module.__path__)  # type: ignore[attr-defined]
                    stub.__file__ = str(init_path)
                    stub.__spec__ = spec
                    sys.modules[dotted] = stub
                else:
                    sys.modules.pop(dotted, None)
                raise
            return module
        except (FileNotFoundError, OSError):
            continue
        except ModuleNotFoundError as exc:
            # A relative import inside the module could not be resolved
            # (the sandbox's directory scan misses files it has cached).
            # Load every module of the parent package directly from disk,
            # then retry: the relative import then becomes a plain
            # sys.modules lookup.
            importlib.invalidate_caches()
            missing = _missing_module_name(exc)
            if missing and missing not in sys.modules and missing != dotted:
                try:
                    load_module(missing, root)
                except Exception:
                    pass
            # A relative import names its sibling in the source line; the
            # sibling's file is in the same directory as this module.
            module_dir = os.path.dirname(path)
            for sibling_name in _relative_import_targets(exc):
                sibling_file = os.path.join(
                    module_dir, sibling_name + ".py"
                )
                if not os.path.exists(sibling_file):
                    continue
                sibling_dotted = (
                    dotted.rpartition(".")[0] + "." + sibling_name
                )
                if sibling_dotted in sys.modules:
                    continue
                try:
                    load_module(sibling_dotted, root)
                except Exception:
                    try:
                        s_spec = importlib.util.spec_from_file_location(
                            sibling_dotted, sibling_file
                        )
                        if s_spec is not None and s_spec.loader is not None:
                            s_mod = importlib.util.module_from_spec(s_spec)
                            sys.modules[sibling_dotted] = s_mod
                            s_spec.loader.exec_module(s_mod)
                    except Exception:
                        pass
            for sibling in _sibling_modules(dotted):
                if sibling in sys.modules:
                    continue
                try:
                    load_module(sibling, root)
                except Exception:
                    pass
            _load_siblings_from_disk(dotted, root)
            try:
                spec3 = importlib.util.spec_from_file_location(dotted, path)
                if spec3 is not None and spec3.loader is not None:
                    module3 = importlib.util.module_from_spec(spec3)
                    sys.modules[dotted] = module3
                    spec3.loader.exec_module(module3)
                    return module3
            except Exception:
                sys.modules.pop(dotted, None)
            raise exc

    # 2) package import
    return importlib.import_module(dotted)


#: Backwards-compatible alias.
load = load_module


__all__ = [
    "ensure_engine_importable",
    "load_module",
    "load",
    "REPO_ROOT",
]
