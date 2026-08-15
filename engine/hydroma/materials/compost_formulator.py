"""Formulation engine for bio-fertilizers and soil amendments."""

from pydantic import BaseModel, Field


class CompostMaterial(BaseModel):
    """Represents a single input material for composting."""

    name: str = Field(..., description="Name of the material (e.g., Straw, Cow Manure)")
    mass_kg: float = Field(..., gt=0, description="Mass of the material in kg")
    carbon_content: float = Field(..., ge=0, le=100, description="Carbon percentage (0-100)")
    nitrogen_content: float = Field(..., ge=0, le=100, description="Nitrogen percentage (0-100)")


def calculate_mix_cn_ratio(materials: list[CompostMaterial]) -> float:
    """Calculate the overall C/N ratio of a compost mixture.

    Args:
        materials: List of input materials with their mass and composition.

    Returns:
        The calculated Carbon to Nitrogen ratio.
    """
    total_c = sum(m.mass_kg * (m.carbon_content / 100.0) for m in materials)
    total_n = sum(m.mass_kg * (m.nitrogen_content / 100.0) for m in materials)

    if total_n == 0:
        return float("inf")

    return total_c / total_n
