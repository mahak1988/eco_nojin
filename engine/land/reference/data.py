"""
Reference Data - Built-in Geographic Reference
==============================================

Initial dataset of countries, regions, and cities.
Can be extended via database or external data sources.

Data sources:
- ISO 3166 for country codes
- UN Statistics Division for area/population
- GeoNames for city coordinates
"""


from .models import City, Continent, Country, DrainageStandard, Region, TerrainClassification

# ======================================================================
# Countries (Top 25 + key countries)
# ======================================================================
COUNTRIES: list[Country] = [
    Country(
        code="IR", name="Iran", name_fa="ایران",
        continent=Continent.ASIA,
        capital_lat=35.69, capital_lon=51.39,
        area_km2=1648195, population=88000000,
        dominant_climate="BWh", currency="IRR"
    ),
    Country(
        code="YE", name="Yemen", name_fa="یمن",
        continent=Continent.ASIA,
        capital_lat=15.35, capital_lon=44.21,
        area_km2=527968, population=33000000,
        dominant_climate="BWh", currency="YER"
    ),
    Country(
        code="US", name="United States", name_fa="ایالات متحده آمریکا",
        continent=Continent.NORTH_AMERICA,
        capital_lat=38.90, capital_lon=-77.04,
        area_km2=9833517, population=331000000,
        dominant_climate="Cfa", currency="USD"
    ),
    Country(
        code="NL", name="Netherlands", name_fa="هلند",
        continent=Continent.EUROPE,
        capital_lat=52.37, capital_lon=4.90,
        area_km2=41543, population=17500000,
        dominant_climate="Cfb", currency="EUR"
    ),
    Country(
        code="SA", name="Saudi Arabia", name_fa="عربستان سعودی",
        continent=Continent.ASIA,
        capital_lat=24.71, capital_lon=46.67,
        area_km2=2149690, population=35000000,
        dominant_climate="BWh", currency="SAR"
    ),
    Country(
        code="EG", name="Egypt", name_fa="مصر",
        continent=Continent.AFRICA,
        capital_lat=30.04, capital_lon=31.24,
        area_km2=1001449, population=104000000,
        dominant_climate="BWh", currency="EGP"
    ),
    Country(
        code="MN", name="Mongolia", name_fa="مغولستان",
        continent=Continent.ASIA,
        capital_lat=47.92, capital_lon=106.91,
        area_km2=1564116, population=3300000,
        dominant_climate="BSk", currency="MNT"
    ),
    Country(
        code="AU", name="Australia", name_fa="استرالیا",
        continent=Continent.OCEANIA,
        capital_lat=-35.28, capital_lon=149.13,
        area_km2=7692024, population=26000000,
        dominant_climate="BWh", currency="AUD"
    ),
    Country(
        code="FR", name="France", name_fa="فرانسه",
        continent=Continent.EUROPE,
        capital_lat=48.86, capital_lon=2.35,
        area_km2=643801, population=67000000,
        dominant_climate="Cfb", currency="EUR"
    ),
    Country(
        code="IT", name="Italy", name_fa="ایتالیا",
        continent=Continent.EUROPE,
        capital_lat=41.90, capital_lon=12.50,
        area_km2=301340, population=60000000,
        dominant_climate="Csa", currency="EUR"
    ),
    Country(
        code="JP", name="Japan", name_fa="ژاپن",
        continent=Continent.ASIA,
        capital_lat=35.68, capital_lon=139.69,
        area_km2=377975, population=125000000,
        dominant_climate="Cfa", currency="JPY"
    ),
    Country(
        code="NZ", name="New Zealand", name_fa="نیوزیلند",
        continent=Continent.OCEANIA,
        capital_lat=-41.29, capital_lon=174.78,
        area_km2=268838, population=5100000,
        dominant_climate="Cfb", currency="NZD"
    ),
    Country(
        code="ZA", name="South Africa", name_fa="آفریقای جنوبی",
        continent=Continent.AFRICA,
        capital_lat=-33.93, capital_lon=18.42,
        area_km2=1221037, population=60000000,
        dominant_climate="Csb", currency="ZAR"
    ),
    Country(
        code="AR", name="Argentina", name_fa="آرژانتین",
        continent=Continent.SOUTH_AMERICA,
        capital_lat=-34.60, capital_lon=-58.38,
        area_km2=2780400, population=45000000,
        dominant_climate="Cfa", currency="ARS"
    ),
    Country(
        code="DE", name="Germany", name_fa="آلمان",
        continent=Continent.EUROPE,
        capital_lat=52.52, capital_lon=13.40,
        area_km2=357022, population=83000000,
        dominant_climate="Cfb", currency="EUR"
    ),
    Country(
        code="RU", name="Russia", name_fa="روسیه",
        continent=Continent.EUROPE,
        capital_lat=55.76, capital_lon=37.62,
        area_km2=17098242, population=145000000,
        dominant_climate="Dfb", currency="RUB"
    ),
    Country(
        code="CA", name="Canada", name_fa="کانادا",
        continent=Continent.NORTH_AMERICA,
        capital_lat=45.42, capital_lon=-75.70,
        area_km2=9984670, population=38000000,
        dominant_climate="Dfb", currency="CAD"
    ),
    Country(
        code="CN", name="China", name_fa="چین",
        continent=Continent.ASIA,
        capital_lat=39.90, capital_lon=116.40,
        area_km2=9596961, population=1412000000,
        dominant_climate="Dwa", currency="CNY"
    ),
    Country(
        code="FI", name="Finland", name_fa="فنلاند",
        continent=Continent.EUROPE,
        capital_lat=60.17, capital_lon=24.94,
        area_km2=338424, population=5500000,
        dominant_climate="Dfb", currency="EUR"
    ),
    Country(
        code="NO", name="Norway", name_fa="نروژ",
        continent=Continent.EUROPE,
        capital_lat=69.65, capital_lon=18.96,
        area_km2=323802, population=5400000,
        dominant_climate="ET", currency="NOK"
    ),
    Country(
        code="IS", name="Iceland", name_fa="ایسلند",
        continent=Continent.EUROPE,
        capital_lat=64.15, capital_lon=-21.94,
        area_km2=103000, population=370000,
        dominant_climate="ET", currency="ISK"
    ),
    Country(
        code="GL", name="Greenland", name_fa="گرینلند",
        continent=Continent.NORTH_AMERICA,
        capital_lat=64.17, capital_lon=-51.74,
        area_km2=2166086, population=56000,
        dominant_climate="ET", currency="DKK"
    ),
    Country(
        code="BR", name="Brazil", name_fa="برزیل",
        continent=Continent.SOUTH_AMERICA,
        capital_lat=-15.78, capital_lon=-47.93,
        area_km2=8515767, population=214000000,
        dominant_climate="Aw", currency="BRL"
    ),
    Country(
        code="ID", name="Indonesia", name_fa="اندونزی",
        continent=Continent.ASIA,
        capital_lat=-6.21, capital_lon=106.85,
        area_km2=1904569, population=275000000,
        dominant_climate="Af", currency="IDR"
    ),
    Country(
        code="NG", name="Nigeria", name_fa="نیجریه",
        continent=Continent.AFRICA,
        capital_lat=9.06, capital_lon=7.49,
        area_km2=923768, population=218000000,
        dominant_climate="Aw", currency="NGN"
    ),
    Country(
        code="IN", name="India", name_fa="هند",
        continent=Continent.ASIA,
        capital_lat=28.61, capital_lon=77.21,
        area_km2=3287263, population=1420000000,
        dominant_climate="Am", currency="INR"
    ),
]


