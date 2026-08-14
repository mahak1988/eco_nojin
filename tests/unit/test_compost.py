"""Test compost formulation logic."""
from engine.hydroma.materials.compost_formulator import CompostMaterial, calculate_mix_cn_ratio

def test_compost_cn_ratio_straw_manure():
    """Verify C/N ratio calculation for a typical straw and manure mix."""
    straw = CompostMaterial(name="Straw", mass_kg=100, carbon_content=40.0, nitrogen_content=0.5) # High C/N
    manure = CompostMaterial(name="Cow Manure", mass_kg=50, carbon_content=20.0, nitrogen_content=2.0) # Low C/N
    
    # Total C = (100 * 0.4) + (50 * 0.2) = 40 + 10 = 50 kg
    # Total N = (100 * 0.005) + (50 * 0.02) = 0.5 + 1.0 = 1.5 kg
    # Expected C/N = 50 / 1.5 = 33.33 (Ideal for composting)
    
    cn_ratio = calculate_mix_cn_ratio([straw, manure])
    assert 33.0 < cn_ratio < 34.0

def test_compost_cn_ratio_zero_nitrogen():
    """Verify handling of materials with zero nitrogen."""
    pure_carbon = CompostMaterial(name="Biochar", mass_kg=10, carbon_content=80.0, nitrogen_content=0.0)
    ratio = calculate_mix_cn_ratio([pure_carbon])
    assert ratio == float('inf')
