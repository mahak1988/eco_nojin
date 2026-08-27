"""Carbon engine Python bindings using existing hydroma_core."""

import math

try:
    from engine.hydroma import cpp_bindings

    _cpp = cpp_bindings.get_module()
    _available = _cpp is not None
except Exception:
    _cpp = None
    _available = False


# ============================================================================
# Constants (scientific)
# ============================================================================
CARBON_FRACTION = 0.47  # IPCC 2006 default
CO2_MOLAR_MASS = 44.01
C_MOLAR_MASS = 12.011
O2_MOLAR_MASS = 32.00
CO2_TO_C_RATIO = CO2_MOLAR_MASS / C_MOLAR_MASS  # 3.664

# Wood densities (g/cm³) - Chave et al.
WOOD_DENSITIES = {
    "tropical_moist": 0.56,
    "tropical_dry": 0.62,
    "temperate_broadleaf": 0.48,
    "temperate_conifer": 0.40,
    "boreal": 0.38,
    "arid": 0.65,
    "mangrove": 0.78,
    "bamboo": 0.35,
    "olive": 0.73,
    "walnut": 0.55,
    "apple": 0.60,
    "pistachio": 0.68,
    "citrus": 0.53,
}

# RothC-26.3 decay rates (per year)
ROTHC_RATES = {
    "DPM": 10.0,  # Decomposable Plant Material
    "RPM": 0.3,  # Resistant Plant Material
    "BIO": 0.66,  # Microbial Biomass
    "HUM": 0.02,  # Humified Organic Matter
    "IOM": 0.0,  # Inert Organic Matter
}


# ============================================================================
# Chave et al. 2014 - Pantropical AGB Allometry
# ============================================================================
def biomass_aboveground(D_cm: float, H_m: float, wood_density: float = 0.55) -> float:
    """
    Aboveground biomass (kg) using Chave et al. 2014 pantropical model.
    AGB = 0.0673 × (ρ × D² × H)^0.976

    Args:
        D_cm: Diameter at breast height (cm)
        H_m: Total tree height (m)
        wood_density: Wood density (g/cm³)

    Returns:
        Aboveground biomass in kg
    """
    if D_cm <= 0 or H_m <= 0 or wood_density <= 0:
        return 0.0
    x = wood_density * (D_cm**2) * H_m
    AGB = 0.0673 * (x**0.976)
    return max(0.0, AGB)


def biomass_belowground(AGB_kg: float) -> float:
    """
    Belowground biomass using Mokany et al. 2006 root-to-shoot ratio.
    BGB = 0.013 × AGB^1.064 (if AGB < 20)
    BGB = 0.079 × AGB^0.936 (if AGB >= 20)
    """
    if AGB_kg <= 0:
        return 0.0
    if AGB_kg < 20:
        return 0.013 * (AGB_kg**1.064)
    else:
        return 0.079 * (AGB_kg**0.936)


def total_biomass(D_cm: float, H_m: float, wood_density: float = 0.55) -> dict[str, float]:
    """Calculate total biomass components."""
    AGB = biomass_aboveground(D_cm, H_m, wood_density)
    BGB = biomass_belowground(AGB)
    total = AGB + BGB
    carbon = total * CARBON_FRACTION
    co2_sequestered = carbon * CO2_TO_C_RATIO

    return {
        "aboveground_kg": round(AGB, 2),
        "belowground_kg": round(BGB, 2),
        "total_biomass_kg": round(total, 2),
        "carbon_kg": round(carbon, 2),
        "co2_sequestered_kg": round(co2_sequestered, 2),
        "co2_sequestered_tons": round(co2_sequestered / 1000, 4),
    }


