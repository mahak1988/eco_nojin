"""S19 -- Plant-Neuro Validation Register: the plant electrical-signal route
against independent signal-processing references.

This module validates ``engine.hydroma.plant_neuro`` (signals, engine, and the
gateway's ``PLANT_NEURO`` route) against references re-derived here from the
primary definitions. Following rule 3 of HYDROMA-QA-001, no expectation is
copied from the engine's own code: a green test only proves the engine matched
an *independent* law. Where a law cannot be reproduced from a source I can cite,
it is marked UNVALIDATED in the module notes rather than asserted.

Independent references
--------------------
Mean / variance       : ``np.mean`` / ``np.var`` (population, ddof=0) of the
                        bandpassed signal, where the bandpass is the one the
                        module documents -- "0.1-50 Hz" -- re-derived from
                        scipy's own ``butter``/``filtfilt`` API. A linear
                        time-invariant filter maps the mean of a signal to the
                        mean of its output, so the reported baseline must equal
                        the reference-filtered mean exactly.
Skewness / kurtosis   : the standard moment ratios mean(((x-m)/s)^3) and
                        mean(((x-m)/s)^4) - 3 with the population standard
                        deviation.
Dominant frequency    : ``np.fft.rfft`` + ``np.fft.rfftfreq``; the DC bin is
                        excluded because a constant electrode offset is not a
                        rhythmic component. A pure tone at f0 inside the
                        passband must be recovered as f0 to the bin spacing
                        fs / N.
Spike counting        : count of local maxima exceeding the action-potential
                        threshold with a refractory period, re-derived with an
                        independent ``scipy.signal.find_peaks`` call on the
                        reference-filtered signal.
Spike duration        : full width at half amplitude (FWHM). An analytic
                        trapezoid pulse of rise R, plateau P and fall F has an
                        exact FWHM of R/2 + P + F/2, which pins the reported
                        duration; the width law is also checked as a monotone
                        function of the injected event width.
Amplitude scaling     : linearity of an LTI filter. Scaling the input by c
                        scales amplitude features by c, the variance by c^2,
                        and leaves duration, frequency, latency, skewness and
                        kurtosis unchanged (a scale-invariant statistic).
Severity bounds       : each severity component is a ratio clipped at 1.0 and
                        the weights sum to 1, so the weighted sum is confined to
                        [0, 1]; the stress-level thresholds are an ordered
                        partition of that interval, so the level must be
                        monotone in severity.
Short-input rejection : scipy's ``filtfilt`` requires len(x) > padlen, with
                        padlen = 3 * max(len(a), len(b)) - 1. A 2nd-order
                        Butterworth has len(a)=len(b)=3, so padlen = 15 and the
                        minimum analysable length is 16 samples.
Label/advisory law    : every stress label the classifier can return must be a
                        key of ``STRESS_RECOMMENDATIONS`` or the documented
                        no-action case, and a named stress must carry advice.

Status of the defects this register first recorded
--------------------------------------------------
While this register was being written, ``engine/hydroma/plant_neuro`` was
patched (the working tree carries ``S19, defect D-2`` / ``D-3`` / ``D-6`` and
``S19`` notes in signals.py and engine.py). Four defects recorded by earlier
runs of this file are closed in the current tree and are kept here as
regression guards rather than failures:

* ``electrical_confidence`` was ``num_spikes / 10.0`` with no clip (4.0 at
  forty events) -- now clipped to [0, 1] (engine.py:171).
* Non-finite recordings returned a healthy assessment with NaN features --
  ``extract_features`` now raises ValueError and the gateway route returns
  EXECUTION_ERROR (signals.py:135-139).
* The classifier returned the labels ``abiotic`` and ``biotic``, which no
  advisory table could serve, and never returned the ``healthy`` it advertised
  -- the label set now matches the table (signals.py:261-285).
* ``PlantNeuroConfig.ap_threshold_mv`` did not reach event detection -- it is
  now a constructor parameter of ``ElectricalSignalProcessor``
  (signals.py:56-67, engine.py:138).
* An energy-free recording reported the FFT bin spacing fs/N as its dominant
  frequency -- ``_dominant_frequency`` now returns None for an all-zero
  spectrum (signals.py:217-218).

Still open, and therefore carried below as a strict xfail in this suite's
convention for known engine defects: *variation potentials are declared and
never detected* -- ``VP_AMPLITUDE_MV`` and ``SP_DURATION_MS`` are declared
constants that nothing reads, a slow depolarisation above the declared VP
amplitude is filtered below the AP threshold and answered as a healthy
assessment, and when it does cross the threshold it is fragmented into an
action-potential burst and labelled ``drought``.

Marked UNVALIDATED (no citable reference here; only structural laws asserted)
----------------------------------------------------------------------------
* The absolute thresholds and normalisation constants are in-house
  calibration values with no citation in the modules: the 10 mV AP threshold
  (``AP_THRESHOLD_MV``), the 5 Hz / 50 mV / 500 ms severity normalisations and
  the 0.5/0.3/0.2 severity weights, the 2.0 Hz / 20 mV / 200 ms / 1000 ms
  classification boundaries, the 0.1-50 Hz bandpass parameters, the 500-sample
  edge trim, and the VOC ppb thresholds (30-100 ppb) with their 500 and 200
  normalisations. Only their bounds, monotonicity and self-consistency are
  asserted below.
* The biological stress-type mapping (which physiological process each
  electrical signature corresponds to) -- nothing in the repository cites an
  experiment that ties the electrical signature to the named stressor.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import signal as scipy_signal

from engine.gateway import (
    EngineGateway,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
)
from engine.hydroma.plant_neuro import (
    ElectricalSignalProcessor,
    PlantNeuroConfig,
    PlantNeuroEngine,
    SignalFeatures,
    VOCProfile,
)

GW = EngineGateway()
PROV = ProvenanceSpec(source="s19", source_type="TEST")

FS = 100.0  # sampling rate used throughout (Hz), the engine's own default

#: The engine trims a 500-sample boundary region from the event statistics
#: (fast/slow transients of the 0.1 Hz high-pass); declared as
#: ``ElectricalSignalProcessor.EDGE_TRIM_SAMPLES``.
TRIM = 500


def _reference_filter(raw: np.ndarray, fs: float = FS) -> np.ndarray:
    """Independent re-derivation of the documented 0.1-50 Hz bandpass.

    The module documents the band as "0.1-50 Hz"; this is the same filter
    written from scipy's public API, so a mismatch means the engine's filtering
    is not the filter it documents.
    """
    nyquist = fs / 2
    low = 0.1 / nyquist
    high = min(50.0 / nyquist, 0.99)
    if low >= high:
        return raw
    b, a = scipy_signal.butter(2, [low, high], btype="band")
    return np.asarray(scipy_signal.filtfilt(b, a, raw))


def _proc(fs: float = FS) -> ElectricalSignalProcessor:
    return ElectricalSignalProcessor(sampling_rate_hz=fs)


def _spike_train(amp_mv: float, count: int, span_s: float, fs: float = FS) -> np.ndarray:
    """A zero-centred record of ``count`` single-sample events, trim-safe.

    Events are placed inside the analysed interior so that a dropped event can
    only come from the detection law, never from the boundary trim.
    """
    sig = np.zeros(int(span_s * fs))
    interior = int(span_s * fs) - 2 * TRIM
    positions = np.linspace(TRIM + 100, TRIM + 100 + interior - 200, count).astype(int)
    sig[positions] = amp_mv
    return sig


def _trapezoid(rise_s: float, plateau_s: float, fall_s: float, amp_mv: float,
               fs: float = FS, total: int = 4000, centre_s: float = 10.0) -> np.ndarray:
    """An isolated trapezoid pulse with an analytic FWHM of R/2 + P + F/2."""
    t = np.arange(total) / fs
    sig = np.zeros(total)
    t0 = centre_s - (rise_s + plateau_s + fall_s) / 2.0
    t1, t2 = t0 + rise_s, t0 + rise_s + plateau_s
    t3 = t2 + fall_s
    for i, tt in enumerate(t):
        if t0 <= tt < t1:
            sig[i] = amp_mv * (tt - t0) / rise_s
        elif t1 <= tt < t2:
            sig[i] = amp_mv
        elif t2 <= tt < t3:
            sig[i] = amp_mv * (t3 - tt) / fall_s
    return sig


def _depolarisation(width_s: float, amp_mv: float, centre_s: float = 10.0,
                    fs: float = FS, total: int = 4000, rise_s: float = 0.15) -> np.ndarray:
    """A slow, broad depolarisation of the shape a variation potential takes."""
    t = np.arange(total) / fs
    sig = np.zeros(total)
    t0 = centre_s - width_s / 2.0
    t3 = centre_s + width_s / 2.0
    for i, tt in enumerate(t):
        if t0 <= tt < t0 + rise_s:
            sig[i] = amp_mv * (tt - t0) / rise_s
        elif t0 + rise_s <= tt < t3 - rise_s:
            sig[i] = amp_mv
        elif t3 - rise_s <= tt < t3:
            sig[i] = amp_mv * (t3 - tt) / rise_s
    return sig


def _assessment_from(signal_mv: np.ndarray):
    return PlantNeuroEngine().analyze_from_signals(signal_mv)


def _ident(features) -> dict:
    """Substantive fingerprint of a feature set (excludes by-design metadata)."""
    return {
        k: getattr(features, k)
        for k in (
            "baseline_mv", "peak_mv", "peak_latency_ms", "num_spikes",
            "mean_spike_frequency_hz", "spike_amplitude_mean_mv",
            "spike_duration_mean_ms", "variance_mv", "skewness", "kurtosis",
            "dominant_frequency_hz",
        )
    }


def _neuro_values(payload: dict) -> GatewayResult:
    r = GW.execute(
        GatewayRequest(model_id="PLANT_NEURO", inputs=payload, input_units={}, provenance=PROV)
    )
    assert isinstance(r, GatewayResult), f"{r.error_code}: {r.message}"
    return r


# ============================================================================
# Filter and statistical features against the independent reference
# ============================================================================
class TestFilterAndStatisticsIndependent:
    """baseline/variance/skewness/kurtosis re-derived with numpy."""

    @staticmethod
    def _noise() -> np.ndarray:
        return np.random.default_rng(7).normal(0.0, 0.3, 3000)

    def test_baseline_is_the_mean_of_the_bandpassed_signal(self) -> None:
        x = self._noise()
        ref = _reference_filter(x)
        got = _proc().extract_features(x).baseline_mv
        assert got == pytest.approx(float(np.mean(ref)), abs=1e-12)

    def test_variance_is_the_population_variance_of_the_bandpassed_signal(self) -> None:
        x = self._noise()
        ref = _reference_filter(x)
        got = _proc().extract_features(x).variance_mv
        assert got == pytest.approx(float(np.var(ref)), abs=1e-12)

    def test_skewness_and_kurtosis_match_the_standard_definitions(self) -> None:
        x = self._noise()
        ref = _reference_filter(x)
        m, s = np.mean(ref), np.std(ref)
        z = (ref - m) / s
        feats = _proc().extract_features(x)
        assert feats.skewness == pytest.approx(float(np.mean(z**3)), abs=1e-12)
        assert feats.kurtosis == pytest.approx(float(np.mean(z**4) - 3.0), abs=1e-12)

    def test_peak_and_latency_follow_the_argmax_law(self) -> None:
        x = self._noise()
        x[1234] = 40.0
        ref = _reference_filter(x)
        feats = _proc().extract_features(x)
        assert feats.peak_mv == pytest.approx(float(np.max(ref)), abs=1e-12)
        assert feats.peak_latency_ms == pytest.approx(int(np.argmax(ref)) / FS * 1000.0)

    def test_bandpass_attenuates_a_signal_below_its_documented_cutoff(self) -> None:
        # 0.02 Hz lies a factor of five below the documented 0.1 Hz high-pass.
        t = np.arange(0, 40, 1 / FS)
        drift = 5.0 * np.sin(2 * np.pi * 0.02 * t)
        feats = _proc().extract_features(drift)
        assert abs(feats.peak_mv) < 0.10 * 5.0, (
            f"0.02 Hz drift should be attenuated by the 0.1 Hz high-pass, "
            f"peak after filtering = {feats.peak_mv}"
        )


# ============================================================================
# Dominant frequency against an rfft reference
# ============================================================================
class TestDominantFrequencyIndependent:
    """dominant_frequency_hz re-derived from numpy's FFT."""

    @staticmethod
    def _tone(tone_hz: float, amp_mv: float = 5.0, n: int | None = None) -> float:
        n = n or int(40 * FS)
        t = np.arange(n) / FS
        feats = _proc().extract_features(amp_mv * np.sin(2 * np.pi * tone_hz * t))
        freq = feats.dominant_frequency_hz
        assert freq is not None
        return freq

    def test_dominant_frequency_matches_the_rfft_reference(self) -> None:
        x = np.random.default_rng(3).normal(0.0, 1.0, 3000)
        ref = _reference_filter(x)
        spectrum = np.abs(np.fft.rfft(ref))
        freqs = np.fft.rfftfreq(len(ref), d=1.0 / FS)
        expected = float(freqs[int(np.argmax(spectrum[1:])) + 1])
        got = _proc().extract_features(x).dominant_frequency_hz
        assert got == pytest.approx(expected, abs=1e-12)

    @pytest.mark.parametrize("tone_hz", [4.0, 0.5, 2.5])
    def test_dominant_frequency_recovers_a_pure_tone(self, tone_hz: float) -> None:
        # Bin spacing is fs/N = 0.025 Hz over 40 s, so these tones are exact bins.
        assert self._tone(tone_hz) == pytest.approx(tone_hz, abs=1e-9)

    def test_dc_offset_is_not_reported_as_the_dominant_frequency(self) -> None:
        t = np.arange(0, 40, 1 / FS)
        biased = 2.0 + 5.0 * np.sin(2 * np.pi * 4.0 * t)
        feats = _proc().extract_features(biased)
        assert feats.dominant_frequency_hz == pytest.approx(4.0, abs=1e-9)

    def test_energy_free_recording_reports_no_dominant_frequency(self) -> None:
        """Regression guard (defect now closed, signals.py:217-218).

        ``argmax`` over an all-zero spectrum used to return index 1, so a
        recording with no spectral energy above DC was reported as having a
        dominant frequency equal to the bin spacing fs/N (0.05 Hz at N=2000 and
        0.02 Hz at N=5000) -- a window artefact, not a measurement.
        """
        for n in (2000, 5000):
            feats = _proc().extract_features(np.zeros(n))
            assert feats.dominant_frequency_hz is None, (
                f"N={n}: an energy-free recording reported dominant frequency "
                f"{feats.dominant_frequency_hz} Hz (= fs/N)"
            )


