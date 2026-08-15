"""Comprehensive soil analysis and remediation router."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import SoilAnalysis

router = APIRouter(prefix="/api/v1/soil", tags=["soil"])


class SoilAnalysisRequest(BaseModel):
    farm_id: int | None = None
    user_id: int | None = None
    pH: float = Field(7.0, ge=0, le=14)
    organic_matter: float = Field(2.0, ge=0)
    nitrogen: float = Field(50, ge=0)
    phosphorus: float = Field(30, ge=0)
    potassium: float = Field(150, ge=0)
    clay: float = Field(30, ge=0, le=100)
    silt: float = Field(40, ge=0, le=100)
    sand: float = Field(30, ge=0, le=100)
    drainage_issues: bool = False
    compaction_issues: bool = False
    language: str = "en"


ORGANIC_REMEDIATION = {
    "low_ph": {
        "title_en": "Agricultural Lime (Calcium Carbonate)",
        "title_fa": "آهک کشاورزی",
        "description_en": "Natural limestone that raises soil pH gradually over 3-6 months.",
        "description_fa": "سنگ آهک طبیعی که pH خاک را به تدریج افزایش می‌دهد.",
        "benefits": [
            "Slow, safe pH adjustment",
            "Adds calcium and magnesium",
            "Improves soil structure",
            "Non-toxic to soil life",
            "Long-lasting (2-3 years)",
        ],
        "risks": [
            "Takes 3-6 months to work",
            "Requires incorporation",
            "Over-application can cause alkalinity",
        ],
        "application": "2-4 tons/ha",
        "cost": "$50-100/ha",
        "time": "3-6 months",
    },
    "high_ph": {
        "title_en": "Elemental Sulfur + Organic Matter",
        "title_fa": "گوگرد عنصری + ماده آلی",
        "description_en": "Microbes convert sulfur to sulfuric acid, lowering pH naturally.",
        "description_fa": "باکتری‌ها گوگرد را به اسید سولفوریک تبدیل می‌کنند.",
        "benefits": [
            "Gradual pH reduction",
            "Improves microbial activity",
            "Adds organic matter",
            "Safe for ecosystem",
        ],
        "risks": [
            "Slow (6-12 months)",
            "Requires warm moist conditions",
            "May need multiple applications",
        ],
        "application": "0.5-2 tons/ha sulfur + 5-10 tons/ha compost",
        "cost": "$100-200/ha",
        "time": "6-12 months",
    },
    "low_nitrogen": {
        "title_en": "Legume Cover Crops + Compost",
        "title_fa": "گیاهان پوششی حبوبات + کمپوست",
        "description_en": "Nitrogen-fixing plants (clover, vetch) + mature compost.",
        "description_fa": "گیاهان تثبیت‌کننده نیتروژن + کمپوست بالغ.",
        "benefits": [
            "Natural nitrogen fixation (50-200 kg N/ha/yr)",
            "Improves soil structure",
            "Adds organic matter",
            "Supports beneficial microbes",
            "Prevents erosion",
        ],
        "risks": ["Takes one growing season", "Requires management", "May compete with main crop"],
        "application": "20-30 kg/ha seed + 10-20 tons/ha compost",
        "cost": "$80-150/ha",
        "time": "3-6 months",
    },
    "low_phosphorus": {
        "title_en": "Rock Phosphate + Mycorrhizal Fungi",
        "title_fa": "فسفات سنگ + قارچ‌های میکوریزا",
        "description_en": "Natural mineral phosphorus + symbiotic fungi.",
        "description_fa": "فسفر معدنی + قارچ‌های همزیست.",
        "benefits": [
            "Slow-release phosphorus",
            "Mycorrhizae increase uptake 10-100x",
            "Improves drought resistance",
            "Long-term investment",
        ],
        "risks": [
            "Slow availability (months)",
            "Mycorrhizae need living roots",
            "Less effective in high-P soils",
        ],
        "application": "500-1000 kg/ha rock phosphate + inoculant",
        "cost": "$100-200/ha",
        "time": "3-6 months",
    },
    "low_potassium": {
        "title_en": "Wood Ash + Greensand",
        "title_fa": "خاکستر چوب + ماسه سبز",
        "description_en": "Natural potassium from hardwood ash and glauconite.",
        "description_fa": "پتاسیم طبیعی از خاکستر و گلوکونیت.",
        "benefits": [
            "Provides potassium + trace minerals",
            "Wood ash adds calcium",
            "Greensand releases slowly",
            "Improves soil structure",
        ],
        "risks": ["Wood ash raises pH", "Greensand slow-acting", "Ash must be from untreated wood"],
        "application": "1-2 tons/ha ash OR 2-5 tons/ha greensand",
        "cost": "$50-150/ha",
        "time": "1-12 months",
    },
    "low_organic_matter": {
        "title_en": "Compost + Biochar + Cover Crops",
        "title_fa": "کمپوست + بیوچار + گیاهان پوششی",
        "description_en": "Triple approach to build soil organic matter.",
        "description_fa": "رویکرد سه‌گانه برای ساخت ماده آلی خاک.",
        "benefits": [
            "Compost: immediate nutrients",
            "Biochar: permanent carbon storage (1000+ yrs)",
            "Cover crops: continuous OM",
            "Improves all properties",
            "Sequesters carbon",
        ],
        "risks": ["Requires significant material", "Biochar must be charged", "Takes time"],
        "application": "20-40 tons/ha compost + 5-10 tons/ha biochar",
        "cost": "$200-500/ha",
        "time": "6-12 months",
    },
    "poor_drainage": {
        "title_en": "Biochar + Organic Matter + French Drains",
        "title_fa": "بیوچار + ماده آلی + زهکش فرانسوی",
        "description_en": "Improve structure and water movement naturally.",
        "description_fa": "بهبود ساختار و حرکت آب طبیعی.",
        "benefits": [
            "Biochar creates permanent pores",
            "Organic matter improves aggregation",
            "French drains provide relief",
            "Prevents waterlogging",
        ],
        "risks": ["May require labor", "Drains need maintenance", "Biochar must be prepared"],
        "application": "10-20 tons/ha biochar + 30-50 tons/ha compost + drains",
        "cost": "$500-1500/ha",
        "time": "3-6 months",
    },
    "compaction": {
        "title_en": "Deep-Rooted Cover Crops + No-Till",
        "title_fa": "گیاهان پوششی ریشه عمیق + بدون شخم",
        "description_en": "Use plant roots to break up compacted layers.",
        "description_fa": "از ریشه گیاهان برای شکستن لایه‌های متراکم استفاده کنید.",
        "benefits": [
            "Radishes penetrate 60+ cm",
            "Roots create channels",
            "No-till prevents re-compaction",
            "Builds structure",
        ],
        "risks": ["Takes multiple seasons", "Requires patience", "May need specialized equipment"],
        "application": "Daikon radish + ryegrass, strict no-till",
        "cost": "$50-150/ha",
        "time": "1-2 seasons",
    },
}


CHEMICAL_REMEDIATION = {
    "low_ph": {
        "title_en": "Hydrated Lime (Calcium Hydroxide)",
        "title_fa": "آهک هیدراته",
        "description_en": "Fast-acting synthetic lime.",
        "description_fa": "آهک مصنوعی سریع.",
        "benefits": ["Works in days", "Precise application", "Immediate results"],
        "risks": [
            "⚠️ Burns plant roots if over-applied",
            "⚠️ Kills 60% of soil microbes",
            "⚠️ Creates dependency",
            "⚠️ Nutrient lockout",
            "⚠️ Runoff pollutes water",
            "⚠️ Caustic to handle",
            "⚠️ Short-term fix",
        ],
        "application": "1-2 tons/ha",
        "cost": "$80-150/ha",
        "time": "1-2 weeks",
    },
    "low_nitrogen": {
        "title_en": "Synthetic NPK Fertilizer",
        "title_fa": "کود NPK مصنوعی",
        "description_en": "Concentrated nitrogen.",
        "description_fa": "نیتروژن غلیظ.",
        "benefits": ["Immediate uptake", "Precise dosing", "Fast greening"],
        "risks": [
            "⚠️ Kills 80% of soil microbes",
            "⚠️ Acidifies soil",
            "⚠️ Nitrate leaching to groundwater",
            "⚠️ Salt buildup",
            "⚠️ Sterilizes soil (dependency)",
            "⚠️ N2O greenhouse gas",
            "⚠️ Burns plants if over-applied",
            "⚠️ Fossil fuel intensive",
            "⚠️ Destroys nitrogen cycle",
        ],
        "application": "100-200 kg N/ha",
        "cost": "$150-300/ha",
        "time": "Immediate",
    },
    "low_phosphorus": {
        "title_en": "Triple Super Phosphate",
        "title_fa": "سوپر فسفات تریپل",
        "description_en": "Concentrated phosphorus.",
        "description_fa": "فسفر غلیظ.",
        "benefits": ["Fast availability", "Precise"],
        "risks": [
            "⚠️ Algal blooms from runoff",
            "⚠️ Binds with Ca/Fe",
            "⚠️ Disrupts mycorrhizae",
            "⚠️ Depletes finite resource",
            "⚠️ Cadmium contamination",
            "⚠️ Dependency",
            "⚠️ Dead zones",
        ],
        "application": "50-100 kg P2O5/ha",
        "cost": "$100-200/ha",
        "time": "1-2 weeks",
    },
    "low_potassium": {
        "title_en": "Muriate of Potash (KCl)",
        "title_fa": "موریات پتاس",
        "description_en": "Concentrated KCl.",
        "description_fa": "کلرید پتاسیم غلیظ.",
        "benefits": ["Immediate K", "Cost-effective"],
        "risks": [
            "⚠️ Chloride toxicity",
            "⚠️ Salt buildup",
            "⚠️ Kills microbes",
            "⚠️ Leaches",
            "⚠️ Mining damage",
            "⚠️ Reduces biodiversity",
            "⚠️ Dependency",
        ],
        "application": "100-200 kg K2O/ha",
        "cost": "$100-250/ha",
        "time": "Immediate",
    },
}


BIOLOGICAL_REMEDIATION = {
    "general": {
        "title_en": "Microbial Inoculants + Compost Tea",
        "title_fa": "مایه‌های میکروبی + چای کمپوست",
        "description_en": "Restore soil life with beneficial microbes.",
        "description_fa": "احیای حیات خاک با میکروب‌های مفید.",
        "benefits": [
            "Restores soil food web",
            "Improves nutrient cycling",
            "Suppresses diseases",
            "Improves structure",
            "Disease resistance",
            "Drought tolerance",
        ],
        "risks": [
            "Requires knowledge",
            "Killed by chemicals",
            "Needs organic matter",
            "Takes time",
        ],
        "application": "Apply tea every 2-4 weeks",
        "cost": "$50-200/ha",
        "time": "1-3 months",
    },
    "mycorrhizae": {
        "title_en": "Mycorrhizal Fungi Inoculation",
        "title_fa": "مایه‌زنی قارچ‌های میکوریزا",
        "description_en": "Symbiotic fungi extend roots 10-100x.",
        "description_fa": "قارچ‌های همزیست ریشه را گسترش می‌دهند.",
        "benefits": [
            "Increases water uptake",
            "Accesses locked nutrients",
            "Drought resistance",
            "Pathogen protection",
            "Connects plants",
            "Sequesters carbon",
        ],
        "risks": [
            "Killed by tillage",
            "Apply at planting",
            "Needs living hosts",
            "Species-specific",
        ],
        "application": "Apply to seeds/roots at planting",
        "cost": "$30-100/ha",
        "time": "1-2 months",
    },
    "nitrogen_fixers": {
        "title_en": "Free-Living Nitrogen Fixers (Azotobacter)",
        "title_fa": "تثبیت‌کنندگان نیتروژن آزادزی",
        "description_en": "Bacteria fix atmospheric N without legumes.",
        "description_fa": "باکتری‌ها N جو را تثبیت می‌کنند.",
        "benefits": [
            "Fixes 20-50 kg N/ha/yr",
            "Works with any crop",
            "Growth hormones",
            "Improves roots",
            "Self-sustaining",
        ],
        "risks": [
            "Killed by synthetic N",
            "Needs organic matter",
            "Slower than synthetic",
            "pH sensitive",
        ],
        "application": "Seed treatment or drench",
        "cost": "$20-60/ha",
        "time": "2-4 weeks",
    },
}


@router.post("/analyze")
def analyze_soil(req: SoilAnalysisRequest, db: Session = Depends(get_db)):
    lang = req.language
    total = req.clay + req.silt + req.sand or 1
    clay_pct = (req.clay / total) * 100
    silt_pct = (req.silt / total) * 100
    sand_pct = (req.sand / total) * 100
    if clay_pct > 40:
        texture = "clay"
    elif sand_pct > 70:
        texture = "sandy"
    elif silt_pct > 50:
        texture = "silty"
    else:
        texture = "loam"
    ph_status = "acidic" if req.pH < 5.5 else "alkaline" if req.pH > 7.5 else "neutral"
    om_rating = (
        "low" if req.organic_matter < 1 else "moderate" if req.organic_matter < 3 else "high"
    )
    health_score = 50
    if ph_status == "neutral":
        health_score += 20
    if om_rating == "high":
        health_score += 15
    elif om_rating == "moderate":
        health_score += 8
    if 30 < req.nitrogen < 80:
        health_score += 5
    if 20 < req.phosphorus < 60:
        health_score += 5
    if 100 < req.potassium < 300:
        health_score += 5
    problems = []
    if req.pH < 5.5:
        problems.append({"type": "low_ph", "severity": "high" if req.pH < 4.5 else "moderate"})
    if req.pH > 7.5:
        problems.append({"type": "high_ph", "severity": "high" if req.pH > 8.5 else "moderate"})
    if req.nitrogen < 30:
        problems.append(
            {"type": "low_nitrogen", "severity": "high" if req.nitrogen < 15 else "moderate"}
        )
    if req.phosphorus < 20:
        problems.append(
            {"type": "low_phosphorus", "severity": "high" if req.phosphorus < 10 else "moderate"}
        )
    if req.potassium < 100:
        problems.append(
            {"type": "low_potassium", "severity": "high" if req.potassium < 50 else "moderate"}
        )
    if req.organic_matter < 1.5:
        problems.append(
            {
                "type": "low_organic_matter",
                "severity": "high" if req.organic_matter < 0.5 else "moderate",
            }
        )
    if req.drainage_issues:
        problems.append({"type": "poor_drainage", "severity": "high"})
    if req.compaction_issues:
        problems.append({"type": "compaction", "severity": "high"})
    organic_solutions = []
    chemical_solutions = []
    biological_solutions = []
    priority = 1
    for problem in problems:
        p_type = problem["type"]
        if p_type in ORGANIC_REMEDIATION:
            d = ORGANIC_REMEDIATION[p_type]
            organic_solutions.append(
                {
                    "category": "organic",
                    "priority": priority,
                    "title": d.get(f"title_{lang}", d["title_en"]),
                    "description": d.get(f"description_{lang}", d["description_en"]),
                    "benefits": d["benefits"],
                    "risks": d["risks"],
                    "application_rate": d["application"],
                    "cost_estimate": d["cost"],
                    "time_to_effect": d["time"],
                }
            )
        if p_type in CHEMICAL_REMEDIATION:
            d = CHEMICAL_REMEDIATION[p_type]
            chemical_solutions.append(
                {
                    "category": "chemical",
                    "priority": priority + 100,
                    "title": d.get(f"title_{lang}", d["title_en"]),
                    "description": d.get(f"description_{lang}", d["description_en"]),
                    "benefits": d["benefits"],
                    "risks": d["risks"],
                    "application_rate": d["application"],
                    "cost_estimate": d["cost"],
                    "time_to_effect": d["time"],
                }
            )
        priority += 1
    for _key, d in BIOLOGICAL_REMEDIATION.items():
        biological_solutions.append(
            {
                "category": "biological",
                "priority": 50 + len(biological_solutions),
                "title": d.get(f"title_{lang}", d["title_en"]),
                "description": d.get(f"description_{lang}", d["description_en"]),
                "benefits": d["benefits"],
                "risks": d["risks"],
                "application_rate": d["application"],
                "cost_estimate": d["cost"],
                "time_to_effect": d["time"],
            }
        )
    drainage_plan = None
    if req.drainage_issues:
        drainage_plan = {
            "immediate_actions": [
                "Install French drains",
                "Create surface swales",
                "Add raised beds",
            ],
            "long_term_solutions": [
                "Incorporate biochar",
                "Add organic matter",
                "Plant deep-rooted crops",
                "Consider drainage tiles",
            ],
            "estimated_cost": "$500-2000/ha",
        }
    saved_id = None
    if req.farm_id:
        try:
            record = SoilAnalysis(
                farm_id=req.farm_id,
                user_id=req.user_id or 1,
                ph=req.pH,
                organic_matter=req.organic_matter,
                nitrogen=req.nitrogen,
                phosphorus=req.phosphorus,
                potassium=req.potassium,
                clay=req.clay,
                silt=req.silt,
                sand=req.sand,
                texture=texture,
                ph_status=ph_status,
                organic_matter_rating=om_rating,
                health_score=health_score,
                recommendations=[s["title"] for s in organic_solutions[:3]],
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            saved_id = record.id
        except:
            db.rollback()
    return {
        "analysis": {
            "texture": texture,
            "texture_percentages": {
                "clay": round(clay_pct, 1),
                "silt": round(silt_pct, 1),
                "sand": round(sand_pct, 1),
            },
            "ph_status": ph_status,
            "ph_value": req.pH,
            "organic_matter_rating": om_rating,
            "organic_matter_value": req.organic_matter,
            "health_score": min(100, health_score),
            "fertility": "high"
            if health_score > 70
            else "moderate"
            if health_score > 40
            else "low",
            "nitrogen_ppm": req.nitrogen,
            "phosphorus_ppm": req.phosphorus,
            "potassium_ppm": req.potassium,
        },
        "problems": problems,
        "organic_solutions": organic_solutions,
        "chemical_solutions": chemical_solutions,
        "biological_solutions": biological_solutions,
        "drainage_plan": drainage_plan,
        "overall_priority": "low" if not problems else "moderate" if len(problems) <= 2 else "high",
        "estimated_cost_range": "$100-500/ha (organic) or $200-800/ha (chemical)",
        "timeline": "3-12 months",
        "saved_id": saved_id,
        "recommendations": [s["title"] for s in organic_solutions[:5]],
    }


@router.get("/history/{farm_id}")
def get_soil_history(farm_id: int, limit: int = 20, db: Session = Depends(get_db)):
    records = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.farm_id == farm_id)
        .order_by(SoilAnalysis.analyzed_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "farm_id": farm_id,
        "count": len(records),
        "analyses": [
            {
                "id": r.id,
                "analyzed_at": r.analyzed_at.isoformat() if r.analyzed_at else None,
                "texture": r.texture,
                "ph_status": r.ph_status,
                "health_score": r.health_score,
                "recommendations": r.recommendations,
            }
            for r in records
        ],
    }


@router.get("/erosion")
def compute_erosion(
    slope_length_m: float = 100,
    slope_percent: float = 5,
    annual_rainfall_mm: float = 400,
    texture: str = "loam",
    c_factor: float = 0.5,
    p_factor: float = 0.8,
):
    try:
        from engine.hydroma.wrapper import compute_erosion as cpp_erosion

        return cpp_erosion(
            slope_length_m, slope_percent, annual_rainfall_mm, texture, c_factor, p_factor
        )
    except Exception as e:
        return {"error": str(e)}