# ============================================================================
# Farquhar-von Caemmerer-Berry Photosynthesis Model
# ============================================================================
def farquhar_photosynthesis(
    PAR_umol: float = 1500,  # Photosynthetically Active Radiation (µmol m⁻² s⁻¹)
    T_leaf_C: float = 25.0,  # Leaf temperature (°C)
    CO2_ppm: float = 420.0,  # Atmospheric CO₂ (ppm)
    Vcmax25: float = 80.0,  # Max carboxylation rate at 25°C (µmol m⁻² s⁻¹)
    Jmax25: float = 150.0,  # Max electron transport at 25°C
    Rd25: float = 1.5,  # Dark respiration at 25°C
) -> dict[str, float]:
    """
    Farquhar-von Caemmerer-Berry (FvCB) model of C3 photosynthesis.

    Returns net assimilation (A), carboxylation-limited (Wc),
    RuBP-regeneration-limited (Wj), and related parameters.
    """
    # Temperature corrections using Q10 and Arrhenius
    T_K = T_leaf_C + 273.15
    T_ref = 298.15

    # Activation energies (kJ/mol)
    Ea_Vcmax = 65.33
    Ea_Jmax = 43.54
    Ea_Rd = 46.39
    Ea_Kc = 79.43
    Ea_Ko = 36.38
    Ea_GammaStar = 37.83

    R = 8.314e-3  # Gas constant (kJ/mol/K)

    # Temperature scaling
    def temp_scale(val25, Ea):
        return val25 * math.exp(Ea / R * (1 / T_ref - 1 / T_K))

    Vcmax = temp_scale(Vcmax25, Ea_Vcmax)
    Jmax = temp_scale(Jmax25, Ea_Jmax)
    Rd = temp_scale(Rd25, Ea_Rd)

    # Michaelis-Menten constants
    Kc = temp_scale(404.9, Ea_Kc)  # µmol/mol for CO₂
    Ko = temp_scale(278.4, Ea_Ko)  # mmol/mol for O₂
    GammaStar = temp_scale(42.75, Ea_GammaStar)  # µmol/mol

    O = 210.0  # O₂ concentration (mmol/mol)
    Ci = CO2_ppm * 0.7  # Intercellular CO₂ (approximation)

    # Carboxylation-limited rate (Rubisco-limited)
    Wc = Vcmax * (Ci - GammaStar) / (Ci + Kc * (1 + O / Ko))

    # Light-limited rate (RuBP regeneration)
    # Electron transport rate from light (rectangular hyperbola)
    alpha = 0.24  # Quantum yield
    theta = 0.7  # Curvature
    J2 = Jmax * alpha * PAR_umol
    J = (
        (J2 + Jmax - math.sqrt((J2 + Jmax) ** 2 - 4 * theta * J2 * Jmax)) / (2 * theta)
        if theta > 0
        else min(J2, Jmax)
    )

    Wj = J * (Ci - GammaStar) / (4 * Ci + 8 * GammaStar)

    # Net assimilation (limited by minimum)
    A = min(Wc, Wj) - Rd
    A = max(0, A)  # Can't be negative in steady state for light

    # Quantum yield (actual)
    quantum_yield = A / PAR_umol if PAR_umol > 0 else 0

    # Daily carbon assimilation (assume 12h light period)
    daily_A = A * 3600 * 12 / 1e6  # mol CO₂ m⁻² day⁻¹
    daily_gCO2_m2 = daily_A * 44.01

    return {
        "net_assimilation_umol": round(A, 3),
        "rubisco_limited_Wc": round(Wc, 3),
        "RuBP_limited_Wj": round(Wj, 3),
        "electron_transport_J": round(J, 3),
        "dark_respiration_Rd": round(Rd, 3),
        "quantum_yield": round(quantum_yield, 4),
        "quantum_yield_max_theoretical": 0.125,
        "quantum_efficiency_pct": round(quantum_yield / 0.125 * 100, 1),
        "daily_CO2_g_m2": round(daily_gCO2_m2, 3),
        "GammaStar": round(GammaStar, 2),
        "Vcmax": round(Vcmax, 2),
        "Jmax": round(Jmax, 2),
    }


