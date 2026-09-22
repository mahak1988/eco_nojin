"""Main orchestrator for plant neuro-stress analysis.

Combines electrical signal analysis (action potentials, variation potentials)
with VOC profile analysis to produce a comprehensive plant stress assessment.

This module integrates the signal processing and VOC analysis components
into a unified workflow for real-time plant stress monitoring.

Typical usage:
    >>> processor = ElectricalSignalProcessor(sampling_rate_hz=100.0)
    >>> features = processor.extract_features(electrical_signal)
    >>> stress_type = processor.classify_stress(features)
    >>>
    >>> analyzer = VOCAnalyzer()
    >>> profile = VOCProfile(compounds={"isoprene": 150.0, "myrcene": 60.0})
    >>> signature = analyzer.classify_stress(profile)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np

from .signals import ElectricalSignalProcessor, SignalFeatures
from .voc import VOCAnalyzer, VOCProfile, StressSignature


class StressLevel(Enum):
    """Plant stress severity levels."""

    HEALTHY = "healthy"
    MILD = "mild_stress"
    MODERATE = "moderate_stress"
    SEVERE = "severe_stress"
    CRITICAL = "critical"


@dataclass
class StressAssessment:
    """Comprehensive plant stress assessment from multiple modalities."""

    electrical_stress_type: Optional[str] = None
    electrical_confidence: float = 0.0
    electrical_severity: float = 0.0
    voc_stress_type: Optional[str] = None
    voc_confidence: float = 0.0
    voc_severity: float = 0.0
    integrated_stress_level: StressLevel = StressLevel.HEALTHY
    integrated_severity_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    signal_features: Optional[SignalFeatures] = None
    stress_signature: Optional[StressSignature] = None
    recommendations: list[str] = field(default_factory=list)


@dataclass
class PlantNeuroConfig:
    """Configuration for plant neuro-stress analysis."""

    sampling_rate_hz: float = 100.0
    ap_threshold_mv: float = 10.0
    spike_freq_threshold_hz: float = 0.5
    voc_threshold_ppb: float = 30.0
    electrical_weight: float = 0.5
    voc_weight: float = 0.5
    severity_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "healthy": 0.0,
            "mild_stress": 0.25,
            "moderate_stress": 0.5,
            "severe_stress": 0.75,
            "critical": 0.9,
        }
    )


class PlantNeuroEngine:
    """Main orchestrator for plant neuro-stress analysis.

    Integrates electrical signal processing and VOC analysis to provide
    a comprehensive assessment of plant stress state.

    Args:
        config: PlantNeuroConfig with analysis parameters.
    """

    # Mapping from stress types to intervention recommendations
    STRESS_RECOMMENDATIONS = {
        "drought": [
            "Check soil moisture levels",
            "Consider irrigation adjustment",
            "Monitor for wilting symptoms",
            "Assess vapor pressure deficit",
        ],
        "pathogen": [
            "Inspect for visible lesions or discoloration",
            "Consider fungicide application if appropriate",
            "Isolate affected plants if possible",
            "Monitor humidity levels",
        ],
        "herbivory": [
            "Inspect for insect activity",
            "Consider pest control measures",
            "Apply beneficial predators if applicable",
            "Check leaf damage patterns",
        ],
        "mechanical": [
            "Assess physical damage to plant structure",
            "Check support systems (stakes, trellises)",
            "Monitor wound response",
        ],
        "heat": [
            "Provide shade or cooling",
            "Increase irrigation frequency",
            "Monitor leaf temperature",
            "Consider anti-transpirant application",
        ],
        "ozone": [
            "Reduce atmospheric pollutants in greenhouse",
            "Monitor air circulation",
            "Consider activated carbon filtration",
        ],
        "healthy": [],
    }

    def __init__(self, config: Optional[PlantNeuroConfig] = None):
        self.config = config or PlantNeuroConfig()
        self.signal_processor = ElectricalSignalProcessor(
            sampling_rate_hz=self.config.sampling_rate_hz,
        )
        self.voc_analyzer = VOCAnalyzer()
        self._reference_fitted = False

    def fit_reference(self, profiles: list[VOCProfile]):
        """Fit VOC analyzer on healthy reference profiles."""
        self.voc_analyzer.fit_reference(profiles)
        self._reference_fitted = True

    def analyze_from_signals(self, signal_mv: np.ndarray) -> StressAssessment:
        """Analyze plant stress from electrical signal data only.

        Args:
            signal_mv: Raw electrical signal in millivolts.

        Returns:
            StressAssessment with electrical analysis results.
        """
        features = self.signal_processor.extract_features(signal_mv)
        stress_type = self.signal_processor.classify_stress(
            features,
            threshold_ap=self.config.ap_threshold_mv,
            threshold_spike_freq=self.config.spike_freq_threshold_hz,
        )

        severity = self._compute_signal_severity(features)
        stress_level = self._map_severity_to_level(severity)

        recommendations = self.STRESS_RECOMMENDATIONS.get(stress_type, [])

        return StressAssessment(
            electrical_stress_type=stress_type,
            electrical_confidence=features.num_spikes / 10.0 if features.num_spikes > 0 else 0.0,
            electrical_severity=severity,
            integrated_stress_level=stress_level,
            integrated_severity_score=severity,
            signal_features=features,
            recommendations=recommendations,
        )

    def analyze_from_voc(self, profile: VOCProfile) -> StressAssessment:
        """Analyze plant stress from VOC profile data only.

        Args:
            profile: VOCProfile with compound concentrations.

        Returns:
            StressAssessment with VOC analysis results.
        """
        signature = self.voc_analyzer.classify_stress(profile)
        severity = signature.severity_score
        stress_level = self._map_severity_to_level(severity)

        recommendations = self.STRESS_RECOMMENDATIONS.get(signature.stress_type, [])

        return StressAssessment(
            voc_stress_type=signature.stress_type,
            voc_confidence=signature.confidence,
            voc_severity=severity,
            integrated_stress_level=stress_level,
            integrated_severity_score=severity,
            stress_signature=signature,
            recommendations=recommendations,
        )

    def analyze_combined(
        self,
        signal_mv: Optional[np.ndarray] = None,
        voc_profile: Optional[VOCProfile] = None,
    ) -> StressAssessment:
        """Fused analysis from both electrical signals and VOC profiles.

        Weights each modality based on config and combines confidence scores.

        Args:
            signal_mv: Optional raw electrical signal in millivolts.
            voc_profile: Optional VOCProfile with compound concentrations.

        Returns:
            StressAssessment combining both modalities.
        """
        if signal_mv is None and voc_profile is None:
            raise ValueError("At least one of signal_mv or voc_profile must be provided")

        electrical_assessment: Optional[StressAssessment] = None
        voc_assessment: Optional[StressAssessment] = None

        if signal_mv is not None:
            electrical_assessment = self.analyze_from_signals(signal_mv)

        if voc_profile is not None:
            if self._reference_fitted:
                is_anomaly, anomaly_score = self.voc_analyzer.detect_anomaly(voc_profile)
                if not is_anomaly and anomaly_score < 0.1:
                    # Profile matches healthy baseline; skip classification
                    voc_assessment = StressAssessment(
                        voc_stress_type="healthy",
                        voc_confidence=1.0 - anomaly_score,
                        voc_severity=0.0,
                        integrated_stress_level=StressLevel.HEALTHY,
                        stress_signature=StressSignature(
                            stress_type="healthy",
                            confidence=1.0 - anomaly_score,
                            key_compounds=[],
                            severity_score=0.0,
                        ),
                    )
                else:
                    voc_assessment = self.analyze_from_voc(voc_profile)
            else:
                voc_assessment = self.analyze_from_voc(voc_profile)

        # Integrate
        integrated_severity = self._integrate_severity(electrical_assessment, voc_assessment)
        stress_level = self._map_severity_to_level(integrated_severity)

        # Combine stress types
        combined_type, combined_confidence = self._combine_stress_types(
            electrical_assessment, voc_assessment
        )

        recommendations = self._generate_recommendations(
            electrical_assessment, voc_assessment, combined_type
        )

        return StressAssessment(
            electrical_stress_type=electrical_assessment.electrical_stress_type
            if electrical_assessment
            else None,
            electrical_confidence=electrical_assessment.electrical_confidence
            if electrical_assessment
            else 0.0,
            electrical_severity=electrical_assessment.electrical_severity
            if electrical_assessment
            else 0.0,
            voc_stress_type=voc_assessment.voc_stress_type if voc_assessment else None,
            voc_confidence=voc_assessment.voc_confidence if voc_assessment else 0.0,
            voc_severity=voc_assessment.voc_severity if voc_assessment else 0.0,
            integrated_stress_level=stress_level,
            integrated_severity_score=integrated_severity,
            signal_features=electrical_assessment.signal_features
            if electrical_assessment
            else None,
            stress_signature=voc_assessment.stress_signature if voc_assessment else None,
            recommendations=recommendations,
        )

    def _compute_signal_severity(self, features: SignalFeatures) -> float:
        """Compute normalized severity from electrical signal features."""
        if features.num_spikes == 0:
            return 0.0

        # Severity based on spike frequency, amplitude, and duration
        freq_component = min(features.mean_spike_frequency_hz / 5.0, 1.0)
        amp_component = min(features.spike_amplitude_mean_mv / 50.0, 1.0)
        duration_component = min(features.spike_duration_mean_ms / 500.0, 1.0)

        return float(0.5 * freq_component + 0.3 * amp_component + 0.2 * duration_component)

    def _integrate_severity(
        self,
        electrical: Optional[StressAssessment],
        voc: Optional[StressAssessment],
    ) -> float:
        """Weighted integration of severity from both modalities."""
        if electrical and voc:
            return (
                self.config.electrical_weight * electrical.electrical_severity
                + self.config.voc_weight * voc.voc_severity
            )
        if electrical:
            return electrical.electrical_severity
        if voc:
            return voc.voc_severity
        return 0.0

    def _combine_stress_types(
        self,
        electrical: Optional[StressAssessment],
        voc: Optional[StressAssessment],
    ) -> tuple[str, float]:
        """Select the stress type with highest weighted confidence."""
        candidates: list[tuple[str, float]] = []

        if electrical and electrical.electrical_stress_type:
            candidates.append(
                (
                    electrical.electrical_stress_type,
                    electrical.electrical_confidence * self.config.electrical_weight,
                )
            )

        if voc and voc.voc_stress_type:
            candidates.append((voc.voc_stress_type, voc.voc_confidence * self.config.voc_weight))

        if not candidates:
            return "healthy", 1.0

        best = max(candidates, key=lambda x: x[1])
        return best[0], best[1]

    def _map_severity_to_level(self, severity: float) -> StressLevel:
        """Map a 0-1 severity score to a StressLevel enum."""
        thresholds = self.config.severity_thresholds
        if severity >= thresholds.get("critical", 0.9):
            return StressLevel.CRITICAL
        if severity >= thresholds.get("severe_stress", 0.75):
            return StressLevel.SEVERE
        if severity >= thresholds.get("moderate_stress", 0.5):
            return StressLevel.MODERATE
        if severity >= thresholds.get("mild_stress", 0.25):
            return StressLevel.MILD
        return StressLevel.HEALTHY

    def _generate_recommendations(
        self,
        electrical: Optional[StressAssessment],
        voc: Optional[StressAssessment],
        combined_type: str,
    ) -> list[str]:
        """Generate combined recommendations from both modalities."""
        recommendations: list[str] = []

        if electrical and electrical.recommendations:
            recommendations.extend(electrical.recommendations)

        if voc and voc.recommendations:
            recommendations.extend(voc.recommendations)

        # Add general recommendations based on combined type
        general = self.STRESS_RECOMMENDATIONS.get(combined_type, [])
        for rec in general:
            if rec not in recommendations:
                recommendations.append(rec)

        return list(dict.fromkeys(recommendations))  # Deduplicate while preserving order