# ============================================================================
# Spike detection against independent threshold crossings
# ============================================================================
class TestSpikeDetectionIndependent:
    """num_spikes / frequency / duration re-derived from first principles."""

    @staticmethod
    def _events(amps: list[float]) -> np.ndarray:
        sig = np.zeros(6000)
        for i, a in enumerate(amps):
            sig[1500 + i * 1000] = a
        return sig

    def _interior_peaks(self, ref: np.ndarray, threshold: float = 10.0) -> np.ndarray:
        peaks, _ = scipy_signal.find_peaks(
            ref[TRIM:-TRIM], height=threshold, distance=int(0.05 * FS)
        )
        return np.asarray(peaks)

    def test_spike_count_matches_independent_threshold_crossings(self) -> None:
        sig = self._events([30.0, 31.0, 32.0, 33.0])
        ref = _reference_filter(sig)
        peaks = self._interior_peaks(ref)
        feats = _proc().extract_features(sig)
        assert feats.num_spikes == len(peaks) == 4

    def test_events_below_the_threshold_are_not_counted(self) -> None:
        sig = np.zeros(2000)
        sig[1000] = 9.0  # below the 10 mV action-potential line
        sig[1200] = 4.0
        assert _proc().extract_features(sig).num_spikes == 0

    def test_refractory_period_collapses_events_closer_than_50ms(self) -> None:
        # find_peaks(distance=int(0.05 * fs)) keeps one event per 50 ms window.
        proc = _proc()
        for gap in (1, 4):  # 10 ms, 40 ms
            sig = np.zeros(1000)
            sig[500] = 20.0
            sig[500 + gap] = 25.0
            assert proc.extract_features(sig).num_spikes == 1, f"gap={gap} samples"
        for gap in (5, 20):  # 50 ms, 200 ms
            sig = np.zeros(1000)
            sig[500] = 20.0
            sig[500 + gap] = 25.0
            assert proc.extract_features(sig).num_spikes == 2, f"gap={gap} samples"

    @pytest.mark.parametrize("gap_s", [1.0, 2.0, 5.0])
    def test_mean_spike_frequency_is_the_reciprocal_inter_spike_interval(
        self, gap_s: float
    ) -> None:
        count = int(19 / gap_s) + 1
        sig = np.zeros(4000)
        for k in range(count):
            sig[int(1000 + k * gap_s * FS)] = 30.0
        feats = _proc().extract_features(sig)
        assert feats.mean_spike_frequency_hz == pytest.approx(1.0 / gap_s, abs=1e-6)

    def test_spike_duration_is_the_full_width_at_half_amplitude(self) -> None:
        # Trapezoid 0.1 s rise, 0.5 s plateau, 0.1 s fall -> FWHM = 0.6 s exactly.
        sig = _trapezoid(0.1, 0.5, 0.1, 30.0)
        feats = _proc().extract_features(sig)
        analytic_ms = (0.1 / 2 + 0.5 + 0.1 / 2) * 1000.0
        assert feats.spike_duration_mean_ms == pytest.approx(analytic_ms, abs=10.0)

    def test_duration_grows_with_the_event_width(self) -> None:
        measured = [
            _proc().extract_features(_trapezoid(0.3, p, 0.3, 30.0)).spike_duration_mean_ms
            for p in (0.1, 0.5, 1.0)
        ]
        assert measured[0] < measured[1] < measured[2], measured

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "OPEN DEFECT (recorded, engine/hydroma/plant_neuro/signals.py:53-54, "
            "108-116): variation-potential detection is advertised but not "
            "implemented. VP_AMPLITUDE_MV = 5.0 and SP_DURATION_MS = 5000.0 are "
            "declared and read nowhere; _detect_spikes only looks for local "
            "maxima above the 10 mV action-potential line. A 12 mV / 3 s "
            "depolarisation -- above the declared VP amplitude -- yields no "
            "events and is answered as a healthy assessment, and the same "
            "pulse at 25 mV is fragmented into a millisecond-scale 'action "
            "potential' burst classified 'drought' instead of the slow "
            "variation potential it physically is. This strict xfail records "
            "the gap instead of hiding it; implementing VP/SP event detection "
            "must flip these two cases to passing (the marker then fails loud)."
        ),
    )
    def test_variation_potential_is_declared_but_not_detected(self) -> None:
        """OPEN DEFECT (engine/hydroma/plant_neuro/signals.py:53-54, 108-116).

        ``ElectricalSignalProcessor`` documents detection of action potentials,
        variation potentials and system potentials, and declares
        ``VP_AMPLITUDE_MV = 5.0`` (a variation-potential amplitude) and
        ``SP_DURATION_MS = 5000.0``. Neither constant is read anywhere in the
        package, and ``_detect_spikes`` looks only for local maxima above the
        10 mV action-potential line, so:

        * a 12 mV depolarisation held for 3 s -- above the declared VP
          amplitude, and a textbook variation potential -- is filtered to
          6.1 mV, yields no events at all, and is answered as a HEALTHY
          assessment with severity 0.0 and no advice;
        * the same pulse at 25 mV does cross the AP line, but the bandpass
          fragments it into a burst of "action potentials" with a measured
          duration of 2800 ms -- an action potential is a millisecond-scale
          event -- and the burst is classified as ``drought`` (an
          action-potential signature), not as the slow variation potential it
          physically is.
        """
        processor = _proc()

        # Case 1: above the declared VP amplitude, below the AP line.
        slow = _depolarisation(3.0, 12.0)
        feats = processor.extract_features(slow)
        assert feats.peak_mv > ElectricalSignalProcessor.VP_AMPLITUDE_MV, (
            "the filtered 12 mV / 3 s event is above the declared VP amplitude"
        )
        assessment = _assessment_from(slow)
        assert feats.num_spikes > 0, (
            "a depolarisation above the declared VP amplitude produced no events"
        )
        assert assessment.electrical_stress_type not in {"healthy", "unclassified"}, (
            "an undetected variation potential was answered as a healthy assessment"
        )

        # Case 2: the same event shape above the AP line must not be reported
        # as an action-potential burst.
        strong = _depolarisation(3.0, 25.0)
        feats2 = processor.extract_features(strong)
        assert feats2.num_spikes > 0, "the 25 mV / 3 s event should be detected"
        assert feats2.spike_duration_mean_ms < 250.0, (
            f"a variation potential was reported as {feats2.num_spikes} action "
            f"potentials of {feats2.spike_duration_mean_ms:.0f} ms each"
        )
        assert processor.classify_stress(feats2) != "drought", (
            "a slow variation potential was classified as an action-potential burst"
        )

    def test_declared_vp_and_sp_constants_are_unused(self) -> None:
        """OPEN DEFECT: the declared VP/SP thresholds are dead constants.

        ``VP_AMPLITUDE_MV`` and ``SP_DURATION_MS`` appear exactly once each in
        the module -- their own declaration -- so no code path can honour them.
        """
        import inspect

        source = inspect.getsource(ElectricalSignalProcessor)
        for name in ("VP_AMPLITUDE_MV", "SP_DURATION_MS"):
            assert source.count(f"{name} = ") == 1
            assert source.count(name) == 1, f"{name} is read somewhere other than its declaration"