# ======================================================================
# Regions (Iran provinces + international samples)
# ======================================================================
REGIONS: list[Region] = [
    # Iran provinces
    Region(code="IR-04", name="Isfahan", name_fa="اصفهان",
           country_code="IR", center_lat=32.65, center_lon=51.67,
           area_km2=107029, population=5200000, elevation_mean_m=1570),
    Region(code="IR-07", name="Tehran", name_fa="تهران",
           country_code="IR", center_lat=35.69, center_lon=51.39,
           area_km2=18814, population=13900000, elevation_mean_m=1200),
    Region(code="IR-10", name="Khuzestan", name_fa="خوزستان",
           country_code="IR", center_lat=31.32, center_lon=48.67,
           area_km2=64055, population=4700000, elevation_mean_m=100),
    Region(code="IR-14", name="Fars", name_fa="فارس",
           country_code="IR", center_lat=29.61, center_lon=52.54,
           area_km2=122608, population=4900000, elevation_mean_m=1500),
    Region(code="IR-21", name="Yazd", name_fa="یزد",
           country_code="IR", center_lat=31.90, center_lon=54.36,
           area_km2=129285, population=1200000, elevation_mean_m=1200),
    Region(code="IR-30", name="Kerman", name_fa="کرمان",
           country_code="IR", center_lat=30.28, center_lon=57.08,
           area_km2=180726, population=3200000, elevation_mean_m=1755),

    # International samples
    Region(code="US-CA", name="California", name_fa="کالیفرنیا",
           country_code="US", center_lat=36.78, center_lon=-119.42,
           area_km2=423972, population=39500000, elevation_mean_m=884),
    Region(code="AU-NT", name="Northern Territory", name_fa="قلمرو شمالی",
           country_code="AU", center_lat=-19.49, center_lon=132.55,
           area_km2=1349129, population=250000, elevation_mean_m=300),
]


