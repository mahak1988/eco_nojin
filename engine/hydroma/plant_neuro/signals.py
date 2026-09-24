"""Electrical signal processing for plant stress detection.

Based on Plant Neurobiology research:
- Action potentials (AP)
- Variation potentials (VP)
- System potentials (SP)

Reference: Fromm & Lautner (2007) "Compartmentation and transport in the
electrical signalling of plants." Plant, Cell & Environment.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as scipy_signal


@dataclass
class SignalFeatures:
    """Extracted features from an electrical signal recording."""

    sampling_rate: float
    duration_s: float
    baseline_mv: float = 0.0
    peak_mv: float = 0.0
    peak_latency_ms: float = 0.0
    num_spikes: int = 0
    mean_spike_frequency_hz: float = 0.0
    spike_amplitude_mean_mv: float = 0.0
    spike_duration_mean_ms: float = 0.0
    variance_mv: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    dominant_frequency_hz: float | None = None
    raw_signal: np.ndarray | None = None


class ElectricalSignalProcessor:
    """Processes plant electrical signals to detect stress patterns.

    Supports detection of action potentials (AP), variation potentials (VP),
    and system potentials (SP) from extracellular potential recordings.
    """

    # Stress signature thresholds (mV) based on literature
    AP_THRESHOLD_MV = 10.0  # Action potential threshold
    VP_AMPLITUDE_MV = 5.0  # Variation potential amplitude
    SP_DURATION_MS = 5000.0  # System potential duration

    def __init__(self, sampling_rate_hz: float = 100.0):
        self.sampling_rate = sampling_rate_hz

    def _filter_signal(self, raw: np.ndarray) -> np.ndarray:
        """Apply bandpass filter to remove noise (0.1-50 Hz)."""
        nyquist = self.sampling_rate / 2
        low = 0.1 / nyquist
        high = min(50.0 / nyquist, 0.99)
        if low >= high:
            return raw
        b, a = scipy_signal.butter(2, [low, high], btype="band")
        return scipy_signal.filtfilt(b, a, raw)

    def _detect_spikes(self, signal: np.ndarray) -> list[tuple[int, float]]:
        """Detect spike events using threshold crossing."""
        threshold = self.AP_THRESHOLD_MV
        peaks, _ = scipy_signal.find_peaks(
            signal,
            height=threshold,
            distance=int(0.05 * self.sampling_rate),  # 50ms refractory
        )
        return [(p, signal[p]) for p in peaks]

    def extract_features(self, signal_mv: np.ndarray) -> SignalFeatures:
        """Extract signal features for stress classification.

        Args:
            signal_mv: Raw electrical signal in millivolts.

        Returns:
            SignalFeatures dataclass with extracted metrics.
        """
        filtered = self._filter_signal(signal_mv)
        n = len(filtered)
        duration_s = n / self.sampling_rate

        spikes = self._detect_spikes(filtered)
        spike_times = [idx / self.sampling_rate for idx, _ in spikes]

        peak_idx = int(np.argmax(filtered)) if n > 0 else 0
        peak_val = float(filtered[peak_idx]) if n > 0 else 0.0
        peak_latency_ms = (peak_idx / self.sampling_rate) * 1000

        # Spike frequency (Hz)
        if len(spike_times) > 1:
            spike_freq = float(np.mean(np.diff(spike_times)))
            spike_freq_hz = 1.0 / spike_freq if spike_freq > 0 else 0.0
        else:
            spike_freq_hz = 0.0

        spike_amps = [amp for _, amp in spikes]
        spike_durations = self._estimate_spike_durations(filtered, spikes)

        # Spectral features
        dom_freq = self._dominant_frequency(filtered)

        # Statistical features
        skewness = float(self._skewness(filtered))
        kurtosis = float(self._kurtosis(filtered))

        return SignalFeatures(
            sampling_rate=self.sampling_rate,
            duration_s=duration_s,
            baseline_mv=float(np.mean(filtered)),
            peak_mv=peak_val,
            peak_latency_ms=peak_latency_ms,
            num_spikes=len(spikes),
            mean_spike_frequency_hz=spike_freq_hz,
            spike_amplitude_mean_mv=float(np.mean(spike_amps)) if spike_amps else 0.0,
            spike_duration_mean_ms=float(np.mean(spike_durations)) if spike_durations else 0.0,
            variance_mv=float(np.var(filtered)),
            skewness=skewness,
            kurtosis=kurtosis,
            dominant_frequency_hz=dom_freq,
        )

    def _estimate_spike_durations(self, signal: np.ndarray, spikes: list) -> list[float]:
        """Estimate spike width at half-amplitude (ms)."""
        durations = []
        for idx, amp in spikes:
            half_amp = amp * 0.5
            left = idx
            while left > 0 and signal[left] > half_amp:
                left -= 1
            right = idx
            while right < len(signal) - 1 and signal[right] > half_amp:
                right += 1
            duration_s = (right - left) / self.sampling_rate
            durations.append(duration_s * 1000)
        return durations

    def _dominant_frequency(self, signal: np.ndarray) -> float | None:
        """Compute dominant frequency via FFT."""
        if len(signal) < 4:
            return None
        fft_vals = np.abs(np.fft.rfft(signal))
        freqs = np.fft.rfftfreq(len(signal), d=1.0 / self.sampling_rate)
        if len(freqs) > 1:
            dom_idx = int(np.argmax(fft_vals[1:])) + 1
            return float(freqs[dom_idx])
        return None

    def _skewness(self, x: np.ndarray) -> float:
        if len(x) < 3:
            return 0.0
        mean = np.mean(x)
        std = np.std(x)
        if std == 0:
            return 0.0
        return float(np.mean(((x - mean) / std) ** 3))

    def _kurtosis(self, x: np.ndarray) -> float:
        if len(x) < 4:
            return 0.0
        mean = np.mean(x)
        std = np.std(x)
        if std == 0:
            return 0.0
        return float(np.mean(((x - mean) / std) ** 4) - 3.0)

    def classify_stress(
        self,
        features: SignalFeatures,
        threshold_ap: float = 10.0,
        threshold_spike_freq: float = 0.5,
    ) -> str:
        """Classify stress type from signal features.

        Returns one of: 'healthy', 'drought', 'pathogen', 'mechanical',
        'herbivory', 'unclassified'
        """
        if features.num_spikes == 0:
            return "unclassified"

        if (
            features.peak_mv > threshold_ap
            and features.mean_spike_frequency_hz > threshold_spike_freq
        ):
            # High-frequency AP bursts correlate with abiotic stress (drought, salinity)
            if features.dominant_frequency_hz and features.dominant_frequency_hz > 2.0:
                return "drought"
            return "abiotic"

        if features.peak_mv > threshold_ap and features.mean_spike_frequency_hz > 0:
            # Low-frequency, high-amplitude VP correlates with pathogen attack
            if features.spike_amplitude_mean_mv > 20.0:
                return "pathogen"
            if features.spike_duration_mean_ms > 200.0:
                return "herbivory"
            return "biotic"

        if features.peak_latency_ms > 1000.0 and features.peak_mv > threshold_ap * 0.5:
            # Delayed systemic response
            return "mechanical"

        return "unclassified"
