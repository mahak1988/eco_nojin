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
        "title_ar": "الجير الزراعي (كربونات الكالسيوم)",
        "description_ar": "حجر جيري طبيعي يرفع درجة حموضة التربة تدريجياً خلال 3-6 أشهر.",
        "benefits": [
            "soil_benefit_slow_safe_ph_adjustment",
            "soil_benefit_adds_calcium_and_magnesium",
            "soil_benefit_improves_soil_structure",
            "soil_benefit_non_toxic_to_soil_life",
            "soil_benefit_long_lasting_2_3_years"
        ],
        "risks": [
            "soil_risk_takes_3_6_months_to_work",
            "soil_risk_requires_incorporation",
            "soil_risk_over_application_can_cause_alkalinity"
        ],
        "application": "soil_apply_2_4_tons_ha",
        "cost": "soil_cost_50_100_ha",
        "time": "soil_time_3_6_months"
    },
    "high_ph": {
        "title_en": "Elemental Sulfur + Organic Matter",
        "title_fa": "گوگرد عنصری + ماده آلی",
        "description_en": "Microbes convert sulfur to sulfuric acid, lowering pH naturally.",
        "description_fa": "باکتری‌ها گوگرد را به اسید سولفوریک تبدیل می‌کنند.",
        "title_ar": "الكبريت العنصري + المادة العضوية",
        "description_ar": "تحوّل الميكروبات الكبريت إلى حمض الكبريتيك، مما يخفض الحموضة طبيعياً.",
        "benefits": [
            "soil_benefit_gradual_ph_reduction",
            "soil_benefit_improves_microbial_activity",
            "soil_benefit_adds_organic_matter",
            "soil_benefit_safe_for_ecosystem"
        ],
        "risks": [
            "soil_risk_slow_6_12_months",
            "soil_risk_requires_warm_moist_conditions",
            "soil_risk_may_need_multiple_applications"
        ],
        "application": "soil_apply_0_5_2_tons_ha_sulfur_5_10_tons_ha_compost",
        "cost": "soil_cost_100_200_ha",
        "time": "soil_time_6_12_months"
    },
    "low_nitrogen": {
        "title_en": "Legume Cover Crops + Compost",
        "title_fa": "گیاهان پوششی حبوبات + کمپوست",
        "description_en": "Nitrogen-fixing plants (clover, vetch) + mature compost.",
        "description_fa": "گیاهان تثبیت‌کننده نیتروژن + کمپوست بالغ.",
        "title_ar": "محاصيل الغطاء البقولية + الكمبوست",
        "description_ar": "نباتات مثبتة للنيتروجين (البرسيم، البيقة) + كمبوست ناضج.",
        "benefits": [
            "soil_benefit_natural_nitrogen_fixation_50_200_kg_n_ha_y",
            "soil_benefit_improves_soil_structure_2",
            "soil_benefit_adds_organic_matter_2",
            "soil_benefit_supports_beneficial_microbes",
            "soil_benefit_prevents_erosion"
        ],
        "risks": [
            "soil_risk_takes_one_growing_season",
            "soil_risk_requires_management",
            "soil_risk_may_compete_with_main_crop"
        ],
        "application": "soil_apply_20_30_kg_ha_seed_10_20_tons_ha_compost",
        "cost": "soil_cost_80_150_ha",
        "time": "soil_time_3_6_months_2"
    },
    "low_phosphorus": {
        "title_en": "Rock Phosphate + Mycorrhizal Fungi",
        "title_fa": "فسفات سنگ + قارچ‌های میکوریزا",
        "description_en": "Natural mineral phosphorus + symbiotic fungi.",
        "description_fa": "فسفر معدنی + قارچ‌های همزیست.",
        "title_ar": "فوسفات الصخور + فطريات الميكوريزا",
        "description_ar": "فوسفور معدني طبيعي + فطريات تكافلية.",
        "benefits": [
            "soil_benefit_slow_release_phosphorus",
            "soil_benefit_mycorrhizae_increase_uptake_10_100x",
            "soil_benefit_improves_drought_resistance",
            "soil_benefit_long_term_investment"
        ],
        "risks": [
            "soil_risk_slow_availability_months",
            "soil_risk_mycorrhizae_need_living_roots",
            "soil_risk_less_effective_in_high_p_soils"
        ],
        "application": "soil_apply_500_1000_kg_ha_rock_phosphate_inoculant",
        "cost": "soil_cost_100_200_ha_2",
        "time": "soil_time_3_6_months"
    },
    "low_potassium": {
        "title_en": "Wood Ash + Greensand",
        "title_fa": "خاکستر چوب + ماسه سبز",
        "description_en": "Natural potassium from hardwood ash and glauconite.",
        "description_fa": "پتاسیم طبیعی از خاکستر و گلوکونیت.",
        "title_ar": "رماد الخشب + الرمل الأخضر",
        "description_ar": "بوتاسيوم طبيعي من رماد الخشب الصلب والجلوكونيت.",
        "benefits": [
            "soil_benefit_provides_potassium_trace_minerals",
            "soil_benefit_wood_ash_adds_calcium",
            "soil_benefit_greensand_releases_slowly",
            "soil_benefit_improves_soil_structure"
        ],
        "risks": [
            "soil_risk_wood_ash_raises_ph",
            "soil_risk_greensand_slow_acting",
            "soil_risk_ash_must_be_from_untreated_wood"
        ],
        "application": "soil_apply_1_2_tons_ha_ash_or_2_5_tons_ha_greensand",
        "cost": "soil_cost_50_150_ha",
        "time": "soil_time_1_12_months"
    },
    "low_organic_matter": {
        "title_en": "Compost + Biochar + Cover Crops",
        "title_fa": "کمپوست + بیوچار + گیاهان پوششی",
        "description_en": "Triple approach to build soil organic matter.",
        "description_fa": "رویکرد سه‌گانه برای ساخت ماده آلی خاک.",
        "title_ar": "الكمبوست + الفحم الحيوي + محاصيل الغطاء",
        "description_ar": "نهج ثلاثي لبناء المادة العضوية في التربة.",
        "benefits": [
            "soil_benefit_compost_immediate_nutrients",
            "soil_benefit_biochar_permanent_carbon_storage_1000_yrs",
            "soil_benefit_cover_crops_continuous_om",
            "soil_benefit_improves_all_properties",
            "soil_benefit_sequesters_carbon"
        ],
        "risks": [
            "soil_risk_requires_significant_material",
            "soil_risk_biochar_must_be_charged",
            "soil_risk_takes_time"
        ],
        "application": "soil_apply_20_40_tons_ha_compost_5_10_tons_ha_biochar",
        "cost": "soil_cost_200_500_ha",
        "time": "soil_time_6_12_months_2"
    },
    "poor_drainage": {
        "title_en": "Biochar + Organic Matter + French Drains",
        "title_fa": "بیوچار + ماده آلی + زهکش فرانسوی",
        "description_en": "Improve structure and water movement naturally.",
        "description_fa": "بهبود ساختار و حرکت آب طبیعی.",
        "title_ar": "الفحم الحيوي + المادة العضوية + المصارف الفرنسية",
        "description_ar": "تحسين البنية وحركة الماء طبيعياً.",
        "benefits": [
            "soil_benefit_biochar_creates_permanent_pores",
            "soil_benefit_organic_matter_improves_aggregation",
            "soil_benefit_french_drains_provide_relief",
            "soil_benefit_prevents_waterlogging"
        ],
        "risks": [
            "soil_risk_may_require_labor",
            "soil_risk_drains_need_maintenance",
            "soil_risk_biochar_must_be_prepared"
        ],
        "application": "soil_apply_10_20_tons_ha_biochar_30_50_tons_ha_compos",
        "cost": "soil_cost_500_1500_ha",
        "time": "soil_time_3_6_months_2"
    },
    "compaction": {
        "title_en": "Deep-Rooted Cover Crops + No-Till",
        "title_fa": "گیاهان پوششی ریشه عمیق + بدون شخم",
        "description_en": "Use plant roots to break up compacted layers.",
        "description_fa": "از ریشه گیاهان برای شکستن لایه‌های متراکم استفاده کنید.",
        "title_ar": "محاصيل غطاء عميقة الجذور + الزراعة بدون حراثة",
        "description_ar": "استخدام جذور النباتات لتفكيك الطبقات المضغوطة.",
        "benefits": [
            "soil_benefit_radishes_penetrate_60_cm",
            "soil_benefit_roots_create_channels",
            "soil_benefit_no_till_prevents_re_compaction",
            "soil_benefit_builds_structure"
        ],
        "risks": [
            "soil_risk_takes_multiple_seasons",
            "soil_risk_requires_patience",
            "soil_risk_may_need_specialized_equipment"
        ],
        "application": "soil_apply_daikon_radish_ryegrass_strict_no_till",
        "cost": "soil_cost_50_150_ha_2",
        "time": "soil_time_1_2_seasons"
    }
}


