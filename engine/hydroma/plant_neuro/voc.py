"""VOC (Volatile Organic Compound) profile analysis for plant stress detection.

Plants emit specific VOC blends when stressed by biotic (pathogens, herbivores)
or abiotic (drought, heat, ozone) factors. This module analyzes GC-MS or
electronic nose VOC profiles to identify stress signatures.

Reference:
- Bruhn et al. (2019) "Volatile organic compounds (VOCs) in plant-insect
  interactions." Plants.
- Loreto & Schnitter (2006) "Why plants produce volatile organic compounds."
  Current Opinion in Plant Biology.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN


@dataclass
class VOCProfile:
    """A normalized VOC profile from a single sample."""

    compounds: dict[str, float]  # compound_name -> concentration (ppb)
    timestamp: Optional[str] = None
    plant_id: Optional[str] = None
    stress_level: float = 0.0  # 0-1 normalized stress index
    profile_hash: Optional[str] = None


@dataclass
class StressSignature:
    """Identified stress signature from VOC analysis."""

    stress_type: str  # 'herbivory', 'pathogen', 'drought', 'heat', 'ozone', 'healthy'
    confidence: float  # 0-1
    key_compounds: list[str]  # diagnostic VOCs
    severity_score: float  # 0-1
    pca_components: Optional[np.ndarray] = None


class VOCAnalyzer:
    """Analyzes VOC profiles to detect and classify plant stress.

    Uses PCA for dimensionality reduction and DBSCAN for anomaly detection
    on compound concentration vectors.
    """

    # Reference VOC signatures for common stress types (ppb thresholds)
    STRESS_SIGNATURES = {
        "herbivory": {
            "green_leaf_volatiles": ["Z-3-hexenyl acetate", "E-2-hexenal", "Z-3-hexenol"],
            "terpenes": ["myrcene", "limonene", "alpha-pinene"],
            "threshold": 50.0,  # ppb minimum for detection
        },
        "pathogen": {
            "green_leaf_volatiles": ["E-2-hexenal", "Z-3-hexenyl butyrate"],
            "terpenes": ["linalool", "geraniol", "camphor"],
            "benzene_derivatives": ["methyl salicylate", "methyl jasmonate"],
            "threshold": 30.0,
        },
        "drought": {
            "isoprene": ["isoprene"],
            "monoterpenes": ["alpha-pinene", "beta-pinene", "limonene"],
            "threshold": 100.0,
        },
        "heat": {
            "isoprene": ["isoprene"],
            "green_leaf_volatiles": ["Z-3-hexenyl acetate"],
            "threshold": 80.0,
        },
        "ozone": {
            "oxygenated_compounds": ["tert-butyl hydroperoxide", "methanol"],
            "green_leaf_volatiles": ["E-2-hexenal"],
            "threshold": 40.0,
        },
    }

    def __init__(self, n_components: int = 3):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components)
        self.n_components = n_components
        self.reference_profiles: list[VOCProfile] = []
        self.compound_names: list[str] = []
        self._fitted = False

    def build_compound_vector(self, profile: VOCProfile) -> np.ndarray:
        """Convert a VOCProfile into a fixed-length compound vector.

        Unknown compounds are ignored; missing compounds default to 0.0.
        """
        if not self.compound_names:
            self.compound_names = list(profile.compounds.keys())
        vec = np.array(
            [profile.compounds.get(c, 0.0) for c in self.compound_names],
            dtype=np.float64,
        )
        return vec

    def fit_reference(self, profiles: list[VOCProfile]):
        """Fit PCA and scaler on a set of healthy reference profiles."""
        if not profiles:
            return
        self.compound_names = list(profiles[0].compounds.keys())
        matrix = np.array([self.build_compound_vector(p) for p in profiles])
        self.scaler.fit(matrix)
        matrix_scaled = self.scaler.transform(matrix)
        self.pca.fit(matrix_scaled)
        self.reference_profiles = profiles
        self._fitted = True

    def transform(self, profile: VOCProfile) -> np.ndarray:
        """Transform a VOCProfile into PCA-reduced feature space."""
        if not self.compound_names:
            self.compound_names = list(profile.compounds.keys())
        vec = self.build_compound_vector(profile).reshape(1, -1)
        if self._fitted:
            vec_scaled = self.scaler.transform(vec)
            return self.pca.transform(vec_scaled)[0]
        return vec.flatten()

    def detect_anomaly(self, profile: VOCProfile) -> tuple[bool, float]:
        """Detect if a VOC profile deviates from healthy baseline.

        Returns:
            Tuple of (is_anomaly, anomaly_score).
        """
        vec = self.build_compound_vector(profile).reshape(1, -1)
        if not self._fitted:
            return True, 1.0
        vec_scaled = self.scaler.transform(vec)
        reconstructed = self.scaler.inverse_transform(
            self.pca.inverse_transform(self.pca.transform(vec_scaled))
        )
        residual = np.abs(vec.flatten() - reconstructed.flatten())
        anomaly_score = float(np.mean(residual) / (np.mean(np.abs(vec.flatten())) + 1e-9))
        return anomaly_score > 0.3, anomaly_score

    def classify_stress(self, profile: VOCProfile) -> StressSignature:
        """Classify stress type based on VOC compound presence.

        Args:
            profile: VOCProfile with compound concentrations in ppb.

        Returns:
            StressSignature with classification and confidence.
        """
        scores: dict[str, float] = {}
        matched_compounds: dict[str, list[str]] = {}

        for stress_type, signature in self.STRESS_SIGNATURES.items():
            total_found = 0.0
            found_names: list[str] = []
            threshold = signature.get("threshold", 30.0)

            for category, compounds in signature.items():
                if category == "threshold":
                    continue
                for compound_name in compounds:
                    conc = profile.compounds.get(compound_name, 0.0)
                    if conc >= threshold:
                        total_found += conc
                        found_names.append(compound_name)

            if total_found > 0:
                scores[stress_type] = min(total_found / 500.0, 1.0)
                matched_compounds[stress_type] = found_names

        if not scores:
            return StressSignature(
                stress_type="healthy",
                confidence=0.9,
                key_compounds=[],
                severity_score=0.0,
            )

        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]

        severity = self._compute_severity(profile, matched_compounds.get(best_type, []))

        return StressSignature(
            stress_type=best_type,
            confidence=confidence,
            key_compounds=matched_compounds.get(best_type, []),
            severity_score=severity,
        )

    def _compute_severity(self, profile: VOCProfile, diagnostic_compounds: list[str]) -> float:
        """Compute severity score from diagnostic compound concentrations."""
        if not diagnostic_compounds:
            return 0.0
        max_conc = max(
            [profile.compounds.get(c, 0.0) for c in diagnostic_compounds],
            default=0.0,
        )
        # Normalize: 50 ppb = severity 0.25, 200 ppb = severity 1.0
        return float(min(max_conc / 200.0, 1.0))

    def cluster_profiles(self, profiles: list[VOCProfile]) -> np.ndarray:
        """Cluster VOC profiles using DBSCAN on PCA components.

        Returns cluster labels (-1 for noise/outliers).
        """
        if not profiles:
            return np.array([])
        if not self.compound_names:
            self.compound_names = list(profiles[0].compounds.keys())

        matrix = np.array([self.build_compound_vector(p) for p in profiles])

        # Standardize before PCA (DBSCAN eps is scale-sensitive)
        scaler = StandardScaler()
        matrix_scaled = scaler.fit_transform(matrix)

        # PCA for dimensionality reduction
        n_components = min(self.n_components, matrix.shape[1], len(profiles))
        if n_components < 1:
            return np.zeros(len(profiles), dtype=int)

        pca = PCA(n_components=n_components)
        reduced = pca.fit_transform(matrix_scaled)

        # DBSCAN clustering (eps in PCA space after standardization)
        clustering = DBSCAN(eps=0.5, min_samples=2)
        labels = clustering.fit_predict(reduced)
        return labels