# ============================================================================
# Soil Carbon - RothC-26.3 Model
# ============================================================================
def rothc_carbon_pools(
    initial_C_tha: float = 40.0,  # Initial soil carbon (t C/ha)
    annual_input_tha: float = 3.0,  # Annual plant residue input
    DPM_RPM_ratio: float = 1.44,  # For agricultural soils
    clay_pct: float = 30.0,  # Soil clay content (%)
    temperature_C: float = 15.0,  # Mean annual temperature
    rainfall_mm: float = 500.0,  # Mean annual rainfall
    years: int = 50,
) -> dict:
    """
    RothC-26.3 model for soil organic carbon dynamics.

    Four active pools: DPM, RPM, BIO, HUM + IOM (inert)
    """
    # Rate modifiers
    # Temperature rate modifier (Arrhenius-like)
    if temperature_C < -5 or temperature_C <= 0:
        temp_modifier = 0.0
    else:
        temp_modifier = 47.91 / (1 + math.exp(106.06 / (18.27 + temperature_C)))

    # Moisture rate modifier
    max_moist_deficit = 20 * (20 + 80 * clay_pct / 100)  # mm
    moisture_modifier = min(1.0, rainfall_mm / (rainfall_mm + max_moist_deficit * 0.5))

    # Plant retention factor
    plant_cover = 0.6

    # Overall rate modifier
    rate_mod = temp_modifier * moisture_modifier * plant_cover

    # Initial pool distribution
    IOM = 0.049 * (initial_C_tha**1.139)  # Falloon equation
    active_C = initial_C_tha - IOM
    HUM = active_C * 0.7
    BIO = active_C * 0.03
    RPM = active_C * 0.15
    DPM = active_C * 0.12

    # Time series
    history = []

    # Annual time steps (RothC uses monthly, simplified to annual)
    dt = 1.0  # year
    for year in range(years + 1):
        total_C = DPM + RPM + BIO + HUM + IOM
        history.append(
            {
                "year": year,
                "total_C_tha": round(total_C, 2),
                "DPM": round(DPM, 3),
                "RPM": round(RPM, 3),
                "BIO": round(BIO, 3),
                "HUM": round(HUM, 3),
                "IOM": round(IOM, 3),
            }
        )

        if year == years:
            break

        # Annual inputs split between DPM and RPM
        DPM_input = annual_input_tha * (DPM_RPM_ratio / (1 + DPM_RPM_ratio))
        RPM_input = annual_input_tha / (1 + DPM_RPM_ratio)

        # Decay
        k_mod = ROTHC_RATES
        DPM_loss = DPM * (1 - math.exp(-k_mod["DPM"] * rate_mod * dt))
        RPM_loss = RPM * (1 - math.exp(-k_mod["RPM"] * rate_mod * dt))
        BIO_loss = BIO * (1 - math.exp(-k_mod["BIO"] * rate_mod * dt))
        HUM_loss = HUM * (1 - math.exp(-k_mod["HUM"] * rate_mod * dt))

        # Decomposition products split
        # 46% to CO₂, 54% to other pools (simplified)
        CO2_fraction = 0.46

        total_loss = DPM_loss + RPM_loss + BIO_loss + HUM_loss
        total_loss * CO2_fraction

        to_BIO = (DPM_loss + RPM_loss) * (1 - CO2_fraction) * 0.46 + (BIO_loss + HUM_loss) * 0.03
        to_HUM = (DPM_loss + RPM_loss) * (1 - CO2_fraction) * 0.54 + (BIO_loss + HUM_loss) * 0.97

        DPM = DPM - DPM_loss + DPM_input
        RPM = RPM - RPM_loss + RPM_input
        BIO = BIO - BIO_loss + to_BIO
        HUM = HUM - HUM_loss + to_HUM

    final = history[-1]
    change = final["total_C_tha"] - initial_C_tha

    return {
        "initial_C_tha": initial_C_tha,
        "final_C_tha": final["total_C_tha"],
        "change_tha": round(change, 2),
        "sequestration_rate_tCO2_ha_yr": round((change / years) * CO2_TO_C_RATIO, 3),
        "pools": final,
        "rate_modifier": round(rate_mod, 3),
        "years_simulated": years,
        "history_sample": history[::5] if len(history) > 10 else history,
    }


# ============================================================================
# Forest Carbon Project Calculation
# ============================================================================
def calculate_project_carbon(
    area_hectares: float,
    species: str = "tropical_moist",
    trees_per_ha: int = 1000,
    avg_diameter_cm: float = 20,
    avg_height_m: float = 12,
    project_years: int = 30,
) -> dict:
    """
    Calculate total carbon sequestration for a forest project.
    """
    # Per-tree biomass
    wood_density = WOOD_DENSITIES.get(species, 0.55)
    tree_biomass = total_biomass(avg_diameter_cm, avg_height_m, wood_density)

    # Per hectare
    per_ha = {
        "biomass_kg": tree_biomass["total_biomass_kg"] * trees_per_ha,
        "carbon_kg": tree_biomass["carbon_kg"] * trees_per_ha,
        "co2_tons": tree_biomass["co2_sequestered_tons"] * trees_per_ha,
    }

    # Total project
    total = {
        "total_trees": int(area_hectares * trees_per_ha),
        "total_biomass_tons": round(per_ha["biomass_kg"] * area_hectares / 1000, 2),
        "total_carbon_tons": round(per_ha["carbon_kg"] * area_hectares / 1000, 2),
        "total_co2_tons": round(per_ha["co2_tons"] * area_hectares, 2),
        "annual_sequestration_tons": round(per_ha["co2_tons"] * area_hectares / project_years, 2),
        "carbon_credits": round(per_ha["co2_tons"] * area_hectares, 0),  # 1 credit = 1 tCO₂
    }

    # Oxygen production (photosynthesis stoichiometry)
    # 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂
    # Mass ratio: O₂/CO₂ = 32/44 = 0.727
    o2_produced_tons = total["total_co2_tons"] * (O2_MOLAR_MASS / CO2_MOLAR_MASS)
    total["oxygen_produced_tons"] = round(o2_produced_tons, 2)

    # Air purification equivalent
    # 1 person breathes ~1 tCO₂/year, produces ~0.3 tO₂/year
    people_breathing = int(total["total_co2_tons"] / project_years)
    total["people_air_purified_annually"] = people_breathing

    return {
        "per_tree": tree_biomass,
        "per_hectare": per_ha,
        "project_total": total,
        "species_used": species,
        "wood_density_g_cm3": wood_density,
    }