# ============================================================================
# Amplitude scaling (linearity of the LTI chain)
# ============================================================================
class TestAmplitudeScalingLaw:
    """Scaling the recording must scale amplitude features, not shape features."""

    SIGNAL = np.zeros(6000)
    SIGNAL[1500], SIGNAL[2500], SIGNAL[3500], SIGNAL[4500] = 30.0, 31.0, 32.0, 33.0

    @classmethod
    def _features(cls, c: float):
        return _proc().extract_features(cls.SIGNAL * c)

    def test_amplitude_features_scale_linearly(self) -> None:
        base = self._features(1.0)
        for c in (0.5, 2.0):
            got = self._features(c)
            assert got.num_spikes == base.num_spikes, "scaling must not change detection"
            assert got.spike_amplitude_mean_mv == pytest.approx(
                base.spike_amplitude_mean_mv * c, rel=1e-9
            )
            assert got.peak_mv == pytest.approx(base.peak_mv * c, rel=1e-9)
            assert got.baseline_mv == pytest.approx(base.baseline_mv * c, abs=1e-9)

    def test_variance_scales_with_the_square_of_the_amplitude(self) -> None:
        base = self._features(1.0)
        for c in (0.5, 2.0):
            got = self._features(c)
            assert got.variance_mv == pytest.approx(base.variance_mv * c**2, rel=1e-9)

    def test_shape_features_are_amplitude_invariant(self) -> None:
        base = self._features(1.0)
        for c in (0.5, 2.0):
            got = self._features(c)
            assert got.spike_duration_mean_ms == pytest.approx(base.spike_duration_mean_ms)
            assert got.mean_spike_frequency_hz == pytest.approx(base.mean_spike_frequency_hz)
            assert got.peak_latency_ms == pytest.approx(base.peak_latency_ms)
            assert got.skewness == pytest.approx(base.skewness, abs=1e-9)
            assert got.kurtosis == pytest.approx(base.kurtosis, abs=1e-9)


