"""Simple Kc lookup table."""
import pandas as pd
from pathlib import Path

Kc_DATA_PATH = Path(__file__).parent / "kc_data.csv"

# Sample Kc data (Growing Season Average)
KC_DF = pd.DataFrame({
    "crop_type": ["wheat", "corn", "rice"],
    "kc_gs_avg": [1.15, 1.20, 1.25]
})

def get_average_kc(crop_type: str) -> float:
    """Get average Kc for a crop during its growing season."""
    try:
        return KC_DF[KC_DF["crop_type"] == crop_type]["kc_gs_avg"].iloc[0]
    except IndexError:
        raise ValueError(f"Crop type '{crop_type}' not found in Kc lookup table.")
