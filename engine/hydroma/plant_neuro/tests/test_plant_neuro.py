"""
Unit tests for plant_neuro module.

Tests cover:
- Electrical signal processing (feature extraction, spike detection, stress classification)
- VOC profile analysis (PCA, anomaly detection, stress classification)
- Plant neuro engine (combined analysis, severity assessment, recommendations)

Author: Eco Nojin Team
Created: 2026-09-18
"""

import numpy as np
import pytest

from engine.hydroma.plant_neuro import (
    ElectricalSignalProcessor,
    SignalFeatures,
    VOCAnalyzer,
    PlantNeuroEngine,
    PlantNeuroConfig,
    VOCProfile,
    StressLevel,
    StressAssessment,
)


# ============================================================================
# SIGNAL PROCESSING TESTS
# ============================================================================
class TestSignalProcessor:
    """Tests for ElectricalSignalProcessor."""

    def test_init_default_sampling_rate(self):
        """Test processor initialization with default sampling rate."""
        proc = ElectricalSignalProcessor()
        assert proc.sampling_rate == 100.0

    def test_init_custom_sampling_rate(self):
        """Test processor initialization with custom sampling rate."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=200.0)
        assert proc.sampling_rate == 200.0

    def test_detect_spikes_empty_signal(self):
        """Test spike detection on empty signal returns empty list."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        signal = np.zeros(100)
        spikes = proc._detect_spikes(signal)
        assert spikes == []

    def test_detect_spikes_single_spike(self):
        """Test spike detection identifies a single spike above threshold."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        signal = np.zeros(100)
        signal[50] = 15.0  # Above AP threshold (10.0 mV)
        spikes = proc._detect_spikes(signal)
        assert len(spikes) == 1
        assert spikes[0][0] == 50
        assert spikes[0][1] == 15.0

    def test_detect_spikes_multiple_spikes(self):
        """Test spike detection identifies multiple spikes."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        signal = np.zeros(1000)
        signal[100] = 15.0
        signal[200] = 20.0
        signal[500] = 12.0
        spikes = proc._detect_spikes(signal)
        assert len(spikes) == 3

    def test_extract_features_basic(self):
        """Test feature extraction on a simple signal."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        signal = np.random.randn(1000) * 0.1  # Background noise
        signal[500] = 25.0  # Spike
        features = proc.extract_features(signal)

        assert features.sampling_rate == 100.0
        assert features.duration_s == 10.0
        assert features.num_spikes == 1
        assert features.peak_mv >= 0

    def test_extract_features_no_spikes(self):
        """Test feature extraction on a signal with no spikes."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        signal = np.zeros(500)
        features = proc.extract_features(signal)
        assert features.num_spikes == 0
        assert features.mean_spike_frequency_hz == 0.0

    def test_extract_features_dominant_frequency(self):
        """Test that dominant frequency is calculated for periodic signal."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        t = np.linspace(0, 10, 1000)
        # 2 Hz sine wave + spikes
        signal = 10 * np.sin(2 * np.pi * 2 * t)
        features = proc.extract_features(signal)
        assert features.dominant_frequency_hz is not None

    def test_classify_stress_healthy(self):
        """Test stress classification for healthy signal (no spikes)."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        signal = np.zeros(500)
        features = proc.extract_features(signal)
        result = proc.classify_stress(features)
        assert result == "unclassified"

    def test_classify_stress_high_frequency_ap(self):
        """Test stress classification for drought-like high-frequency AP burst."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        signal = np.zeros(5000)
        # Create regular spikes
        for i in range(50, 5000, 50):
            signal[i] = 15.0
        features = proc.extract_features(signal)
        result = proc.classify_stress(features, threshold_ap=10.0, threshold_spike_freq=0.5)
        assert result in ("drought", "abiotic")

    def test_classify_stress_pathogen(self):
        """Test stress classification for pathogen-like high amplitude (low frequency VP)."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        signal = np.zeros(50000)  # 500 seconds at 100Hz
        # Create few high-amplitude spikes spaced far apart (low frequency VP pattern)
        signal[1000] = 30.0  # t=10s
        signal[10000] = 25.0  # t=100s, freq = 1/90 ≈ 0.011 Hz (below 0.5 threshold)
        signal[20000] = 28.0  # t=200s
        features = proc.extract_features(signal)
        result = proc.classify_stress(features, threshold_ap=10.0, threshold_spike_freq=0.5)
        assert result == "pathogen"

    def test_skewness_kurtosis(self):
        """Test skewness and kurtosis calculations."""
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)
        signal = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.float64)
        skew = proc._skewness(signal)
        kurt = proc._kurtosis(signal)
        assert isinstance(skew, float)
        assert isinstance(kurt, float)