# ============================================================================
# Determinism
# ============================================================================
class TestDeterminism:
    """Identical facts must give identical substantive answers."""

    SIGNAL = _spike_train(30.0, 12, 60.0)

    def test_features_are_identical_for_identical_input(self) -> None:
        a = _proc().extract_features(self.SIGNAL)
        b = _proc().extract_features(self.SIGNAL)
        assert _ident(a) == _ident(b)

    def test_assessment_content_is_identical_for_identical_input(self) -> None:
        engine = PlantNeuroEngine()
        a = engine.analyze_from_signals(self.SIGNAL)
        b = engine.analyze_from_signals(self.SIGNAL)
        for field in (
            "electrical_stress_type", "electrical_confidence", "electrical_severity",
            "integrated_severity_score", "integrated_stress_level", "recommendations",
        ):
            assert getattr(a, field) == getattr(b, field), field
        assert _ident(a.signal_features) == _ident(b.signal_features)

    def test_shuffled_event_order_does_not_change_the_conclusion(self) -> None:
        # The same multiset of events on the same time grid, presented in the
        # opposite order, must produce the same statistics and the same
        # classification: the processor reads statistics of the whole record
        # and nothing in the classification depends on event order. The
        # tolerances are filter round-off, not specification -- the convolution
        # at a sample is a different sum of its neighbours once the events are
        # permuted -- so the counts and the derived frequency agree exactly and
        # the filtered amplitudes agree to ~1e-6 relative.
        positions = np.linspace(1000, 5400, 12).astype(int)
        forward = np.zeros(6000)
        forward[positions] = [30.0 if i % 2 == 0 else 20.0 for i in range(12)]
        backward = np.zeros(6000)
        backward[positions] = [20.0 if i % 2 == 0 else 30.0 for i in range(12)]
        fa = _proc().extract_features(forward)
        fb = _proc().extract_features(backward)
        # Exactly order-invariant: every multiset statistic.
        assert fa.num_spikes == fb.num_spikes == 12
        assert fa.mean_spike_frequency_hz == pytest.approx(fb.mean_spike_frequency_hz, rel=1e-9)
        assert fa.spike_amplitude_mean_mv == pytest.approx(
            fb.spike_amplitude_mean_mv, rel=1e-4
        )
        assert _proc().classify_stress(fa) == _proc().classify_stress(fb)
        # Neighborhood-dependent, not order-invariant: the filtered value at
        # an event's position is a sum over its neighbours, so swapping which
        # events carry 30 mV and which carry 20 mV changes each event's own
        # superposition. The peak and the half-amplitude width therefore move
        # by a few percent; the true law is that both stay within a small
        # band of each other, not that they agree bit-for-bit.
        assert fa.peak_mv == pytest.approx(fb.peak_mv, rel=0.05), (
            f"peak moved {100 * (fa.peak_mv - fb.peak_mv) / fb.peak_mv:+.1f} % "
            "between the two orderings"
        )
        assert fa.spike_duration_mean_ms == pytest.approx(fb.spike_duration_mean_ms, rel=0.10)


