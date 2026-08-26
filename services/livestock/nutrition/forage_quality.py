"""محاسبه کیفیت علوفه از NDVI ماهواره‌ای"""
from services.livestock.schemas import ForageQuality

def ndvi_to_forage_quality(ndvi: float, season: str = "spring") -> ForageQuality:
    """تبدیل NDVI به پارامترهای کیفیت علوفه (FAO Methodology)"""
    # NDVI 0.2-0.8 → CP 8-20%
    crude_protein = 8 + (ndvi - 0.2) * 20 if ndvi > 0.2 else 8
    
    # NDVI → Digestibility
    digestibility = 50 + ndvi * 30
    
    # NDVI → Biomass (ton/ha)
    dry_matter = ndvi * 6  # حداکثر ۶ تن در هکتار
    
    return ForageQuality(
        ndvi_value=ndvi,
        crude_protein_pct=round(crude_protein, 1),
        digestibility_pct=round(digestibility, 1),
        dry_matter_ton_ha=round(dry_matter, 2),
        season=season,
    )
    