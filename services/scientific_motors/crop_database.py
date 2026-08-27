"""
Hydroma Nojin - Global Crop Database
Comprehensive database with Köppen-Geiger climate classification (30 climates)
for worldwide agricultural recommendations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class KoppenClimate(Enum):
    """Köppen-Geiger climate classification (global standard)."""
    # Group A - Tropical
    Af = "Tropical rainforest"
    Am = "Tropical monsoon"
    Aw = "Tropical savanna"
    # Group B - Dry
    BWh = "Hot desert"
    BWk = "Cold desert"
    BSh = "Hot semi-arid (steppe)"
    BSk = "Cold semi-arid (steppe)"
    # Group C - Temperate
    Csa = "Hot-summer Mediterranean"
    Csb = "Warm-summer Mediterranean"
    Csc = "Cold-summer Mediterranean"
    Cfa = "Humid subtropical"
    Cfb = "Oceanic (temperate)"
    Cfc = "Subpolar oceanic"
    Cwa = "Dry-winter humid subtropical"
    Cwb = "Dry-winter subtropical highland"
    Cwc = "Dry-winter cold subtropical"
    # Group D - Continental
    Dsa = "Hot-summer Mediterranean continental"
    Dsb = "Warm-summer Mediterranean continental"
    Dsc = "Dry cold-summer continental"
    Dsd = "Very cold dry-winter continental"
    Dfa = "Hot-summer humid continental"
    Dfb = "Warm-summer humid continental"
    Dfc = "Subarctic"
    Dfd = "Extremely cold subarctic"
    Dwa = "Dry-winter hot continental"
    Dwb = "Dry-winter warm continental"
    Dwc = "Dry-winter subarctic"
    Dwd = "Dry-winter extremely cold"
    # Group E - Polar
    ET = "Tundra"
    EF = "Ice cap"


class CropFamily(Enum):
    CEREAL = "Cereals / غلات"
    LEGUME = "Legumes / حبوبات"
    VEGETABLE = "Vegetables / سبزیجات"
    FRUIT = "Fruits / میوه‌ها"
    INDUSTRIAL = "Industrial / صنعتی"
    OILSEED = "Oilseeds / دانه‌های روغنی"
    MEDICINAL = "Medicinal & Aromatic / دارویی"
    FORAGE = "Forage / علوفه"
    NUT = "Tree nuts / آجیل"
    TUBER = "Tubers / غده‌ای"
    FLOWER = "Ornamental / زینتی"
    BEVERAGE = "Beverage / نوشیدنی"


class WaterTolerance(Enum):
    LOW = "low"             # حساس به خشکی
    MEDIUM = "medium"       # متوسط
    HIGH = "high"           # مقاوم
    VERY_HIGH = "very_high" # بسیار مقاوم


class SalinityTolerance(Enum):
    SENSITIVE = "sensitive"
    MODERATE = "moderate"
    TOLERANT = "tolerant"
    HIGHLY_TOLERANT = "highly_tolerant"


@dataclass
class WaterRequirement:
    min_mm: float
    opt_mm: float
    max_mm: float
    drought_tolerance: WaterTolerance


@dataclass
class SoilRequirement:
    ph_min: float
    ph_opt_min: float
    ph_opt_max: float
    ph_max: float
    preferred_texture: list[int]  # USDA 1-12
    salinity_tolerance: SalinityTolerance
    min_depth_cm: float


@dataclass
class TemperatureRequirement:
    min_c: float
    opt_min_c: float
    opt_max_c: float
    max_c: float
    chilling_hours: int  # نیاز سرمایی (برای درختان)
    frost_tolerance: bool


@dataclass
class EconomicData:
    yield_ton_ha: float
    market_price_per_kg_usd: float  # قیمت جهانی USD
    production_cost_per_ha_usd: float
    labor_days_per_ha: float


@dataclass
class CropProfile:
    id: str
    name_fa: str
    name_en: str
    scientific_name: str
    family: CropFamily
    growing_days: int
    planting_months: list[int]  # 1-12 (ماه‌های کاشت جهانی)

    water: WaterRequirement
    soil: SoilRequirement
    temperature: TemperatureRequirement

    # سازگاری با Köppen
    suitable_climates: list[KoppenClimate]
    max_slope_percent: float
    suitable_lcc_classes: list[int]
    altitude_range_m: tuple  # (min, max)

    economics: EconomicData
    rotation_compatible: list[str]

    # توزیع جهانی (به جای استان)
    major_producers: list[str]  # کشورهای تولیدکننده اصلی

    # کاربردها
    uses: list[str]  # human_food, animal_feed, industrial, medicinal
    shelf_life_days: int

    notes: str = ""


# ============================================================
# Global Crop Database (30 representative crops)
# ============================================================

CROP_DATABASE: dict[str, CropProfile] = {
    # ===== CEREALS =====
    "wheat": CropProfile(
        id="wheat", name_fa="گندم", name_en="Wheat",
        scientific_name="Triticum aestivum", family=CropFamily.CEREAL,
        growing_days=210, planting_months=[9,10,11,3,4],
        water=WaterRequirement(350, 550, 750, WaterTolerance.MEDIUM),
        soil=SoilRequirement(5.5, 6.0, 7.5, 8.5, [4,5,6,7], SalinityTolerance.MODERATE, 50),
        temperature=TemperatureRequirement(-8, 10, 22, 32, 0, True),
        suitable_climates=[
            KoppenClimate.BSk, KoppenClimate.Csa, KoppenClimate.Csb,
            KoppenClimate.Cfa, KoppenClimate.Cfb, KoppenClimate.Cwa,
            KoppenClimate.Dfa, KoppenClimate.Dfb, KoppenClimate.Dwa, KoppenClimate.Dwb,
        ],
        max_slope_percent=8, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 3000),
        economics=EconomicData(4.5, 0.28, 900, 25),
        rotation_compatible=["chickpea", "lentil", "sunflower", "soybean"],
        major_producers=["China", "India", "Russia", "USA", "France", "Ukraine", "Argentina"],
        uses=["human_food", "animal_feed", "industrial"],
        shelf_life_days=365,
        notes="Staple food for 2.5B people. 770M tons annual global production."
    ),
    "rice_paddy": CropProfile(
        id="rice_paddy", name_fa="برنج آبی", name_en="Paddy Rice",
        scientific_name="Oryza sativa", family=CropFamily.CEREAL,
        growing_days=150, planting_months=[4,5,6],
        water=WaterRequirement(1200, 1500, 2500, WaterTolerance.LOW),
        soil=SoilRequirement(5.0, 5.5, 6.5, 7.5, [8,9,10,11], SalinityTolerance.MODERATE, 40),
        temperature=TemperatureRequirement(15, 22, 32, 38, 0, False),
        suitable_climates=[
            KoppenClimate.Af, KoppenClimate.Am, KoppenClimate.Aw,
            KoppenClimate.Cfa, KoppenClimate.Cwa, KoppenClimate.Cwb,
        ],
        max_slope_percent=3, suitable_lcc_classes=[1,2], altitude_range_m=(0, 2000),
        economics=EconomicData(6.5, 0.55, 1500, 80),
        rotation_compatible=["legume", "fallow"],
        major_producers=["China", "India", "Indonesia", "Bangladesh", "Vietnam", "Thailand"],
        uses=["human_food"],
        shelf_life_days=730,
        notes="Feeds 3.5B people. Requires flooded conditions."
    ),
    "maize": CropProfile(
        id="maize", name_fa="ذرت", name_en="Maize/Corn",
        scientific_name="Zea mays", family=CropFamily.CEREAL,
        growing_days=130, planting_months=[4,5,6,11,12],
        water=WaterRequirement(450, 650, 900, WaterTolerance.LOW),
        soil=SoilRequirement(5.8, 6.0, 7.0, 7.5, [4,5,6,7], SalinityTolerance.MODERATE, 60),
        temperature=TemperatureRequirement(10, 18, 30, 38, 0, False),
        suitable_climates=[
            KoppenClimate.Aw, KoppenClimate.BSh, KoppenClimate.Cfa,
            KoppenClimate.Cwa, KoppenClimate.Cwb, KoppenClimate.Dfa,
            KoppenClimate.Dwa,
        ],
        max_slope_percent=8, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 3500),
        economics=EconomicData(7.0, 0.24, 1100, 30),
        rotation_compatible=["soybean", "wheat", "cotton"],
        major_producers=["USA", "China", "Brazil", "Argentina", "Ukraine", "Mexico"],
        uses=["human_food", "animal_feed", "industrial", "biofuel"],
        shelf_life_days=365,
        notes="C4 crop. Most produced cereal globally (1.2B tons)."
    ),
    "sorghum": CropProfile(
        id="sorghum", name_fa="سورگوم", name_en="Sorghum",
        scientific_name="Sorghum bicolor", family=CropFamily.CEREAL,
        growing_days=120, planting_months=[5,6,7],
        water=WaterRequirement(300, 500, 700, WaterTolerance.VERY_HIGH),
        soil=SoilRequirement(5.5, 6.0, 8.0, 9.0, [3,4,5,6,7,8], SalinityTolerance.TOLERANT, 40),
        temperature=TemperatureRequirement(12, 22, 32, 42, 0, False),
        suitable_climates=[
            KoppenClimate.BWh, KoppenClimate.BWk, KoppenClimate.BSh,
            KoppenClimate.BSk, KoppenClimate.Aw, KoppenClimate.Cwa,
        ],
        max_slope_percent=10, suitable_lcc_classes=[1,2,3,4], altitude_range_m=(0, 2000),
        economics=EconomicData(3.5, 0.30, 600, 18),
        rotation_compatible=["legume", "cotton"],
        major_producers=["USA", "India", "Nigeria", "Sudan", "Ethiopia", "Mexico"],
        uses=["human_food", "animal_feed", "biofuel"],
        shelf_life_days=365,
        notes="Climate-resilient C4 crop. Essential for Sahel Africa."
    ),
    "barley": CropProfile(
        id="barley", name_fa="جو", name_en="Barley",
        scientific_name="Hordeum vulgare", family=CropFamily.CEREAL,
        growing_days=130, planting_months=[10,11,3,4],
        water=WaterRequirement(250, 400, 550, WaterTolerance.HIGH),
        soil=SoilRequirement(6.0, 6.5, 8.0, 9.0, [3,4,5,6,7], SalinityTolerance.TOLERANT, 40),
        temperature=TemperatureRequirement(-10, 8, 20, 30, 0, True),
        suitable_climates=[
            KoppenClimate.BSk, KoppenClimate.BWk, KoppenClimate.BSh,
            KoppenClimate.Csa, KoppenClimate.Csb, KoppenClimate.Dfb,
            KoppenClimate.ET,
        ],
        max_slope_percent=15, suitable_lcc_classes=[1,2,3,4], altitude_range_m=(0, 4000),
        economics=EconomicData(4.0, 0.25, 700, 20),
        rotation_compatible=["legume", "fallow"],
        major_producers=["Russia", "Australia", "Germany", "France", "Canada", "Turkey"],
        uses=["human_food", "animal_feed", "beverage"],
        shelf_life_days=365,
        notes="Most cold and salinity tolerant cereal."
    ),
    "millet_pearl": CropProfile(
        id="millet_pearl", name_fa="ارزن مرواریدی", name_en="Pearl Millet",
        scientific_name="Pennisetum glaucum", family=CropFamily.CEREAL,
        growing_days=90, planting_months=[6,7],
        water=WaterRequirement(200, 350, 500, WaterTolerance.VERY_HIGH),
        soil=SoilRequirement(5.5, 6.0, 8.0, 9.0, [2,3,4,5], SalinityTolerance.TOLERANT, 30),
        temperature=TemperatureRequirement(15, 25, 35, 45, 0, False),
        suitable_climates=[
            KoppenClimate.BWh, KoppenClimate.BSh, KoppenClimate.Aw,
        ],
        max_slope_percent=12, suitable_lcc_classes=[1,2,3,4,5], altitude_range_m=(0, 1500),
        economics=EconomicData(1.8, 0.35, 400, 15),
        rotation_compatible=["legume"],
        major_producers=["India", "Niger", "Nigeria", "Mali", "Chad", "Senegal"],
        uses=["human_food", "animal_feed"],
        shelf_life_days=365,
        notes="Drought champion - survives where maize fails. Sahel staple."
    ),

    # ===== LEGUMES =====
    "chickpea": CropProfile(
        id="chickpea", name_fa="نخود", name_en="Chickpea",
        scientific_name="Cicer arietinum", family=CropFamily.LEGUME,
        growing_days=130, planting_months=[10,11,3,4],
        water=WaterRequirement(250, 380, 500, WaterTolerance.HIGH),
        soil=SoilRequirement(6.0, 6.5, 8.0, 9.0, [4,5,6,7], SalinityTolerance.MODERATE, 50),
        temperature=TemperatureRequirement(-5, 12, 26, 33, 0, True),
        suitable_climates=[
            KoppenClimate.BSk, KoppenClimate.Csa, KoppenClimate.Csb,
            KoppenClimate.Cfa, KoppenClimate.Cwa,
        ],
        max_slope_percent=12, suitable_lcc_classes=[1,2,3,4], altitude_range_m=(0, 2500),
        economics=EconomicData(1.5, 0.90, 800, 25),
        rotation_compatible=["wheat", "barley", "rice"],
        major_producers=["India", "Australia", "Myanmar", "Turkey", "Pakistan", "Ethiopia"],
        uses=["human_food"],
        shelf_life_days=730,
        notes="N-fixer. Essential in rotation with cereals."
    ),
    "lentil": CropProfile(
        id="lentil", name_fa="عدس", name_en="Lentil",
        scientific_name="Lens culinaris", family=CropFamily.LEGUME,
        growing_days=120, planting_months=[10,11,3,4],
        water=WaterRequirement(200, 300, 450, WaterTolerance.HIGH),
        soil=SoilRequirement(6.0, 6.5, 8.0, 8.5, [4,5,6,7], SalinityTolerance.MODERATE, 30),
        temperature=TemperatureRequirement(-5, 10, 24, 30, 0, True),
        suitable_climates=[
            KoppenClimate.BSk, KoppenClimate.Csa, KoppenClimate.Csb,
            KoppenClimate.Cfb, KoppenClimate.Dfb,
        ],
        max_slope_percent=15, suitable_lcc_classes=[1,2,3,4], altitude_range_m=(0, 3000),
        economics=EconomicData(1.2, 1.20, 700, 25),
        rotation_compatible=["wheat", "barley"],
        major_producers=["Canada", "India", "Turkey", "USA", "Nepal", "Australia"],
        uses=["human_food"],
        shelf_life_days=1095,
        notes="Ancient crop, high protein. Excellent for marginal soils."
    ),
    "soybean": CropProfile(
        id="soybean", name_fa="سویا", name_en="Soybean",
        scientific_name="Glycine max", family=CropFamily.LEGUME,
        growing_days=130, planting_months=[5,6,11,12],
        water=WaterRequirement(450, 650, 850, WaterTolerance.MEDIUM),
        soil=SoilRequirement(6.0, 6.5, 7.0, 7.5, [5,6,7], SalinityTolerance.MODERATE, 50),
        temperature=TemperatureRequirement(10, 20, 30, 38, 0, False),
        suitable_climates=[
            KoppenClimate.Cfa, KoppenClimate.Cwa, KoppenClimate.Dfa,
            KoppenClimate.Dfb, KoppenClimate.Dwa, KoppenClimate.Aw,
        ],
        max_slope_percent=8, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 2000),
        economics=EconomicData(3.2, 0.55, 950, 30),
        rotation_compatible=["maize", "wheat", "rice"],
        major_producers=["Brazil", "USA", "Argentina", "China", "India", "Paraguay"],
        uses=["human_food", "animal_feed", "industrial", "oilseed"],
        shelf_life_days=365,
        notes="Highest protein legume. 370M tons global production."
    ),
    "common_bean": CropProfile(
        id="common_bean", name_fa="لوبیا", name_en="Common Bean",
        scientific_name="Phaseolus vulgaris", family=CropFamily.LEGUME,
        growing_days=100, planting_months=[4,5,8,9],
        water=WaterRequirement(350, 480, 650, WaterTolerance.MEDIUM),
        soil=SoilRequirement(6.0, 6.5, 7.5, 8.0, [4,5,6,7], SalinityTolerance.SENSITIVE, 40),
        temperature=TemperatureRequirement(10, 18, 26, 32, 0, False),
        suitable_climates=[
            KoppenClimate.Cfa, KoppenClimate.Cfb, KoppenClimate.Cwb,
            KoppenClimate.Dfa, KoppenClimate.Dfb, KoppenClimate.Dwa,
        ],
        max_slope_percent=12, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 3500),
        economics=EconomicData(1.8, 1.10, 800, 35),
        rotation_compatible=["maize", "wheat", "potato"],
        major_producers=["Brazil", "India", "Myanmar", "China", "Mexico", "USA"],
        uses=["human_food"],
        shelf_life_days=730,
        notes="Latin American staple. Multiple varieties."
    ),
    "cowpea": CropProfile(
        id="cowpea", name_fa="لوبیا چشم‌بلبلی", name_en="Cowpea",
        scientific_name="Vigna unguiculata", family=CropFamily.LEGUME,
        growing_days=90, planting_months=[5,6,7],
        water=WaterRequirement(250, 400, 600, WaterTolerance.VERY_HIGH),
        soil=SoilRequirement(5.5, 6.0, 7.5, 8.5, [2,3,4,5,6], SalinityTolerance.TOLERANT, 30),
        temperature=TemperatureRequirement(15, 22, 32, 40, 0, False),
        suitable_climates=[
            KoppenClimate.Aw, KoppenClimate.BSh, KoppenClimate.BSk,
            KoppenClimate.Cwa,
        ],
        max_slope_percent=10, suitable_lcc_classes=[1,2,3,4], altitude_range_m=(0, 2000),
        economics=EconomicData(1.2, 0.80, 500, 25),
        rotation_compatible=["sorghum", "millet_pearl", "maize"],
        major_producers=["Nigeria", "Niger", "Burkina Faso", "Senegal", "Kenya"],
        uses=["human_food", "animal_feed"],
        shelf_life_days=365,
        notes="African climate hero. Grows on poor soils with minimal rain."
    ),
    "mung_bean": CropProfile(
        id="mung_bean", name_fa="ماش", name_en="Mung Bean",
        scientific_name="Vigna radiata", family=CropFamily.LEGUME,
        growing_days=80, planting_months=[5,6,7],
        water=WaterRequirement(300, 400, 550, WaterTolerance.HIGH),
        soil=SoilRequirement(6.0, 6.5, 7.5, 8.0, [4,5,6,7], SalinityTolerance.MODERATE, 30),
        temperature=TemperatureRequirement(15, 22, 32, 38, 0, False),
        suitable_climates=[
            KoppenClimate.Aw, KoppenClimate.Cwa, KoppenClimate.Cwb,
            KoppenClimate.BSh,
        ],
        max_slope_percent=10, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 2000),
        economics=EconomicData(1.3, 1.00, 600, 25),
        rotation_compatible=["rice", "wheat"],
        major_producers=["India", "China", "Myanmar", "Indonesia", "Australia"],
        uses=["human_food", "sprouts"],
        shelf_life_days=730,
    ),

    # ===== TUBERS =====
    "potato": CropProfile(
        id="potato", name_fa="سیب‌زمینی", name_en="Potato",
        scientific_name="Solanum tuberosum", family=CropFamily.TUBER,
        growing_days=110, planting_months=[3,4,9,10],
        water=WaterRequirement(500, 650, 850, WaterTolerance.MEDIUM),
        soil=SoilRequirement(5.0, 5.5, 6.5, 7.0, [2,3,4,5], SalinityTolerance.SENSITIVE, 50),
        temperature=TemperatureRequirement(5, 15, 22, 28, 0, False),
        suitable_climates=[
            KoppenClimate.Cfb, KoppenClimate.Cfa, KoppenClimate.Cwb,
            KoppenClimate.Dfb, KoppenClimate.Dfc, KoppenClimate.Dwb,
        ],
        max_slope_percent=10, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 4000),
        economics=EconomicData(25.0, 0.30, 2500, 80),
        rotation_compatible=["cereal", "legume"],
        major_producers=["China", "India", "Ukraine", "Russia", "USA", "Germany"],
        uses=["human_food", "industrial", "animal_feed"],
        shelf_life_days=180,
        notes="4th largest food crop. Andes origin. 370M tons global."
    ),
    "cassava": CropProfile(
        id="cassava", name_fa="کاساوا", name_en="Cassava",
        scientific_name="Manihot esculenta", family=CropFamily.TUBER,
        growing_days=240, planting_months=[3,4,9,10,11],
        water=WaterRequirement(500, 1000, 1800, WaterTolerance.VERY_HIGH),
        soil=SoilRequirement(4.5, 5.0, 6.5, 7.5, [2,3,4,5,6], SalinityTolerance.MODERATE, 40),
        temperature=TemperatureRequirement(16, 25, 32, 38, 0, False),
        suitable_climates=[
            KoppenClimate.Af, KoppenClimate.Am, KoppenClimate.Aw,
            KoppenClimate.BSh, KoppenClimate.Cwa,
        ],
        max_slope_percent=15, suitable_lcc_classes=[1,2,3,4,5], altitude_range_m=(0, 2000),
        economics=EconomicData(15.0, 0.15, 800, 60),
        rotation_compatible=["legume", "maize"],
        major_producers=["Nigeria", "Thailand", "Brazil", "DR Congo", "Indonesia", "Ghana"],
        uses=["human_food", "industrial", "animal_feed", "biofuel"],
        shelf_life_days=30,
        notes="Drought champion of tropics. 300M tons. African staple."
    ),
    "sweet_potato": CropProfile(
        id="sweet_potato", name_fa="سیب‌زمینی شیرین", name_en="Sweet Potato",
        scientific_name="Ipomoea batatas", family=CropFamily.TUBER,
        growing_days=140, planting_months=[4,5,6],
        water=WaterRequirement(450, 650, 900, WaterTolerance.HIGH),
        soil=SoilRequirement(5.0, 5.5, 6.5, 7.5, [2,3,4,5], SalinityTolerance.MODERATE, 40),
        temperature=TemperatureRequirement(15, 22, 30, 35, 0, False),
        suitable_climates=[
            KoppenClimate.Af, KoppenClimate.Am, KoppenClimate.Aw,
            KoppenClimate.Cfa, KoppenClimate.Cwa, KoppenClimate.Cwb,
        ],
        max_slope_percent=15, suitable_lcc_classes=[1,2,3,4], altitude_range_m=(0, 2500),
        economics=EconomicData(18.0, 0.25, 1000, 70),
        rotation_compatible=["legume", "cereal"],
        major_producers=["China", "Nigeria", "Tanzania", "Ethiopia", "Mozambique", "Uganda"],
        uses=["human_food", "animal_feed", "industrial"],
        shelf_life_days=90,
        notes="High β-carotene varieties combat vitamin A deficiency."
    ),

    # ===== VEGETABLES =====
    "tomato": CropProfile(
        id="tomato", name_fa="گوجه‌فرنگی", name_en="Tomato",
        scientific_name="Solanum lycopersicum", family=CropFamily.VEGETABLE,
        growing_days=120, planting_months=[3,4,5,8,9],
        water=WaterRequirement(500, 700, 900, WaterTolerance.LOW),
        soil=SoilRequirement(6.0, 6.5, 7.0, 7.5, [4,5,6,7], SalinityTolerance.MODERATE, 50),
        temperature=TemperatureRequirement(12, 18, 28, 35, 0, False),
        suitable_climates=[
            KoppenClimate.Csa, KoppenClimate.Csb, KoppenClimate.Cfa,
            KoppenClimate.Cwa, KoppenClimate.Cwb, KoppenClimate.BSh,
        ],
        max_slope_percent=8, suitable_lcc_classes=[1,2], altitude_range_m=(0, 3000),
        economics=EconomicData(50.0, 1.20, 4000, 120),
        rotation_compatible=["cereal", "legume"],
        major_producers=["China", "India", "Turkey", "USA", "Egypt", "Italy"],
        uses=["human_food", "industrial"],
        shelf_life_days=14,
        notes="186M tons global. Greenhouse extends range to all climates."
    ),
    "onion": CropProfile(
        id="onion", name_fa="پیاز", name_en="Onion",
        scientific_name="Allium cepa", family=CropFamily.VEGETABLE,
        growing_days=150, planting_months=[3,4,9,10],
        water=WaterRequirement(400, 550, 700, WaterTolerance.MEDIUM),
        soil=SoilRequirement(6.0, 6.5, 7.0, 7.5, [3,4,5,6], SalinityTolerance.MODERATE, 40),
        temperature=TemperatureRequirement(-3, 12, 25, 32, 0, True),
        suitable_climates=[
            KoppenClimate.BSk, KoppenClimate.Csa, KoppenClimate.Csb,
            KoppenClimate.Cfa, KoppenClimate.Cfb, KoppenClimate.Dfb,
        ],
        max_slope_percent=8, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 3000),
        economics=EconomicData(35.0, 0.40, 2500, 70),
        rotation_compatible=["cereal", "legume"],
        major_producers=["China", "India", "USA", "Egypt", "Turkey", "Pakistan"],
        uses=["human_food"],
        shelf_life_days=180,
    ),

    # ===== OILSEEDS =====
    "sunflower": CropProfile(
        id="sunflower", name_fa="آفتابگردان", name_en="Sunflower",
        scientific_name="Helianthus annuus", family=CropFamily.OILSEED,
        growing_days=120, planting_months=[4,5,10,11],
        water=WaterRequirement(400, 550, 750, WaterTolerance.MEDIUM),
        soil=SoilRequirement(6.0, 6.5, 7.5, 8.0, [4,5,6,7], SalinityTolerance.TOLERANT, 50),
        temperature=TemperatureRequirement(8, 18, 28, 35, 0, False),
        suitable_climates=[
            KoppenClimate.BSk, KoppenClimate.Csa, KoppenClimate.Cfa,
            KoppenClimate.Dfa, KoppenClimate.Dfb, KoppenClimate.Dwa,
        ],
        max_slope_percent=10, suitable_lcc_classes=[1,2,3,4], altitude_range_m=(0, 2500),
        economics=EconomicData(2.5, 0.55, 800, 25),
        rotation_compatible=["wheat", "maize"],
        major_producers=["Ukraine", "Russia", "Argentina", "EU", "China", "Turkey"],
        uses=["oilseed", "human_food", "animal_feed"],
        shelf_life_days=365,
        notes="Deep-rooted, drought-adapted oilseed."
    ),
    "rapeseed_canola": CropProfile(
        id="rapeseed_canola", name_fa="کلزا", name_en="Rapeseed/Canola",
        scientific_name="Brassica napus", family=CropFamily.OILSEED,
        growing_days=200, planting_months=[9,10],
        water=WaterRequirement(350, 500, 700, WaterTolerance.MEDIUM),
        soil=SoilRequirement(5.5, 6.0, 7.5, 8.0, [4,5,6,7], SalinityTolerance.MODERATE, 40),
        temperature=TemperatureRequirement(-8, 8, 22, 28, 0, True),
        suitable_climates=[
            KoppenClimate.Cfb, KoppenClimate.Cfa, KoppenClimate.Csb,
            KoppenClimate.Dfa, KoppenClimate.Dfb, KoppenClimate.Dwa,
        ],
        max_slope_percent=10, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 2500),
        economics=EconomicData(3.0, 0.60, 900, 25),
        rotation_compatible=["wheat", "barley", "rice"],
        major_producers=["Canada", "EU", "China", "India", "Australia", "Ukraine"],
        uses=["oilseed", "animal_feed", "biofuel"],
        shelf_life_days=365,
    ),

    # ===== FRUITS =====
    "apple": CropProfile(
        id="apple", name_fa="سیب", name_en="Apple",
        scientific_name="Malus domestica", family=CropFamily.FRUIT,
        growing_days=365 * 20, planting_months=[11,12,1,2],
        water=WaterRequirement(600, 900, 1200, WaterTolerance.MEDIUM),
        soil=SoilRequirement(6.0, 6.5, 7.0, 7.5, [4,5,6,7], SalinityTolerance.SENSITIVE, 100),
        temperature=TemperatureRequirement(-25, 10, 25, 32, 800, True),
        suitable_climates=[
            KoppenClimate.Cfb, KoppenClimate.Cfa, KoppenClimate.Dfb,
            KoppenClimate.Dfa, KoppenClimate.Cwb, KoppenClimate.Dwb,
        ],
        max_slope_percent=20, suitable_lcc_classes=[2,3,4,5], altitude_range_m=(500, 3500),
        economics=EconomicData(25.0, 0.90, 5000, 60),
        rotation_compatible=["perennial"],
        major_producers=["China", "USA", "Turkey", "Poland", "India", "Italy"],
        uses=["human_food", "beverage"],
        shelf_life_days=180,
        notes="Requires chilling hours. 87M tons global."
    ),
    "citrus_orange": CropProfile(
        id="citrus_orange", name_fa="پرتقال", name_en="Sweet Orange",
        scientific_name="Citrus × sinensis", family=CropFamily.FRUIT,
        growing_days=365 * 20, planting_months=[2,3,10,11],
        water=WaterRequirement(900, 1200, 1600, WaterTolerance.LOW),
        soil=SoilRequirement(5.5, 6.0, 7.5, 8.0, [3,4,5,6,7], SalinityTolerance.SENSITIVE, 100),
        temperature=TemperatureRequirement(-3, 15, 30, 38, 0, False),
        suitable_climates=[
            KoppenClimate.Csa, KoppenClimate.Cfa, KoppenClimate.Cwa,
            KoppenClimate.Aw, KoppenClimate.BSh,
        ],
        max_slope_percent=15, suitable_lcc_classes=[1,2,3,4], altitude_range_m=(0, 2000),
        economics=EconomicData(25.0, 0.50, 4500, 60),
        rotation_compatible=["perennial"],
        major_producers=["Brazil", "China", "India", "USA", "Mexico", "Spain"],
        uses=["human_food", "beverage", "industrial"],
        shelf_life_days=45,
        notes="Frost-sensitive. 75M tons oranges annually."
    ),
    "banana": CropProfile(
        id="banana", name_fa="موز", name_en="Banana",
        scientific_name="Musa acuminata", family=CropFamily.FRUIT,
        growing_days=365, planting_months=[1,2,3,4,5,6,7,8,9,10,11,12],
        water=WaterRequirement(1200, 2000, 3000, WaterTolerance.LOW),
        soil=SoilRequirement(5.5, 6.0, 7.0, 7.5, [4,5,6,7], SalinityTolerance.SENSITIVE, 80),
        temperature=TemperatureRequirement(15, 22, 30, 35, 0, False),
        suitable_climates=[
            KoppenClimate.Af, KoppenClimate.Am, KoppenClimate.Aw,
        ],
        max_slope_percent=20, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 2000),
        economics=EconomicData(40.0, 0.60, 3500, 100),
        rotation_compatible=["perennial"],
        major_producers=["India", "China", "Indonesia", "Brazil", "Ecuador", "Philippines"],
        uses=["human_food"],
        shelf_life_days=14,
        notes="150M tons. Staple for 400M people in tropics."
    ),
    "mango": CropProfile(
        id="mango", name_fa="انبه", name_en="Mango",
        scientific_name="Mangifera indica", family=CropFamily.FRUIT,
        growing_days=365 * 10, planting_months=[6,7,8],
        water=WaterRequirement(700, 1200, 2000, WaterTolerance.HIGH),
        soil=SoilRequirement(5.5, 6.0, 7.5, 8.0, [3,4,5,6,7], SalinityTolerance.MODERATE, 120),
        temperature=TemperatureRequirement(5, 22, 32, 42, 0, False),
        suitable_climates=[
            KoppenClimate.Aw, KoppenClimate.Am, KoppenClimate.BSh,
            KoppenClimate.Cwa,
        ],
        max_slope_percent=20, suitable_lcc_classes=[1,2,3,4,5], altitude_range_m=(0, 1500),
        economics=EconomicData(15.0, 1.00, 3000, 50),
        rotation_compatible=["perennial"],
        major_producers=["India", "China", "Thailand", "Indonesia", "Mexico", "Pakistan"],
        uses=["human_food", "industrial"],
        shelf_life_days=21,
    ),
    "olive": CropProfile(
        id="olive", name_fa="زیتون", name_en="Olive",
        scientific_name="Olea europaea", family=CropFamily.FRUIT,
        growing_days=365 * 25, planting_months=[11,12,1,2,3],
        water=WaterRequirement(400, 650, 900, WaterTolerance.HIGH),
        soil=SoilRequirement(6.0, 6.5, 8.0, 8.5, [3,4,5,6,7], SalinityTolerance.TOLERANT, 100),
        temperature=TemperatureRequirement(-8, 12, 28, 38, 200, True),
        suitable_climates=[
            KoppenClimate.Csa, KoppenClimate.Csb, KoppenClimate.BSk,
            KoppenClimate.BSh,
        ],
        max_slope_percent=35, suitable_lcc_classes=[2,3,4,5,6], altitude_range_m=(0, 1500),
        economics=EconomicData(6.0, 2.50, 2500, 50),
        rotation_compatible=["perennial"],
        major_producers=["Spain", "Italy", "Greece", "Turkey", "Tunisia", "Morocco"],
        uses=["human_food", "oilseed", "medicinal"],
        shelf_life_days=365,
        notes="Mediterranean icon. 3000-year lifespan. Oil-rich."
    ),
    "date_palm": CropProfile(
        id="date_palm", name_fa="خرما", name_en="Date Palm",
        scientific_name="Phoenix dactylifera", family=CropFamily.FRUIT,
        growing_days=365 * 30, planting_months=[2,3,4],
        water=WaterRequirement(600, 1000, 1500, WaterTolerance.VERY_HIGH),
        soil=SoilRequirement(6.5, 7.0, 8.5, 9.5, [2,3,4,5,6,7,8], SalinityTolerance.HIGHLY_TOLERANT, 150),
        temperature=TemperatureRequirement(-5, 20, 38, 50, 0, True),
        suitable_climates=[
            KoppenClimate.BWh, KoppenClimate.BWk, KoppenClimate.BSh,
        ],
        max_slope_percent=10, suitable_lcc_classes=[1,2,3,4,5], altitude_range_m=(0, 1500),
        economics=EconomicData(10.0, 2.00, 2500, 60),
        rotation_compatible=["perennial"],
        major_producers=["Egypt", "Saudi Arabia", "Iran", "Algeria", "Iraq", "Pakistan"],
        uses=["human_food", "medicinal"],
        shelf_life_days=365,
        notes="Desert oasis symbol. Thrives in BWh with irrigation."
    ),

    # ===== INDUSTRIAL =====
    "cotton": CropProfile(
        id="cotton", name_fa="پنبه", name_en="Cotton",
        scientific_name="Gossypium hirsutum", family=CropFamily.INDUSTRIAL,
        growing_days=180, planting_months=[4,5,10,11],
        water=WaterRequirement(600, 850, 1100, WaterTolerance.MEDIUM),
        soil=SoilRequirement(6.0, 6.5, 8.0, 8.5, [4,5,6,7,8], SalinityTolerance.TOLERANT, 60),
        temperature=TemperatureRequirement(15, 22, 32, 40, 0, False),
        suitable_climates=[
            KoppenClimate.BWh, KoppenClimate.BSh, KoppenClimate.Cfa,
            KoppenClimate.Cwa, KoppenClimate.Aw,
        ],
        max_slope_percent=5, suitable_lcc_classes=[1,2,3], altitude_range_m=(0, 2000),
        economics=EconomicData(2.5, 2.00, 2000, 80),
        rotation_compatible=["wheat", "legume"],
        major_producers=["India", "China", "USA", "Brazil", "Pakistan", "Turkey"],
        uses=["industrial", "oilseed"],
        shelf_life_days=365,
        notes="25M tons fiber. Major textile raw material."
    ),
    "sugarcane": CropProfile(
        id="sugarcane", name_fa="نیشکر", name_en="Sugarcane",
        scientific_name="Saccharum officinarum", family=CropFamily.INDUSTRIAL,
        growing_days=365, planting_months=[2,3,9,10],
        water=WaterRequirement(1500, 2000, 2500, WaterTolerance.LOW),
        soil=SoilRequirement(6.0, 6.5, 7.5, 8.0, [5,6,7,8], SalinityTolerance.MODERATE, 80),
        temperature=TemperatureRequirement(15, 25, 35, 42, 0, False),
        suitable_climates=[
            KoppenClimate.Af, KoppenClimate.Am, KoppenClimate.Aw,
            KoppenClimate.Cfa, KoppenClimate.Cwa,
        ],
        max_slope_percent=8, suitable_lcc_classes=[1,2], altitude_range_m=(0, 1500),
        economics=EconomicData(80.0, 0.04, 2000, 100),
        rotation_compatible=["perennial_3yr"],
        major_producers=["Brazil", "India", "China", "Thailand", "Pakistan", "Mexico"],
        uses=["human_food", "industrial", "biofuel"],
        shelf_life_days=14,
        notes="1.9B tons. Largest crop by weight. Bioethanol source."
    ),
    "tea": CropProfile(
        id="tea", name_fa="چای", name_en="Tea",
        scientific_name="Camellia sinensis", family=CropFamily.BEVERAGE,
        growing_days=365 * 30, planting_months=[6,7,8],
        water=WaterRequirement(1500, 2000, 3000, WaterTolerance.LOW),
        soil=SoilRequirement(4.5, 5.0, 6.0, 6.5, [4,5,6], SalinityTolerance.SENSITIVE, 80),
        temperature=TemperatureRequirement(-5, 15, 25, 32, 0, True),
        suitable_climates=[
            KoppenClimate.Cfb, KoppenClimate.Cfa, KoppenClimate.Cwb,
            KoppenClimate.Cwa, KoppenClimate.Am,
        ],
        max_slope_percent=40, suitable_lcc_classes=[3,4,5,6], altitude_range_m=(800, 2500),
        economics=EconomicData(3.0, 3.50, 4000, 200),
        rotation_compatible=["perennial"],
        major_producers=["China", "India", "Kenya", "Sri Lanka", "Turkey", "Vietnam"],
        uses=["beverage", "medicinal"],
        shelf_life_days=730,
        notes="Highland crop. Acid soils required. 6M tons."
    ),
    "coffee_arabica": CropProfile(
        id="coffee_arabica", name_fa="قهوه عربیکا", name_en="Arabica Coffee",
        scientific_name="Coffea arabica", family=CropFamily.BEVERAGE,
        growing_days=365 * 20, planting_months=[5,6,7],
        water=WaterRequirement(1200, 1800, 2500, WaterTolerance.LOW),
        soil=SoilRequirement(5.0, 5.5, 6.5, 7.0, [4,5,6], SalinityTolerance.SENSITIVE, 100),
        temperature=TemperatureRequirement(10, 15, 24, 30, 0, False),
        suitable_climates=[
            KoppenClimate.Af, KoppenClimate.Am, KoppenClimate.Cwb,
            KoppenClimate.Cfb,
        ],
        max_slope_percent=30, suitable_lcc_classes=[2,3,4,5], altitude_range_m=(1000, 2200),
        economics=EconomicData(1.5, 5.00, 4000, 150),
        rotation_compatible=["perennial"],
        major_producers=["Brazil", "Colombia", "Ethiopia", "Honduras", "Peru", "Guatemala"],
        uses=["beverage"],
        shelf_life_days=365,
        notes="High-value highland crop. Climate-sensitive to warming."
    ),

    # ===== FORAGE =====
    "alfalfa": CropProfile(
        id="alfalfa", name_fa="یونجه", name_en="Alfalfa",
        scientific_name="Medicago sativa", family=CropFamily.FORAGE,
        growing_days=60, planting_months=[3,4,9,10],
        water=WaterRequirement(600, 900, 1300, WaterTolerance.MEDIUM),
        soil=SoilRequirement(6.5, 7.0, 8.0, 8.5, [4,5,6,7], SalinityTolerance.MODERATE, 80),
        temperature=TemperatureRequirement(-20, 12, 28, 38, 0, True),
        suitable_climates=[
            KoppenClimate.BSk, KoppenClimate.Csa, KoppenClimate.Cfa,
            KoppenClimate.Cfb, KoppenClimate.Dfa, KoppenClimate.Dfb,
        ],
        max_slope_percent=12, suitable_lcc_classes=[1,2,3,4], altitude_range_m=(0, 3000),
        economics=EconomicData(18.0, 0.20, 1500, 25),
        rotation_compatible=["perennial_5yr"],
        major_producers=["USA", "China", "Russia", "Argentina", "India"],
        uses=["animal_feed"],
        shelf_life_days=365,
        notes="Queen of forages. N-fixing. 5-year perennial."
    ),
}


# ============================================================
# Query Functions
# ============================================================

def get_crop_by_id(crop_id: str) -> CropProfile | None:
    return CROP_DATABASE.get(crop_id)


def get_all_crops() -> list[CropProfile]:
    return list(CROP_DATABASE.values())


def filter_by_climate(climate: KoppenClimate) -> list[CropProfile]:
    return [c for c in CROP_DATABASE.values() if climate in c.suitable_climates]


def filter_by_family(family: CropFamily) -> list[CropProfile]:
    return [c for c in CROP_DATABASE.values() if c.family == family]


def filter_drought_tolerant() -> list[CropProfile]:
    return [c for c in CROP_DATABASE.values()
            if c.water.drought_tolerance in (WaterTolerance.HIGH, WaterTolerance.VERY_HIGH)]


def filter_salinity_tolerant() -> list[CropProfile]:
    return [c for c in CROP_DATABASE.values()
            if c.soil.salinity_tolerance in (SalinityTolerance.TOLERANT, SalinityTolerance.HIGHLY_TOLERANT)]


def get_crop_statistics() -> dict:
    crops = list(CROP_DATABASE.values())
    return {
        "total_crops": len(crops),
        "by_family": {f.value: len([c for c in crops if c.family == f]) for f in CropFamily},
        "by_climate": {c.name: len([cr for cr in crops if c in cr.suitable_climates])
                      for c in KoppenClimate},
        "drought_tolerant": len([c for c in crops if c.water.drought_tolerance in
                                (WaterTolerance.HIGH, WaterTolerance.VERY_HIGH)]),
        "salinity_tolerant": len([c for c in crops if c.soil.salinity_tolerance in
                                 (SalinityTolerance.TOLERANT, SalinityTolerance.HIGHLY_TOLERANT)]),
        "annual_crops": len([c for c in crops if c.growing_days < 365]),
        "perennial_crops": len([c for c in crops if c.growing_days >= 365]),
        "koppen_climates_covered": len({c for crop in crops for c in crop.suitable_climates}),
    }


def climate_description(code: KoppenClimate) -> str:
    """توضیحات کامل هر اقلیم"""
    descriptions = {
        KoppenClimate.Af: "Hot, humid year-round. No dry season. Rainforest.",
        KoppenClimate.Am: "Tropical with short dry season. Monsoon-driven.",
        KoppenClimate.Aw: "Distinct wet/dry seasons. Tropical savanna.",
        KoppenClimate.BWh: "Hot desert. <250mm rain. Extreme heat.",
        KoppenClimate.BWk: "Cold desert. <250mm rain. Cold winters.",
        KoppenClimate.BSh: "Hot semi-arid. 250-500mm. Steppe grasslands.",
        KoppenClimate.BSk: "Cold semi-arid. 250-500mm. Cold winters.",
        KoppenClimate.Csa: "Mediterranean. Hot dry summer, mild wet winter.",
        KoppenClimate.Csb: "Cool Mediterranean. Cooler summers.",
        KoppenClimate.Csc: "Rare. Cold-summer Mediterranean.",
        KoppenClimate.Cfa: "Humid subtropical. Hot summer, year-round rain.",
        KoppenClimate.Cfb: "Oceanic. Mild year-round, even rain.",
        KoppenClimate.Cfc: "Subpolar oceanic. Cool summers, mild winters.",
        KoppenClimate.Cwa: "Subtropical with dry winter. Monsoon-influenced.",
        KoppenClimate.Cwb: "Subtropical highland. Dry winter, mild.",
        KoppenClimate.Cwc: "Cold dry-winter subtropical. Rare.",
        KoppenClimate.Dsa: "Dry-summer continental. Rare.",
        KoppenClimate.Dsb: "Dry-summer continental. Mediterranean-like.",
        KoppenClimate.Dsc: "Dry cold-summer continental. Rare.",
        KoppenClimate.Dsd: "Extremely cold dry-winter. Siberia.",
        KoppenClimate.Dfa: "Humid continental. Hot summer. Great Plains USA.",
        KoppenClimate.Dfb: "Humid continental. Warm summer. N Europe.",
        KoppenClimate.Dfc: "Subarctic. Short cool summer. Boreal forest.",
        KoppenClimate.Dfd: "Extremely cold subarctic. Yakutia.",
        KoppenClimate.Dwa: "Monsoon continental. Hot summer. NE China.",
        KoppenClimate.Dwb: "Monsoon continental. Warm summer. Manchuria.",
        KoppenClimate.Dwc: "Dry-winter subarctic. Mongolia.",
        KoppenClimate.Dwd: "Extreme cold dry-winter. NE Siberia.",
        KoppenClimate.ET: "Tundra. No month >10°C. Permafrost.",
        KoppenClimate.EF: "Ice cap. All months <0°C. Antarctica.",
    }
    return descriptions.get(code, "Unknown")
