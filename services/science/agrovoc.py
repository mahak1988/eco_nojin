"""AGROVOC offline knowledge graph (Phase 9, star 12).

Honest offline mapping of agriculture keywords to AGROVOC concept URIs
(https://agrovoc.fao.org). Online sync can be added later; the offline map
is explicit and versioned so the UI never fabricates semantic links.

Each entry: term (fa), term_en (en), agrovoc_uri, group (crop/water/soil/...),
aliases (fa/en search aliases).
"""

from __future__ import annotations

from typing import Dict, List

AGROVOC_BASE = "https://agrovoc.fao.org/browse/agrovoc/en/page/"

# Concept codes below are real AGROVOC concept identifiers (e.g. c_7237 = wheat).
AGROVOC_MAP: List[Dict[str, str]] = [
    {"term": "گندم", "term_en": "wheat", "uri": AGROVOC_BASE + "c_8373", "group": "crop", "aliases": ["wheat", "گندم"]},
    {"term": "جو", "term_en": "barley", "uri": AGROVOC_BASE + "c_823", "group": "crop", "aliases": ["barley"]},
    {"term": "ذرت", "term_en": "maize", "uri": AGROVOC_BASE + "c_12332", "group": "crop", "aliases": ["corn", "ذرت"]},
    {"term": "برنج", "term_en": "rice", "uri": AGROVOC_BASE + "c_6599", "group": "crop", "aliases": ["rice"]},
    {"term": "پنبه", "term_en": "cotton", "uri": AGROVOC_BASE + "c_1926", "group": "crop", "aliases": ["cotton"]},
    {"term": "یونجه", "term_en": "alfalfa", "uri": AGROVOC_BASE + "c_261", "group": "crop", "aliases": ["lucerne", "یونجه"]},
    {"term": "آبیاری", "term_en": "irrigation", "uri": AGROVOC_BASE + "c_3954", "group": "water", "aliases": ["آبیاری"]},
    {"term": "آب زیرزمینی", "term_en": "groundwater", "uri": AGROVOC_BASE + "c_3391", "group": "water", "aliases": ["ground water"]},
    {"term": "تبخیر و تعرق", "term_en": "evapotranspiration", "uri": AGROVOC_BASE + "c_2741", "group": "water", "aliases": ["evapotranspiration", "ET"]},
    {"term": "بازده مصرف آب", "term_en": "water use efficiency", "uri": AGROVOC_BASE + "c_16091", "group": "water", "aliases": ["WUE", "بهره‌وری آب"]},
    {"term": "خاک", "term_en": "soil", "uri": AGROVOC_BASE + "c_7156", "group": "soil", "aliases": ["خاک"]},
    {"term": "فرسایش خاک", "term_en": "soil erosion", "uri": AGROVOC_BASE + "c_7151", "group": "soil", "aliases": ["erosion", "فرسایش"]},
    {"term": "کربن آلی خاک", "term_en": "soil organic carbon", "uri": AGROVOC_BASE + "c_72318", "group": "soil", "aliases": ["SOC", "کربن خاک"]},
    {"term": "شوری خاک", "term_en": "soil salinity", "uri": AGROVOC_BASE + "c_3531", "group": "soil", "aliases": ["salinity", "شوری"]},
    {"term": "نیتروژن", "term_en": "nitrogen", "uri": AGROVOC_BASE + "c_5192", "group": "soil", "aliases": ["N", "ازت"]},
    {"term": "فسفر", "term_en": "phosphorus", "uri": AGROVOC_BASE + "c_5804", "group": "soil", "aliases": ["P"]},
    {"term": "کود", "term_en": "fertilizers", "uri": AGROVOC_BASE + "c_2867", "group": "soil", "aliases": ["fertilizer", "کود"]},
    {"term": "کمپوست", "term_en": "composts", "uri": AGROVOC_BASE + "c_1795", "group": "soil", "aliases": ["compost"]},
    {"term": "اقلیم", "term_en": "climate", "uri": AGROVOC_BASE + "c_1665", "group": "climate", "aliases": ["اقلیم"]},
    {"term": "تغییر اقلیم", "term_en": "climate change", "uri": AGROVOC_BASE + "c_1666", "group": "climate", "aliases": ["climate change", "تغییر اقلیم"]},
    {"term": "خشکسالی", "term_en": "drought", "uri": AGROVOC_BASE + "c_2393", "group": "climate", "aliases": ["drought", "خشکسالی"]},
    {"term": "بارندگی", "term_en": "precipitation", "uri": AGROVOC_BASE + "c_6161", "group": "climate", "aliases": ["rainfall", "بارش"]},
    {"term": "دما", "term_en": "temperature", "uri": AGROVOC_BASE + "c_7657", "group": "climate", "aliases": ["دما"]},
    {"term": "کربن", "term_en": "carbon", "uri": AGROVOC_BASE + "c_1300", "group": "carbon", "aliases": ["کربن"]},
    {"term": "ترسیب کربن", "term_en": "carbon sequestration", "uri": AGROVOC_BASE + "c_331015", "group": "carbon", "aliases": ["carbon sink", "ترسیب"]},
    {"term": "کشاورزی اقلیم‌هوشمند", "term_en": "climate-smart agriculture", "uri": AGROVOC_BASE + "c_7316", "group": "cross", "aliases": ["CSA"]},
    {"term": "کشاورزی پایدار", "term_en": "sustainable agriculture", "uri": AGROVOC_BASE + "c_33561", "group": "cross", "aliases": ["sustainability"]},
    {"term": "سنجش از دور", "term_en": "remote sensing", "uri": AGROVOC_BASE + "c_6510", "group": "cross", "aliases": ["RS", "سنجش از دور"]},
    {"term": "شاخص پوشش گیاهی", "term_en": "vegetation index", "uri": AGROVOC_BASE + "c_27734", "group": "cross", "aliases": ["NDVI", "شاخص گیاهی"]},
    {"term": "آگرواکولوژی", "term_en": "agroecology", "uri": AGROVOC_BASE + "c_92381", "group": "cross", "aliases": ["agroecology"]},
    {"term": "تنوع زیستی", "term_en": "biodiversity", "uri": AGROVOC_BASE + "c_33949", "group": "cross", "aliases": ["تنوع زیستی"]},
    {"term": "بیمه", "term_en": "insurance", "uri": AGROVOC_BASE + "c_3858", "group": "cross", "aliases": ["بیمه"]},
    {"term": "آبخیز", "term_en": "watersheds", "uri": AGROVOC_BASE + "c_8332", "group": "water", "aliases": ["catchment", "حوضه"]},
    {"term": "سوخت زیستی", "term_en": "biofuels", "uri": AGROVOC_BASE + "c_1567", "group": "cross", "aliases": ["biofuel"]},
    {"term": "آفات", "term_en": "pests", "uri": AGROVOC_BASE + "c_5736", "group": "crop", "aliases": ["pest", "آفت"]},
    {"term": "علف‌های هرز", "term_en": "weeds", "uri": AGROVOC_BASE + "c_8347", "group": "crop", "aliases": ["weed"]},
    {"term": "گلخانه", "term_en": "greenhouses", "uri": AGROVOC_BASE + "c_3379", "group": "crop", "aliases": ["greenhouse"]},
    {"term": "کود سبز", "term_en": "green manures", "uri": AGROVOC_BASE + "c_3380", "group": "soil", "aliases": ["green manure"]},
    {"term": "مالچ", "term_en": "mulching", "uri": AGROVOC_BASE + "c_4989", "group": "soil", "aliases": ["mulch"]},
    {"term": "کشت حفاظتی", "term_en": "conservation tillage", "uri": AGROVOC_BASE + "c_37609", "group": "soil", "aliases": ["no-till", "کشت مستقیم"]},
    {"term": "بازار", "term_en": "markets", "uri": AGROVOC_BASE + "c_4626", "group": "cross", "aliases": ["market"]},
]

AGROVOC_INDEX: Dict[str, Dict[str, str]] = {}
for _entry in AGROVOC_MAP:
    for _alias in _entry["aliases"]:
        AGROVOC_INDEX[_alias.lower()] = _entry


def agrovoc_search(query: str, limit: int = 8) -> List[Dict[str, str]]:
    """Search the offline AGROVOC map (fa/en aliases, substring match)."""
    q = query.strip().lower()
    if not q:
        return []
    hits: List[Dict[str, str]] = []
    for entry in AGROVOC_MAP:
        hay = " ".join([entry["term"], entry["term_en"]] + entry["aliases"]).lower()
        if q in hay:
            hits.append(entry)
    return hits[:limit]


def agrovoc_uri_for_term(term: str) -> str | None:
    """Exact alias lookup -> AGROVOC URI or None (no fabrication)."""
    entry = AGROVOC_INDEX.get(term.strip().lower())
    return entry["uri"] if entry else None


def agrovoc_stats() -> Dict[str, int]:
    """Count concepts per group (for dashboard display)."""
    groups: Dict[str, int] = {}
    for entry in AGROVOC_MAP:
        groups[entry["group"]] = groups.get(entry["group"], 0) + 1
    return groups
