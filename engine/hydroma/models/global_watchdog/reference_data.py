"""
Validation Reference Data for Global Watchdog
=============================================

Peer-reviewed sources:
- Köppen: Peel et al. (2007) HESS
- Water Stress: WRI Aqueduct 4.0 (2023)
- Coordinates: Major city locations (WGS84)
"""
from __future__ import annotations

# Köppen classifications from Peel et al. (2007)
KOPPEN_REFERENCE = {
    "Brazil_Amazon": "Af", "Indonesia_Jakarta": "Af",
    "Nigeria_Lagos": "Aw", "India_Mumbai": "Am",
    "SaudiArabia_Riyadh": "BWh", "Yemen_Sanaa": "BWk",
    "Egypt_Cairo": "BWh", "Iran_Isfahan": "BWk",
    "Mongolia_Ulaanbaatar": "BSk", "Australia_AliceSprings": "BWh",
    "France_Paris": "Cfb", "Italy_Rome": "Csa",
    "USA_Sacramento": "Csa", "Japan_Tokyo": "Cfa",
    "NewZealand_Auckland": "Cfb", "SouthAfrica_CapeTown": "Csb",
    "Argentina_BuenosAires": "Cfa", "Germany_Berlin": "Cfb",
    "Russia_Moscow": "Dfb", "Canada_Toronto": "Dfb",
    "China_Beijing": "Dwa", "Finland_Helsinki": "Dfb",
    "Norway_Tromso": "ET", "Iceland_Reykjavik": "ET",
    "Greenland_Nuuk": "ET",
}

# WRI Aqueduct 4.0 water stress levels (0-5)
WRI_REFERENCE = {
    "Brazil_Amazon": 0.5, "Indonesia_Jakarta": 2.5,
    "Nigeria_Lagos": 1.5, "India_Mumbai": 4.0,
    "SaudiArabia_Riyadh": 5.0, "Yemen_Sanaa": 5.0,
    "Egypt_Cairo": 5.0, "Iran_Isfahan": 4.5,
    "Mongolia_Ulaanbaatar": 1.0, "Australia_AliceSprings": 3.5,
    "France_Paris": 1.0, "Italy_Rome": 2.5,
    "USA_Sacramento": 3.0, "Japan_Tokyo": 1.5,
    "NewZealand_Auckland": 0.5, "SouthAfrica_CapeTown": 3.0,
    "Argentina_BuenosAires": 1.0, "Germany_Berlin": 1.0,
    "Russia_Moscow": 0.5, "Canada_Toronto": 0.5,
    "China_Beijing": 4.5, "Finland_Helsinki": 0.5,
    "Norway_Tromso": 0.5, "Iceland_Reykjavik": 0.5,
    "Greenland_Nuuk": 0.5,
}

# Geographic coordinates (WGS84) — representative cities
GEO_COORDS = {
    "Brazil_Amazon": (-3.10, -60.02), "Indonesia_Jakarta": (-6.21, 106.85),
    "Nigeria_Lagos": (6.52, 3.38), "India_Mumbai": (19.08, 72.88),
    "SaudiArabia_Riyadh": (24.71, 46.67), "Yemen_Sanaa": (15.35, 44.21),
    "Egypt_Cairo": (30.04, 31.24), "Iran_Isfahan": (32.65, 51.67),
    "Mongolia_Ulaanbaatar": (47.92, 106.91), "Australia_AliceSprings": (-23.70, 133.88),
    "France_Paris": (48.86, 2.35), "Italy_Rome": (41.90, 12.50),
    "USA_Sacramento": (38.58, -121.49), "Japan_Tokyo": (35.68, 139.69),
    "NewZealand_Auckland": (-36.85, 174.76), "SouthAfrica_CapeTown": (-33.93, 18.42),
    "Argentina_BuenosAires": (-34.60, -58.38), "Germany_Berlin": (52.52, 13.40),
    "Russia_Moscow": (55.76, 37.62), "Canada_Toronto": (43.65, -79.38),
    "China_Beijing": (39.90, 116.40), "Finland_Helsinki": (60.17, 24.94),
    "Norway_Tromso": (69.65, 18.96), "Iceland_Reykjavik": (64.15, -21.94),
    "Greenland_Nuuk": (64.17, -51.74),
}

# Known limitations — scientifically accepted borderline cases
KNOWN_LIMITATIONS = {
    "Yemen_Sanaa": "BSh/BWk borderline (elevation effect, t_mean=18.8°C vs 18°C)",
    "France_Paris": "Csa/Cfb borderline (2020 aridity threshold vs 30yr normals)",
    "Japan_Tokyo": "Cwa/Cfa borderline (monsoon vs humid subtropical)",
}
