# services/scientific_motors/aquacrop_adapter.py
from aquacrop import AquaCropModel, Crop, Soil, IrrigationManagement
from sqlalchemy.ext.asyncio import AsyncSession

class AquaCropAdapter:
    """
    Adapter برای اتصال AquaCrop-OSPy به موتورهای علمی Eco Nojin
    
    ورودی: Land Profile از services/land
    خروجی: پیش‌بینی عملکرد، نیاز آبی، تاریخ کاشت
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def simulate_crop(
        self,
        crop_type: str,
        soil_profile: dict,
        weather_data: dict,
        planting_date: str,
    ) -> dict:
        # تنظیم خاک از Land Profile
        soil = Soil(soil_type=soil_profile["texture"])
        
        # تنظیم گیاه از crop_database
        crop = Crop(crop_type, planting_date=planting_date)
        
        # استراتژی آبیاری
        irrigation = IrrigationManagement(irrigation_method=3)
        
        # اجرای شبیه‌سازی
        model = AquaCropModel(
            soil=soil, crop=crop, weather=weather_data,
            irrigation=irrigation
        )
        model.run_model()
        
        # استخراج نتایج
        return {
            "yield_kg_ha": model.get_yield(),
            "water_use_efficiency": model.get_wue(),
            "total_irrigation_mm": model.get_irrigation(),
            "harvest_date": model.get_harvest_date(),
        }