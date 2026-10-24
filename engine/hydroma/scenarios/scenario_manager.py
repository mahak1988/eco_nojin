"""
Scenario Management Engine.

Orchestrates the definition, execution, and storage of various scenarios
(e.g., climate, crop management, infrastructure).
"""

import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

from engine.hydroma.economics.integration import calculate_agricultural_project_economics
from engine.hydroma.risk.assessment import perform_comprehensive_risk_analysis
from engine.hydroma.scenarios.climate_scenarios import get_climate_projection
from engine.hydroma.scenarios.crop_scenarios import simulate_crop_yield
from engine.hydroma.simulation.contracts import ScenarioParams
from engine.hydroma.simulation.orchestrator import ChainInputs, run_chain
from engine.ports import SessionFactory, default_session_factory, resolve_database_attr

logger = logging.getLogger(__name__)

#: RUSLE and RothC inputs the orchestrator's ``ChainInputs`` contract requires
#: and a land profile does not carry. They are module constants, not per-call
#: guesses, so a run is reproducible; a profile that does carry a real value
#: (``r_factor``, ``k_factor``, ``ls_factor``, ``c_factor_base``,
#: ``initial_soc_t_ha``, ``clay_pct``) always wins over the default.
_DEFAULT_CHAIN_FACTORS: dict[str, float] = {
    "r_factor": 1200.0,  # rainfall erosivity (MJ mm ha-1 h-1 yr-1)
    "k_factor": 0.03,  # soil erodibility (t h MJ-1 mm-1)
    "ls_factor": 1.4,  # slope length/steepness factor
    "c_factor_base": 0.3,  # baseline cover-management factor
    "initial_soc_t_ha": 25.0,  # soil organic carbon (t/ha)
    "clay_pct": 22.0,  # clay content (%)
}


def _as_dict(value: Any) -> dict[str, Any]:
    """Return ``value`` when it is a mapping, otherwise an empty dict."""
    return value if isinstance(value, dict) else {}


def _finite(value: Any, default: float = 0.0) -> float:
    """Coerce to a finite float, returning ``default`` for anything else."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _number(value: Any) -> float | None:
    """Finite float or ``None``, so chain output stays JSON-storable."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _positive(profile: dict[str, Any], name: str) -> float:
    """Read a strictly positive chain factor, else its documented default."""
    value = _finite(profile.get(name), _DEFAULT_CHAIN_FACTORS[name])
    return value if value > 0 else _DEFAULT_CHAIN_FACTORS[name]


def _optional_coordinate(profile: dict[str, Any], name: str, limit: float) -> float | None:
    """Read a latitude/longitude within its valid range, else ``None``.

    Out-of-range values are dropped rather than passed on, so a malformed
    profile degrades to synthetic weather instead of a pydantic validation
    error inside the orchestrator.
    """
    if profile.get(name) is None:
        return None
    value = _finite(profile.get(name), float("nan"))
    if not math.isfinite(value) or abs(value) > limit:
        return None
    return value