# ============================================================================
# Severity and stress-level bounds
# ============================================================================
class TestSeverityAndLevelBounds:
    """Severity is a weighted sum of clipped ratios, so it must stay in [0, 1]."""

    LEVEL_ORDER = {"healthy": 0, "mild_stress": 1, "moderate_stress": 2, "severe_stress": 3,
                   "critical": 4}

    @pytest.mark.parametrize("count,amp", [(0, 0.0), (1, 15.0), (12, 30.0), (150, 40.0),
                                           (700, 60.0)])
    def test_severity_stays_within_the_unit_interval(self, count: int, amp: float) -> None:
        sig = _spike_train(amp, count, 60.0) if count else np.zeros(6000)
        severity = PlantNeuroEngine()._compute_signal_severity(
            _proc().extract_features(sig)
        )
        assert 0.0 <= severity <= 1.0, severity

    def test_severity_is_monotone_in_the_event_rate(self) -> None:
        engine = PlantNeuroEngine()
        severities = [
            engine._compute_signal_severity(_proc().extract_features(_spike_train(40.0, n, 60.0)))
            for n in (0, 5, 10, 20, 40, 80, 150)
        ]
        assert severities == sorted(severities), severities

    def test_severity_is_monotone_in_event_amplitude(self) -> None:
        engine = PlantNeuroEngine()
        severities = [
            engine._compute_signal_severity(
                _proc().extract_features(_spike_train(amp, 12, 60.0))
            )
            for amp in (12.0, 20.0, 30.0, 45.0, 60.0, 90.0)
        ]
        assert severities == sorted(severities), severities

    def test_stress_level_is_monotone_in_severity(self) -> None:
        engine = PlantNeuroEngine()
        level_of = engine._map_severity_to_level
        ranks = [self.LEVEL_ORDER[level_of(s).value] for s in np.linspace(0.0, 1.0, 201)]
        assert ranks == sorted(ranks)

    def test_degraded_signal_never_lowers_the_stress_level(self) -> None:
        engine = PlantNeuroEngine()
        levels = [
            engine._map_severity_to_level(
                engine._compute_signal_severity(
                    _proc().extract_features(_spike_train(40.0, n, 60.0))
                )
            ).value
            for n in (0, 5, 20, 40, 80, 150)
        ]
        ranks = [self.LEVEL_ORDER[level] for level in levels]
        assert ranks == sorted(ranks), levels

    def test_voc_confidence_and_severity_are_bounded(self) -> None:
        engine = PlantNeuroEngine()
        profiles = [
            VOCProfile(
                compounds={"E-2-hexenal": 500.0, "linalool": 400.0, "methyl salicylate": 300.0}
            ),
            VOCProfile(compounds={"E-2-hexenal": 1e6, "linalool": 1e6}),
            VOCProfile(compounds={"isoprene": 1.0}),
        ]
        for profile in profiles:
            assessment = engine.analyze_from_voc(profile)
            assert 0.0 <= assessment.voc_confidence <= 1.0
            assert 0.0 <= assessment.voc_severity <= 1.0


