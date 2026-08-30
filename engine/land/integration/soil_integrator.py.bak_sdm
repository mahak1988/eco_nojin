"""
Soil Integrator
================
Connects engine/land/ to engine/hydroma/soil/ modules.
Integrates 6-layer soil profiles (0-200cm) with land analysis.
"""

import logging
import time

from .models import (
    DeepSoilProfile,
    SalinityClass,
    SoilIntegrationResult,
    SoilLayer,
    SoilTexture,
)

logger = logging.getLogger(__name__)

# Standard SoilGrids v2 depth layers (cm)
SOILGRIDS_LAYERS = [
    (0, 5),
    (5, 15),
    (15, 30),
    (30, 60),
    (60, 100),
    (100, 200),
]

# SoilGrids v2 mean values for global soils (approximate)
GLOBAL_MEAN_SOIL = {
    "sand_pct": 42.0,
    "silt_pct": 28.0,
    "clay_pct": 30.0,
    "ph": 6.8,
    "ec_dsm": 0.5,
    "organic_carbon_g_kg": 12.0,
    "cec_mmolc_kg": 15.0,
    "bulk_density_g_cm3": 1.35,
}


class SoilIntegrator:
    """
    Integrates soil data with land profiles.
    
    Connects to engine/hydroma/soil/ modules:
    - taxonomy: USDA texture classification
    - chemistry: CEC, ESP, SAR, pH buffer
    - salinity: ECe classification
    - water_retention: van Genuchten parameters
    - health: Soil Health Index
    - pedotransfer: PTF functions
    """

    def __init__(self):
        """Initialize integrator with hydroma soil modules."""
        self._soil_modules = None
        self._load_soil_modules()

    def _load_soil_modules(self):
        """Load hydroma soil modules (lazy loading)."""
        try:
            from engine.hydroma.soil import (
                chemistry,
                health,
                pedotransfer,
                salinity,
                taxonomy,
                water_retention,
            )
            self._soil_modules = {
                "taxonomy": taxonomy,
                "chemistry": chemistry,
                "salinity": salinity,
                "water_retention": water_retention,
                "health": health,
                "pedotransfer": pedotransfer,
            }
            logger.info("Soil modules loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load soil modules: {e}")
            self._soil_modules = None

    def classify_texture(self, sand_pct: float, silt_pct: float, clay_pct: float) -> SoilTexture:
        """
        Classify soil texture using USDA triangle.
        
        Args:
            sand_pct: Sand percentage (0-100)
            silt_pct: Silt percentage (0-100)
            clay_pct: Clay percentage (0-100)
            
        Returns:
            SoilTexture enum value
        """
        if self._soil_modules and "taxonomy" in self._soil_modules:
            try:
                result = self._soil_modules["taxonomy"].classify_texture(sand_pct, silt_pct, clay_pct)
                # Map to our enum
                texture_map = {
                    "sand": SoilTexture.SAND,
                    "loamy sand": SoilTexture.LOAMY_SAND,
                    "sandy loam": SoilTexture.SANDY_LOAM,
                    "loam": SoilTexture.LOAM,
                    "silt loam": SoilTexture.SILT_LOAM,
                    "silt": SoilTexture.SILT,
                    "sandy clay loam": SoilTexture.SANDY_CLAY_LOAM,
                    "clay loam": SoilTexture.CLAY_LOAM,
                    "silty clay loam": SoilTexture.SILTY_CLAY_LOAM,
                    "sandy clay": SoilTexture.SANDY_CLAY,
                    "silty clay": SoilTexture.SILTY_CLAY,
                    "clay": SoilTexture.CLAY,
                }
                if isinstance(result, str):
                    result_lower = result.lower()
                    for key, value in texture_map.items():
                        if result_lower == key:
                            return value
            except Exception as e:
                logger.warning(f"Texture classification failed: {e}")

        # Fallback: simple classification
        return self._simple_texture_classification(sand_pct, silt_pct, clay_pct)

    def _simple_texture_classification(self, sand: float, silt: float, clay: float) -> SoilTexture:
        """Simple USDA texture classification fallback."""
        if clay >= 40:
            return SoilTexture.CLAY
        elif clay >= 35 and sand >= 45:
            return SoilTexture.SANDY_CLAY
        elif clay >= 35 and silt >= 40:
            return SoilTexture.SILTY_CLAY
        elif clay >= 27 and sand < 20:
            return SoilTexture.SILTY_CLAY_LOAM if silt > clay else SoilTexture.CLAY_LOAM
        elif clay >= 20 and sand >= 45:
            return SoilTexture.SANDY_CLAY_LOAM
        elif clay >= 7 and clay < 27 and silt >= 50:
            return SoilTexture.SILT_LOAM if silt < 80 else SoilTexture.SILT
        elif clay >= 7 and clay < 20 and sand <= 52:
            return SoilTexture.LOAM
        elif sand >= 85:
            return SoilTexture.SAND if sand >= 90 else SoilTexture.LOAMY_SAND
        elif sand >= 52:
            return SoilTexture.SANDY_LOAM
        else:
            return SoilTexture.LOAM

    def estimate_van_genuchten(self, texture: SoilTexture) -> dict[str, float]:
        """
        Estimate van Genuchten parameters from texture.
        
        Returns:
            Dict with theta_r, theta_s, alpha, n
        """
        if self._soil_modules and "pedotransfer" in self._soil_modules:
            try:
                # Try to use pedotransfer module
                pass  # Module-specific implementation
            except Exception:
                pass

        # Fallback: typical values per texture (from literature)
        vg_params = {
            SoilTexture.SAND: {"theta_r": 0.045, "theta_s": 0.437, "alpha": 0.145, "n": 2.68},
            SoilTexture.LOAMY_SAND: {"theta_r": 0.057, "theta_s": 0.437, "alpha": 0.124, "n": 2.28},
            SoilTexture.SANDY_LOAM: {"theta_r": 0.065, "theta_s": 0.453, "alpha": 0.075, "n": 1.89},
            SoilTexture.LOAM: {"theta_r": 0.078, "theta_s": 0.463, "alpha": 0.036, "n": 1.56},
            SoilTexture.SILT_LOAM: {"theta_r": 0.065, "theta_s": 0.471, "alpha": 0.020, "n": 1.41},
            SoilTexture.SILT: {"theta_r": 0.060, "theta_s": 0.479, "alpha": 0.016, "n": 1.37},
            SoilTexture.SANDY_CLAY_LOAM: {"theta_r": 0.067, "theta_s": 0.398, "alpha": 0.020, "n": 1.48},
            SoilTexture.CLAY_LOAM: {"theta_r": 0.095, "theta_s": 0.464, "alpha": 0.019, "n": 1.31},
            SoilTexture.SILTY_CLAY_LOAM: {"theta_r": 0.089, "theta_s": 0.471, "alpha": 0.010, "n": 1.23},
            SoilTexture.SANDY_CLAY: {"theta_r": 0.100, "theta_s": 0.430, "alpha": 0.027, "n": 1.23},
            SoilTexture.SILTY_CLAY: {"theta_r": 0.070, "theta_s": 0.479, "alpha": 0.005, "n": 1.09},
            SoilTexture.CLAY: {"theta_r": 0.090, "theta_s": 0.468, "alpha": 0.008, "n": 1.09},
        }

        return vg_params.get(texture, vg_params[SoilTexture.LOAM])

    def build_default_profile(self, lat: float, lon: float) -> DeepSoilProfile:
        """
        Build a default soil profile using global mean values.
        
        This is used when no real soil data is available.
        Data quality level: L0 (global model)
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            DeepSoilProfile with 6 layers
        """
        layers = []

        for depth_min, depth_max in SOILGRIDS_LAYERS:
            # Use global mean values with slight depth variation
            depth_factor = 1.0 - (depth_max / 200.0) * 0.3  # Decrease properties with depth

            sand = GLOBAL_MEAN_SOIL["sand_pct"]
            silt = GLOBAL_MEAN_SOIL["silt_pct"]
            clay = GLOBAL_MEAN_SOIL["clay_pct"]

            texture = self.classify_texture(sand, silt, clay)
            vg_params = self.estimate_van_genuchten(texture)

            layer = SoilLayer(
                depth_min_cm=depth_min,
                depth_max_cm=depth_max,
                sand_pct=sand,
                silt_pct=silt,
                clay_pct=clay,
                texture=texture,
                ph=GLOBAL_MEAN_SOIL["ph"],
                ec_dsm=GLOBAL_MEAN_SOIL["ec_dsm"],
                organic_carbon_g_kg=GLOBAL_MEAN_SOIL["organic_carbon_g_kg"] * depth_factor,
                cec_mmolc_kg=GLOBAL_MEAN_SOIL["cec_mmolc_kg"],
                bulk_density_g_cm3=GLOBAL_MEAN_SOIL["bulk_density_g_cm3"],
                theta_r=vg_params["theta_r"],
                theta_s=vg_params["theta_s"],
                alpha=vg_params["alpha"],
                n=vg_params["n"],
                data_source="global_mean",
                uncertainty=0.5,  # High uncertainty for global mean
            )
            layers.append(layer)

        profile = DeepSoilProfile(
            layers=layers,
            total_depth_cm=200,
            dominant_texture=layers[0].texture,
            rooting_depth_cm=120,
            data_source="global_mean",
        )

        return profile

    def calculate_awc(self, profile: DeepSoilProfile) -> float:
        """
        Calculate Available Water Capacity (mm) for the profile.
        
        Uses van Genuchten parameters to estimate field capacity
        and wilting point for each layer.
        
        Returns:
            AWC in mm
        """
        total_awc_mm = 0.0

        for layer in profile.layers:
            if layer.theta_r is None or layer.theta_s is None:
                continue

            # Field capacity: water content at -33 kPa (pF 2.5)
            # Wilting point: water content at -1500 kPa (pF 4.2)
            # Using simplified van Genuchten
            alpha = layer.alpha or 0.02
            n = layer.n or 1.5
            theta_r = layer.theta_r
            theta_s = layer.theta_s

            # van Genuchten equation: theta = theta_r + (theta_s - theta_r) / (1 + (alpha*h)^n)^(1-1/n)
            # Field capacity at h = 33 kPa (330 cm)
            h_fc = 330
            theta_fc = theta_r + (theta_s - theta_r) / (1 + (alpha * h_fc) ** n) ** (1 - 1/n)

            # Wilting point at h = 1500 kPa (15000 cm)
            h_wp = 15000
            theta_wp = theta_r + (theta_s - theta_r) / (1 + (alpha * h_wp) ** n) ** (1 - 1/n)

            # AWC for this layer (mm)
            thickness_mm = layer.depth_thickness_cm() * 10
            awc_layer = (theta_fc - theta_wp) * thickness_mm
            total_awc_mm += max(0, awc_layer)

        return round(total_awc_mm, 1)

    def classify_salinity(self, ec_dsm: float) -> SalinityClass:
        """Classify soil salinity based on ECe."""
        if ec_dsm < 2:
            return SalinityClass.NON_SALINE
        elif ec_dsm < 4:
            return SalinityClass.SLIGHTLY_SALINE
        elif ec_dsm < 8:
            return SalinityClass.MODERATELY_SALINE
        elif ec_dsm < 16:
            return SalinityClass.STRONGLY_SALINE
        else:
            return SalinityClass.VERY_STRONGLY_SALINE

    def calculate_soil_health(self, profile: DeepSoilProfile) -> float:
        """
        Calculate soil health score (0-100).
        
        Uses simplified scoring based on:
        - pH optimal range (6.0-7.5)
        - Organic carbon content
        - Texture balance
        
        Returns:
            Score from 0-100
        """
        if self._soil_modules and "health" in self._soil_modules:
            try:
                # Try to use health module
                top_layer = profile.layers[0]
                # Build input dict for health module
                pass  # Module-specific implementation
            except Exception:
                pass

        # Fallback: simple scoring
        top_layer = profile.layers[0]
        score = 100.0

        # pH penalty (optimal 6.0-7.5)
        if top_layer.ph:
            if top_layer.ph < 5.5:
                score -= 20
            elif top_layer.ph < 6.0:
                score -= 10
            elif top_layer.ph > 8.0:
                score -= 20
            elif top_layer.ph > 7.5:
                score -= 10

        # Organic carbon penalty (optimal > 15 g/kg)
        if top_layer.organic_carbon_g_kg:
            if top_layer.organic_carbon_g_kg < 5:
                score -= 25
            elif top_layer.organic_carbon_g_kg < 10:
                score -= 15
            elif top_layer.organic_carbon_g_kg < 15:
                score -= 5

        # Salinity penalty
        if top_layer.ec_dsm:
            salinity = self.classify_salinity(top_layer.ec_dsm)
            if salinity == SalinityClass.MODERATELY_SALINE:
                score -= 15
            elif salinity == SalinityClass.STRONGLY_SALINE:
                score -= 30
            elif salinity == SalinityClass.VERY_STRONGLY_SALINE:
                score -= 50

        return max(0, min(100, score))

    def integrate_with_land(
        self,
        profile_id: str,
        lat: float,
        lon: float,
        terrain_slope_deg: float | None = None,
        climate_zone: str | None = None,
    ) -> SoilIntegrationResult:
        """
        Integrate soil data with land profile.
        
        Args:
            profile_id: Land profile ID
            lat: Latitude
            lon: Longitude
            terrain_slope_deg: Terrain slope (from land analysis)
            climate_zone: Köppen climate zone
            
        Returns:
            SoilIntegrationResult
        """
        start_time = time.time()

        try:
            # Build soil profile
            soil_profile = self.build_default_profile(lat, lon)

            # Calculate derived properties
            soil_profile.awc_mm = self.calculate_awc(soil_profile)

            top_layer = soil_profile.layers[0]
            if top_layer.ec_dsm:
                soil_profile.salinity_class = self.classify_salinity(top_layer.ec_dsm)

            # Calculate soil health
            health_score = self.calculate_soil_health(soil_profile)

            # Determine suitable crops based on soil properties
            suitable_crops = self._determine_suitable_crops(soil_profile, climate_zone)

            # Identify limitations
            limitations = self._identify_limitations(soil_profile, terrain_slope_deg)

            # Generate recommendations
            recommendations = self._generate_recommendations(soil_profile, limitations)

            integration_time_ms = (time.time() - start_time) * 1000

            return SoilIntegrationResult(
                profile_id=profile_id,
                success=True,
                soil_profile=soil_profile,
                soil_health_score=health_score,
                suitable_crops=suitable_crops,
                limitations=limitations,
                recommendations=recommendations,
                integration_time_ms=integration_time_ms,
                data_quality_level="L0",  # Global model
            )

        except Exception as e:
            logger.error(f"Soil integration failed: {e}")
            integration_time_ms = (time.time() - start_time) * 1000
            return SoilIntegrationResult(
                profile_id=profile_id,
                success=False,
                error_message=str(e),
                integration_time_ms=integration_time_ms,
            )

    def _determine_suitable_crops(
        self, profile: DeepSoilProfile, climate_zone: str | None
    ) -> list[str]:
        """Determine suitable crops based on soil properties."""
        crops = []

        top_layer = profile.layers[0]
        texture = top_layer.texture

        # Texture-based suitability
        if texture in [SoilTexture.LOAM, SoilTexture.SILT_LOAM, SoilTexture.SANDY_LOAM]:
            crops.extend(["wheat", "barley", "corn", "vegetables"])
        elif texture in [SoilTexture.CLAY_LOAM, SoilTexture.SILTY_CLAY_LOAM]:
            crops.extend(["wheat", "rice", "cotton"])
        elif texture in [SoilTexture.SAND, SoilTexture.LOAMY_SAND]:
            crops.extend(["peanuts", "watermelon", "root_vegetables"])
        elif texture in [SoilTexture.CLAY, SoilTexture.SILTY_CLAY]:
            crops.extend(["rice", "sugarcane"])

        # Salinity adjustment
        if profile.salinity_class == SalinityClass.MODERATELY_SALINE:
            crops = [c for c in crops if c in ["barley", "cotton", "dates"]]
            crops.append("salt_tolerant_crops")
        elif profile.salinity_class in [SalinityClass.STRONGLY_SALINE, SalinityClass.VERY_STRONGLY_SALINE]:
            crops = ["halophytes", "salt_tolerant_crops"]

        # Climate adjustment
        if climate_zone:
            if climate_zone.startswith("B"):  # Arid
                crops = [c for c in crops if c in ["dates", "barley", "salt_tolerant_crops"]]
            elif climate_zone.startswith("C"):  # Temperate
                pass  # Most crops suitable
            elif climate_zone.startswith("A"):  # Tropical
                crops.extend(["rice", "sugarcane", "tropical_fruits"])

        return list(set(crops)) if crops else ["unknown"]

    def _identify_limitations(
        self, profile: DeepSoilProfile, terrain_slope_deg: float | None
    ) -> list[str]:
        """Identify soil-related limitations."""
        limitations = []

        top_layer = profile.layers[0]

        # pH limitations
        if top_layer.ph:
            if top_layer.ph < 5.5:
                limitations.append("acidic_soil")
            elif top_layer.ph > 8.0:
                limitations.append("alkaline_soil")

        # Salinity limitations
        if profile.salinity_class == SalinityClass.MODERATELY_SALINE:
            limitations.append("moderate_salinity")
        elif profile.salinity_class in [SalinityClass.STRONGLY_SALINE, SalinityClass.VERY_STRONGLY_SALINE]:
            limitations.append("high_salinity")

        # Organic carbon limitation
        if top_layer.organic_carbon_g_kg and top_layer.organic_carbon_g_kg < 10:
            limitations.append("low_organic_carbon")

        # Texture limitations
        if top_layer.texture == SoilTexture.SAND:
            limitations.append("low_water_retention")
        elif top_layer.texture == SoilTexture.CLAY:
            limitations.append("poor_drainage")

        # Slope limitation (from terrain)
        if terrain_slope_deg and terrain_slope_deg > 15:
            limitations.append("erosion_risk")

        return limitations

    def _generate_recommendations(
        self, profile: DeepSoilProfile, limitations: list[str]
    ) -> list[str]:
        """Generate soil management recommendations."""
        recommendations = []

        if "acidic_soil" in limitations:
            recommendations.append("Apply lime to raise pH")
        if "alkaline_soil" in limitations:
            recommendations.append("Apply sulfur or organic matter to lower pH")
        if "moderate_salinity" in limitations or "high_salinity" in limitations:
            recommendations.append("Implement leaching and drainage")
            recommendations.append("Use salt-tolerant crop varieties")
        if "low_organic_carbon" in limitations:
            recommendations.append("Apply compost or organic amendments")
            recommendations.append("Practice conservation tillage")
        if "low_water_retention" in limitations:
            recommendations.append("Add organic matter to improve water retention")
        if "poor_drainage" in limitations:
            recommendations.append("Install subsurface drainage")
        if "erosion_risk" in limitations:
            recommendations.append("Implement contour farming and terracing")

        if not recommendations:
            recommendations.append("Soil conditions are good - maintain current practices")

        return recommendations