# ============================================================================
# Quantum Coherence in Photosynthesis
# ============================================================================
def quantum_efficiency(T_C: float = 25.0) -> dict:
    """
    Calculate quantum coherence efficiency in FMO complex.

    The Fenna-Matthews-Olson (FMO) complex shows near-unity
    quantum efficiency in excitation energy transfer (99.99%).

    This is due to quantum coherence in the 7 bacteriochlorophylls.
    """
    T_K = T_C + 273.15

    # Quantum coherence time (femtoseconds) - Engel et al. 2007
    coherence_time_fs = 660 * math.exp(-T_K / 500)  # Temperature dependent

    # Quantum yield of excitation transfer (Engel et al.)
    # At physiological temperature: ~99.99%
    quantum_yield = 0.9999 * math.exp(-0.001 * (T_K - 298))

    # Compare to classical random walk (much lower efficiency)
    classical_efficiency = 0.70

    # Wavelength of absorbed photons (peak: 800-810 nm)
    peak_wavelength_nm = 806

    # Energy per photon (Planck-Einstein relation)
    h = 6.626e-34  # Planck constant
    c = 2.998e8  # Speed of light
    E_photon = h * c / (peak_wavelength_nm * 1e-9)  # Joules

    return {
        "coherence_time_fs": round(coherence_time_fs, 1),
        "quantum_yield_transfer": round(quantum_yield, 6),
        "classical_efficiency": classical_efficiency,
        "quantum_advantage_pct": round((quantum_yield - classical_efficiency) * 100, 2),
        "peak_wavelength_nm": peak_wavelength_nm,
        "photon_energy_eV": round(E_photon / 1.602e-19, 3),
        "note": "Quantum coherence allows near-perfect energy transfer via superposition",
    }


# ============================================================================
# Evapotranspiration (trees cooling effect)
# ============================================================================
def tree_cooling_effect(
    tree_count: int = 100,
    avg_crown_m2: float = 25.0,
    daily_ET_mm: float = 5.0,
) -> dict:
    """
    Calculate cooling effect of trees via evapotranspiration.

    1 liter of water evaporated = 2.45 MJ cooling energy
    """
    total_crown_m2 = tree_count * avg_crown_m2

    # Water transpired (liters per day)
    # 1 mm ET over 1 m² = 1 liter
    water_liters_day = total_crown_m2 * daily_ET_mm

    # Cooling energy (MJ/day)
    # Latent heat of vaporization: 2.45 MJ/liter
    cooling_MJ_day = water_liters_day * 2.45

    # Equivalent AC units (1 ton AC = 3.5 kW cooling)
    ac_equivalent_kW = cooling_MJ_day * 1000 / 86400 / 3.5

    # Temperature reduction estimate (approximate)
    # Roughly 1°C per 5 liters/m²/day
    temp_reduction_C = daily_ET_mm / 5.0

    return {
        "total_crown_area_m2": round(total_crown_m2, 1),
        "water_transpired_liters_day": round(water_liters_day, 0),
        "cooling_energy_MJ_day": round(cooling_MJ_day, 1),
        "cooling_energy_kWh_day": round(cooling_MJ_day / 3.6, 2),
        "equivalent_AC_units": round(ac_equivalent_kW, 1),
        "temperature_reduction_C": round(temp_reduction_C, 2),
        "note": "Trees act as natural air conditioners through evapotranspiration",
    }