def _resolve_chain_inputs(land_profile: dict[str, Any]) -> ChainInputs:
    """Map a land profile onto the orchestrator's ``ChainInputs`` contract."""
    profile = land_profile if isinstance(land_profile, dict) else {}

    area_hectares = _finite(profile.get("area_hectares"), 1.0)
    if area_hectares <= 0:
        area_hectares = 1.0

    # c_factor_base is a valid zero (complete ground cover), so it is not
    # routed through the "must be positive" default resolution.
    c_default = _DEFAULT_CHAIN_FACTORS["c_factor_base"]
    c_factor_base = min(1.0, _finite(profile.get("c_factor_base"), c_default))
    clay_default = _DEFAULT_CHAIN_FACTORS["clay_pct"]
    clay_pct = min(100.0, max(0.0, _finite(profile.get("clay_pct"), clay_default)))

    return ChainInputs(
        site_id=str(profile.get("id") or profile.get("land_profile_id") or "scenario-site"),
        area_ha=area_hectares,
        scenario=ScenarioParams(
            name="Baseline", cn_change=0.0, c_factor_factor=1.0, p_factor=1.0
        ),
        r_factor=_positive(profile, "r_factor"),
        k_factor=_positive(profile, "k_factor"),
        ls_factor=_positive(profile, "ls_factor"),
        c_factor_base=c_factor_base,
        crop=str(profile.get("crop") or "Wheat"),
        soil_type=str(profile.get("soil_type") or "SiltLoam"),
        initial_soc_t_ha=_positive(profile, "initial_soc_t_ha"),
        clay_pct=clay_pct,
        residue_c_t_ha_per_month=max(
            0.0, _finite(profile.get("residue_c_t_ha_per_month"), 0.0)
        ),
        years=1,
        # The land profile's own coordinates, when it carries them. Weather
        # stays synthetic: use_real_weather=False keeps this path offline and
        # reproducible, and run_chain only fetches when the flag is set.
        lat=_optional_coordinate(profile, "location_lat", 90.0),
        lon=_optional_coordinate(profile, "location_lon", 180.0),
        use_real_weather=False,
    )


def run_simulation_chain(land_profile: dict[str, Any]) -> dict[str, Any]:
    """Run the real simulation chain for one land profile.

    ``scenario_manager`` used to import a ``run_simulation_chain`` from
    ``engine.hydroma.simulation.orchestrator`` that the module never defined —
    its entry point is ``run_chain(ChainInputs)`` — so this call site was
    dead. This adapter is the bridge: it maps a land profile onto the
    orchestrator's contract, runs the chain, and returns the flat
    ``<Model>Output`` mapping the rest of this module consumes.

    The chain's own provenance and status are carried through, including the
    steps it reported as ``not_computed`` (SWAT+ hydrology needs an external
    binary), rather than being flattened into numbers.
    """
    result = run_chain(_resolve_chain_inputs(land_profile))
    outputs = _as_dict(result.outputs)
    aquacrop = _as_dict(outputs.get("aquacrop"))
    rusle = _as_dict(outputs.get("rusle"))
    rothc = _as_dict(outputs.get("rothc"))

    aquacrop_out: dict[str, Any] = {
        "crop": aquacrop.get("crop"),
        "yield_kg_ha": _number(aquacrop.get("yield_kg_ha")),
        "biomass_kg_ha": _number(aquacrop.get("biomass_kg_ha")),
        "data_source": aquacrop.get("data_source"),
        "model": aquacrop.get("model"),
        "weather_source": aquacrop.get("weather_source"),
    }
    # The economics call reads ``AquaCropOutput.yield_t_ha`` with a 3.0 t/ha
    # fallback, so the key is only added when the model produced a number.
    yield_kg_ha = _number(aquacrop.get("yield_kg_ha"))
    if yield_kg_ha is not None and yield_kg_ha > 0:
        aquacrop_out["yield_t_ha"] = yield_kg_ha / 1000.0

    not_computed = {
        key: {
            "status": _as_dict(outputs.get(key)).get("status"),
            "reason": _as_dict(outputs.get(key)).get("reason"),
        }
        for key in ("swat_plus", "weap", "hecras")
        if _as_dict(outputs.get(key)).get("status") == "not_computed"
    }

    return {
        "AquaCropOutput": aquacrop_out,
        "RUSLEOutput": {
            "erosion_before_t_ha": _number(rusle.get("erosion_before_t_ha")),
            "erosion_after_t_ha": _number(rusle.get("erosion_after_t_ha")),
            "reduction_pct": _number(rusle.get("reduction_pct")),
            "data_source": rusle.get("data_source"),
            "model": rusle.get("model"),
        },
        "RothCOutput": {
            "soc_before_t_ha": _number(rothc.get("soc_before_t_ha")),
            "soc_after_t_ha": _number(rothc.get("soc_after_t_ha")),
            "soc_change_t_ha_yr": _number(rothc.get("soc_change_t_ha_yr")),
            "co2e_t_ha": _number(rothc.get("co2e_t_ha")),
            "data_source": rothc.get("data_source"),
            "model": rothc.get("model"),
        },
        "NotComputed": not_computed,
        "chain_status": result.status,
        "chain_message": result.message,
    }