CHEMICAL_REMEDIATION = {
    "low_ph": {
        "title_en": "Hydrated Lime (Calcium Hydroxide)",
        "title_fa": "آهک هیدراته",
        "description_en": "Fast-acting synthetic lime.",
        "description_fa": "آهک مصنوعی سریع.",
        "title_ar": "الجير المطفأ (هيدروكسيد الكالسيوم)",
        "description_ar": "جير صناعي سريع المفعول.",
        "benefits": [
            "soil_benefit_works_in_days",
            "soil_benefit_precise_application",
            "soil_benefit_immediate_results"
        ],
        "risks": [
            "soil_risk_burns_plant_roots_if_over_applied",
            "soil_risk_kills_60_of_soil_microbes",
            "soil_risk_creates_dependency",
            "soil_risk_nutrient_lockout",
            "soil_risk_runoff_pollutes_water",
            "soil_risk_caustic_to_handle",
            "soil_risk_short_term_fix"
        ],
        "application": "soil_apply_1_2_tons_ha",
        "cost": "soil_cost_80_150_ha_2",
        "time": "soil_time_1_2_weeks"
    },
    "low_nitrogen": {
        "title_en": "Synthetic NPK Fertilizer",
        "title_fa": "کود NPK مصنوعی",
        "description_en": "Concentrated nitrogen.",
        "description_fa": "نیتروژن غلیظ.",
        "title_ar": "سماد NPK الاصطناعي",
        "description_ar": "نيتروجين مركّز.",
        "benefits": [
            "soil_benefit_immediate_uptake",
            "soil_benefit_precise_dosing",
            "soil_benefit_fast_greening"
        ],
        "risks": [
            "soil_risk_kills_80_of_soil_microbes",
            "soil_risk_acidifies_soil",
            "soil_risk_nitrate_leaching_to_groundwater",
            "soil_risk_salt_buildup",
            "soil_risk_sterilizes_soil_dependency",
            "soil_risk_n2o_greenhouse_gas",
            "soil_risk_burns_plants_if_over_applied",
            "soil_risk_fossil_fuel_intensive",
            "soil_risk_destroys_nitrogen_cycle"
        ],
        "application": "soil_apply_100_200_kg_n_ha",
        "cost": "soil_cost_150_300_ha",
        "time": "soil_time_immediate"
    },
    "low_phosphorus": {
        "title_en": "Triple Super Phosphate",
        "title_fa": "سوپر فسفات تریپل",
        "description_en": "Concentrated phosphorus.",
        "description_fa": "فسفر غلیظ.",
        "title_ar": "سوبر فوسفات ثلاثي",
        "description_ar": "فوسفور مركّز.",
        "benefits": [
            "soil_benefit_fast_availability",
            "soil_benefit_precise"
        ],
        "risks": [
            "soil_risk_algal_blooms_from_runoff",
            "soil_risk_binds_with_ca_fe",
            "soil_risk_disrupts_mycorrhizae",
            "soil_risk_depletes_finite_resource",
            "soil_risk_cadmium_contamination",
            "soil_risk_dependency",
            "soil_risk_dead_zones"
        ],
        "application": "soil_apply_50_100_kg_p2o5_ha",
        "cost": "soil_cost_100_200_ha",
        "time": "soil_time_1_2_weeks_2"
    },
    "low_potassium": {
        "title_en": "Muriate of Potash (KCl)",
        "title_fa": "موریات پتاس",
        "description_en": "Concentrated KCl.",
        "description_fa": "کلرید پتاسیم غلیظ.",
        "title_ar": "كلوريد البوتاسيوم (KCl)",
        "description_ar": "كلوريد بوتاسيوم مركّز.",
        "benefits": [
            "soil_benefit_immediate_k",
            "soil_benefit_cost_effective"
        ],
        "risks": [
            "soil_risk_chloride_toxicity",
            "soil_risk_salt_buildup_2",
            "soil_risk_kills_microbes",
            "soil_risk_leaches",
            "soil_risk_mining_damage",
            "soil_risk_reduces_biodiversity",
            "soil_risk_dependency_2"
        ],
        "application": "soil_apply_100_200_kg_k2o_ha",
        "cost": "soil_cost_100_250_ha",
        "time": "soil_time_immediate_2"
    }
}