# ============================================================================
# Honest rejection of empty, short and non-finite input
# ============================================================================
class TestHonestRejection:
    """An unknown input must not be answered as if it were a measurement."""

    def test_empty_signal_is_rejected_by_the_engine(self) -> None:
        with pytest.raises(ValueError):
            _proc().extract_features(np.array([], dtype=np.float64))

    def test_short_signal_is_rejected_by_the_engine(self) -> None:
        # scipy's filtfilt requires len(x) > padlen = 3*max(len(a),len(b))-1 = 15
        # for a 2nd-order Butterworth, so 16 samples is the real minimum.
        for n in (8, 12, 15):
            with pytest.raises(ValueError):
                _proc().extract_features(np.zeros(n))
        assert _proc().extract_features(np.zeros(16)).sampling_rate == FS

    def test_gateway_rejects_empty_and_short_input(self) -> None:
        payloads: list[dict] = [{"signal_mv": []}, {"signal_mv": [1.0] * 5}]
        for payload in payloads:
            r = GW.execute(
                GatewayRequest(
                    model_id="PLANT_NEURO", inputs=payload, input_units={}, provenance=PROV
                )
            )
            assert isinstance(r, GatewayError), payload
            assert r.error_code == "EXECUTION_ERROR"

    def test_gateway_names_the_real_minimum_length(self) -> None:
        r = GW.execute(
            GatewayRequest(
                model_id="PLANT_NEURO", inputs={"signal_mv": [1.0] * 15}, input_units={},
                provenance=PROV,
            )
        )
        assert isinstance(r, GatewayError)
        assert "16" in r.message, r.message

    def test_non_finite_samples_are_rejected_by_the_engine(self) -> None:
        """Regression guard (defect now closed, signals.py:135-139).

        A NaN- or inf-contaminated recording used to be filtered and answered as
        a healthy assessment with NaN in ``peak_mv``, ``variance_mv`` and
        ``skewness``. A statistic of an unmeasurable recording is not a
        measurement, so it must be rejected rather than reported.
        """
        for fill in (np.nan, np.inf, -np.inf):
            with pytest.raises(ValueError, match="non-finite"):
                _proc().extract_features(np.full(2000, fill, dtype=np.float64))

    def test_non_finite_samples_are_rejected_by_the_route(self) -> None:
        """Regression guard (defect now closed, gateway PLANT_NEURO route)."""
        for fill in (np.nan, np.inf):
            r = GW.execute(
                GatewayRequest(
                    model_id="PLANT_NEURO", inputs={"signal_mv": [float(fill)] * 2000},
                    input_units={}, provenance=PROV,
                )
            )
            assert isinstance(r, GatewayError), fill
            assert r.error_code == "EXECUTION_ERROR"
            assert "non-finite" in r.message, r.message

    def test_gateway_names_the_finiteness_requirement(self) -> None:
        r = GW.execute(
            GatewayRequest(
                model_id="PLANT_NEURO",
                inputs={"signal_mv": [1.0] * 100 + [float("nan")] + [1.0] * 100},
                input_units={}, provenance=PROV,
            )
        )
        assert isinstance(r, GatewayError)
        assert "non-finite" in r.message, r.message