# ======================================================================
# Cities (major cities for quick access)
# ======================================================================
CITIES: list[City] = [
    # Iran
    City(name="Isfahan", name_fa="اصفهان", country_code="IR",
         region_code="IR-04", lat=32.65, lon=51.67,
         population=2100000, elevation_m=1574),
    City(name="Tehran", name_fa="تهران", country_code="IR",
         region_code="IR-07", lat=35.69, lon=51.39,
         population=8700000, elevation_m=1189),
    City(name="Shiraz", name_fa="شیراز", country_code="IR",
         region_code="IR-14", lat=29.61, lon=52.54,
         population=1600000, elevation_m=1486),
    City(name="Yazd", name_fa="یزد", country_code="IR",
         region_code="IR-21", lat=31.90, lon=54.36,
         population=530000, elevation_m=1216),

    # Yemen
    City(name="Sanaa", name_fa="صنعاء", country_code="YE",
         lat=15.35, lon=44.21, population=3200000, elevation_m=2250),

    # USA
    City(name="Sacramento", name_fa="ساکرامنتو", country_code="US",
         region_code="US-CA", lat=38.58, lon=-121.49,
         population=520000, elevation_m=9),

    # Europe
    City(name="Paris", name_fa="پاریس", country_code="FR",
         lat=48.86, lon=2.35, population=2100000, elevation_m=35),
    City(name="Rome", name_fa="رم", country_code="IT",
         lat=41.90, lon=12.50, population=2800000, elevation_m=21),
    City(name="Berlin", name_fa="برلین", country_code="DE",
         lat=52.52, lon=13.40, population=3600000, elevation_m=34),
    City(name="Amsterdam", name_fa="آمردام", country_code="NL",
         lat=52.37, lon=4.90, population=870000, elevation_m=-2),
    City(name="Moscow", name_fa="مسکو", country_code="RU",
         lat=55.76, lon=37.62, population=12500000, elevation_m=156),
    City(name="Helsinki", name_fa="هلسینکی", country_code="FI",
         lat=60.17, lon=24.94, population=660000, elevation_m=6),

    # Asia
    City(name="Tokyo", name_fa="توکیو", country_code="JP",
         lat=35.68, lon=139.69, population=13900000, elevation_m=40),
    City(name="Beijing", name_fa="پکن", country_code="CN",
         lat=39.90, lon=116.40, population=21500000, elevation_m=43),
    City(name="Mumbai", name_fa="بمبئی", country_code="IN",
         lat=19.08, lon=72.88, population=20400000, elevation_m=14),
    City(name="Jakarta", name_fa="جاکارتا", country_code="ID",
         lat=-6.21, lon=106.85, population=10600000, elevation_m=8),
    City(name="Riyadh", name_fa="ریاض", country_code="SA",
         lat=24.71, lon=46.67, population=7600000, elevation_m=612),
    City(name="Cairo", name_fa="قاهره", country_code="EG",
         lat=30.04, lon=31.24, population=10000000, elevation_m=23),
    City(name="Ulaanbaatar", name_fa="اولان‌باتور", country_code="MN",
         lat=47.92, lon=106.91, population=1500000, elevation_m=1350),

    # Others
    City(name="Alice Springs", name_fa="آلیس اسپرینگز", country_code="AU",
         region_code="AU-NT", lat=-23.70, lon=133.88,
         population=26000, elevation_m=576),
    City(name="Cape Town", name_fa="کیپ‌تاون", country_code="ZA",
         lat=-33.93, lon=18.42, population=4600000, elevation_m=44),
    City(name="Buenos Aires", name_fa="بوئنوس آیرس", country_code="AR",
         lat=-34.60, lon=-58.38, population=3000000, elevation_m=25),
    City(name="Toronto", name_fa="تورنتو", country_code="CA",
         lat=43.65, lon=-79.38, population=2900000, elevation_m=76),
    City(name="Tromsø", name_fa="ترومسو", country_code="NO",
         lat=69.65, lon=18.96, population=77000, elevation_m=10),
    City(name="Reykjavik", name_fa="ریکیاویک", country_code="IS",
         lat=64.15, lon=-21.94, population=130000, elevation_m=0),
    City(name="Nuuk", name_fa="نوک", country_code="GL",
         lat=64.17, lon=-51.74, population=18000, elevation_m=5),
    City(name="Manaus", name_fa="ماناوس", country_code="BR",
         lat=-3.10, lon=-60.02, population=2200000, elevation_m=92),
    City(name="Lagos", name_fa="لاگوس", country_code="NG",
         lat=6.52, lon=3.38, population=15000000, elevation_m=41),
    City(name="Auckland", name_fa="اوکلند", country_code="NZ",
         lat=-36.85, lon=174.76, population=1600000, elevation_m=25),
]


