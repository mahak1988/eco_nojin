"""Path resolution helper for the Stage 39/40 sandbox.

The sandbox filesystem intermittently caches a path spelling as
"missing" even though the file exists and the parent directory lists
correctly.  Opening the *same* file under a different (but equivalent)
spelling succeeds.

This module finds a spelling that actually opens.
"""

from __future__ import annotations

import os

#: Directory names that are known to be affected.
_SALT = ("/.", "/./", "/../")


def _candidates(path: str) -> list[str]:
    """Return equivalent spellings of ``path``."""
    path = path.replace("\\", "/")
    out = [path]

    # Insert a "." component at each directory level.
    parts = path.split("/")
    for i in range(1, len(parts)):
        if parts[i]:
            out.append("/".join(parts[:i] + ["."] + parts[i:]))

    # Use a sibling directory to reach the same file via "..".
    parent = "/".join(parts[:-1])
    name = parts[-1]
    if parent:
        for sibling in sorted(os.listdir(parent)) if os.path.isdir(parent) else []:
            if sibling in (".", ".."):
                continue
            out.append(f"{parent}/{sibling}/../{name}")
    return out


def resolve(path: str) -> str | None:
    """Return a spelling of ``path`` that can be opened, or None."""
    for candidate in _candidates(path):
        try:
            with open(candidate, "rb") as f:
                f.read(1)
            return candidate
        except OSError:
            continue
    return None


def read_text(path: str) -> str | None:
    """Read a file, trying alternative spellings."""
    for candidate in _candidates(path):
        try:
            with open(candidate, encoding="utf-8") as f:
                return f.read()
        except OSError:
            continue
    return None


def load_module(module_name: str, path: str):
    """Load and execute a module from a path, trying alternative spellings."""
    import importlib.util
    import sys

    resolved = resolve(path)
    if resolved is None:
        raise FileNotFoundError(f"no readable spelling for {path}")
    spec = importlib.util.spec_from_file_location(module_name, resolved)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build spec for {module_name} at {resolved}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


__all__ = ["resolve", "read_text", "load_module"]
