"""USDA Soil Texture Triangle classification (Phase 1).

Reference:
- USDA Natural Resources Conservation Service, Soil Texture Triangle
  (12 standard texture classes based on sand/silt/clay percentages)
"""

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

    # USDA triangle boundaries (12 classes)
    if clay >= 40 and sand <= 45 and silt < 40:
        return "clay"
    if clay >= 40 and sand > 45:
        return "sandy_clay"
    if clay >= 40 and silt >= 40:
        return "silty_clay"
    if clay >= 27 and clay < 40 and sand <= 20:
        return "silty_clay_loam"
    if clay >= 27 and clay < 40 and sand > 20 and sand <= 45:
        return "clay_loam"
    if clay >= 27 and clay < 40 and sand > 45:
        return "sandy_clay_loam"
    if clay >= 20 and clay < 27 and silt >= 40 and sand <= 40:
        return "silty_clay_loam"
    if clay >= 20 and clay < 27 and sand > 40 and sand <= 52:
        return "clay_loam"
    if clay >= 20 and clay < 27 and sand > 52:
        return "sandy_clay_loam"
    if clay < 20 and silt >= 80:
        return "silt"
    if clay < 12 and silt < 20 and sand > 85:
        return "sand"
    if clay < 12 and silt < 30 and sand > 70:
        return "loamy_sand"
    if clay < 20 and silt >= 30 and silt < 50 and sand <= 52:
        return "silt_loam"
    if clay < 27 and silt >= 50 and sand <= 52:
        return "silt_loam"
    if clay < 27 and sand > 52 and sand <= 70 and (100 - sand - clay) < 30:
        return "sandy_loam"
    if clay < 20 and sand > 52 and silt >= 20 and silt < 30:
        return "sandy_loam"
    if clay < 35 and clay >= 20 and sand > 45:
        return "sandy_clay_loam"
    # fallback: loam covers the remaining central area
    return "loam"


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