class ScenarioType(Enum):
    CLIMATE_CHANGE = "climate_change"
    CROP_MANAGEMENT = "crop_management"
    INFRASTRUCTURE_DEVELOPMENT = "infrastructure_development"
    BIOFERTILIZER_APPLICATION = "biofertilizer_application"
    COMBINED = "combined"


@dataclass
class ScenarioDefinition:
    """Defines a single scenario."""

    project_id: str
    scenario_name: str
    scenario_type: ScenarioType
    baseline_scenario_id: str | None = None
    description: str = ""
    assumptions: dict[str, Any] | None = None
    # e.g., {"temp_change_degC": 2.0, "rainfall_change_percent": -10}
    parameters: dict[str, Any] | None = None


class ScenarioManager:
    """Main class for managing scenarios."""

    def __init__(self, session_factory: SessionFactory | None = None):
        """
        Args:
            session_factory: Source of the persistence session. Defaults to
                ``database.config.SessionLocal``, resolved on first use rather
                than at import.
        """
        self._session_factory = session_factory
        # The generators that actually exist in the sibling modules. The
        # previous names (``generate_climate_scenario`` /
        # ``define_crop_scenario``) were never defined by them, so building
        # this dict raised ImportError and the whole module was unimportable.
        self.known_types = {
            ScenarioType.CLIMATE_CHANGE: get_climate_projection,
            ScenarioType.CROP_MANAGEMENT: simulate_crop_yield,
            # Add more as needed
        }

    def _session(self):
        """Open a session, resolving the default factory on first call."""
        factory = self._session_factory or default_session_factory()
        return factory()

    def create_scenario(self, definition: ScenarioDefinition) -> str:
        """Creates a new scenario record in the database."""
        logger.info(
            f"Creating scenario '{definition.scenario_name}' for project {definition.project_id}"
        )
        scenario_db = resolve_database_attr("models", "ScenarioDB")
        db_scenario = scenario_db(
            project_id=definition.project_id,
            scenario_name=definition.scenario_name,
            scenario_type=definition.scenario_type.value,
            baseline_scenario_id=definition.baseline_scenario_id,
            description=definition.description,
            assumptions=definition.assumptions or {},
            parameters=definition.parameters or {},
            status="created",
            created_by="System",
        )
        db = self._session()
        try:
            db.add(db_scenario)
            db.commit()
            logger.info(f"Scenario '{definition.scenario_name}' created with ID {db_scenario.id}.")
            return str(db_scenario.id)
        except Exception as e:
            logger.error(f"Failed to create scenario: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def run_scenario(self, scenario_id: str, land_profile_data: dict[str, Any]) -> dict[str, Any]:
        """Executes a scenario by retrieving its definition and running the simulation chain."""
        logger.info(f"Running scenario with ID {scenario_id}")
        scenario_db = resolve_database_attr("models", "ScenarioDB")
        scenario_result_db = resolve_database_attr("models", "ScenarioResultDB")
        db = self._session()
        try:
            scenario = db.query(scenario_db).filter(scenario_db.id == scenario_id).first()
            if not scenario:
                raise ValueError(f"Scenario with ID {scenario_id} not found.")

            scenario_type = ScenarioType(scenario.scenario_type)
            scenario_params = scenario.parameters

            # --- Apply Scenario Modifications ---
            # This is a critical part where the scenario parameters modify the land profile or inputs
            modified_inputs = self._apply_modifications(
                land_profile_data, scenario_type, scenario_params
            )

            # --- Execute Simulation Chain ---
            logger.info("Starting simulation chain for scenario...")
            simulation_outputs = run_simulation_chain(modified_inputs)

            # --- Calculate Economics ---
            logger.info("Calculating economics for scenario...")
            # This requires outputs from sim chain (e.g., yield) and inputs (e.g., costs).
            # For simplicity, we use a placeholder.
            economic_analysis = calculate_agricultural_project_economics(
                land_profile_data=modified_inputs,
                crop_advisor_output={
                    "top_recommendations": [
                        {
                            "name_en": "Wheat",
                            "yield_t_ha": simulation_outputs.get("AquaCropOutput", {}).get(
                                "yield_t_ha", 3.0
                            ),
                        }
                    ]
                },
                biofertilizer_output={"recommendations": []},
                market_data={"commodity_price_per_ton_irr": 2000000},
                costing_params={"labor_cost_per_hour_irr": 20000, "bio_fert_cost_per_kg_irr": 1000},
                roi_params={"discount_rate": 0.08, "projection_years": 10},
                risk_params={"price_volatility": 0.15, "yield_std_dev": 0.3},
            )

            # --- Perform Risk Analysis ---
            logger.info("Performing risk analysis for scenario...")
            risk_analysis = perform_comprehensive_risk_analysis(
                simulation_outputs, economic_analysis
            )

            # --- Store Results ---
            result_data = {
                "simulation_outputs": simulation_outputs,
                "economic_analysis": economic_analysis,
                "risk_analysis": risk_analysis,
            }

            db_result = scenario_result_db(
                scenario_id=scenario_id,
                result_type="full_analysis",  # More granular types possible
                result_data=result_data,
                # Uncertainty could be derived from Monte Carlo or sensitivity analysis
                uncertainty_data={},
                confidence_level=0.9,  # Placeholder
            )
            db.add(db_result)
            db.commit()

            logger.info(f"Scenario {scenario_id} run completed and results stored.")
            return result_data

        except Exception as e:
            logger.error(f"Failed during scenario run: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def _apply_modifications(
        self, land_profile: dict[str, Any], scenario_type: ScenarioType, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Applies scenario-specific modifications to the base land profile or input data."""
        modified = land_profile.copy()

        if scenario_type == ScenarioType.CLIMATE_CHANGE:
            # Modify climate data within the land profile based on params
            temp_shift = params.get("temp_change_degC", 0.0)
            precip_change = params.get("rainfall_change_percent", 0.0)
            # This is a simplified example. In reality, this might modify a separate climate data object.
            # For now, we'll add them to the modified profile for downstream use.
            modified["scenario_climate_shifts"] = {
                "temp_change_degC": temp_shift,
                "precip_change_percent": precip_change,
            }
        elif scenario_type == ScenarioType.CROP_MANAGEMENT:
            # Modify crop choice, irrigation, etc.
            modified["scenario_crop_choice"] = params.get("crop_type", "default")
            modified["scenario_management_practice"] = params.get("practice", "traditional")

        # Add logic for other scenario types (INFRASTRUCTURE_DEVELOPMENT, etc.)

        return modified

    def compare_scenarios(self, scenario_ids: list[str]) -> dict[str, Any]:
        """Compares results from multiple scenarios."""
        logger.info(f"Comparing scenarios: {scenario_ids}")
        comparisons = {}
        for sid in scenario_ids:
            scenario_result_db = resolve_database_attr("models", "ScenarioResultDB")
            db = self._session()
            try:
                result = (
                    db.query(scenario_result_db)
                    .filter(scenario_result_db.scenario_id == sid)
                    .first()
                )
                if result:
                    # Extract key metrics for comparison (e.g., yield, NPV, risk score)
                    sim_out = result.result_data.get("simulation_outputs", {})
                    econ_out = result.result_data.get("economic_analysis", {})
                    risk_out = result.result_data.get("risk_analysis", {})

                    comparisons[sid] = {
                        "yield_t_ha_avg": sim_out.get("AquaCropOutput", {}).get("yield_t_ha", 0),
                        "npv_irr": econ_out.get("roi", {}).get("npv_irr", 0),
                        "projected_risk_score": risk_out.get("overall_risk_score", 1.0),
                        # Add more metrics as needed
                    }
            finally:
                db.close()
        return comparisons