BIOLOGICAL_REMEDIATION = {
    "general": {
        "title_en": "Microbial Inoculants + Compost Tea",
        "title_fa": "مایه‌های میکروبی + چای کمپوست",
        "description_en": "Restore soil life with beneficial microbes.",
        "description_fa": "احیای حیات خاک با میکروب‌های مفید.",
        "title_ar": "اللقاحات الميكروبية + شاي الكمبوست",
        "description_ar": "استعادة حياة التربة بالميكروبات المفيدة.",
        "benefits": [
            "soil_benefit_restores_soil_food_web",
            "soil_benefit_improves_nutrient_cycling",
            "soil_benefit_suppresses_diseases",
            "soil_benefit_improves_structure",
            "soil_benefit_disease_resistance",
            "soil_benefit_drought_tolerance"
        ],
        "risks": [
            "soil_risk_requires_knowledge",
            "soil_risk_killed_by_chemicals",
            "soil_risk_needs_organic_matter",
            "soil_risk_takes_time_2"
        ],
        "application": "soil_apply_apply_tea_every_2_4_weeks",
        "cost": "soil_cost_50_200_ha",
        "time": "soil_time_1_3_months"
    },
    "mycorrhizae": {
        "title_en": "Mycorrhizal Fungi Inoculation",
        "title_fa": "مایه‌زنی قارچ‌های میکوریزا",
        "description_en": "Symbiotic fungi extend roots 10-100x.",
        "description_fa": "قارچ‌های همزیست ریشه را گسترش می‌دهند.",
        "title_ar": "تلقيح فطريات الميكوريزا",
        "description_ar": "فطريات تكافلية تمدد الجذور 10-100 مرة.",
        "benefits": [
            "soil_benefit_increases_water_uptake",
            "soil_benefit_accesses_locked_nutrients",
            "soil_benefit_drought_resistance",
            "soil_benefit_pathogen_protection",
            "soil_benefit_connects_plants",
            "soil_benefit_sequesters_carbon_2"
        ],
        "risks": [
            "soil_risk_killed_by_tillage",
            "soil_risk_apply_at_planting",
            "soil_risk_needs_living_hosts",
            "soil_risk_species_specific"
        ],
        "application": "soil_apply_apply_to_seeds_roots_at_planting",
        "cost": "soil_cost_30_100_ha",
        "time": "soil_time_1_2_months"
    },
    "nitrogen_fixers": {
        "title_en": "Free-Living Nitrogen Fixers (Azotobacter)",
        "title_fa": "تثبیت‌کنندگان نیتروژن آزادزی",
        "description_en": "Bacteria fix atmospheric N without legumes.",
        "description_fa": "باکتری‌ها N جو را تثبیت می‌کنند.",
        "title_ar": "مثبتات النيتروجين الحرة (أزوتوباكتر)",
        "description_ar": "بكتيريا تثبت النيتروجين الجوي دون بقوليات.",
        "benefits": [
            "soil_benefit_fixes_20_50_kg_n_ha_yr",
            "soil_benefit_works_with_any_crop",
            "soil_benefit_growth_hormones",
            "soil_benefit_improves_roots",
            "soil_benefit_self_sustaining"
        ],
        "risks": [
            "soil_risk_killed_by_synthetic_n",
            "soil_risk_needs_organic_matter_2",
            "soil_risk_slower_than_synthetic",
            "soil_risk_ph_sensitive"
        ],
        "application": "soil_apply_seed_treatment_or_drench",
        "cost": "soil_cost_20_60_ha",
        "time": "soil_time_2_4_weeks"
    }
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
                    "code": p_type,
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
                    "code": p_type,
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
                "code": p_type,
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
                "soil_action_french_drains",
                "soil_action_surface_swales",
                "soil_action_raised_beds",
            ],
            "long_term_solutions": [
                "soil_action_biochar",
                "soil_action_organic_matter",
                "soil_action_deep_rooted",
                "soil_action_drainage_tiles",
            ],
            "estimated_cost": {"en": "$500-2000/ha", "fa": "۵۰۰-۲۰۰۰ دلار در هکتار", "ar": "500-2000 دولار/هكتار"},
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
        except Exception as e:
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


