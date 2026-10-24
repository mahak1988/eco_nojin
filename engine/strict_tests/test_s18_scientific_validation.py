"""S18 -- Scientific Validation Register: gateway models against independent
references.

Every expected value in this module is re-derived from an *independent*
implementation of the published equation, law or table, written from the
primary source. No expectation is copied from the engine's own code: a test
that restates the implementation cannot validate it (قاعدهٔ ۳ of
HYDROMA-QA-001). Where the engine rounds its output, the tolerance is the
documented rounding granularity, never a loosened scientific claim.

Sources
-------
SAR, ESP, sodic/salinity thresholds : USDA Handbook 60 (1954) / Salinity Lab
Leaching requirement                : FAO-29 (Rhoades/van der Molen)
van Genuchten retention             : van Genuchten (1980)
Carsel & Parrish parameters         : Carsel & Parrish (1988), table values
AWC = theta(FC) - theta(PWP)        : definitional (FC -33 kPa, PWP -1500 kPa)
Compost mix C:N                     : mass balance (closed form)
SOC stock                           : SOC% x BD x depth x (1 - stone) / 10
Rational method                     : Qp = C i A / 360 (SI), C = 0.6 FAO default
Check-dam storage / spillway        : trapezoid V = L(Bh + z h^2/2);
                                       broad-crested weir W = Qp / (Cd H^1.5)
Price-risk VaR                      : z0.95 sigma P sqrt(T), standard normal
NPV                                 : discounted sum with t = 0
"""

from __future__ import annotations

import math
from typing import Any, cast

import pytest

from engine.gateway import (
    EngineGateway,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
)

GW = EngineGateway()
PROV = ProvenanceSpec(source="s18", source_type="TEST")

# Carsel & Parrish (1988) van Genuchten parameters for loam; the same table
# the compiled soil kernel embeds (verified there at 1e-12).
LOAM = {"theta_r": 0.078, "theta_s": 0.43, "alpha": 0.036, "n": 1.56}


