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

    data_source: str = "modelled"
    model: str = "electrical signal features (DSP)"
    computed: bool = True

    sampling_rate: float | None = None
    duration_s: float | None = None
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

    def __init__(
        self,
        sampling_rate_hz: float = 100.0,
        ap_threshold_mv: float | None = None,
    ):
        self.sampling_rate = sampling_rate_hz
        # The AP line is a constructor parameter so the engine's configured
        # threshold reaches event detection, not just the classifier
        # (S19: a 30 mV configuration used to leave a 12 mV event counted).
        self._ap_threshold_mv = (
            float(ap_threshold_mv) if ap_threshold_mv is not None else self.AP_THRESHOLD_MV
        )

    #: Samples excluded at each end before *event* statistics (peak, spike
    #: detection and everything derived from them) are computed.
    #: ``filtfilt`` pads the trace by odd extension, and the 0.1 Hz low cut of
    #: this bandpass has a time constant of order 1 / (2*pi*0.1) ~ 1.6 s
    #: (~160 samples at the default 100 Hz, so ~3 tau ~ 480 samples), so the
    #: boundary region carries a large transient: on a 20 mV in-band tone the
    #: un-trimmed ``argmax`` reported 44 mV at sample 1985 of 2000, and a 6 mV
    #: tone produced three fabricated action potentials above the 10 mV line
    #: (S19, defect D-3). The trim below is ~3 time constants of that cut.
    #: The summary moments (mean, variance, skewness, kurtosis) and the
    #: spectrum stay on the full trace: they are extensive statistics whose
    #: published definitions S19's DSP reference checks against the whole
    #: record, and the transient they see is bounded by the trace length.
    EDGE_TRIM_SAMPLES = 500
    EDGE_TRIM_MIN_LENGTH = 800

    def _filter_signal(self, raw: np.ndarray) -> np.ndarray:
        """Apply bandpass filter to remove noise (0.1-50 Hz)."""
        nyquist = self.sampling_rate / 2
        low = 0.1 / nyquist
        high = min(50.0 / nyquist, 0.99)
        if low >= high:
            return raw
        b, a = scipy_signal.butter(2, [low, high], btype="band")
        filtered: np.ndarray = scipy_signal.filtfilt(b, a, raw)
        return filtered

    def _edge_trim(self, n: int) -> int:
        """Length of the transient region excluded from event statistics.

        Short traces keep their full length: a 16-sample record barely spans
        the filter's own pad length, and trimming it would leave nothing to
        measure (S19 tests the documented 16-sample minimum).
        """
        if n < self.EDGE_TRIM_MIN_LENGTH:
            return 0
        return min(self.EDGE_TRIM_SAMPLES, n // 4)

    def _detect_spikes(self, signal: np.ndarray) -> list[tuple[int, float]]:
        """Detect spike events using threshold crossing.

        An event must both exceed the AP line and stand at least half that
        line above its surrounding baseline (``prominence``). Without the
        prominence test the Butterworth ringing around a wide pulse is
        counted as separate events: a single 30 mV / 0.6 s trapezoid
        produced eight supra-threshold maxima and a 510 ms mean duration
        against its 600 ms analytic width (S19).
        """
        threshold = self._ap_threshold_mv
        peaks, _ = scipy_signal.find_peaks(
            signal,
            height=threshold,
            prominence=threshold * 0.5,
            distance=int(0.05 * self.sampling_rate),  # 50ms refractory
        )
        return [(p, signal[p]) for p in peaks]

    def extract_features(self, signal_mv: np.ndarray) -> SignalFeatures:
        """Extract signal features for stress classification.

        Args:
            signal_mv: Raw electrical signal in millivolts.

        Returns:
            SignalFeatures dataclass with extracted metrics.

        Raises:
            ValueError: if the recording is shorter than the filter's pad
                length, or if it contains non-finite samples. A statistic of
                a NaN- or inf-contaminated recording is not a measurement,
                and reporting one as a definitive healthy verdict would be a
                fabricated result (S19, defect D-2).
        """
        signal_mv = np.asarray(signal_mv, dtype=float)
        if not np.all(np.isfinite(signal_mv)):
            raise ValueError(
                "signal_mv contains non-finite samples (NaN or inf); the "
                "recording is unmeasurable and no feature may be derived from it"
            )

        filtered = self._filter_signal(signal_mv)
        n = len(filtered)
        duration_s = n / self.sampling_rate

        # Event detection runs on the full trace -- scipy's find_peaks never
        # returns the first or last sample, so an event sitting exactly on a
        # trimmed boundary would vanish structurally -- and the detected
        # events are then restricted to the stationary region. Durations walk
        # the full trace so a half-amplitude crossing is never clipped by a
        # trim boundary (S19: FWHM of a 0.6 s trapezoid measured 510 ms when
        # the walk was clipped to the interior).
        trim = self._edge_trim(n)
        spikes = [
            (idx, amp)
            for idx, amp in self._detect_spikes(filtered)
            if trim <= idx < n - trim or trim == 0
        ]
        spike_times = [idx / self.sampling_rate for idx, _ in spikes]

        interior = filtered[trim : n - trim] if trim else filtered
        peak_idx = int(np.argmax(interior)) + trim if len(interior) else 0
        peak_val = float(interior[peak_idx - trim]) if len(interior) else 0.0
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
        """Compute dominant frequency via FFT.

        Returns ``None`` when the record carries no spectral energy above DC:
        an all-zero spectrum's ``argmax`` would otherwise report index 1, i.e.
        the bin spacing fs/N -- a window artefact, not a measurement (S19).
        """
        if len(signal) < 4:
            return None
        fft_vals = np.abs(np.fft.rfft(signal))
        if len(fft_vals) < 2 or not np.any(fft_vals[1:] > 0.0):
            return None
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
        'herbivory', 'unclassified'.

        The label set is a contract: it matches ``PlantNeuroEngine``'s
        stress-level table and its ``STRESS_RECOMMENDATIONS`` keys. The
        classifier previously also returned the undocumented catch-alls
        'abiotic' and 'biotic', which no consumer could map to advice, and
        never returned the 'healthy' it advertises, so a quiet recording
        came back 'unclassified' with no actionable verdict (S19, D-6).
        """
        if features.num_spikes == 0:
            # No action potentials. A recording that also shows no deflection
            # above half the AP line is the healthy case the recommendation
            # table carries (an empty advice list); a record with a real
            # deflection that simply matches no AP signature is unclassified,
            # not healthy -- calling a 12 mV variation potential 'healthy'
            # would be a fabricated verdict (S19).
            if features.peak_mv > threshold_ap * 0.5:
                return "unclassified"
            return "healthy"

        if (
            features.peak_mv > threshold_ap
            and features.mean_spike_frequency_hz > threshold_spike_freq
        ):
            # High-frequency AP bursts correlate with abiotic stress (drought, salinity)
            return "drought"

        if features.peak_mv > threshold_ap and features.mean_spike_frequency_hz > 0:
            # Low-frequency, high-amplitude VP correlates with pathogen attack
            if features.spike_amplitude_mean_mv > 20.0:
                return "pathogen"
            if features.spike_duration_mean_ms > 200.0:
                return "herbivory"
            return "pathogen"

        if features.peak_latency_ms > 1000.0 and features.peak_mv > threshold_ap * 0.5:
            # Delayed systemic response
            return "mechanical"

        return "unclassified"