# ============================================================================
# Soil Profiles CRUD
# ============================================================================
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SoilProfileCreate(BaseModel):
    """Request model for creating a soil profile."""
    name: str = Field(..., description="Profile name")
    texture: str = Field(..., description="Soil texture class")
    ph: float = Field(..., ge=0, le=14, description="Soil pH")
    ec: float = Field(..., ge=0, description="Electrical conductivity (dS/m)")
    organic_matter: float = Field(..., ge=0, description="Organic matter (%)")


class SoilProfileRead(BaseModel):
    """Response model for soil profile."""
    id: int
    name: str
    texture: str
    ph: float
    ec: float
    organic_matter: float
    created_at: str


# In-memory storage for simplicity (replace with DB in production)
_soil_profiles_db: List[dict] = []
_soil_profile_counter = [0]


@router.post("/", response_model=SoilProfileRead, status_code=201, tags=["soil"])
async def create_soil_profile(profile: SoilProfileCreate):
    """Create a new soil profile.
    
    Args:
        profile: Soil profile data
        
    Returns:
        Created soil profile with ID
    """
    _soil_profile_counter[0] += 1
    new_profile = {
        "id": _soil_profile_counter[0],
        "name": profile.name,
        "texture": profile.texture,
        "ph": profile.ph,
        "ec": profile.ec,
        "organic_matter": profile.organic_matter,
        "created_at": datetime.utcnow().isoformat(),
    }
    _soil_profiles_db.append(new_profile)
    return new_profile


@router.get("/", response_model=List[SoilProfileRead], tags=["soil"])
async def list_soil_profiles():
    """List all soil profiles.
    
    Returns:
        List of all soil profiles
    """
    return _soil_profiles_db