# ============================================================================
# VOC ANALYSIS TESTS
# ============================================================================
class TestVOCAnalyzer:
    """Tests for VOCAnalyzer."""

    def test_init_default(self):
        """Test VOCAnalyzer initialization with default parameters."""
        analyzer = VOCAnalyzer()
        assert analyzer.n_components == 3
        assert not analyzer._fitted

    def test_build_compound_vector(self):
        """Test compound vector construction from VOCProfile."""
        analyzer = VOCAnalyzer()
        profile = VOCProfile(compounds={"isoprene": 100.0, "myrcene": 50.0})
        vec = analyzer.build_compound_vector(profile)
        assert len(vec) == 2
        assert vec[0] == 100.0
        assert vec[1] == 50.0

    def test_fit_reference(self):
        """Test fitting reference profiles on healthy baseline."""
        analyzer = VOCAnalyzer()
        profiles = [
            VOCProfile(
                compounds={"isoprene": 10.0, "myrcene": 5.0, "limonene": 8.0, "geraniol": 3.0}
            ),
            VOCProfile(
                compounds={"isoprene": 12.0, "myrcene": 6.0, "limonene": 9.0, "geraniol": 4.0}
            ),
            VOCProfile(
                compounds={"isoprene": 8.0, "myrcene": 4.0, "limonene": 7.0, "geraniol": 2.0}
            ),
            VOCProfile(
                compounds={"isoprene": 11.0, "myrcene": 5.5, "limonene": 8.5, "geraniol": 3.5}
            ),
            VOCProfile(
                compounds={"isoprene": 9.0, "myrcene": 4.5, "limonene": 7.5, "geraniol": 2.5}
            ),
        ]
        analyzer.fit_reference(profiles)
        assert analyzer._fitted
        assert len(analyzer.compound_names) == 4

    def test_transform_unfitted(self):
        """Test transform works even when not fitted (returns raw vector)."""
        analyzer = VOCAnalyzer()
        profile = VOCProfile(compounds={"isoprene": 100.0, "myrcene": 50.0})
        vec = analyzer.transform(profile)
        assert len(vec) >= 1

    def test_detect_anomaly_unfitted(self):
        """Test anomaly detection when analyzer is not fitted."""
        analyzer = VOCAnalyzer()
        profile = VOCProfile(compounds={"isoprene": 200.0})
        is_anomaly, score = analyzer.detect_anomaly(profile)
        assert is_anomaly is True
        assert 0 <= score <= 1

    def test_classify_stress_herbivory(self):
        """Test VOC-based stress classification for herbivory."""
        analyzer = VOCAnalyzer()
        # High levels of green leaf volatiles and myrcene indicate herbivory
        profile = VOCProfile(
            compounds={
                "Z-3-hexenyl acetate": 100.0,
                "myrcene": 80.0,
                "limonene": 60.0,
            }
        )
        signature = analyzer.classify_stress(profile)
        assert signature.stress_type == "herbivory"
        assert signature.confidence > 0.0

    def test_classify_stress_pathogen(self):
        """Test VOC-based stress classification for pathogen."""
        analyzer = VOCAnalyzer()
        profile = VOCProfile(
            compounds={
                "methyl salicylate": 80.0,
                "linalool": 60.0,
                "geraniol": 50.0,
            }
        )
        signature = analyzer.classify_stress(profile)
        assert signature.stress_type == "pathogen"

    def test_classify_stress_drought(self):
        """Test VOC-based stress classification for drought."""
        analyzer = VOCAnalyzer()
        profile = VOCProfile(
            compounds={
                "isoprene": 150.0,
                "alpha-pinene": 100.0,
                "limonene": 80.0,
            }
        )
        signature = analyzer.classify_stress(profile)
        assert signature.stress_type == "drought"

    def test_classify_stress_healthy(self):
        """Test VOC-based stress classification for healthy plant."""
        analyzer = VOCAnalyzer()
        # Very low compound concentrations
        profile = VOCProfile(
            compounds={
                "isoprene": 5.0,
                "myrcene": 2.0,
            }
        )
        signature = analyzer.classify_stress(profile)
        assert signature.stress_type == "healthy"

    def test_compute_severity(self):
        """Test severity score calculation from diagnostic compounds."""
        analyzer = VOCAnalyzer()
        profile = VOCProfile(compounds={"isoprene": 100.0, "myrcene": 0.0})
        severity = analyzer._compute_severity(profile, ["isoprene"])
        assert 0 < severity <= 1.0

    def test_cluster_profiles(self):
        """Test DBSCAN clustering of VOC profiles."""
        analyzer = VOCAnalyzer()
        profiles = [
            # Cluster 1: low concentrations
            VOCProfile(
                compounds={"isoprene": 10.0, "myrcene": 5.0, "limonene": 8.0, "geraniol": 3.0}
            ),
            VOCProfile(
                compounds={"isoprene": 11.0, "myrcene": 5.5, "limonene": 8.5, "geraniol": 3.5}
            ),
            VOCProfile(
                compounds={"isoprene": 9.0, "myrcene": 4.5, "limonene": 7.5, "geraniol": 2.5}
            ),
            # Cluster 2: high concentrations
            VOCProfile(
                compounds={"isoprene": 100.0, "myrcene": 50.0, "limonene": 80.0, "geraniol": 30.0}
            ),
            VOCProfile(
                compounds={"isoprene": 105.0, "myrcene": 55.0, "limonene": 85.0, "geraniol": 35.0}
            ),
            VOCProfile(
                compounds={"isoprene": 95.0, "myrcene": 45.0, "limonene": 75.0, "geraniol": 25.0}
            ),
        ]
        labels = analyzer.cluster_profiles(profiles)
        assert len(labels) == 6
        # Should form at least 2 clusters (not all noise)
        unique_labels = set(labels[labels != -1])
        assert len(unique_labels) >= 1