# ============================================================================
# Advisory consistency: labels, configuration, and served advice
# ============================================================================
class TestAdvisoryConsistency:
    """Emitted stress labels must match the advisory table and the config."""

    def test_electrical_confidence_is_bounded_to_the_unit_interval(self) -> None:
        """Regression guard (defect now closed, engine.py:171).

        ``electrical_confidence`` was ``features.num_spikes / 10.0`` with no
        clip, so it was 4.0 at forty events and 8.9 at eighty-nine, and it also
        feeds ``_combine_stress_types`` where it is multiplied by a modality
        weight, so an over-counted burst both exceeded the unit interval and
        dominated the fusion.
        """
        for count in (4, 40, 89):
            assessment = _assessment_from(_spike_train(30.0, count, 120.0))
            assert 0.0 <= assessment.electrical_confidence <= 1.0, (
                f"{assessment.signal_features.num_spikes} spikes reported confidence "
                f"{assessment.electrical_confidence}"
            )

    def test_every_reachable_label_is_served_by_the_recommendation_table(self) -> None:
        """Regression guard (defect now closed, signals.py:261-285).

        The classifier used to return the catch-all labels ``abiotic`` and
        ``biotic`` -- neither a key of ``STRESS_RECOMMENDATIONS`` nor in the
        method's own documented return list -- so a named stress produced an
        empty advisory, and the ``healthy`` it advertised was never returned.
        Here each documented label is produced (by exercising the classifier's
        branches directly, then through a real recording) and each must either
        carry advice or be the documented no-action case.
        """
        engine = PlantNeuroEngine()
        processor = _proc()
        documents = set(PlantNeuroEngine.STRESS_RECOMMENDATIONS)

        # Every branch of classify_stress, driven with synthetic features so
        # the label set itself -- not one DSP realisation -- is the subject.
        branch_cases = {
            "healthy": SignalFeatures(num_spikes=0),
            "drought": SignalFeatures(num_spikes=5, peak_mv=30.0, mean_spike_frequency_hz=1.0),
            "pathogen": SignalFeatures(num_spikes=3, peak_mv=30.0, mean_spike_frequency_hz=0.2,
                                       spike_amplitude_mean_mv=25.0),
            "herbivory": SignalFeatures(num_spikes=3, peak_mv=30.0,
                                        mean_spike_frequency_hz=0.2,
                                        spike_amplitude_mean_mv=15.0,
                                        spike_duration_mean_ms=300.0),
            "mechanical": SignalFeatures(num_spikes=1, peak_mv=30.0,
                                         mean_spike_frequency_hz=0.0,
                                         peak_latency_ms=35000.0),
            "unclassified": SignalFeatures(num_spikes=1, peak_mv=30.0,
                                           mean_spike_frequency_hz=0.0,
                                           peak_latency_ms=10.0),
        }
        for expected_label, features in branch_cases.items():
            got = processor.classify_stress(features, threshold_ap=10.0,
                                            threshold_spike_freq=0.5)
            assert got == expected_label, f"branch {expected_label!r} returned {got!r}"
            assert got in documents or got in {"unclassified", "healthy"}, (
                f"label {got!r} has no advisory mapping"
            )
            if got not in {"unclassified", "healthy"}:
                assert engine.STRESS_RECOMMENDATIONS[got], (
                    f"label {got!r} maps to an empty advisory"
                )

        # The same law at the assessment level, on real recordings.
        recordings = {
            "drought": _spike_train(30.0, 40, 60.0),
            "pathogen": _spike_train(35.0, 4, 60.0),
            "mechanical": np.concatenate([np.zeros(3500), [30.0], np.zeros(4500)]),
        }
        for expected_label, sig in recordings.items():
            assessment = engine.analyze_from_signals(sig)
            recorded = assessment.signal_features
            assert recorded is not None
            label = assessment.electrical_stress_type
            assert label == expected_label, (
                f"{expected_label!r} fixture classified as {label!r} "
                f"(num_spikes={recorded.num_spikes})"
            )
            assert assessment.recommendations, f"{label!r} returned no recommendations"

    def test_configured_ap_threshold_controls_detection(self) -> None:
        """Regression guard (defect now closed, signals.py:56-67, engine.py:138).

        ``PlantNeuroConfig.ap_threshold_mv`` used to reach only
        ``classify_stress`` while the events had already been counted against
        the hard-coded ``AP_THRESHOLD_MV = 10.0``, so configuring 30 mV left a
        12 mV event counted as an action potential.
        """
        for threshold, expected in ((10.0, 3), (20.0, 1), (30.0, 0)):
            engine = PlantNeuroEngine(config=PlantNeuroConfig(ap_threshold_mv=threshold))
            sig = np.zeros(6000)
            sig[1500], sig[3000], sig[4500] = 12.0, 25.0, 12.0
            feats = engine.signal_processor.extract_features(sig)
            assert feats.num_spikes == expected, (
                f"ap_threshold_mv={threshold} counted {feats.num_spikes} events; only "
                f"{expected} of the injected amplitudes reach that line"
            )