# ======================================================================
# Terrain Classification Standards
# ======================================================================
TERRAIN_CLASSIFICATIONS: list[TerrainClassification] = [
    TerrainClassification(
        code="flat", name="Flat",
        slope_min_deg=0, slope_max_deg=2,
        description="Nearly level terrain, suitable for all uses",
        source="USDA/FAO"
    ),
    TerrainClassification(
        code="nearly_flat", name="Nearly Flat",
        slope_min_deg=2, slope_max_deg=4,
        description="Very gentle slopes, minimal limitations",
        source="USDA/FAO"
    ),
    TerrainClassification(
        code="gentle", name="Gentle Slope",
        slope_min_deg=4, slope_max_deg=8,
        description="Gentle slopes, some erosion risk",
        source="USDA/FAO"
    ),
    TerrainClassification(
        code="rolling", name="Rolling",
        slope_min_deg=8, slope_max_deg=15,
        description="Undulating terrain with moderate erosion risk",
        source="USDA/FAO"
    ),
    TerrainClassification(
        code="hilly", name="Hilly",
        slope_min_deg=15, slope_max_deg=25,
        description="Hilly terrain, significant erosion risk",
        source="USDA/FAO"
    ),
    TerrainClassification(
        code="steep", name="Steep",
        slope_min_deg=25, slope_max_deg=45,
        description="Steep slopes, high erosion risk, limited use",
        source="USDA/FAO"
    ),
    TerrainClassification(
        code="very_steep", name="Very Steep",
        slope_min_deg=45, slope_max_deg=90,
        description="Very steep terrain, conservation only",
        source="USDA/FAO"
    ),
]


