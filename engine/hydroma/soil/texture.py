"""USDA Soil Texture Triangle classification (Phase 1).

Reference:
- USDA Natural Resources Conservation Service, Soil Texture Triangle
  (12 standard texture classes based on sand/silt/clay percentages)

The triangle itself lives in ``taxonomy.TEXTURE_CLASSES``. This module used to
carry a second one -- a chain of fourteen ordered ``if`` branches encoding the
boundaries as thresholds -- and the two disagreed for 1427 of the 5151 integer
compositions of the triangle (27.7 %). Both were reachable from
``services/api_gateway/routers/hydroma_soil.py``, one per endpoint, so a caller
asking the same question of ``soil-texture`` and ``soil-taxonomy`` got two
different answers.

The branch chain is gone and ``classify_texture`` delegates. It is not a
cosmetic consolidation: the chain was wrong where it differed, not merely
differently-rounded. For clay 5 / silt 5 / sand 90 it returned ``loamy_sand``,
which is inside the ``loamy_sand`` range but is also inside the ``sand`` range
(0-10 clay, 0-15 silt, 85-100 sand) that the triangle resolves first, and the
repository's own reference composition for that class expects ``sand``.

Argument order stays ``(sand, silt, clay)`` and the two ``ValueError`` messages
below are unchanged, because both are part of this function's public contract and
``pedotransfer.estimate_texture_from_particles`` and
``services/validation/formula_checks.py`` call it positionally. Note that
``taxonomy.classify_usda_texture`` takes ``(clay, silt, sand)`` -- the two
signatures were already transposed relative to each other.
"""

from .taxonomy import _determine_texture_class

# USDA texture class names (canonical order)
TEXTURE_CLASSES = [
    "clay",
    "silty_clay",
    "sandy_clay",
    "clay_loam",
    "silty_clay_loam",
    "sandy_clay_loam",
    "loam",
    "silt_loam",
    "silt",
    "sandy_loam",
    "loamy_sand",
    "sand",
]

# Human-readable names
TEXTURE_NAMES: dict[str, str] = {
    "clay": "Clay",
    "silty_clay": "Silty Clay",
    "sandy_clay": "Sandy Clay",
    "clay_loam": "Clay Loam",
    "silty_clay_loam": "Silty Clay Loam",
    "sandy_clay_loam": "Sandy Clay Loam",
    "loam": "Loam",
    "silt_loam": "Silt Loam",
    "silt": "Silt",
    "sandy_loam": "Sandy Loam",
    "loamy_sand": "Loamy Sand",
    "sand": "Sand",
}


def classify_texture(sand: float, silt: float, clay: float) -> str:
    """Classify soil texture from particle-size percentages (USDA triangle).

    Delegates to ``taxonomy._determine_texture_class``; see the module docstring
    for why there is only one triangle in the package now. The validation below
    is kept here rather than inherited so that both error messages this function
    has always raised stay exactly as they were.

    Args:
        sand: sand percentage (0-100)
        silt: silt percentage (0-100)
        clay: clay percentage (0-100)

    Returns:
        USDA texture class name (one of TEXTURE_CLASSES).

    Raises:
        ValueError: if percentages do not sum to ~100 or are negative.
    """
    total = sand + silt + clay
    if total <= 0 or abs(total - 100.0) > 1.0:
        raise ValueError(f"sand+silt+clay must sum to 100 (got {sand}+{silt}+{clay}={total})")
    if min(sand, silt, clay) < 0:
        raise ValueError("percentages must be non-negative")

    return _determine_texture_class(clay, silt, sand)


def texture_triangle_coords(sand: float, silt: float, clay: float) -> tuple[float, float]:
    """Project (sand, silt, clay) onto 2D triangle coordinates for plotting.

    Returns (x, y) in a 0-1 triangle (apex = clay at top).
    """
    return (0.5 * silt + sand) / 100.0, clay / 100.0


def is_sandy(texture: str) -> bool:
    return texture in {"sand", "loamy_sand", "sandy_loam"}


def is_clayey(texture: str) -> bool:
    return texture in {"clay", "silty_clay", "sandy_clay"}


def is_silty(texture: str) -> bool:
    return texture in {"silt", "silt_loam", "silty_clay_loam", "silty_clay"}
