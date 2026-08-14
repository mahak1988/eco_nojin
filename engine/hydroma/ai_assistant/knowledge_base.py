"""Curated knowledge base for agricultural and ecological guidance.

Each document is aligned with FAO standards and scientific references.
This serves as the retrieval corpus for the RAG system.
"""
from dataclasses import dataclass

@dataclass
class KnowledgeDocument:
    id: str
    title: str
    content: str
    source: str
    category: str


# Scientific guidance aligned with FAO-56, FAO AquaCrop, and IPM principles
KNOWLEDGE_BASE: list[KnowledgeDocument] = [
    KnowledgeDocument(
        id="doc_001",
        title="Compost C/N Ratio Optimization",
        content=(
            "The optimal Carbon to Nitrogen (C/N) ratio for composting is between 25:1 and 35:1. "
            "A ratio above 40 slows decomposition significantly, while a ratio below 20 causes nitrogen "
            "loss as ammonia and produces odor. Straw (C/N 80:1) should be mixed with cow manure (C/N 20:1) "
            "in approximately 2:1 mass ratio to achieve optimal balance."
        ),
        source="FAO Composting Guidelines",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_002",
        title="Biochar Application in Sandy Soils",
        content=(
            "Biochar improves water retention in sandy soils by increasing Cation Exchange Capacity (CEC). "
            "Recommended application rate is 10-20 tons per hectare. Biochar should be 'charged' with "
            "compost or manure before application to prevent initial nutrient immobilization. "
            "Pyrolysis temperature should be 400-600°C for optimal porosity."
        ),
        source="International Biochar Initiative",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_003",
        title="FAO-56 Reference Evapotranspiration (ET0)",
        content=(
            "The Hargreaves-Samani method estimates ET0 using only temperature data: "
            "ET0 = 0.0023 × 0.408 × Ra × (Tmean + 17.8) × √(Tmax - Tmin), where Ra is extraterrestrial "
            "radiation in MJ/m²/day. This method is recommended by FAO when humidity and wind data "
            "are unavailable. Typical ET0 ranges from 2-8 mm/day depending on climate."
        ),
        source="FAO Irrigation and Drainage Paper 56",
        category="water_management",
    ),
    KnowledgeDocument(
        id="doc_004",
        title="Drought-Resistant Crops for Arid Regions",
        content=(
            "For regions with annual rainfall below 300mm, recommended crops include: "
            "millet (Pennisetum glaucum), sorghum (Sorghum bicolor), chickpea (Cicer arietinum), "
            "and prickly pear cactus (Opuntia ficus-indica). These crops require 200-400mm of water "
            "per season and can tolerate temperatures up to 40°C. Prickly pear is particularly valuable "
            "as both food source and soil stabilization plant."
        ),
        source="FAO Crop Production Guidelines",
        category="crop_selection",
    ),
    KnowledgeDocument(
        id="doc_005",
        title="RUSLE Soil Erosion Model",
        content=(
            "The Revised Universal Soil Loss Equation (RUSLE) estimates annual soil loss: "
            "A = R × K × LS × C × P, where R is rainfall erosivity, K is soil erodibility, "
            "LS is slope length/steepness factor, C is cover management, and P represents "
            "conservation practices. Tolerable soil loss is typically 5-10 tons/hectare/year."
        ),
        source="USDA/RUSLE Handbook",
        category="erosion_control",
    ),
    KnowledgeDocument(
        id="doc_006",
        title="Small-Scale Watershed Structures",
        content=(
            "Check dams, contour trenches, and half-moons are effective low-cost structures. "
            "Check dams should be built in series with spacing 5-10 times the dam height. "
            "Contour trenches (50cm × 50cm cross-section) increase infiltration by 30-50% in "
            "sloping terrain. Half-moons (2-4m diameter) are ideal for seedling establishment "
            "in degraded rangelands."
        ),
        source="FAO Watershed Management Field Manual",
        category="watershed",
    ),
    KnowledgeDocument(
        id="doc_007",
        title="Integrated Pest Management (IPM)",
        content=(
            "IPM prioritizes biological control over chemical pesticides. Key strategies include: "
            "(1) Use of Trichoderma for soil-borne fungal diseases, (2) Release of ladybugs and "
            "lacewings for aphid control, (3) Pheromone traps for monitoring, (4) Crop rotation "
            "to break pest cycles. Economic threshold levels should guide intervention timing."
        ),
        source="FAO IPM Guidelines",
        category="pest_management",
    ),
    KnowledgeDocument(
        id="doc_008",
        title="Soil Salinity Management",
        content=(
            "Soils with EC > 4 dS/m are considered saline. Management strategies: "
            "(1) Leaching with 15-30cm of good-quality water, (2) Gypsum application for sodic soils "
            "(SAR > 13), (3) Planting salt-tolerant species like barley, sugar beet, or Atriplex, "
            "(4) Drip irrigation to maintain low salinity in root zone. Avoid ash application "
            "on already saline soils as it increases pH and EC."
        ),
        source="FAO Irrigation Paper 32",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_009",
        title="Carbon Sequestration in Agricultural Soils",
        content=(
            "Agricultural soils can sequester 0.5-2.0 tons CO2/ha/year through: "
            "(1) No-till farming (0.3-0.5 t/ha/yr), (2) Cover cropping (0.2-0.4 t/ha/yr), "
            "(3) Biochar application (stable for centuries), (4) Agroforestry systems. "
            "Soil organic carbon should be measured annually to verify sequestration rates "
            "for carbon credit programs (Verra VCS, Gold Standard)."
        ),
        source="IPCC Guidelines for Agriculture",
        category="carbon",
    ),
    KnowledgeDocument(
        id="doc_010",
        title="Medicinal Plants for Arid Climates",
        content=(
            "High-value medicinal plants adapted to dry conditions include: "
            "thyme (Thymus vulgaris), rosemary (Rosmarinus officinalis), sage (Salvia officinalis), "
            "lavender (Lavandula angustifolia), and cumin (Cuminum cyminum). These require "
            "300-500mm annual rainfall and well-drained soils. Market value can be 5-10x higher "
            "than conventional crops, making them ideal for smallholder economic diversification."
        ),
        source="WHO Traditional Medicine Strategy",
        category="crop_selection",
    ),
]