# ======================================================================
# Drainage Density Standards
# ======================================================================
DRAINAGE_STANDARDS: list[DrainageStandard] = [
    DrainageStandard(
        code="very_low", name="Very Low Density",
        density_min_km_km2=0, density_max_km_km2=2,
        description="Sparse drainage, typical of arid regions",
        typical_geology="Desert, limestone karst"
    ),
    DrainageStandard(
        code="low", name="Low Density",
        density_min_km_km2=2, density_max_km_km2=5,
        description="Coarse drainage, permeable substrate",
        typical_geology="Sandstone, granite"
    ),
    DrainageStandard(
        code="moderate", name="Moderate Density",
        density_min_km_km2=5, density_max_km_km2=15,
        description="Moderate drainage density",
        typical_geology="Mixed sedimentary"
    ),
    DrainageStandard(
        code="high", name="High Density",
        density_min_km_km2=15, density_max_km_km2=30,
        description="Fine drainage, impermeable substrate",
        typical_geology="Shale, clay"
    ),
    DrainageStandard(
        code="very_high", name="Very High Density",
        density_min_km_km2=30, density_max_km_km2=100,
        description="Very fine drainage, badlands terrain",
        typical_geology="Badlands, highly erodible"
    ),
]


# ======================================================================
# Lookup Functions
# ======================================================================

def get_country(code: str) -> Country:
    """Get country by ISO code."""
    for c in COUNTRIES:
        if c.code.upper() == code.upper():
            return c
    raise ValueError(f"Country not found: {code}")


def get_region(code: str) -> Region:
    """Get region by code."""
    for r in REGIONS:
        if r.code.upper() == code.upper():
            return r
    raise ValueError(f"Region not found: {code}")


def get_city(name: str) -> City:
    """Get city by name (English or Persian)."""
    name_lower = name.lower()
    for c in CITIES:
        if (c.name.lower() == name_lower or
                (c.name_fa and c.name_fa == name)):
            return c
    raise ValueError(f"City not found: {name}")


def list_countries(continent: str = None) -> list[Country]:
    """List countries, optionally filtered by continent."""
    if continent is None:
        return COUNTRIES
    return [c for c in COUNTRIES if c.continent.value == continent]


def list_regions(country_code: str = None) -> list[Region]:
    """List regions, optionally filtered by country."""
    if country_code is None:
        return REGIONS
    return [r for r in REGIONS
            if r.country_code.upper() == country_code.upper()]


def list_cities(country_code: str = None,
                region_code: str = None) -> list[City]:
    """List cities, optionally filtered."""
    result = CITIES
    if country_code:
        result = [c for c in result
                  if c.country_code.upper() == country_code.upper()]
    if region_code:
        result = [c for c in result if c.region_code == region_code]
    return result


def find_nearest_city(lat: float, lon: float) -> City:
    """Find nearest city to given coordinates (haversine)."""
    import math

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = (math.sin(dphi/2)**2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2)
        return 2 * R * math.asin(math.sqrt(a))

    nearest = None
    min_dist = float("inf")

    for city in CITIES:
        dist = haversine(lat, lon, city.lat, city.lon)
        if dist < min_dist:
            min_dist = dist
            nearest = city

    return nearest


def get_all_reference_summary() -> dict[str, int]:
    """Get summary of available reference data."""
    return {
        "countries": len(COUNTRIES),
        "regions": len(REGIONS),
        "cities": len(CITIES),
        "terrain_classifications": len(TERRAIN_CLASSIFICATIONS),
        "drainage_standards": len(DRAINAGE_STANDARDS),
    }