# ============================================================================
# The gateway route
# ============================================================================
class TestGatewayRoute:
    """``PLANT_NEURO`` through ``engine/gateway/__init__.py.execute``."""

    SIGNAL = _spike_train(30.0, 12, 60.0)

    def test_route_returns_labelled_values(self) -> None:
        values = _neuro_values({"signal_mv": list(self.SIGNAL)}).values
        assert values["model_id"] == "PLANT_NEURO"
        neuro = values["neuro"]
        assert neuro["computed"] is True
        assert neuro["data_source"] == "modelled"
        features = neuro["signal_features"]
        assert features["computed"] is True
        assert features["sampling_rate"] == FS
        for key in (
            "baseline_mv", "num_spikes", "spike_amplitude_mean_mv", "spike_duration_mean_ms",
            "mean_spike_frequency_hz", "dominant_frequency_hz", "variance_mv",
            "skewness", "kurtosis", "peak_mv", "peak_latency_ms", "duration_s",
        ):
            assert key in features, key

    def test_route_matches_the_engine_directly(self) -> None:
        direct = _proc().extract_features(self.SIGNAL)
        routed = _neuro_values({"signal_mv": list(self.SIGNAL)}).values["neuro"]["signal_features"]
        for key in ("baseline_mv", "num_spikes", "spike_amplitude_mean_mv",
                    "spike_duration_mean_ms", "variance_mv", "skewness", "kurtosis",
                    "dominant_frequency_hz"):
            assert routed[key] == pytest.approx(getattr(direct, key)), key

    def test_route_content_is_deterministic(self) -> None:
        # trace_id / execution timestamps and the assessment's own wall-clock
        # stamp differ per call by design (one trace per execution); every
        # substantive value must be identical.
        first = _neuro_values({"signal_mv": list(self.SIGNAL)}).values
        second = _neuro_values({"signal_mv": list(self.SIGNAL)}).values

        def strip(neuro: dict) -> dict:
            return {k: v for k, v in neuro.items() if k != "timestamp"}

        assert strip(first["neuro"]) == strip(second["neuro"])

    def test_route_requires_a_signal(self) -> None:
        r = GW.execute(
            GatewayRequest(model_id="PLANT_NEURO", inputs={}, input_units={}, provenance=PROV)
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "INVALID_REQUEST"