# ============================================================================
# Carbon Credit Verification (standards compliance)
# ============================================================================
STANDARDS = {
    "IPCC_2006": {
        "name": "IPCC 2006 Guidelines",
        "tier": "Tier 2",
        "uncertainty_pct": 20,
        "monitoring_years": 5,
        "permanence_years": 100,
        "additionality_required": True,
        "baseline_scenario": "Without project land use",
    },
    "Verra_VM0047": {
        "name": "Verra VM0047 (Afforestation/Reforestation)",
        "tier": "Project",
        "uncertainty_pct": 15,
        "monitoring_years": 5,
        "permanence_years": 100,
        "additionality_required": True,
        "buffer_pool_pct": 20,
    },
    "Verra_VM0042": {
        "name": "Verra VM0042 (Improved Forest Management)",
        "tier": "Project",
        "uncertainty_pct": 15,
        "monitoring_years": 5,
        "permanence_years": 100,
        "additionality_required": True,
        "buffer_pool_pct": 20,
    },
    "Gold_Standard": {
        "name": "Gold Standard for Global Goals",
        "tier": "Premium",
        "uncertainty_pct": 10,
        "monitoring_years": 5,
        "permanence_years": 40,
        "additionality_required": True,
        "co_benefits_required": True,
        "SDG_alignment": True,
    },
    "ISO_14064_2": {
        "name": "ISO 14064-2 (Project-level GHG)",
        "tier": "Standard",
        "uncertainty_pct": 15,
        "monitoring_years": 3,
        "permanence_years": "N/A",
        "additionality_required": False,
        "verification_required": True,
    },
    "Plan_Vivo": {
        "name": "Plan Vivo Standard",
        "tier": "Community",
        "uncertainty_pct": 20,
        "monitoring_years": 5,
        "permanence_years": 30,
        "additionality_required": True,
        "smallholder_focus": True,
    },
}


def verify_project(
    project_C_tons: float,
    baseline_C_tons: float = 0.0,
    leakage_tons: float = 0.0,
    standard: str = "Verra_VM0047",
) -> dict:
    """
    Verify carbon credits according to standard.
    """
    std = STANDARDS.get(standard, STANDARDS["Verra_VM0047"])

    # Additionality check
    additionality = project_C_tons > baseline_C_tons * 1.1

    # Gross credits (before buffer/leakage)
    gross_credits = max(0, project_C_tons - baseline_C_tons - leakage_tons)

    # Apply uncertainty deduction
    uncertainty_factor = 1 - (std.get("uncertainty_pct", 20) / 100)

    # Apply buffer pool (for permanence risk)
    buffer_pct = std.get("buffer_pool_pct", 20) / 100

    # Net credits
    net_credits = gross_credits * uncertainty_factor * (1 - buffer_pct)

    return {
        "standard": std["name"],
        "gross_credits": round(gross_credits, 2),
        "uncertainty_deduction_pct": std.get("uncertainty_pct", 20),
        "buffer_pool_pct": std.get("buffer_pool_pct", 20),
        "net_credits": round(net_credits, 2),
        "additionality_confirmed": additionality,
        "monitoring_years_required": std.get("monitoring_years", 5),
        "permanence_years_required": std.get("permanence_years", "N/A"),
    }


# ============================================================================
# Main export
# ============================================================================
def get_all_calculations(
    D_cm: float,
    H_m: float,
    species: str,
    area_ha: float,
    trees_per_ha: int,
    project_years: int,
    soil_C_tha: float = 40.0,
    T_C: float = 25.0,
):
    """Comprehensive carbon project calculation."""
    project = calculate_project_carbon(area_ha, species, trees_per_ha, D_cm, H_m, project_years)
    photosynthesis = farquhar_photosynthesis(T_leaf_C=T_C)
    quantum = quantum_efficiency(T_C)
    soil = rothc_carbon_pools(initial_C_tha=soil_C_tha, years=project_years)
    cooling = tree_cooling_effect(project["project_total"]["total_trees"], avg_crown_m2=25)
    verification = verify_project(project["project_total"]["total_co2_tons"])

    return {
        "project_summary": project,
        "photosynthesis": photosynthesis,
        "quantum_efficiency": quantum,
        "soil_carbon": soil,
        "cooling_effect": cooling,
        "verification": verification,
        "available_standards": list(STANDARDS.keys()),
        "scientific_references": [
            "Chave et al. 2014 - Improved allometric models",
            "Farquhar et al. 1980 - Biochemical model of C3 photosynthesis",
            "Engel et al. 2007 - Quantum coherence in FMO complex",
            "Coleman et al. 1996 - RothC-26.3 model",
            "IPCC 2006 Guidelines for National GHG Inventories",
        ],
    }
