"""What can this environment actually run?

Why this is a probe and not a field on the registry
---------------------------------------------------

The registry records what the *code* contains. Whether those models can execute
depends on the *environment*: `flopy` installed or not, `gpytorch` present or
not, a SWAT+ binary on PATH or not. Storing that answer inside a JSON file makes
it a claim that cannot correct itself. Someone installs `flopy`, and the
registry keeps saying MODFLOW 6 is unavailable. Someone uninstalls a package,
and it keeps saying the opposite. Either way the file is wrong and nothing in
the pipeline knows.

So the three questions are kept apart:

    registry  -> what the code claims to have      (static, reviewable in source)
    probe     -> what this environment can execute (runtime, recomputed on demand)
    Provenance-> what a specific run actually produced (on the result itself)

The probe is a function, not a record, for exactly that reason.

What it does and does not claim
--------------------------------

It answers one question -- can this dependency be imported right now -- and it
answers it honestly, including when the answer is "no". It does not claim a
model is *correct*, only that its code path is reachable. Those are different
questions and conflating them is how a model that returns noise gets described
as available.

The one judgement call: `gp_surrogate` reports unavailable without `gpytorch`
installed, but its mock path returns random numbers and reports `success=True`.
That is the exact failure the probe exists to stop being invisible, so it is
reported as unavailable rather than as a working model with a caveat.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Any

#: Model name -> the import that must succeed for the model to run.
#:
#: A model absent from this map is assumed to be pure-Python and always
#: runnable; that assumption is the conservative one here, because a false
#: "available" is worse than a false "unavailable" for a selector that will hand
#: the result to a user.
REQUIRED_IMPORTS: dict[str, tuple[str, ...]] = {
    "SWAT+": (),  # needs an external binary, not an import -- see _binary_present
    "MODFLOW 6": ("flopy",),
    "Heat Equation PINN": ("torch",),
    "Richards Equation PINN": ("torch",),
    "Gaussian Process Surrogate": ("gpytorch",),
    "Distributed PINN Trainer": ("torch",),
}

#: Models that need an external executable rather than a Python package.
REQUIRED_BINARIES: dict[str, tuple[str, ...]] = {
    "SWAT+": ("swat",),
}

#: Models whose code path is known-broken in this repository, independent of the
#: environment. An import check would report these as available, because the
#: defect is inside the training loop rather than at import time.
#:
#: This is a different kind of fact from the maps above, and keeping it in a
#: separate table is deliberate: environment and source defect are different
#: things, and a selector that conflates them will tell a user a model is ready
#: when it raises on first use. Each entry names the defect so the reason is
#: actionable rather than a bare "no".
#:
#: Provenance: engine/hydroma/hybrid_ml/pinn.py -- the collocation tensors carry
#: no `requires_grad`, so `torch.autograd.grad` raises on the first training
#: epoch. Found during the Phase 2 sweep; still open.
KNOWN_BROKEN: dict[str, str] = {
    "Heat Equation PINN": "pinn.py collocation tensors lack requires_grad; autograd.grad raises on first epoch",
    "Richards Equation PINN": "pinn.py collocation tensors lack requires_grad; autograd.grad raises on first epoch",
}


@dataclass(frozen=True)
class Availability:
    """The runtime answer for one model. Never persisted."""

    name: str
    available: bool
    reason: str
    missing_imports: tuple[str, ...] = ()
    missing_binaries: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "reason": self.reason,
            "missing_imports": list(self.missing_imports),
            "missing_binaries": list(self.missing_binaries),
        }


def _importable(name: str) -> bool:
    """True if `name` can be located, without executing it.

    find_spec rather than import: a successful import of a heavy optional
    dependency would make the probe itself expensive, and some of these fail at
    import time for reasons unrelated to presence.
    """
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def _binary_present(name: str) -> bool:
    import shutil

    return shutil.which(name) is not None


def check_model(name: str) -> Availability:
    """Ask whether one model can run here, now, in this process."""
    # A source defect outranks an environment fact. Checking imports first would
    # report the PINNs as available, because torch imports fine and the failure
    # is inside the training loop.
    if name in KNOWN_BROKEN:
        return Availability(name, False, f"known source defect: {KNOWN_BROKEN[name]}")

    missing_imports = tuple(m for m in REQUIRED_IMPORTS.get(name, ()) if not _importable(m))
    missing_binaries = tuple(b for b in REQUIRED_BINARIES.get(name, ()) if not _binary_present(b))

    if missing_imports or missing_binaries:
        bits = []
        if missing_imports:
            bits.append("missing " + ", ".join(missing_imports))
        if missing_binaries:
            bits.append("no binary on PATH for " + ", ".join(missing_binaries))
        return Availability(name, False, "; ".join(bits), missing_imports, missing_binaries)

    return Availability(name, True, "all requirements importable")


def check_all(names: list[str]) -> dict[str, Availability]:
    """Probe a list of model names. Recomputed on every call, by design."""
    return {n: check_model(n) for n in names}
