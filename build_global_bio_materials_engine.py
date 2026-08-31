#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
موتور جهانی مصالح زیستی هیدروما (Global Bio-Materials Engine)
فاز دوم: تبدیل هیدروما از مدل تئوریک به سامانه تجویزگر عملیاتی جهانی
============================================================================
"""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "docs" / "hydroma" / "bio_materials"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════
# بخش ۱: میکروبیوم‌های جهانی (Global Microbiomes)
# ══════════════════════════════════════════════════════════════

GLOBAL_MICROBIOMES = [
    # ─────────────────────────────────────────────────────────
    # باکتری‌های تثبیت‌کننده نیتروژن
    # ─────────────────────────────────────────────────────────
    {
        "id": "MIC001",
        "name_fa": "ریزوبیوم لگومینوزاروم",
        "name_en": "Rhizobium leguminosarum",
        "category": "nitrogen_fixing",
        "mechanism": "همزیستی با ریشه حبوبات مناطق معتدل؛ تشکیل گره‌های ریشه و تثبیت ۱۰۰-۳۰۰ کیلوگرم نیتروژن در هکتار",
        "biomes": ["Mediterranean", "Temperate_Continental", "Semi-arid"],
        "target_soils": ["calcareous", "loam", "silt_loam"],
        "optimal_conditions": {"temp_c": (15, 28), "ph": (6.0, 8.0), "ec_ds_m_max": 4},
        "application_rate": "1-2 kg/ha مایه تلقیح",
        "reference": "FAO/IAEA 2021; Zahran 1999",
        "regional_examples": {
            "iran": "حبوبات دیم همدان و کرمانشاه",
            "global": "عدس ترکیه، نخود استرالیا، لوبیای مدیترانه"
        }
    },
    {
        "id": "MIC002",
        "name_fa": "برادی‌ریزوبیوم ژاپونیکوم",
        "name_en": "Bradyrhizobium japonicum",
        "category": "nitrogen_fixing",
        "mechanism": "همزیستی با سویا و حبوبات حاره‌ای؛ تثبیت ۱۵۰-۴۰۰ کیلوگرم نیتروژن در هکتار؛ تحمل شوری ملایم",
        "biomes": ["Tropical_Savanna", "Tropical_Rainforest", "Temperate_Continental"],
        "target_soils": ["loam", "clay_loam", "sandy_loam"],
        "optimal_conditions": {"temp_c": (20, 35), "ph": (5.5, 7.5), "ec_ds_m_max": 6},
        "application_rate": "2-3 kg/ha مایه تلقیح",
        "reference": "ICRISAT 2020; Hungria et al. 2015",
        "regional_examples": {
            "iran": "سویای شمال و غرب",
            "global": "سویای برزیل، آرژانتین، آمریکا، هند"
        }
    },
    {
        "id": "MIC003",
        "name_fa": "آزوتوباکتر کروکوکوم",
        "name_en": "Azotobacter chroococcum",
        "category": "nitrogen_fixing_free_living",
        "mechanism": "تثبیت آزاد نیتروژن بدون نیاز به گیاه میزبان؛ تولید هورمون‌های رشد (اکسین، جیبرلین)؛ ۲۰-۴۰ کیلوگرم نیتروژن در هکتار",
        "biomes": ["Semi-arid", "Mediterranean", "Temperate_Continental"],
        "target_soils": ["loam", "sandy_loam", "calcareous"],
        "optimal_conditions": {"temp_c": (20, 30), "ph": (6.5, 8.5), "ec_ds_m_max": 8},
        "application_rate": "5-10 kg/ha",
        "reference": "FAO Biofertilizer Manual 2022; Bhattacharyya & Jha 2012",
        "regional_examples": {
            "iran": "گندم و جو دیم فلات مرکزی",
            "global": "غلات دیم مناطق نیمه‌خشک هند، پاکستان، آفریقا"
        }
    },
    {
        "id": "MIC004",
        "name_fa": "آزواسپیریلوم برازیلنس",
        "name_en": "Azospirillum brasilense",
        "category": "nitrogen_fixing_associative",
        "mechanism": "همزیستی همراه با ریشه غلات (گندم، ذرت، برنج)؛ تثبیت ۳۰-۶۰ کیلوگرم نیتروژن؛ تحریک رشد ریشه با اکسین",
        "biomes": ["Tropical_Savanna", "Semi-arid", "Temperate_Continental"],
        "target_soils": ["loam", "sandy_loam", "clay_loam"],
        "optimal_conditions": {"temp_c": (25, 37), "ph": (5.5, 7.5), "ec_ds_m_max": 6},
        "application_rate": "1-2 kg/ha مایه تلقیح بذر",
        "reference": "ICARDA 2019; Bashan et al. 2014",
        "regional_examples": {
            "iran": "گندم و ذرت آبی خوزستان",
            "global": "گندم آرژانتین، ذرت برزیل، برنج هند"
        }
    },
    {
        "id": "MIC005",
        "name_fa": "فرنکیا آلنی",
        "name_en": "Frankia alni",
        "category": "nitrogen_fixing_actinorhizal",
        "mechanism": "همزیستی با گیاهان اکتینوریزال (توسکا، کازوآرینا، میروبالان)؛ تثبیت ۱۰۰-۲۵۰ کیلوگرم نیتروژن؛ مناسب برای احیای اراضی تخریب‌شده",
        "biomes": ["Temperate_Continental", "Mediterranean", "Boreal", "Alpine"],
        "target_soils": ["sandy", "silty", "degraded"],
        "optimal_conditions": {"temp_c": (10, 30), "ph": (5.0, 7.5), "ec_ds_m_max": 4},
        "application_rate": "10-20 g/نهال مایه تلقیح",
        "reference": "FAO Forestry Paper 2020; Dawson 2008",
        "regional_examples": {
            "iran": "توسکای جنگل‌های هیرکانی، کازوآرینای جنوب",
            "global": "کازوآرینای استرالیا، توسکای اروپا، میروبالان آفریقا"
        }
    },
    # ─────────────────────────────────────────────────────────
    # قارچ‌های مایکوریزا
    # ─────────────────────────────────────────────────────────
    {
        "id": "MIC006",
        "name_fa": "ریزوفاگوس ایرگولاریس (گلوموس سابق)",
        "name_en": "Rhizophagus irregularis (Glomus intraradices)",
        "category": "arbuscular_mycorrhiza",
        "mechanism": "افزایش جذب فسفر تا ۷۰٪؛ بهبود جذب آب در خشکی؛ افزایش تحمل شوری؛ همزیستی با ۸۰٪ گیاهان",
        "biomes": ["ALL"],
        "target_soils": ["ALL"],
        "optimal_conditions": {"temp_c": (10, 35), "ph": (5.0, 8.5), "ec_ds_m_max": 8},
        "application_rate": "50-100 spore/g soil یا 2-5 kg/ha",
        "reference": "FAO/ICARDA 2021; Smith & Read 2008",
        "regional_examples": {
            "iran": "گندم و جو دیم تمام مناطق",
            "global": "همه غلات، سبزیجات و درختان میوه جهان"
        }
    },
    {
        "id": "MIC007",
        "name_fa": "فونلیفورمیس موسه‌آ",
        "name_en": "Funneliformis mosseae",
        "category": "arbuscular_mycorrhiza",
        "mechanism": "مؤثرترین قارچ مایکوریزا برای خاک‌های آهکی و قلیایی؛ بهبود جذب روی و آهن؛ تحمل خشکی",
        "biomes": ["Semi-arid", "Mediterranean", "Arid"],
        "target_soils": ["calcareous", "alkaline", "loam"],
        "optimal_conditions": {"temp_c": (15, 35), "ph": (7.0, 8.5), "ec_ds_m_max": 6},
        "application_rate": "50-100 spore/g soil",
        "reference": "ICARDA 2020; Al-Karaki 2006",
        "regional_examples": {
            "iran": "پسته کرمان، زعفران خراسان",
            "global": "زیتون مدیترانه، انگور کالیفرنیا"
        }
    },
    {
        "id": "MIC008",
        "name_fa": "گلوموس دزرتیکولا",
        "name_en": "Glomus deserticola",
        "category": "arbuscular_mycorrhiza",
        "mechanism": "مایکوریزای اختصاصی بیابان؛ تحمل شوری تا ۱۲ dS/m؛ بهبود استقرار گیاه در خاک‌های تخریب‌شده",
        "biomes": ["Hyper-arid", "Arid", "Semi-arid"],
        "target_soils": ["sandy", "saline", "degraded"],
        "optimal_conditions": {"temp_c": (20, 45), "ph": (6.5, 9.0), "ec_ds_m_max": 12},
        "application_rate": "100-200 spore/g soil",
        "reference": "Al-Karaki 2013; Requena et al. 1997",
        "regional_examples": {
            "iran": "احیای کویر مرکزی، تثبیت شن‌های روان",
            "global": "بیابان‌های صحرای بزرگ، گوبی، آتاکاما"
        }
    },
    {
        "id": "MIC009",
        "name_fa": "پیزولیتوس تینکتوریوس",
        "name_en": "Pisolithus tinctorius",
        "category": "ectomycorrhiza",
        "mechanism": "اکتومایکوریزای پیشگام برای اراضی تخریب‌شده، معادن و خاک‌های اسیدی؛ همزیستی با کاج، اکالیپتوس، بلوط",
        "biomes": ["Temperate_Continental", "Boreal", "Tropical_Savanna", "Volcanic"],
        "target_soils": ["acidic", "degraded", "mining_spoil"],
        "optimal_conditions": {"temp_c": (5, 35), "ph": (4.0, 7.0), "ec_ds_m_max": 4},
        "application_rate": "20-50 g/نهال",
        "reference": "FAO Forestry 2019; Marx 1982",
        "regional_examples": {
            "iran": "جنگل‌کاری کاج در زاگرس و البرز",
            "global": "بازجنگل‌کاری برزیل، استرالیا، آفریقای جنوبی"
        }
    },
    # ─────────────────────────────────────────────────────────
    # باکتری‌های محرک رشد و حل‌کننده فسفات
    # ─────────────────────────────────────────────────────────
    {
        "id": "MIC010",
        "name_fa": "باسیلوس سوبتیلیس",
        "name_en": "Bacillus subtilis",
        "category": "pgpr_phosphate_solubilizer",
        "mechanism": "حل‌کننده فسفات نامحلول (تا ۳۰۰٪ افزایش فسفر قابل دسترس)؛ تولید آنتی‌بیوتیک ضد قارچ‌های بیمارگر؛ تحمل شوری و خشکی",
        "biomes": ["ALL"],
        "target_soils": ["ALL"],
        "optimal_conditions": {"temp_c": (15, 40), "ph": (5.5, 9.0), "ec_ds_m_max": 10},
        "application_rate": "1-2 kg/ha",
        "reference": "FAO 2022; Glick 2014",
        "regional_examples": {
            "iran": "همه محصولات زراعی و باغی",
            "global": "همه محصولات جهان"
        }
    },
    {
        "id": "MIC011",
        "name_fa": "سودوموناس فلورسنس",
        "name_en": "Pseudomonas fluorescens",
        "category": "pgpr_biocontrol",
        "mechanism": "کنترل بیولوژیک بیماری‌های قارچی (فیوزاریوم، ریزوکتونیا)؛ تولید سیدروفور برای جذب آهن؛ تحریک مقاومت سیستمیک",
        "biomes": ["Temperate_Continental", "Mediterranean", "Semi-arid"],
        "target_soils": ["loam", "sandy_loam", "silt_loam"],
        "optimal_conditions": {"temp_c": (10, 30), "ph": (6.0, 8.0), "ec_ds_m_max": 6},
        "application_rate": "2-5 kg/ha یا مایه تلقیح بذر",
        "reference": "ICARDA 2021; Weller 2007",
        "regional_examples": {
            "iran": "کنترل پژمردگی گندم و گوجه",
            "global": "کنترل بیماری‌های ریشه در سبزیجات و غلات"
        }
    },
    {
        "id": "MIC012",
        "name_fa": "هالوموناس (گونه‌های شورپسند)",
        "name_en": "Halomonas spp.",
        "category": "halophilic_pgpr",
        "mechanism": "باکتری اختصاصی خاک‌های شور (تحمل تا ۲۰٪ نمک)؛ تولید اکسوپلی‌ساکارید برای بهبود ساختار خاک شور؛ تحریک رشد در شوری",
        "biomes": ["Hyper-arid", "Arid", "Coastal_Saline"],
        "target_soils": ["saline", "sodic", "coastal"],
        "optimal_conditions": {"temp_c": (20, 40), "ph": (7.0, 9.5), "ec_ds_m_max": 25},
        "application_rate": "2-4 kg/ha",
        "reference": "Ventosa & Oren 2019; FAO Salinity 2022",
        "regional_examples": {
            "iran": "خاک‌های شور خوزستان، کویر نمک",
            "global": "دلتای نیل، دره سند، دشت‌های شور استرالیا"
        }
    },
    {
        "id": "MIC013",
        "name_fa": "تریکودرما هارزیانوم",
        "name_en": "Trichoderma harzianum",
        "category": "biocontrol_fungus",
        "mechanism": "قارچ آنتاگونیست علیه پاتوژن‌های ریشه (فیوزاریوم، ریزوکتونیا، اسکلروتینیا)؛ تحریک رشد ریشه؛ حل‌کننده فسفات",
        "biomes": ["ALL"],
        "target_soils": ["ALL"],
        "optimal_conditions": {"temp_c": (15, 35), "ph": (5.0, 8.0), "ec_ds_m_max": 8},
        "application_rate": "2-5 kg/ha یا 10-20 g/نهال",
        "reference": "FAO IPM 2021; Harman et al. 2004",
        "regional_examples": {
            "iran": "کنترل بیماری‌های سبزی و صیفی",
            "global": "همه محصولات زراعی و باغی جهان"
        }
    },
    {
        "id": "MIC014",
        "name_fa": "آزوتوباکتر سالینستریس",
        "name_en": "Azotobacter salinestris",
        "category": "nitrogen_fixing_halotolerant",
        "mechanism": "تثبیت نیتروژن در خاک‌های شور (تحمل تا ۸ dS/m)؛ مناسب برای گندم و جو مناطق شور؛ تولید هورمون رشد",
        "biomes": ["Arid", "Semi-arid", "Coastal_Saline"],
        "target_soils": ["saline", "sodic", "calcareous"],
        "optimal_conditions": {"temp_c": (20, 35), "ph": (7.0, 9.0), "ec_ds_m_max": 8},
        "application_rate": "5-8 kg/ha",
        "reference": "ICARDA 2022; Zahran 2001",
        "regional_examples": {
            "iran": "گندم و جو مناطق شور خوزستان و کرمان",
            "global": "غلات مناطق شور عراق، پاکستان، مصر"
        }
    }
]


# ══════════════════════════════════════════════════════════════
# بخش ۲: اصلاح‌کننده‌های طبیعی جهانی (Global Amendments)
# ══════════════════════════════════════════════════════════════

GLOBAL_AMENDMENTS = [
    {
        "id": "AMD001",
        "name_fa": "گچ کشاورزی (سولفات کلسیم)",
        "name_en": "Agricultural Gypsum (CaSO₄·2H₂O)",
        "category": "mineral_amendment",
        "mechanism": "جایگزینی سدیم با کلسیم در خاک‌های سدیک؛ بهبود ساختار و نفوذپذیری؛ کاهش شوری از طریق آبشویی",
        "biomes": ["Semi-arid", "Arid", "Coastal_Saline"],
        "target_problems": ["sodicity", "salinity", "poor_structure"],
        "application_rate": "5-20 تن/هکتار بسته به میزان سدیم",
        "cost_class": "low",
        "reference": "FAO Salinity Handbook 60; USAID 2021",
        "global_sources": "معادن گچ ایران، ترکیه، اسپانیا، آمریکا، تایلند"
    },
    {
        "id": "AMD002",
        "name_fa": "بیوچار (زغال زیستی)",
        "name_en": "Biochar",
        "category": "organic_amendment",
        "mechanism": "افزایش ظرفیت نگهداری آب تا ۵۰٪؛ ترسیب کربن تا ۵۰۰ سال؛ بهبود ساختار خاک شنی و شنی؛ جذب فلزات سنگین",
        "biomes": ["ALL"],
        "target_problems": ["low_organic_matter", "sandy_soil", "carbon_loss", "heavy_metals"],
        "application_rate": "10-50 تن/هکتار",
        "cost_class": "medium",
        "feedstocks": {
            "palm_waste": "پسماند نخیلات جنوب ایران، عراق، مصر، عربستان",
            "rice_husk": "کاه برنج هند، ویتنام، بنگلادش، تایلند",
            "coconut_shell": "پوست نارگیل فیلیپین، اندونزی، سریلانکا",
            "wood_chips": "ضایعات چوب اسکاندیناوی، کانادا، روسیه"
        },
        "reference": "IBI 2023; Lehmann & Joseph 2015",
        "global_sources": "تولید محلی از پسماندهای کشاورزی"
    },
    {
        "id": "AMD003",
        "name_fa": "زئولیت طبیعی",
        "name_en": "Natural Zeolite (Clinoptilolite)",
        "category": "mineral_amendment",
        "mechanism": "افزایش ظرفیت تبادل کاتیونی (CEC)؛ نگهداری آب و مواد مغذی؛ کاهش شستشوی کود؛ تحمل خشکی",
        "biomes": ["Semi-arid", "Arid", "Hyper-arid"],
        "target_problems": ["sandy_soil", "nutrient_leaching", "low_water_holding"],
        "application_rate": "10-30 تن/هکتار",
        "cost_class": "medium",
        "reference": "Mumpton 1999; FAO 2020",
        "global_sources": "معادن زئولیت ایران، ترکیه، آمریکا، کوبا، ژاپن، مجارستان"
    },
    {
        "id": "AMD004",
        "name_fa": "پودر بازالت (سنگ آتشفشانی)",
        "name_en": "Basalt Rock Dust",
        "category": "mineral_amendment",
        "mechanism": "آزادسازی تدریجی مواد معدنی (پتاسیم، منیزیم، آهن)؛ ترسیب کربن از طریق هوازدگی؛ بهبود حاصلخیزی بلندمدت",
        "biomes": ["Tropical_Savanna", "Tropical_Rainforest", "Volcanic", "Temperate_Continental"],
        "target_problems": ["nutrient_depletion", "acidic_soil", "mineral_deficiency"],
        "application_rate": "20-50 تن/هکتار",
        "cost_class": "medium",
        "reference": "Beerling et al. 2020; UNFCCC 2022",
        "global_sources": "معدن‌های بازالت هند، برزیل، اندونزی، اتیوپی، ایسلند"
    },
    {
        "id": "AMD005",
        "name_fa": "کمپوست و ورمی‌کمپوست",
        "name_en": "Compost & Vermicompost",
        "category": "organic_amendment",
        "mechanism": "افزایش ماده آلی تا ۳٪؛ بهبود ساختار و نفوذپذیری؛ افزایش فعالیت میکروبی؛ تغذیه تدریجی گیاه",
        "biomes": ["ALL"],
        "target_problems": ["low_organic_matter", "poor_structure", "degraded_soil"],
        "application_rate": "کمپوست: 20-50 تن/ها | ورمی‌کمپوست: 5-15 تن/ها",
        "cost_class": "low_to_medium",
        "reference": "FAO Compost Guide 2021; Edwards et al. 2011",
        "global_sources": "تولید محلی از پسماندهای شهری و کشاورزی"
    },
    {
        "id": "AMD006",
        "name_fa": "کود سبز و گیاهان پوششی",
        "name_en": "Green Manure & Cover Crops",
        "category": "biological_amendment",
        "mechanism": "تثبیت نیتروژن (حبوبات پوششی)؛ افزایش ماده آلی؛ جلوگیری از فرسایش؛ کاهش علف‌های هرز",
        "biomes": ["ALL"],
        "target_problems": ["erosion", "low_nitrogen", "weed_pressure", "bare_soil"],
        "application_rate": "بذر 20-50 کیلوگرم/هکتار",
        "cost_class": "low",
        "species": {
            "nitrogen_fixers": ["Vicia (شامله)", "Trifolium (شبدر)", "Lupinus (ترمس)", "Medicago (یونجه)"],
            "grasses": ["Secale (چاودار)", "Avena (یولاف)", "Sorghum (سورگوم)"],
            "brassicas": ["Raphanus (تربچه)", "Sinapis (خردل)"]
        },
        "reference": "FAO Conservation Agriculture 2022; SARE 2023",
        "global_sources": "بذر محلی و منطقه‌ای"
    },
    {
        "id": "AMD007",
        "name_fa": "آهک کشاورزی (کربنات کلسیم)",
        "name_en": "Agricultural Lime (CaCO₃)",
        "category": "mineral_amendment",
        "mechanism": "افزایش pH خاک‌های اسیدی؛ کاهش سمیت آلومینیوم؛ بهبود جذب فسفر و کلسیم",
        "biomes": ["Tropical_Rainforest", "Temperate_Continental", "Boreal"],
        "target_problems": ["acidic_soil", "aluminum_toxicity", "phosphorus_fixation"],
        "application_rate": "2-10 تن/هکتار بسته به بافر خاک",
        "cost_class": "low",
        "reference": "FAO Soil Bulletin 2020; Goulding et al. 1989",
        "global_sources": "معادن آهک برزیل، هند، آمریکا، استرالیا"
    },
    {
        "id": "AMD008",
        "name_fa": "عصاره جلبک دریایی",
        "name_en": "Seaweed Extract",
        "category": "organic_biostimulant",
        "mechanism": "تحریک رشد با هورمون‌های طبیعی (اکسین، سیتوکینین، جیبرلین)؛ افزایش تحمل تنش شوری و خشکی؛ بهبود جذب مواد مغذی",
        "biomes": ["Coastal_Saline", "Arid", "Semi-arid", "Mediterranean"],
        "target_problems": ["salt_stress", "drought_stress", "low_growth"],
        "application_rate": "2-5 لیتر/هکتار (محلول‌پاشی) یا 10-20 لیتر (آبیاری)",
        "cost_class": "medium",
        "reference": "FAO 2022; du Jardin 2015",
        "global_sources": "جلبک‌های دریایی ایران، مراکش، شیلی، نروژ، اندونزی"
    },
    {
        "id": "AMD009",
        "name_fa": "گوگرد کشاورزی (برای کاهش شوری)",
        "name_en": "Agricultural Sulfur",
        "category": "mineral_amendment",
        "mechanism": "کاهش تدریجی شوری با تولید اسید سولفوریک توسط باکتری تیوباسیلوس؛ کاهش شوری خاک‌های قلیایی",
        "biomes": ["Semi-arid", "Arid", "Coastal_Saline"],
        "target_problems": ["salinity", "alkalinity"],
        "application_rate": "1-5 تن/هکتار + مایه تلقیح تیوباسیلوس",
        "cost_class": "medium",
        "reference": "FAO 2021; Al-Busaidi 2008",
        "global_sources": "معادن گوگرد ایران، عراق، عربستان، آمریکا"
    },
    {
        "id": "AMD010",
        "name_fa": "مالچ‌پاشی (پوشش سطح)",
        "name_en": "Mulching",
        "category": "physical_amendment",
        "mechanism": "کاهش تبخیر تا ۷۰٪؛ کنترل علف هرز؛ تنظیم دمای خاک؛ افزایش نفوذ باران",
        "biomes": ["ALL"],
        "target_problems": ["evaporation", "weed_pressure", "soil_temperature"],
        "application_rate": "5-15 تن/هکتار کاه یا 1000-2000 کیلوگرم پلاستیک زیست‌تخریب‌پذیر",
        "cost_class": "low_to_medium",
        "types": {
            "organic": "کاه، برگ، پوست درخت، تراشه چوب",
            "plastic": "پلاستیک زیست‌تخریب‌پذیر",
            "stone": "ریگ و شن (مالچ سنگی مناطق بیابانی)"
        },
        "reference": "FAO Conservation Agriculture 2022; FAO Mulching Guide",
        "global_sources": "پسماندهای محلی"
    }
]


# ══════════════════════════════════════════════════════════════
# بخش ۳: گیاهان پیشگام جهانی (Global Pioneer Plants)
# ══════════════════════════════════════════════════════════════

GLOBAL_PIONEER_PLANTS = [
    # ─────────────────────────────────────────────────────────
    # شورپسندان (Halophytes)
    # ─────────────────────────────────────────────────────────
    {
        "id": "PP001",
        "name_fa": "آتریپلکس (تبریزی/شورپسند)",
        "name_en": "Atriplex spp.",
        "category": "halophyte",
        "stress_tolerance": {"salinity_ds_m": 40, "drought": "very_high", "frost": "high"},
        "mechanism": "تجمع نمک در برگ‌ها (کریستال‌های نمکی)؛ سیستم ریشه عمیق (تا ۵ متر)؛ تثبیت خاک شور",
        "biomes": ["Hyper-arid", "Arid", "Semi-arid", "Coastal_Saline"],
        "ecosystem_services": ["soil_stabilization", "salinity_reduction", "fodder", "carbon_sequestration"],
        "establishment": "بذرپاشی در پاییز یا کاشت نهال در بهار",
        "water_requirement": "بسیار کم (بارش > 100 میلی‌متر کافی است)",
        "reference": "ICARDA 2021; FAO Halophytes 2020",
        "global_distribution": {
            "middle_east": "Atriplex halimus, A. canescens (ایران، عربستان، اردن)",
            "north_africa": "A. halimus (مراکش، تونس، الجزایر، مصر)",
            "australia": "Atriplex spp. (استرالیا)",
            "americas": "Atriplex canescens, A. nummularia (آمریکا، شیلی، آرژانتین)"
        }
    },
    {
        "id": "PP002",
        "name_fa": "گز (تاملاریکس)",
        "name_en": "Tamarix spp.",
        "category": "halophyte_xerophyte",
        "stress_tolerance": {"salinity_ds_m": 25, "drought": "very_high", "frost": "moderate"},
        "mechanism": "ترشح نمک از غدد برگ؛ ریشه بسیار عمیق (تا ۱۰ متر)؛ تثبیت شن‌های روان؛ کاهش سرعت باد",
        "biomes": ["Hyper-arid", "Arid", "Coastal_Saline"],
        "ecosystem_services": ["dune_stabilization", "windbreak", "salinity_reduction", "habitat"],
        "establishment": "قلمه در بهار یا بذرپاشی در مناطق مرطوب",
        "water_requirement": "بسیار کم؛ استفاده از آب زیرزمینی شور",
        "reference": "FAO 2021; ICARDA 2020",
        "global_distribution": {
            "middle_east": "Tamarix aphylla, T. tetrandra (ایران، عراق، مصر)",
            "central_asia": "Tamarix ramosissima (ترکمنستان، ازبکستان)",
            "mediterranean": "Tamarix gallica (تونس، مراکش)",
            "americas": "Tamarix ramosissima (غرب آمریکا)"
        }
    },
    {
        "id": "PP003",
        "name_fa": "اسپند (پگانوم هارمالا)",
        "name_en": "Peganum harmala",
        "category": "xerophyte_medicinal",
        "stress_tolerance": {"salinity_ds_m": 8, "drought": "high", "frost": "high"},
        "mechanism": "ریشه عمیق و گسترده؛ تولید آلکالوئیدهای طبیعی (هارمین)؛ مقاوم به خشکی و شوری ملایم",
        "biomes": ["Semi-arid", "Arid", "Temperate_Continental"],
        "ecosystem_services": ["soil_stabilization", "medicinal_value", "biodiversity"],
        "establishment": "بذرپاشی پاییزه در مناطق نیمه‌خشک",
        "water_requirement": "بسیار کم (بارش > 150 میلی‌متر)",
        "reference": "FAO 2020; ICARDA 2019",
        "global_distribution": {
            "middle_east": "ایران، ترکیه، عراق، سوریه",
            "central_asia": "ترکمنستان، ازبکستان، افغانستان",
            "north_africa": "مراکش، الجزایر، تونس",
            "south_asia": "هند، پاکستان"
        }
    },
    {
        "id": "PP004",
        "name_fa": "سالیکورنیا (علف شور)",
        "name_en": "Salicornia spp.",
        "category": "halophyte_edible",
        "stress_tolerance": {"salinity_ds_m": 50, "drought": "moderate", "frost": "moderate"},
        "mechanism": "گیاه گوشتی شورپسند (هالوفیت اجباری)؛ قابل استفاده به عنوان سبزی، علوفه و روغن؛ تصفیه پساب شور",
        "biomes": ["Coastal_Saline", "Hyper-arid", "Arid"],
        "ecosystem_services": ["saline_water_remediation", "food_production", "biodiversity"],
        "establishment": "بذرپاشی در مناطق ساحلی یا حاشیه شوره‌زارها",
        "water_requirement": "آب شور (تا ۵۰٪ آب دریا)",
        "reference": "FAO Halophytes 2022; Glenn et al. 1999",
        "global_distribution": {
            "middle_east": "ایران (خلیج فارس)، امارات، عربستان",
            "europe": "هلند، انگلستان، فرانسه (سواحل)",
            "americas": "مکزیک، پرو، شیلی (سواحل)",
            "asia": "هند، کره جنوبی، ژاپن"
        }
    },
    # ─────────────────────────────────────────────────────────
    # خشکی‌پسندان (Xerophytes)
    # ─────────────────────────────────────────────────────────
    {
        "id": "PP005",
        "name_fa": "سدر/عناب (زیزیفوس)",
        "name_en": "Ziziphus spp.",
        "category": "xerophyte_fruit_tree",
        "stress_tolerance": {"salinity_ds_m": 8, "drought": "very_high", "frost": "moderate"},
        "mechanism": "ریشه بسیار عمیق؛ برگ‌های کوچک با پوشش مومی؛ تولید میوه خوراکی با ارزش اقتصادی",
        "biomes": ["Semi-arid", "Arid", "Tropical_Savanna"],
        "ecosystem_services": ["food_production", "soil_stabilization", "shade", "habitat"],
        "establishment": "نهال‌کاری در بهار با آبیاری اولیه",
        "water_requirement": "بسیار کم پس از استقرار (بارش > 200 میلی‌متر)",
        "reference": "ICARDA 2022; FAO Dryland Fruit Trees 2021",
        "global_distribution": {
            "middle_east": "Z. spina-christi, Z. mauritiana (ایران، عمان، یمن)",
            "south_asia": "Z. mauritiana (هند، پاکستان)",
            "africa": "Z. mauritiana (سنگال، مالی، نیجر)",
            "asia": "Z. jujuba (چین، کره)"
        }
    },
    {
        "id": "PP006",
        "name_fa": "کبر (کاپاریس)",
        "name_en": "Capparis spinosa",
        "category": "xerophyte_medicinal",
        "stress_tolerance": {"salinity_ds_m": 10, "drought": "very_high", "frost": "high"},
        "mechanism": "ریشه بسیار عمیق و مقاوم به سنگلاخ؛ تولید گل‌های خوراکی (کبر) با ارزش اقتصادی بالا",
        "biomes": ["Semi-arid", "Arid", "Mediterranean"],
        "ecosystem_services": ["soil_stabilization", "food_production", "biodiversity"],
        "establishment": "بذرپاشی یا قلمه در مناطق سنگلاخ",
        "water_requirement": "بسیار کم (بارش > 150 میلی‌متر)",
        "reference": "FAO 2021; ICARDA 2020",
        "global_distribution": {
            "mediterranean": "ایتالیا، اسپانیا، یونان، ترکیه، مراکش",
            "middle_east": "ایران، سوریه، اردن",
            "central_asia": "افغانستان، ازبکستان"
        }
    },
    {
        "id": "PP007",
        "name_fa": "گوان (آسترگالوس)",
        "name_en": "Astragalus spp.",
        "category": "xerophyte_legume",
        "stress_tolerance": {"salinity_ds_m": 6, "drought": "very_high", "frost": "very_high"},
        "mechanism": "تثبیت نیتروژن (حبوبه)؛ تولید صمغ (کتیرا) با ارزش اقتصادی؛ مقاوم به خشکی و سرما",
        "biomes": ["Semi-arid", "Arid", "Alpine", "Temperate_Continental"],
        "ecosystem_services": ["nitrogen_fixation", "gum_production", "soil_stabilization"],
        "establishment": "بذرپاشی پاییزه",
        "water_requirement": "بسیار کم (بارش > 150 میلی‌متر)",
        "reference": "FAO 2020; ICARDA 2019",
        "global_distribution": {
            "middle_east": "A. gummifer (ایران، ترکیه، سوریه) - کتیرا",
            "central_asia": "ترکمنستان، افغانستان",
            "mediterranean": "یونان، اسپانیا"
        }
    },
    {
        "id": "PP008",
        "name_fa": "درمنه (آرتمیزیا)",
        "name_en": "Artemisia spp.",
        "category": "xerophyte_medicinal",
        "stress_tolerance": {"salinity_ds_m": 8, "drought": "very_high", "frost": "very_high"},
        "mechanism": "پوشش نقره‌ای برگ برای بازتاب نور؛ تولید اسانس‌های دارویی؛ تثبیت خاک بیابانی",
        "biomes": ["Semi-arid", "Arid", "Temperate_Continental", "Alpine"],
        "ecosystem_services": ["soil_stabilization", "medicinal_value", "essential_oil"],
        "establishment": "بذرپاشی پاییزه یا بهاره",
        "water_requirement": "بسیار کم (بارش > 100 میلی‌متر)",
        "reference": "FAO 2021; ICARDA 2020",
        "global_distribution": {
            "middle_east": "A. sieberi, A. aucheri (ایران)",
            "central_asia": "A. absinthium (ترکمنستان، قزاقستان)",
            "north_africa": "A. herba-alba (مراکش، تونس، الجزایر)",
            "americas": "A. tridentata (غرب آمریکا)"
        }
    },
    # ─────────────────────────────────────────────────────────
    # تثبیت‌کننده‌های نیتروژن (Nitrogen-Fixing Pioneers)
    # ─────────────────────────────────────────────────────────
    {
        "id": "PP009",
        "name_fa": "کهور (پروسوپیس)",
        "name_en": "Prosopis spp.",
        "category": "nitrogen_fixing_xerophyte",
        "stress_tolerance": {"salinity_ds_m": 15, "drought": "very_high", "frost": "moderate"},
        "mechanism": "تثبیت نیتروژن (همزیستی با ریزوبیوم)؛ ریشه تا ۵۰ متر عمق؛ تولید غلاف خوراکی و چوب",
        "biomes": ["Semi-arid", "Arid", "Hyper-arid"],
        "ecosystem_services": ["nitrogen_fixation", "fodder", "fuel_wood", "shade"],
        "establishment": "نهال‌کاری یا بذرپاشی",
        "water_requirement": "بسیار کم؛ استفاده از آب زیرزمینی",
        "reference": "FAO 2022; ICARDA 2021",
        "global_distribution": {
            "middle_east": "P. cineraria, P. juliflora (ایران، عمان، امارات)",
            "africa": "P. juliflora (کنیا، اتیوپی، سودان)",
            "south_asia": "P. cineraria (هند، پاکستان)",
            "americas": "P. chilensis, P. alba (آرژانتین، پرو، مکزیک)"
        }
    },
    {
        "id": "PP010",
        "name_fa": "اقاقیا/آکاسیا",
        "name_en": "Acacia spp.",
        "category": "nitrogen_fixing_pioneer",
        "stress_tolerance": {"salinity_ds_m": 10, "drought": "very_high", "frost": "moderate"},
        "mechanism": "تثبیت نیتروژن؛ رشد سریع؛ تولید چوب و صمغ عربی؛ ایجاد سایه برای گیاهان زیرین",
        "biomes": ["Semi-arid", "Arid", "Tropical_Savanna", "Mediterranean"],
        "ecosystem_services": ["nitrogen_fixation", "gum_arabic", "fuel_wood", "shade"],
        "establishment": "نهال‌کاری در بهار",
        "water_requirement": "کم تا متوسط",
        "reference": "FAO Forestry 2021; Sarrailh & Ayrault 2001",
        "global_distribution": {
            "africa": "A. senegal (صمغ عربی - سنگال، سودان، چاد)",
            "australia": "Acacia spp. (واطله، مولگا)",
            "middle_east": "A. tortilis, A. saligna (عربستان، اردن، اسرائیل)",
            "asia": "A. mangium, A. auriculiformis (هند، اندونزی)"
        }
    },
    {
        "id": "PP011",
        "name_fa": "کازوآرینا",
        "name_en": "Casuarina equisetifolia",
        "category": "nitrogen_fixing_actinorhizal",
        "stress_tolerance": {"salinity_ds_m": 12, "drought": "high", "frost": "low"},
        "mechanism": "تثبیت نیتروژن (همزیستی با فرنکیا)؛ تحمل شوری و باد؛ رشد سریع در سواحل",
        "biomes": ["Coastal_Saline", "Tropical_Savanna", "Arid"],
        "ecosystem_services": ["windbreak", "coastal_stabilization", "nitrogen_fixation", "fuel_wood"],
        "establishment": "نهال‌کاری در سواحل و مناطق ساحلی",
        "water_requirement": "کم تا متوسط",
        "reference": "FAO 2021; Dawson 2008",
        "global_distribution": {
            "australia": "بومی استرالیا",
            "asia": "هند، ویتنام، تایلند، فیلیپین",
            "africa": "مصر، مراکش، سنگال",
            "middle_east": "ایران (جنوب)، عمان، امارات"
        }
    },
    {
        "id": "PP012",
        "name_fa": "لوسینا",
        "name_en": "Leucaena leucocephala",
        "category": "nitrogen_fixing_fast_growing",
        "stress_tolerance": {"salinity_ds_m": 6, "drought": "high", "frost": "low"},
        "mechanism": "تثبیت نیتروژن (۵۰۰+ کیلوگرم/هکتار)؛ رشد بسیار سریع (تا ۵ متر در سال)؛ علوفه با کیفیت",
        "biomes": ["Tropical_Savanna", "Semi-arid", "Mediterranean"],
        "ecosystem_services": ["nitrogen_fixation", "fodder", "fuel_wood", "green_manure"],
        "establishment": "بذرپاشی یا نهال‌کاری",
        "water_requirement": "متوسط (بارش > 500 میلی‌متر)",
        "reference": "FAO 2022; Shelton 2000",
        "global_distribution": {
            "tropics": "برزیل، کلمبیا، فیلیپین، اندونزی",
            "africa": "کنیا، تانزانیا، نیجریه",
            "asia": "هند، تایلند، ویتنام",
            "americas": "مکزیک (بومی)"
        }
    },
    # ─────────────────────────────────────────────────────────
    # تثبیت‌کننده‌های خاک و شن (Soil Stabilizers)
    # ─────────────────────────────────────────────────────────
    {
        "id": "PP013",
        "name_fa": "استیپا (علف بیابانی)",
        "name_en": "Stipa spp.",
        "category": "xerophyte_grass",
        "stress_tolerance": {"salinity_ds_m": 6, "drought": "very_high", "frost": "high"},
        "mechanism": "ریشه فیبری متراکم برای تثبیت خاک؛ تولید بذر خوراکی برای دام؛ پوشش دائمی",
        "biomes": ["Semi-arid", "Arid", "Temperate_Continental", "Alpine"],
        "ecosystem_services": ["soil_stabilization", "fodder", "biodiversity"],
        "establishment": "بذرپاشی پاییزه",
        "water_requirement": "بسیار کم (بارش > 150 میلی‌متر)",
        "reference": "FAO 2021; ICARDA 2020",
        "global_distribution": {
            "middle_east": "S. barbata, S. capensis (ایران، ترکیه)",
            "central_asia": "S. orientalis (ترکمنستان، قزاقستان)",
            "americas": "Stipa comata, S. tenuissima (غرب آمریکا، آرژانتین)",
            "africa": "Stipa tenacissima (مراکش، تونس، الجزایر)"
        }
    },
    {
        "id": "PP014",
        "name_fa": "پانیکوم تورگیدوم (علف بیابانی گرمسیری)",
        "name_en": "Panicum turgidum",
        "category": "xerophyte_grass",
        "stress_tolerance": {"salinity_ds_m": 12, "drought": "very_high", "frost": "low"},
        "mechanism": "علف بیابانی با ریشه عمیق؛ تحمل شوری بالا؛ تثبیت شن‌های روان؛ علوفه با کیفیت",
        "biomes": ["Hyper-arid", "Arid", "Coastal_Saline"],
        "ecosystem_services": ["dune_stabilization", "fodder", "soil_stabilization"],
        "establishment": "بذرپاشی در پاییز یا کاشت نشاء",
        "water_requirement": "بسیار کم (بارش > 50 میلی‌متر)",
        "reference": "FAO 2022; ICARDA 2021",
        "global_distribution": {
            "middle_east": "ایران، عمان، امارات، عربستان",
            "north_africa": "مصر، لیبی، تونس",
            "south_asia": "هند، پاکستان (بلوچستان)"
        }
    },
    {
        "id": "PP015",
        "name_fa": "بوفل گرس (سینخرس سیاک)",
        "name_en": "Cenchrus ciliaris (Buffel Grass)",
        "category": "xerophyte_grass",
        "stress_tolerance": {"salinity_ds_m": 8, "drought": "very_high", "frost": "moderate"},
        "mechanism": "علف چندساله با ریشه عمیق؛ تحمل خشکی و شوری؛ پوشش دائمی برای تثبیت خاک",
        "biomes": ["Semi-arid", "Arid", "Tropical_Savanna"],
        "ecosystem_services": ["soil_stabilization", "fodder", "erosion_control"],
        "establishment": "بذرپاشی در فصل بارش",
        "water_requirement": "کم (بارش > 250 میلی‌متر)",
        "reference": "FAO 2021; SARE 2022",
        "global_distribution": {
            "australia": "بومی آفریقا، گسترده در استرالیا",
            "americas": "تگزاس، مکزیک، برزیل",
            "africa": "کنیا، تانزانیا، آفریقای جنوبی",
            "asia": "هند، پاکستان"
        }
    }
]


# ══════════════════════════════════════════════════════════════
# بخش ۴: تولید و ذخیره خروجی
# ══════════════════════════════════════════════════════════════

def build_engine():
    print("=" * 70)
    print("موتور جهانی مصالح زیستی هیدروما")
    print("فاز دوم: تبدیل هیدروما به سامانه تجویزگر عملیاتی جهانی")
    print("=" * 70)
    
    # بارگذاری پایگاه دانش
    kb_file = ROOT / "docs" / "hydroma" / "knowledge_base_detailed.json"
    if kb_file.exists():
        kb = json.loads(kb_file.read_text(encoding="utf-8"))
        print(f"\n✅ پایگاه دانش بارگذاری شد: {len(kb)} گرایش")
    
    # ساختار نهایی
    bio_engine = {
        "engine_name": "Hydroma Global Bio-Materials Engine",
        "version": "2.0-global",
        "generated_at": datetime.now().isoformat(),
        "philosophy": "تن زمین خسته است - ما در خدمت بشر و زمین هستیم با پیوند طبیعت و بشر",
        "global_coverage": {
            "biomes": 12,
            "continents": "همه قارات",
            "climate_zones": "از بیابان فراخشک تا توندرا و جنگل بارانی",
        },
        "statistics": {
            "microbiomes": len(GLOBAL_MICROBIOMES),
            "amendments": len(GLOBAL_AMENDMENTS),
            "pioneer_plants": len(GLOBAL_PIONEER_PLANTS),
            "total_entries": len(GLOBAL_MICROBIOMES) + len(GLOBAL_AMENDMENTS) + len(GLOBAL_PIONEER_PLANTS),
        },
        "microbiomes": GLOBAL_MICROBIOMES,
        "amendments": GLOBAL_AMENDMENTS,
        "pioneer_plants": GLOBAL_PIONEER_PLANTS,
        "integration": {
            "connects_to_algorithms": ["H09", "H10", "H13", "H21", "H25"],
            "feeds_decision_engine": True,
            "supports_crisis_scenarios": True,
            "provides_prescriptions": True,
        },
        "knowledge_base_reference": f"{len(kb)} گرایش تخصصی فعال",
    }
    
    # ذخیره
    output_file = OUTPUT_DIR / "global_bio_materials_engine.json"
    output_file.write_text(
        json.dumps(bio_engine, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    # آمار
    print(f"\n📊 آمار موتور جهانی:")
    print(f"   🦠 میکروبیوم‌ها: {len(GLOBAL_MICROBIOMES)}")
    print(f"   🧪 اصلاح‌کننده‌ها: {len(GLOBAL_AMENDMENTS)}")
    print(f"   🌱 گیاهان پیشگام: {len(GLOBAL_PIONEER_PLANTS)}")
    print(f"   📦 مجموع: {bio_engine['statistics']['total_entries']}")
    print(f"\n💾 ذخیره شد: {output_file}")
    
    # نمونه‌های کلیدی
    print("\n" + "=" * 70)
    print("🌍 نمونه‌های کلیدی (نمایندگی جهانی):")
    print("=" * 70)
    
    print("\n🦠 میکروبیوم‌های شاخص:")
    for mic in GLOBAL_MICROBIOMES[:5]:
        biomes_str = ", ".join(mic["biomes"][:2])
        print(f"   • {mic['name_fa']} ({mic['name_en']}) → {biomes_str}")
    
    print("\n🧪 اصلاح‌کننده‌های شاخص:")
    for amd in GLOBAL_AMENDMENTS[:5]:
        print(f"   • {amd['name_fa']} → {amd['category']}")
    
    print("\n🌱 گیاهان پیشگام شاخص:")
    for pp in GLOBAL_PIONEER_PLANTS[:5]:
        print(f"   • {pp['name_fa']} ({pp['name_en']}) → تحمل شوری: {pp['stress_tolerance'].get('salinity_ds_m', 'N/A')} dS/m")
    
    print("\n" + "=" * 70)
    print("🎯 شعار: تن زمین خسته است")
    print("   ما در خدمت بشر و زمین هستیم با پیوند طبیعت و بشر")
    print("=" * 70)
    
    return bio_engine


if __name__ == "__main__":
    build_engine()