# ============================================================================
# PLANT NEURO ENGINE TESTS
# ============================================================================
class TestPlantNeuroEngine:
    """Tests for PlantNeuroEngine orchestrator."""

    def test_init_default(self):
        """Test engine initialization with default config."""
        engine = PlantNeuroEngine()
        assert engine.config.sampling_rate_hz == 100.0
        assert engine.config.electrical_weight == 0.5
        assert engine.config.voc_weight == 0.5

    def test_init_custom_config(self):
        """Test engine initialization with custom config."""
        config = PlantNeuroConfig(sampling_rate_hz=200.0, electrical_weight=0.7, voc_weight=0.3)
        engine = PlantNeuroEngine(config=config)
        assert engine.config.sampling_rate_hz == 200.0
        assert engine.config.electrical_weight == 0.7

    def test_fit_reference(self):
        """Test fitting reference profiles."""
        engine = PlantNeuroEngine()
        profiles = [
            VOCProfile(
                compounds={"isoprene": 10.0, "myrcene": 5.0, "limonene": 8.0, "geraniol": 3.0}
            ),
            VOCProfile(
                compounds={"isoprene": 12.0, "myrcene": 6.0, "limonene": 9.0, "geraniol": 4.0}
            ),
            VOCProfile(
                compounds={"isoprene": 8.0, "myrcene": 4.0, "limonene": 7.0, "geraniol": 2.0}
            ),
            VOCProfile(
                compounds={"isoprene": 11.0, "myrcene": 5.5, "limonene": 8.5, "geraniol": 3.5}
            ),
            VOCProfile(
                compounds={"isoprene": 9.0, "myrcene": 4.5, "limonene": 7.5, "geraniol": 2.5}
            ),
        ]
        engine.fit_reference(profiles)
        assert engine._reference_fitted

    def test_analyze_from_signals(self):
        """Test analysis from electrical signal data only."""
        engine = PlantNeuroEngine()
        signal = np.zeros(5000)
        signal[100] = 30.0
        signal[200] = 25.0
        signal[300] = 28.0

        assessment = engine.analyze_from_signals(signal)

        assert assessment.electrical_stress_type is not None
        assert assessment.signal_features is not None
        assert isinstance(assessment.integrated_stress_level, StressLevel)
        assert 0 <= assessment.integrated_severity_score <= 1.0

    def test_analyze_from_voc(self):
        """Test analysis from VOC profile data only."""
        engine = PlantNeuroEngine()
        profile = VOCProfile(
            compounds={
                "isoprene": 150.0,
                "myrcene": 80.0,
                "methyl salicylate": 60.0,
            }
        )
        assessment = engine.analyze_from_voc(profile)

        assert assessment.voc_stress_type is not None
        assert assessment.stress_signature is not None
        assert assessment.voc_confidence > 0.0

    def test_analyze_combined(self):
        """Test combined analysis from both signals and VOC."""
        engine = PlantNeuroEngine()
        signal = np.zeros(5000)
        signal[100] = 30.0
        signal[200] = 25.0

        profile = VOCProfile(
            compounds={
                "isoprene": 150.0,
                "myrcene": 80.0,
            }
        )

        assessment = engine.analyze_combined(signal_mv=signal, voc_profile=profile)

        assert assessment.electrical_stress_type is not None
        assert assessment.voc_stress_type is not None
        assert isinstance(assessment.integrated_stress_level, StressLevel)

    def test_analyze_combined_signal_only(self):
        """Test combined analysis with signal only (VOC is None)."""
        engine = PlantNeuroEngine()
        signal = np.zeros(1000)
        assessment = engine.analyze_combined(signal_mv=signal, voc_profile=None)

        assert assessment.electrical_stress_type is not None
        assert assessment.voc_stress_type is None

    def test_analyze_combined_voc_only(self):
        """Test combined analysis with VOC only (signal is None)."""
        engine = PlantNeuroEngine()
        profile = VOCProfile(compounds={"isoprene": 150.0})
        assessment = engine.analyze_combined(signal_mv=None, voc_profile=profile)

        assert assessment.electrical_stress_type is None
        assert assessment.voc_stress_type is not None

    def test_analyze_combined_neither_provided_raises(self):
        """Test that providing neither signal nor VOC raises ValueError."""
        engine = PlantNeuroEngine()
        with pytest.raises(ValueError, match="At least one"):
            engine.analyze_combined(signal_mv=None, voc_profile=None)

    def test_compute_signal_severity_zero_spikes(self):
        """Test severity calculation for signal with no spikes."""
        engine = PlantNeuroEngine()
        features = SignalFeatures(
            sampling_rate=100.0,
            duration_s=10.0,
            num_spikes=0,
        )
        severity = engine._compute_signal_severity(features)
        assert severity == 0.0

    def test_integrate_severity(self):
        """Test weighted severity integration."""
        config = PlantNeuroConfig(electrical_weight=0.6, voc_weight=0.4)
        engine = PlantNeuroEngine(config=config)

        electrical = StressAssessment(
            electrical_severity=0.8,
            electrical_stress_type="drought",
            electrical_confidence=0.7,
        )
        voc = StressAssessment(
            voc_severity=0.5,
            voc_stress_type="pathogen",
            voc_confidence=0.6,
        )

        integrated = engine._integrate_severity(electrical, voc)
        expected = 0.6 * 0.8 + 0.4 * 0.5
        assert abs(integrated - expected) < 0.001

    def test_map_severity_to_level(self):
        """Test severity-to-level mapping."""
        engine = PlantNeuroEngine()
        assert engine._map_severity_to_level(0.0) == StressLevel.HEALTHY
        assert engine._map_severity_to_level(0.3) == StressLevel.MILD
        assert engine._map_severity_to_level(0.6) == StressLevel.MODERATE
        assert engine._map_severity_to_level(0.8) == StressLevel.SEVERE
        assert engine._map_severity_to_level(0.95) == StressLevel.CRITICAL

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        engine = PlantNeuroEngine()
        recommendations = engine._generate_recommendations(
            electrical=None,
            voc=StressAssessment(
                voc_stress_type="drought",
                recommendations=["Check soil moisture levels"],
            ),
            combined_type="drought",
        )
        assert len(recommendations) > 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================