def _values(model_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    r = GW.execute(
        GatewayRequest(model_id=model_id, inputs=inputs, input_units={}, provenance=PROV)
    )
    assert isinstance(r, GatewayResult), (
        f"{model_id}: gateway returned {r.error_code}: {r.message}"
    )
    return r.values


# --------------------------------------------------------------------------- #
# Soil chemistry and salinity -- USDA Handbook 60 / FAO-29                     #
# --------------------------------------------------------------------------- #
class TestSoilChemistryIndependent:
    def test_sar_matches_the_usda_definition(self) -> None:
        """SAR = Na / sqrt((Ca + Mg) / 2) -- USDA Salinity Laboratory."""
        na, ca, mg = 10.0, 4.0, 2.0
        got = _values("SOIL_SAR", {"na": na, "ca": ca, "mg": mg})
        assert got["sar"] == pytest.approx(na / math.sqrt((ca + mg) / 2), abs=0.005)

    def test_sar_rejects_negative_ion_concentrations(self) -> None:
        r = GW.execute(
            GatewayRequest(
                model_id="SOIL_SAR",
                inputs={"na": -1.0, "ca": 1.0, "mg": 1.0},
                input_units={},
                provenance=PROV,
            )
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "EXECUTION_ERROR"

    def test_esp_matches_na_over_cec_and_reports_both_thresholds(self) -> None:
        """ESP = 100 * exchangeable Na / CEC; USDA Handbook 60 defines sodic
        at ESP >= 15, the management/amendment line at 10."""
        got = _values("SOIL_ESP", {"na": 6.0, "cex": 20.0})
        assert got["esp"] == pytest.approx(30.0)
        assert got["threshold"] == 15.0
        assert got["amendment_threshold"] == 10.0
        assert got["classification"] == "sodic"

    @pytest.mark.parametrize(
        "ec,classification",
        [(0.5, "non_saline"), (3.0, "slightly_saline"), (6.0, "moderately_saline"),
         (12.0, "strongly_saline"), (20.0, "very_strongly_saline")],
    )
    def test_salinity_classes_follow_usda_handbook_60(
        self, ec: float, classification: str
    ) -> None:
        got = _values("SOIL_SALINITY_CLASSIFY", {"ec": ec})
        assert got["classification"] == classification

    def test_leaching_requirement_matches_fao29(self) -> None:
        """LR = EC_water / (5 * EC_target - EC_water) (FAO-29)."""
        ec_water, ec_target = 1.5, 4.0
        got = _values(
            "SOIL_LEACHING",
            {"ec_soil": 6.0, "ec_water": ec_water, "target_ec": ec_target},
        )
        assert got["leaching_fraction"] == pytest.approx(
            ec_water / (5 * ec_target - ec_water), abs=0.001
        )

    def test_gypsum_requirement_is_linear_in_amended_depth(self) -> None:
        """The internal rate is a calibration, not a published constant, so
        the checkable laws are the depth linearity and the ESP trigger."""
        shallow = _values("SOIL_AMENDMENT", {"esp": 15.0, "soil_depth": 15.0})
        deep = _values("SOIL_AMENDMENT", {"esp": 15.0, "soil_depth": 30.0})
        assert shallow["gypsum_kg_per_ha"] == pytest.approx(deep["gypsum_kg_per_ha"] / 2)
        assert shallow["units"] == "kg/ha", "the envelope must report the engine's unit"

    def test_amendment_triggers_at_the_usda_sodic_line(self) -> None:
        below = _values("SOIL_AMENDMENT", {"esp": 8.0, "soil_depth": 15.0})
        at = _values("SOIL_AMENDMENT", {"esp": 15.0, "soil_depth": 15.0})
        assert not below["gypsum_required"]
        assert at["gypsum_required"]


# --------------------------------------------------------------------------- #
# Soil physics -- van Genuchten (1980) with Carsel & Parrish (1988) params     #
# --------------------------------------------------------------------------- #
class TestSoilRetentionIndependent:
    def test_loam_theta_at_100cm_matches_van_genuchten(self) -> None:
        h = -100.0
        p = LOAM
        m = 1 - 1 / p["n"]
        reference = p["theta_r"] + (p["theta_s"] - p["theta_r"]) / (
            1 + abs(p["alpha"] * h) ** p["n"]
        ) ** m
        got = _values(
            "CANON-006",
            {"matric_potential": h, "theta_r": p["theta_r"], "theta_s": p["theta_s"],
             "vg_alpha": p["alpha"], "vg_n": p["n"]},
        )
        assert got["van_genuchten_theta"] == pytest.approx(reference, rel=1e-12)

    def test_saturation_and_dry_endpoints(self) -> None:
        """theta(0) = theta_s exactly; theta approaches theta_r as the soil
        dries (asymptotic, never below it)."""
        p = LOAM
        saturated = _values(
            "CANON-006",
            {"matric_potential": 0.0, "theta_r": p["theta_r"], "theta_s": p["theta_s"],
             "vg_alpha": p["alpha"], "vg_n": p["n"]},
        )
        assert saturated["van_genuchten_theta"] == pytest.approx(p["theta_s"], rel=1e-12)
        dry = _values(
            "CANON-006",
            {"matric_potential": -1e6, "theta_r": p["theta_r"], "theta_s": p["theta_s"],
             "vg_alpha": p["alpha"], "vg_n": p["n"]},
        )
        # Asymptotic approach: within 2 % of theta_r, and never below it.
        assert dry["van_genuchten_theta"] >= p["theta_r"]
        assert dry["van_genuchten_theta"] == pytest.approx(p["theta_r"], rel=2e-2)
        # Monotone drainage: wetting raises theta.
        mid = _values(
            "CANON-006",
            {"matric_potential": -100.0, "theta_r": p["theta_r"], "theta_s": p["theta_s"],
             "vg_alpha": p["alpha"], "vg_n": p["n"]},
        )
        assert p["theta_r"] < dry["van_genuchten_theta"] < mid["van_genuchten_theta"]
        assert mid["van_genuchten_theta"] < p["theta_s"]

    def test_awc_is_theta_fc_minus_theta_pwp_for_loam(self) -> None:
        """AWC = theta(FC) - theta(PWP) at the engine's documented heads
        (33 cm and 15000 cm of water), re-derived from the van Genuchten
        closed form. S05 pins these heads against the Saxton & Rawls (2006)
        AWC table for all twelve textures."""
        p = LOAM
        m = 1 - 1 / p["n"]

        def theta(h: float) -> float:
            theta_val: float = p["theta_r"] + (p["theta_s"] - p["theta_r"]) / (
                1 + abs(p["alpha"] * h) ** p["n"]
            ) ** m
            return theta_val

        reference = theta(-33.0) - theta(-15000.0)
        got = _values("SOIL_AWC", {"texture_class": "loam"})
        assert got["awc"] == pytest.approx(reference, rel=1e-9)

    def test_awc_orders_textures_by_the_published_ranking(self) -> None:
        """Coarser textures hold less plant-available water: AWC must fall
        from silt loam through loam and sandy loam to sand."""
        values = {}
        for texture in ("silt_loam", "loam", "sandy_loam", "sand"):
            values[texture] = _values("SOIL_AWC", {"texture_class": texture})["awc"]
        ordering = [values[t] for t in ("silt_loam", "loam", "sandy_loam", "sand")]
        assert ordering == sorted(ordering, reverse=True), ordering


# --------------------------------------------------------------------------- #
# Mass balance and composition                                               #
# --------------------------------------------------------------------------- #
class TestMassBalance:
    MATERIALS = [
        {"name": "straw", "mass_kg": 100.0, "carbon_content": 0.45, "nitrogen_content": 0.005},
        {"name": "manure", "mass_kg": 50.0, "carbon_content": 0.35, "nitrogen_content": 0.02},
    ]

    def test_compost_mix_cn_is_the_mass_weighted_mean(self) -> None:
        total_mass = sum(cast(float, m["mass_kg"]) for m in self.MATERIALS)
        carbon = sum(
            cast(float, m["mass_kg"]) * cast(float, m["carbon_content"])
            for m in self.MATERIALS
        )
        nitrogen = sum(
            cast(float, m["mass_kg"]) * cast(float, m["nitrogen_content"])
            for m in self.MATERIALS
        )
        reference = (carbon / total_mass) / (nitrogen / total_mass)
        got = _values("COMPOST_CN", {"materials": self.MATERIALS})
        assert got["cn_ratio"] == pytest.approx(reference, rel=1e-12)

    def test_soc_stock_is_the_bulk_density_integral(self) -> None:
        """SOC stock (t C/ha) = SOC% x BD (g/cm3) x depth (cm) x 100.

        The x100 is the g/cm2-to-t/ha conversion for one hectare: 1 g/cm2 of
        soil over 1 ha is 100 t. A 1.5 % SOC soil at BD 1.3 over 0-30 cm holds
        58.5 t C/ha, the canonical order of magnitude for a topsoil.
        """
        soc_pct, bd, depth_m = 1.5, 1.3, 0.3
        depth_cm = depth_m * 100.0
        reference = soc_pct / 100.0 * bd * depth_cm * 100.0
        assert reference == pytest.approx(58.5)
        got = _values(
            "MRV_METRICS",
            {"soc_pct": soc_pct, "depth_m": depth_m, "bulk_density_g_cm3": bd,
             "rainfall_mm": 600.0, "slope_length_m": 22.0, "slope_percent": 8.0},
        )
        assert got["mrv"]["soc_stock_tha"] == pytest.approx(reference, rel=1e-12)


# --------------------------------------------------------------------------- #
# Watershed design -- rational method and structure geometry (FAO)            #
# --------------------------------------------------------------------------- #
class TestWatershedDesignIndependent:
    """The routes used to forward ``drainage_area_ha`` into the slope-percent
    slot and ``peak_flow`` into the area slot, so a plausible request silently
    designed a dam for a 1.5 m2 catchment on a 50 % slope (S18 R-6). These
    checks re-derive the whole sizing chain from the rational method.
    """

    AREA_HA = 5.0
    SLOPE_PCT = 15.0
    RAINFALL_MM = 120.0

    def _design(self) -> dict[str, Any]:
        return _values(
            "WATERSHED_CHECK_DAM",
            {
                "drainage_area_ha": self.AREA_HA,
                "slope": self.SLOPE_PCT / 100.0,
                "rainfall_mm": self.RAINFALL_MM,
            },
        )

    def test_peak_flow_is_the_rational_method_value(self) -> None:
        """Qp = C i A / 360 with C = 0.6, i = rainfall / storm duration."""
        intensity = self.RAINFALL_MM / 6.0  # 6 h default design storm
        qp = 0.6 * intensity * self.AREA_HA / 360.0
        design = self._design()
        # The design head and width must return exactly this peak flow
        # through the broad-crested weir law W = Qp / (Cd H^1.5).
        head = design["design_head_m"]
        width = design["spillway_width_m"]
        q_reconstructed = 1.7 * head**1.5 * width
        assert q_reconstructed == pytest.approx(qp, rel=0.02)

    def test_storage_is_the_sediment_volume_for_the_retention_period(self) -> None:
        """V = assumed_TE x (yield x area / bulk density) x years, solved
        through the trapezoid geometry V = L (B h + z h^2 / 2)."""
        annual_sediment = 5.0 * self.AREA_HA / 1.3  # t/ha/yr, 1.3 t/m3 bulk density
        storage = 0.8 * annual_sediment * 10.0  # ASSUMED_TRAP_EFFICIENCY x 10 yr
        design = self._design()
        length = design["dam_length_m"]
        height = design["dam_height_m"]
        channel_width = 5.0
        z = 1.5
        geometry = length * (channel_width * height + z * height**2 / 2)
        assert geometry == pytest.approx(storage, rel=0.05)

    def test_dam_length_is_fao_minimum_of_twice_the_channel(self) -> None:
        assert self._design()["dam_length_m"] == pytest.approx(10.0)

    def test_structure_route_resolves_the_same_geometry(self) -> None:
        """The structuring route must agree with the dedicated check-dam
        route for identical inputs (they share one design function)."""
        dedicated = self._design()
        generic = _values(
            "WATERSHED_STRUCT",
            {
                "structure_type": "check_dam",
                "drainage_area_ha": self.AREA_HA,
                "slope": self.SLOPE_PCT / 100.0,
                "rainfall_mm": self.RAINFALL_MM,
            },
        )
        assert generic["dam_height_m"] == pytest.approx(dedicated["dam_height_m"], rel=1e-6)
        assert generic["spillway_width_m"] == pytest.approx(
            dedicated["spillway_width_m"], rel=1e-6
        )

    def test_area_and_slope_are_never_silently_defaulted(self) -> None:
        r = GW.execute(
            GatewayRequest(
                model_id="WATERSHED_CHECK_DAM",
                inputs={"peak_flow": 1.5},
                input_units={},
                provenance=PROV,
            )
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "INVALID_REQUEST"
        errors = " ".join(r.validation_errors or [])
        assert "slope" in errors and "area" in errors.replace("area_m2", "area")


# --------------------------------------------------------------------------- #
# Economics -- closed forms                                                    #
# --------------------------------------------------------------------------- #
class TestEconomicsIndependent:
    def test_price_risk_var_is_the_normal_quantile(self) -> None:
        """VaR = z_{0.95} sigma P sqrt(T) for a lognormal price model."""
        z95 = 1.6448536269514722
        price, vol, years = 200.0, 0.15, 1
        got = _values(
            "ECON_PRICE_RISK",
            {"base_price": price, "volatility": vol, "time_horizon_years": years},
        )
        assert got["value_at_risk_irr"] == pytest.approx(z95 * vol * price, abs=0.01)

    def test_npv_discounts_the_first_flow_at_t0(self) -> None:
        got = _values(
            "ECON_NPV",
            {"cash_flows": [-1000.0, 300.0, 400.0, 500.0], "discount_rate": 0.1},
        )
        reference = -1000 + 300 / 1.1 + 400 / 1.21 + 500 / 1.331
        assert got["npv"] == pytest.approx(reference, rel=1e-12)

    def test_yield_risk_revenue_is_the_product_of_its_factors(self) -> None:
        got = _values(
            "ECON_YIELD_RISK",
            {"expected_yield": 4.2, "yield_std_dev": 0.5, "area_hectares": 10.0,
             "price_per_unit": 200.0},
        )
        assert got["expected_total_revenue_irr"] == pytest.approx(4.2 * 10.0 * 200.0)
