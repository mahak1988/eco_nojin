"""Read-only access to the frozen Rosetta-3 PTF reference artifact.

The artifact (``ptf_reference.json``, ``PTF-REFERENCE-ROSETTA-3`` v1.0.0) holds,
for each of the twelve USDA texture classes the engine carries, the van
Genuchten parameters and saturated conductivity that the **Rosetta 3**
pedotransfer function predicts *at the engine's own inputs*, together with the
bootstrap standard deviations Rosetta reports for them.

What this module is for
-----------------------
It is a **reference for comparison and for uncertainty bands**, nothing more.
It lets a caller ask "how far does Rosetta, the published CC0 / USDA-ARS PTF,
land from the engine's own table, and how wide is Rosetta's own predictive
uncertainty here?" without shipping the prediction package into the runtime.

What this module is NOT
-----------------------
It does **not** replace ``engine.hydroma.soil.physics.SOIL_PARAMETERS_VG``. The
engine's table stays exactly as it is; the documented disagreement between the
two sources (gap **G-S6**, the withdrawn Carsel & Parrish attribution) remains an
open decision, and adding this reader changes no engine behaviour and no engine
table or equation. Nothing here is imported by any engine computation path: this
is purely a dependency-free auditing lens over a frozen data file.

How the numbers were made
-------------------------
Generated once by ``tools/regenerate_ptf_reference.py`` from the installed
Rosetta 3 pedotransfer package (CC0-1.0, v0.3.2, model code 5). The inputs
recorded in the artifact are the engine's own: sand/silt/clay are the engine's
reference compositions for its texture classes, bulk density is
``2.65*(1-theta_s)`` from the engine table, and theta_33/theta_1500 are the
engine's own van Genuchten curve at 330/15000 cm. The artifact therefore records
Rosetta's prediction *at the engine's own inputs*, which is what the divergence
audit measures; it is not an independent USDA canonical table.

Rosetta's standard deviation of Ks is given on the linear Ks scale. The pivotal
(+-1 sd logarithmic) width used by :func:`uncertainty_band` converts it with the
delta method for a logarithm,

    sd_log10_ks ~= |sd_ks / (ks * ln(10))|,

which is the first-order propagation of the ``log10`` transform and is a good
approximation whenever ``sd_ks`` is small relative to ``ks`` (as it is here).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import cast

#: Location of the frozen artifact, resolved relative to this module so the
#: reader works from any working directory.
REFERENCE_PATH: Path = Path(__file__).resolve().parent / "ptf_reference.json"

#: The five judged parameters, in artifact column order. Used to keep
#: :func:`uncertainty_band` aligned with the stored ``mean``/``sd`` blocks.
_PARAMETER_KEYS: tuple[str, ...] = (
    "theta_r",
    "theta_s",
    "alpha",
    "n",
    "ks_cm_per_day",
)


@dataclass(frozen=True)
class PTFUncertainty:
    """Rosetta's predictive uncertainty for one texture.

    ``sd_*`` are the bootstrap standard deviations Rosetta reports for the four
    van Genuchten parameters. ``sd_log10_ks_cm_per_day`` is derived from Rosetta's
    sd of Ks via the delta method for the log10 transform (see the module
    docstring): it is the +-1 sd width on a log10(Ks) axis, which is the scale on
    which saturated conductivity varies by orders of magnitude.
    """

    texture: str
    sd_theta_r: float
    sd_theta_s: float
    sd_alpha: float
    sd_n: float
    sd_log10_ks_cm_per_day: float


@lru_cache(maxsize=1)
def load_reference() -> dict:
    """The parsed artifact (read-only), cached after the first read.

    Returns:
        The whole ``ptf_reference.json`` document as a dict.

    Raises:
        FileNotFoundError: if the artifact file is absent. The message names the
            path and the regenerator that recreates it.
    """
    if not REFERENCE_PATH.is_file():
        raise FileNotFoundError(
            f"PTF reference artifact not found at {REFERENCE_PATH}. This file "
            "is a frozen data artifact and is expected to ship with the engine; "
            "it can be recreated with tools/regenerate_ptf_reference.py."
        )
    document: dict = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    return document


def reference_row(texture: str) -> dict | None:
    """The stored row for one texture, or ``None`` if the texture is unknown.

    The returned row has ``inputs``, ``mean`` and ``sd`` sub-dicts exactly as
    written to the artifact. It is the cached document's own sub-structure, so
    treat it as read-only; copy it before mutating.
    """
    textures = load_reference().get("textures", {})
    return cast("dict | None", textures.get(texture))


def uncertainty_band(texture: str) -> PTFUncertainty:
    """Rosetta's +-1 sd predictive band for one texture.

    Args:
        texture: a USDA texture class present in the artifact.

    Returns:
        A :class:`PTFUncertainty` carrying the four Rosetta parameter standard
        deviations and the derived ``sd_log10_ks_cm_per_day``.

    Raises:
        KeyError: if the texture is not one of the twelve in the artifact.
    """
    row = reference_row(texture)
    if row is None:
        available = sorted(load_reference().get("textures", {}))
        raise KeyError(
            f"unknown texture {texture!r} in the Rosetta reference artifact; "
            f"available: {available}"
        )
    mean = row["mean"]
    sd = row["sd"]
    ks = float(mean["ks_cm_per_day"])
    sd_ks = float(sd["ks_cm_per_day"])
    sd_log10_ks = abs(sd_ks / (ks * math.log(10.0))) if ks > 0.0 else math.inf
    return PTFUncertainty(
        texture=texture,
        sd_theta_r=float(sd["theta_r"]),
        sd_theta_s=float(sd["theta_s"]),
        sd_alpha=float(sd["alpha"]),
        sd_n=float(sd["n"]),
        sd_log10_ks_cm_per_day=sd_log10_ks,
    )