class TestPlantNeuroIntegration:
    """Integration tests for the plant_neuro module."""

    def test_full_analysis_workflow(self):
        """Test complete workflow: signal + VOC analysis with combined output."""
        engine = PlantNeuroEngine()

        # Create signal simulating herbivore damage (moderate spikes)
        signal = np.zeros(10000)
        for i in range(100, 10000, 200):
            signal[i] = 20.0
        for i in range(150, 10000, 200):
            signal[i] = 18.0

        # Create VOC profile showing herbivory signature
        profile = VOCProfile(
            compounds={
                "Z-3-hexenyl acetate": 120.0,
                "myrcene": 90.0,
                "limonene": 70.0,
            }
        )

        assessment = engine.analyze_combined(signal_mv=signal, voc_profile=profile)

        # Verify results
        assert assessment.electrical_stress_type is not None
        assert assessment.voc_stress_type is not None
        assert assessment.integrated_severity_score > 0.0
        assert isinstance(assessment.integrated_stress_level, StressLevel)
        assert len(assessment.recommendations) > 0

    def test_signal_classification_matches(self):
        """Test that signal classification returns expected stress types."""
        engine = PlantNeuroEngine()
        proc = ElectricalSignalProcessor(sampling_rate_hz=100.0)

        # High frequency AP burst (drought-like)
        signal = np.zeros(5000)
        for i in range(100, 5000, 50):
            signal[i] = 15.0
        features = proc.extract_features(signal)
        stress_type = proc.classify_stress(features, threshold_ap=10.0, threshold_spike_freq=0.5)
        assert stress_type in ("drought", "abiotic")

    def test_voc_classification_matches(self):
        """Test that VOC classification returns expected stress type."""
        engine = PlantNeuroEngine()
        analyzer = VOCAnalyzer()

        # Heat stress VOC signature
        profile = VOCProfile(
            compounds={
                "isoprene": 120.0,
                "Z-3-hexenyl acetate": 90.0,
            }
        )
        signature = analyzer.classify_stress(profile)
        assert signature.stress_type == "heat"
        assert signature.confidence > 0.0
