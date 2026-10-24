#!/usr/bin/env python3
"""B-4 — scan the business layer for inline copies of published formulas.

The engine owns every published relation HyDroMA computes: FAO-56 Hargreaves
eq. 52, the FAO-56 net-radiation terms, the USDA SCS curve-number triplet, the
RUSLE topographic factor, the Theis well function, the van Genuchten retention
curve and RothC. ``services/`` is meant to *call* the engine through
``services/_gateway_facade.py``, never to re-implement it. This tool is the
measurement half of remediation item B-4: it reports every place in the
business layer where a published-formula skeleton appears inline.

It is deliberately stdlib-only (no engine import, no services import), so it
runs in any checkout, in CI, before the engine is even importable.

Signatures
----------
Each signature names the published relation it stands for:

``HARGREAVES_EQ52``
    FAO-56 eq. 52 (Allen et al. 1998): the literal ``0.0023`` together with
    ``17.8``, or ``0.0023`` raised against a ``** 0.5`` diurnal-range term.
``MISSING_0_408``
    The eq. 52 skeleton consuming ``Ra`` in MJ/m2/day without the FAO-56
    eq. 40 conversion ``0.408`` — the 2.45x over-statement recorded in the
    divergence register.
``PM_NET_SHORTWAVE_077``
    FAO-56 net shortwave (``1 - 0.23``) applied to ``Rs``.
``PM_RSO_ELEVATION_075``
    FAO-56 clear-sky radiation ``Rso = (0.75 + 2e-5 z) Ra``.
``PM_RADIATION_TO_ET_0408``
    The MJ -> mm conversion ``0.408`` inside an ``Rn`` (net radiation) term.
``SCS_CN_RETENTION``
    USDA SCS retention ``S = 25400 / CN - 254`` (or the mm form
    ``(1000 / CN - 10) * 25.4``).
``SCS_CN_ABSTRACTION``
    The initial abstraction ``Ia = 0.2 S`` (and its ``0.8 S`` runoff twin).
``SCS_CN_RUNOFF_EQ``
    The runoff depth ``Q = (P - Ia)^2 / (P - Ia + 0.8 S)``.
``RUSLE_LS_22_13``
    The RUSLE slope-length factor ``L = (lambda / 22.13) ** m``.
``RUSLE_SLOPE_STEEPNESS_10_8``
    The two-branch USDA steepness factor (``10.8 sin`` / ``16.8 sin``).
``RUSLE_M_EXPONENT_0896``
    The slope-length exponent ``beta = (sin / 0.0896) / (3 sin^0.8 + 0.56)``.
``THEIS_WELL_FUNCTION_4PI``
    The Theis drawdown ``s = Q / (4 pi T) W(u)``.
``THEIS_EXP_INTEGRAL``
    The exponential-integral well function ``expi`` / ``exp1`` / ``E1``.
``VG_THETA_PARAM``
    van Genuchten ``theta_r`` / ``theta_s`` used outside the engine's soil
    package: a copy when it is arithmetic, a schema constant otherwise.
``VG_EXPONENT_HALF``
    The retention-curve shape ``(1 + (alpha h)^n) ** m`` with ``m = 0.5``.
``ROTHC_DECOMP_RATE``
    The RothC-26.3 pool decomposition rates (DPM 10.0, RPM 0.3, BIO 0.66,
    HUM 0.02, IOM 0.0 per year).
``ROTHC_IOM_049``
    The Falloon et al. (1998) initialisation ``IOM = 0.049 SOC^1.139``.

Severity
--------
``HIGH`` — a re-implementation of a quantity the engine computes. The copy
can drift from the canonical value, and the B-3 divergence register records
that it already has (the 0.48 exponent, the missing 0.408 conversion, two
different PM equations).
``INFO`` — the same identifier appearing in a schema, a parameter spec or a
default. No science is computed there, but a published parameter name belongs
in the model registry rather than in a hand-written declaration.

Scope
-----
``services/**/*.py``, ``runtime/**/*.py`` and ``adapters/**/*.py`` by default
(``--root`` adds or replaces directories). Test modules (any ``tests/``
directory, ``test_*.py``, ``conftest.py``) are excluded because pinning a
published value is what tests are *for*; ``--include-tests`` scans them too.
Comments and docstrings are never matched: prose that names a formula is
documentation, not a second implementation.

Usage
-----
    python tools/find_inline_science.py [--root DIR ...] [--md PATH] [--json]
                                        [--include-tests]

Exit status
-----------
``0`` — only ``INFO`` hits remain; ``1`` — at least one ``HIGH`` hit remains,
which is what CI gates on; ``2`` — the scan could not run (unknown root).
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import sys
import tokenize
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ROOTS: tuple[str, ...] = ("services", "runtime", "adapters")
EXCLUDED_DIRS = frozenset(
    {
        "__pycache__",
        ".git",
        ".hypothesis",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".snapshots",
        ".venv",
        "build",
        "dist",
        "node_modules",
        "venv",
    }
)
TEST_DIR_NAMES = frozenset({"tests"})
TEST_FILE_NAMES = frozenset({"conftest.py"})
TEST_FILE_PREFIX = "test_"

SEVERITY_HIGH = "HIGH"
SEVERITY_INFO = "INFO"
SNIPPET_WIDTH = 100

STRING_TOKEN_TYPES = {tokenize.STRING}
for _token_name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"):
    _token_type = getattr(tokenize, _token_name, None)
    if _token_type is not None:
        STRING_TOKEN_TYPES.add(_token_type)

RA_NAMES = frozenset({"Ra", "ra", "ra_mj", "ra_m2_day", "ra_m2", "ra_solar"})
RS_NAMES = frozenset({"Rs", "rs", "solar", "solar_radiation"})
RN_NAMES = frozenset({"Rn", "rn", "rnet", "net_radiation"})
S_NAMES = frozenset({"S", "s", "retention", "retention_s", "ret", "s_mm"})
RUNOFF_NAMES = frozenset({"runoff", "runoff_mm", "surface_runoff"})
T_NAMES = frozenset({"T", "transmissivity", "trans"})
EXPI_NAMES = frozenset({"expi", "exp1", "E1"})
VG_CURVE_NAMES = frozenset({"alpha", "theta_r", "theta_s", "vg", "vg_alpha", "vg_n"})

NUMBER_FORMS: dict[str, tuple[str, ...]] = {
    "0.0023": (r"0\.0023", r"2\.3e-3"),
    "17.8": (r"17\.8",),
    "0.408": (r"0\.408\d*",),
    "0.77": (r"0\.77",),
    "0.75": (r"0\.75",),
    "2e-5": (r"2e-5", r"0\.00002"),
    "25400": (r"25400",),
    "25.4": (r"25\.4",),
    "10.8": (r"10\.8",),
    "16.8": (r"16\.8",),
    "22.13": (r"22\.13",),
    "0.0896": (r"0\.0896",),
    "0.049": (r"0\.049",),
}

DECLARATION_RE = re.compile(
    r"\b(?:ParamSpec|Field|Column|mapped_column|argument|query|Option)\s*\("
)
ANNOTATION_DEFAULT_RE = re.compile(r":\s*(?:float|int|str|Decimal|Any)\b[^=]*=")
ARITHMETIC_OPERATOR = r"(?:\*\*|[-+*/])"
ROTHC_RATE_RE = re.compile(
    r"""["']?(dpm|rpm|bio|hum|iom)["']?\s*[:=]\s*(10\.0|0\.3|0\.66|0\.02|0\.0)\b""",
    re.IGNORECASE,
)
THEIS_PI_RE = re.compile(r"4\s*\*\s*(?:math\.)?(?:pi|\u03c0)\b|4\u03c0")
HALF_POWER_RE = re.compile(r"\*\*\s*0\.5\b")
RUNOFF_SQUARE_RE = re.compile(r"\*\*\s*2\s*/")
ABSTRACTION_FACTOR_RE = re.compile(r"(?<![\w.])0\.[28]\s*\*")
SCS_CONTEXT_RE = re.compile(r"(?i)(curve_number|\bcn\b|scs|runoff)")


@dataclass(frozen=True)
class Hit:
    """One inline published-formula skeleton, at one line of one file."""

    path: str
    line: int
    signature: str
    family: str
    severity: str
    published: str
    route: str
    snippet: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class FileScan:
    """A source file reduced to the lines that can carry executable code."""

    path: str
    source: str
    lines: list[str]
    code_lines: dict[int, str]
    string_spans: dict[int, list[tuple[int, int]]]
    names: dict[int, tuple[str, ...]]


@dataclass(frozen=True)
class Signature:
    """A published relation, how to recognise it, and where it must live."""

    sig_id: str
    family: str
    published: str
    route: str
    detect: Callable[[FileScan], list[tuple[int, str]]]


def _number_matches(scan: FileScan, lineno: int, key: str) -> list[re.Match[str]]:
    """Matches for a numeric literal on ``lineno``, outside string literals."""
    line = scan.code_lines.get(lineno)
    if line is None:
        return []
    found: list[re.Match[str]] = []
    for form in NUMBER_FORMS[key]:
        pattern = rf"(?<![\w.]){form}(?![\w])"
        for match in re.finditer(pattern, line):
            if not _inside_string(scan, lineno, match.start()):
                found.append(match)
    return found


def _file_has_number(scan: FileScan, key: str) -> bool:
    return any(_number_matches(scan, lineno, key) for lineno in scan.code_lines)


def _inside_string(scan: FileScan, lineno: int, position: int) -> bool:
    return any(lo < position < hi for lo, hi in scan.string_spans.get(lineno, ()))


def _names_on(scan: FileScan, lineno: int) -> frozenset[str]:
    return frozenset(scan.names.get(lineno, ()))


def _has_name(scan: FileScan, lineno: int, wanted: frozenset[str]) -> bool:
    return bool(_names_on(scan, lineno) & wanted)


def _has_name_like(scan: FileScan, lineno: int, predicate: Callable[[str], bool]) -> bool:
    return any(predicate(name) for name in _names_on(scan, lineno))


def _is_cn_name(name: str) -> bool:
    lowered = name.lower()
    return lowered in {"cn", "curve_number"} or lowered.startswith("cn_") or lowered.endswith("_cn")


def _is_ia_name(name: str) -> bool:
    lowered = name.lower()
    return lowered == "ia" or lowered.startswith("ia_")


def _name_touches_arithmetic(line: str, name: str) -> bool:
    escaped = re.escape(name)
    pattern = rf"\b{escaped}\b\s*{ARITHMETIC_OPERATOR}|{ARITHMETIC_OPERATOR}\s*\b{escaped}\b"
    return re.search(pattern, line) is not None


def _is_declaration(line: str) -> bool:
    return bool(DECLARATION_RE.search(line) or ANNOTATION_DEFAULT_RE.search(line))


def _has_hargreaves_skeleton(scan: FileScan) -> bool:
    return _file_has_number(scan, "0.0023")


def _ra_arithmetic_line(scan: FileScan, lineno: int) -> bool:
    line = scan.code_lines.get(lineno, "")
    return any(
        name in RA_NAMES and _name_touches_arithmetic(line, name)
        for name in _names_on(scan, lineno)
    )


def _mentions_scs_context(scan: FileScan) -> bool:
    return any(SCS_CONTEXT_RE.search(line) for line in scan.code_lines.values())


def detect_hargreaves_eq52(scan: FileScan) -> list[tuple[int, str]]:
    """FAO-56 eq. 52 written inline: 0.0023 with 17.8, or with a ``** 0.5``."""
    hits: list[tuple[int, str]] = []
    for lineno, line in scan.code_lines.items():
        if not _number_matches(scan, lineno, "0.0023"):
            continue
        if _number_matches(scan, lineno, "17.8") or HALF_POWER_RE.search(line):
            hits.append((lineno, SEVERITY_HIGH))
    return hits


def detect_missing_0_408(scan: FileScan) -> list[tuple[int, str]]:
    """The eq. 52 body consuming Ra in MJ/m2/day without the 0.408 conversion."""
    if _file_has_number(scan, "0.408") or not _has_hargreaves_skeleton(scan):
        return []
    return [
        (lineno, SEVERITY_HIGH)
        for lineno in scan.code_lines
        if _ra_arithmetic_line(scan, lineno)
    ]


def detect_pm_net_shortwave(scan: FileScan) -> list[tuple[int, str]]:
    """FAO-56 net shortwave ``(1 - 0.23) Rs`` written inline."""
    return [
        (lineno, SEVERITY_HIGH)
        for lineno in scan.code_lines
        if _number_matches(scan, lineno, "0.77") and _has_name(scan, lineno, RS_NAMES)
    ]


def detect_pm_rso_elevation(scan: FileScan) -> list[tuple[int, str]]:
    """FAO-56 clear-sky radiation ``Rso = (0.75 + 2e-5 z) Ra`` written inline."""
    return [
        (lineno, SEVERITY_HIGH)
        for lineno in scan.code_lines
        if _number_matches(scan, lineno, "0.75") and _number_matches(scan, lineno, "2e-5")
    ]


def detect_pm_radiation_to_et(scan: FileScan) -> list[tuple[int, str]]:
    """The MJ -> mm ``0.408`` conversion inside an ``Rn`` term."""
    return [
        (lineno, SEVERITY_HIGH)
        for lineno in scan.code_lines
        if _number_matches(scan, lineno, "0.408") and _has_name(scan, lineno, RN_NAMES)
    ]


def detect_scs_retention(scan: FileScan) -> list[tuple[int, str]]:
    """USDA SCS retention ``S = 25400 / CN - 254`` (or the mm form)."""
    return [
        (lineno, SEVERITY_HIGH)
        for lineno in scan.code_lines
        if (_number_matches(scan, lineno, "25400") or _number_matches(scan, lineno, "25.4"))
        and _has_name_like(scan, lineno, _is_cn_name)
    ]


def detect_scs_abstraction(scan: FileScan) -> list[tuple[int, str]]:
    """The initial abstraction ``Ia = 0.2 S`` and its ``0.8 S`` runoff twin."""
    if not _mentions_scs_context(scan):
        return []
    return [
        (lineno, SEVERITY_HIGH)
        for lineno, line in scan.code_lines.items()
        if ABSTRACTION_FACTOR_RE.search(line) and _has_name(scan, lineno, S_NAMES)
    ]


def detect_scs_runoff_equation(scan: FileScan) -> list[tuple[int, str]]:
    """The runoff depth ``Q = (P - Ia)^2 / (P - Ia + 0.8 S)``."""
    if not _mentions_scs_context(scan):
        return []
    hits: list[tuple[int, str]] = []
    for lineno, line in scan.code_lines.items():
        if not RUNOFF_SQUARE_RE.search(line):
            continue
        has_ia = _has_name_like(scan, lineno, _is_ia_name)
        has_runoff_pair = _has_name(scan, lineno, RUNOFF_NAMES) and _has_name(scan, lineno, S_NAMES)
        if has_ia or has_runoff_pair:
            hits.append((lineno, SEVERITY_HIGH))
    return hits


def detect_rusle_ls_22_13(scan: FileScan) -> list[tuple[int, str]]:
    """The RUSLE slope-length factor ``L = (lambda / 22.13) ** m``."""
    return [
        (lineno, SEVERITY_HIGH)
        for lineno in scan.code_lines
        if _number_matches(scan, lineno, "22.13")
    ]


def _has_sine_name(scan: FileScan, lineno: int) -> bool:
    return _has_name_like(
        scan, lineno, lambda name: name == "sin" or name.startswith("sin_") or name.endswith("_sin")
    )


def detect_rusle_slope_steepness(scan: FileScan) -> list[tuple[int, str]]:
    """The two-branch USDA steepness factor (``10.8 sin`` / ``16.8 sin``)."""
    hits: list[tuple[int, str]] = []
    for lineno in scan.code_lines:
        if not _has_sine_name(scan, lineno):
            continue
        if _number_matches(scan, lineno, "10.8") or _number_matches(scan, lineno, "16.8"):
            hits.append((lineno, SEVERITY_HIGH))
    return hits


def detect_rusle_m_exponent(scan: FileScan) -> list[tuple[int, str]]:
    """The RUSLE slope-length exponent ``beta = (sin / 0.0896) / (...)``."""
    hits: list[tuple[int, str]] = []
    for lineno in scan.code_lines:
        if _has_sine_name(scan, lineno) and _number_matches(scan, lineno, "0.0896"):
            hits.append((lineno, SEVERITY_HIGH))
    return hits


def detect_theis_well_function(scan: FileScan) -> list[tuple[int, str]]:
    """The Theis drawdown denominator ``4 pi T``."""
    return [
        (lineno, SEVERITY_HIGH)
        for lineno, line in scan.code_lines.items()
        if THEIS_PI_RE.search(line) and _has_name(scan, lineno, T_NAMES)
    ]


def detect_theis_exp_integral(scan: FileScan) -> list[tuple[int, str]]:
    """The exponential-integral well function ``expi`` / ``exp1`` / ``E1``."""
    return [
        (lineno, SEVERITY_HIGH)
        for lineno in scan.code_lines
        if _has_name(scan, lineno, EXPI_NAMES)
    ]


VG_THETA_TOKEN_RE = re.compile(r"\btheta_(?:r|s)\b")


def _split_by_string(scan: FileScan, lineno: int, matches: list[re.Match[str]]) -> tuple[
    list[re.Match[str]], list[re.Match[str]]
]:
    """Split matches into those in executable code and those inside literals."""
    in_code: list[re.Match[str]] = []
    in_string: list[re.Match[str]] = []
    for match in matches:
        if _inside_string(scan, lineno, match.start()):
            in_string.append(match)
        else:
            in_code.append(match)
    return in_code, in_string


def detect_vg_theta_parameter(scan: FileScan) -> list[tuple[int, str]]:
    """van Genuchten ``theta_r`` / ``theta_s`` outside the engine's soil package."""
    hits: list[tuple[int, str]] = []
    for lineno, line in scan.code_lines.items():
        found = list(VG_THETA_TOKEN_RE.finditer(line))
        in_code, in_string = _split_by_string(scan, lineno, found)
        computed = any(_name_touches_arithmetic(line, match.group(0)) for match in in_code)
        if computed:
            hits.append((lineno, SEVERITY_HIGH))
        elif (in_code or in_string) and _is_declaration(line):
            hits.append((lineno, SEVERITY_INFO))
    return hits


def detect_vg_exponent_half(scan: FileScan) -> list[tuple[int, str]]:
    """The retention-curve shape ``(1 + (alpha h)^n) ** m`` with ``m = 0.5``."""
    return [
        (lineno, SEVERITY_HIGH)
        for lineno, line in scan.code_lines.items()
        if HALF_POWER_RE.search(line) and _has_name(scan, lineno, VG_CURVE_NAMES)
    ]


def detect_rothc_decomposition_rate(scan: FileScan) -> list[tuple[int, str]]:
    """A RothC-26.3 pool name bound to a published decomposition rate."""
    hits: list[tuple[int, str]] = []
    for lineno, line in scan.code_lines.items():
        match = ROTHC_RATE_RE.search(line)
        if match is None:
            continue
        rate_start = line.index(match.group(2), match.start())
        if not _inside_string(scan, lineno, rate_start):
            hits.append((lineno, SEVERITY_HIGH))
    return hits


def detect_rothc_iom_049(scan: FileScan) -> list[tuple[int, str]]:
    """The Falloon et al. (1998) initialisation ``IOM = 0.049 SOC^1.139``."""
    return [
        (lineno, SEVERITY_HIGH)
        for lineno in scan.code_lines
        if _number_matches(scan, lineno, "0.049")
    ]


SIGNATURES: tuple[Signature, ...] = (
    Signature(
        sig_id="HARGREAVES_EQ52",
        family="Hargreaves / FAO-56",
        published=(
            "Allen et al. 1998, FAO-56 eq. 52: "
            "ET0 = 0.0023 (Tmean + 17.8) (Tmax - Tmin)^0.5 Ra"
        ),
        route=(
            "services/_gateway_facade.calc_et0_hargreaves"
            " -> engine/hydroma/climate/et_calculator.py::calc_et0_hargreaves"
            " (gateway CANON-002)"
        ),
        detect=detect_hargreaves_eq52,
    ),
    Signature(
        sig_id="MISSING_0_408",
        family="Hargreaves / FAO-56",
        published="Allen et al. 1998, FAO-56 eq. 40: Ra (MJ/m2/day) x 0.408 -> mm/day",
        route=(
            "services/_gateway_facade.calc_et0_hargreaves"
            " -> engine/hydroma/climate/et_calculator.py::_hargreaves_core"
            " (gateway CANON-002; the core owns the 0.408 conversion)"
        ),
        detect=detect_missing_0_408,
    ),
    Signature(
        sig_id="PM_NET_SHORTWAVE_077",
        family="Penman-Monteith / net radiation",
        published="Allen et al. 1998, FAO-56 eq. 38: Rns = (1 - 0.23) Rs",
        route=(
            "services/_gateway_facade.calc_et0_penman_monteith"
            " -> engine/hydroma/climate/et_calculator.py::calc_net_radiation"
            " (gateway CANON-001 / CANON-011_RAD)"
        ),
        detect=detect_pm_net_shortwave,
    ),
    Signature(
        sig_id="PM_RSO_ELEVATION_075",
        family="Penman-Monteith / net radiation",
        published="Allen et al. 1998, FAO-56 eq. 37: Rso = (0.75 + 2e-5 z) Ra",
        route=(
            "services/_gateway_facade.calc_et0_penman_monteith"
            " -> engine/hydroma/climate/et_calculator.py::calc_net_radiation"
            " (gateway CANON-001 / CANON-011_RAD)"
        ),
        detect=detect_pm_rso_elevation,
    ),
    Signature(
        sig_id="PM_RADIATION_TO_ET_0408",
        family="Penman-Monteith / net radiation",
        published="Allen et al. 1998, FAO-56 eq. 40/41: Rn converted by 0.408 into mm/day",
        route=(
            "services/_gateway_facade.calc_et0_penman_monteith"
            " -> engine/hydroma/climate/et_calculator.py::calc_net_radiation"
            " (gateway CANON-001 / CANON-011_RAD)"
        ),
        detect=detect_pm_radiation_to_et,
    ),
    Signature(
        sig_id="SCS_CN_RETENTION",
        family="SCS curve number",
        published="USDA SCS-CN: S = 25400 / CN - 254 mm (or (1000 / CN - 10) * 25.4)",
        route=(
            "services/_gateway_facade.calculate_runoff"
            " -> engine/hydroma/models/runoff_model.py::RunoffCalculator._scs_cn_method"
            " (gateway CANON-004)"
        ),
        detect=detect_scs_retention,
    ),
    Signature(
        sig_id="SCS_CN_ABSTRACTION",
        family="SCS curve number",
        published="USDA SCS-CN: Ia = 0.2 S, runoff denominator P + 0.8 S",
        route=(
            "services/_gateway_facade.calculate_runoff"
            " -> engine/hydroma/models/runoff_model.py::RunoffCalculator._scs_cn_method"
            " (gateway CANON-004)"
        ),
        detect=detect_scs_abstraction,
    ),
    Signature(
        sig_id="SCS_CN_RUNOFF_EQ",
        family="SCS curve number",
        published="USDA SCS-CN: Q = (P - Ia)^2 / (P - Ia + 0.8 S) for P > Ia, else 0",
        route=(
            "services/_gateway_facade.calculate_runoff"
            " -> engine/hydroma/models/runoff_model.py::RunoffCalculator._scs_cn_method"
            " (gateway CANON-004)"
        ),
        detect=detect_scs_runoff_equation,
    ),
    Signature(
        sig_id="RUSLE_LS_22_13",
        family="RUSLE",
        published="Wischmeier & Smith 1978: L = (lambda / 22.13)^m",
        route=(
            "services/_gateway_facade.compute_erosion"
            " -> engine/land/erosion_risk.py::calculate_ls_factor"
            " (gateway CANON-007 / RUSLE_LS)"
        ),
        detect=detect_rusle_ls_22_13,
    ),
    Signature(
        sig_id="RUSLE_SLOPE_STEEPNESS_10_8",
        family="RUSLE",
        published="USDA two-branch steepness: 10.8 sin + 0.03 below 9 %, 16.8 sin - 0.50 above",
        route=(
            "services/_gateway_facade.compute_erosion"
            " -> engine/land/erosion_risk.py::calculate_ls_factor"
            " (gateway CANON-007 / RUSLE_LS)"
        ),
        detect=detect_rusle_slope_steepness,
    ),
    Signature(
        sig_id="RUSLE_M_EXPONENT_0896",
        family="RUSLE",
        published="RUSLE handbook: beta = (sin / 0.0896) / (3 sin^0.8 + 0.56)",
        route=(
            "services/_gateway_facade.compute_erosion"
            " -> engine/land/erosion_risk.py::calculate_ls_factor"
            " (gateway CANON-007 / RUSLE_LS)"
        ),
        detect=detect_rusle_m_exponent,
    ),
    Signature(
        sig_id="THEIS_WELL_FUNCTION_4PI",
        family="Theis groundwater",
        published="Theis 1935: s = Q / (4 pi T) W(u)",
        route=(
            "services/_gateway_facade.GroundwaterService"
            " -> engine/hydroma/theis.py::compute_theis (gateway CANON-005)"
        ),
        detect=detect_theis_well_function,
    ),
    Signature(
        sig_id="THEIS_EXP_INTEGRAL",
        family="Theis groundwater",
        published="Theis 1935 well function: W(u) = expi(u) = exp1(u) = -Ei(-u)",
        route=(
            "services/_gateway_facade.GroundwaterService"
            " -> engine/hydroma/groundwater/models.py::calculate_theis_drawdown"
            " (gateway CANON-005)"
        ),
        detect=detect_theis_exp_integral,
    ),
    Signature(
        sig_id="VG_THETA_PARAM",
        family="Van Genuchten / Rosetta",
        published=(
            "van Genuchten 1980: theta(h) = theta_r + (theta_s - theta_r) "
            "/ (1 + |alpha h|^n)^m"
        ),
        route=(
            "services/_gateway_facade.van_genuchten_theta"
            " -> engine/hydroma/soil/physics.py::van_genuchten_theta"
            " (gateway CANON-006; parameters from SOIL_VG_PARAMETERS)"
        ),
        detect=detect_vg_theta_parameter,
    ),
    Signature(
        sig_id="VG_EXPONENT_HALF",
        family="Van Genuchten / Rosetta",
        published="van Genuchten 1980: m = 1 - 1/n, written inline as a 0.5 exponent",
        route=(
            "services/_gateway_facade.van_genuchten_theta"
            " -> engine/hydroma/soil/physics.py::van_genuchten_theta"
            " (gateway CANON-006; parameters from SOIL_VG_PARAMETERS)"
        ),
        detect=detect_vg_exponent_half,
    ),
    Signature(
        sig_id="ROTHC_DECOMP_RATE",
        family="RothC",
        published="RothC-26.3: DPM 10.0, RPM 0.3, BIO 0.66, HUM 0.02, IOM 0.0 per year",
        route=(
            "services/_gateway_facade.RothCRunner"
            " -> engine/hydroma/simulation/runners/rothc_runner.py::run_rothc"
        ),
        detect=detect_rothc_decomposition_rate,
    ),
    Signature(
        sig_id="ROTHC_IOM_049",
        family="RothC",
        published="Falloon et al. 1998: IOM = 0.049 SOC^1.139",
        route=(
            "services/_gateway_facade.RothCRunner"
            " -> engine/hydroma/simulation/runners/rothc_runner.py::initial_pools"
        ),
        detect=detect_rothc_iom_049,
    ),
)


def _docstring_lines(tree: ast.Module) -> set[int]:
    """Line numbers occupied by module, class and function docstrings."""
    lines: set[int] = set()
    nodes: list[ast.AST] = [tree]
    while nodes:
        node = nodes.pop()
        docstring = None
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node, clean=False)
            for child in ast.iter_child_nodes(node):
                nodes.append(child)
        if docstring is None or not node.body:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            start = first.value.lineno
            end = first.value.end_lineno or start
            lines.update(range(start, end + 1))
    return lines


def _token_index(
    source: str, lines: list[str]
) -> tuple[
    dict[int, list[tuple[int, int]]], dict[int, tuple[int, int]], dict[int, tuple[str, ...]]
]:
    """Per-line string spans, comment spans and identifier tokens."""
    string_spans: dict[int, list[tuple[int, int]]] = {}
    comment_spans: dict[int, tuple[int, int]] = {}
    names: dict[int, list[str]] = {}
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            row, col = token.start
            if token.type == tokenize.COMMENT:
                comment_spans[row] = (col, token.end[1])
            elif token.type in STRING_TOKEN_TYPES:
                last_row = token.end[0]
                for span_row in range(row, last_row + 1):
                    low = col if span_row == row else 0
                    high = token.end[1] if span_row == last_row else len(lines[span_row - 1]) + 1
                    string_spans.setdefault(span_row, []).append((low, high))
            elif token.type == tokenize.NAME:
                names.setdefault(row, []).append(token.string)
    except (tokenize.TokenError, IndentationError, SyntaxError, IndexError):
        return string_spans, comment_spans, {key: tuple(value) for key, value in names.items()}
    return string_spans, comment_spans, {key: tuple(value) for key, value in names.items()}


def scan_file(abs_path: Path, display_path: str) -> FileScan | None:
    """Read one Python file and reduce it to executable lines only."""
    try:
        source = abs_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None
    docstrings = _docstring_lines(tree) if tree is not None else set()
    string_spans, comment_spans, names = _token_index(source, lines)
    code_lines: dict[int, str] = {}
    for lineno, text in enumerate(lines, start=1):
        if lineno in docstrings:
            continue
        if not text.strip():
            continue
        comment = comment_spans.get(lineno)
        if comment is not None and not text[: comment[0]].strip():
            continue
        end = comment[0] if comment is not None else len(text)
        code_lines[lineno] = text[:end]
    return FileScan(
        path=display_path,
        source=source,
        lines=lines,
        code_lines=code_lines,
        string_spans=string_spans,
        names=names,
    )


def _display_root(root: Path) -> str:
    try:
        return root.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return root.as_posix()


def _display_path(abs_path: Path, root: Path) -> str:
    resolved = abs_path.resolve()
    for base in (PROJECT_ROOT, root):
        try:
            return resolved.relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return resolved.as_posix()


def is_scannable(path: Path, *, include_tests: bool = False) -> bool:
    """Whether a discovered file is in scope for the scan."""
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False
    if include_tests:
        return True
    if path.name in TEST_FILE_NAMES or path.name.startswith(TEST_FILE_PREFIX):
        return False
    return not any(part in TEST_DIR_NAMES for part in path.parts)


def iter_python_files(root: Path, *, include_tests: bool = False) -> Iterator[Path]:
    """Every in-scope Python file under one root."""
    if root.is_file():
        if root.suffix == ".py" and is_scannable(root, include_tests=include_tests):
            yield root
        return
    for path in sorted(root.rglob("*.py")):
        if is_scannable(path, include_tests=include_tests):
            yield path


def scan_roots(
    roots: list[Path], *, include_tests: bool = False
) -> tuple[list[Hit], int, int]:
    """Scan every root; return the hits plus the scanned and skipped counts."""
    hits: list[Hit] = []
    scanned = 0
    skipped = 0
    for root in roots:
        for abs_path in iter_python_files(root, include_tests=include_tests):
            display = _display_path(abs_path, root)
            file_scan = scan_file(abs_path, display)
            if file_scan is None:
                skipped += 1
                continue
            scanned += 1
            for signature in SIGNATURES:
                for lineno, severity in signature.detect(file_scan):
                    hits.append(
                        Hit(
                            path=display,
                            line=lineno,
                            signature=signature.sig_id,
                            family=signature.family,
                            severity=severity,
                            published=signature.published,
                            route=signature.route,
                            snippet=file_scan.lines[lineno - 1].strip()[:SNIPPET_WIDTH],
                        )
                    )
    hits.sort(key=lambda hit: (hit.path, hit.line, hit.signature))
    return hits, scanned, skipped


def _snippet_cell(hit: Hit) -> str:
    return hit.snippet.replace("|", "\\|").replace("`", "'")


def _route_cell(route: str) -> str:
    return " → ".join(f"`{part.strip()}`" for part in route.split("->"))


def _hit_count(count: int) -> str:
    return f"{count} hit" if count == 1 else f"{count} hits"


def summarise(hits: list[Hit]) -> dict[str, dict[str, int]]:
    """Hit counts per signature, split by severity."""
    summary: dict[str, dict[str, int]] = {}
    for signature in SIGNATURES:
        summary[signature.sig_id] = {SEVERITY_HIGH: 0, SEVERITY_INFO: 0}
    for hit in hits:
        bucket = summary.setdefault(hit.signature, {SEVERITY_HIGH: 0, SEVERITY_INFO: 0})
        bucket[hit.severity] = bucket.get(hit.severity, 0) + 1
    return summary


def build_payload(
    hits: list[Hit], roots: list[Path], scanned: int, skipped: int
) -> dict[str, object]:
    """The machine-readable scan result."""
    high = sum(1 for hit in hits if hit.severity == SEVERITY_HIGH)
    info = len(hits) - high
    return {
        "tool": "tools/find_inline_science.py",
        "plan_item": "B-4",
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "roots": [_display_root(root) for root in roots],
        "files_scanned": scanned,
        "files_skipped": skipped,
        "signatures": [signature.sig_id for signature in SIGNATURES],
        "total_hits": len(hits),
        "high_hits": high,
        "info_hits": info,
        "by_signature": summarise(hits),
        "by_file": _count_by(hits, "path"),
        "hits": [hit.as_dict() for hit in hits],
        "exit_code": 1 if high else 0,
    }


def _count_by(hits: list[Hit], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for hit in hits:
        value = getattr(hit, key)
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def render_markdown(payload: dict[str, object], hits: list[Hit]) -> str:
    """The committed B-4 report."""
    summary = payload["by_signature"]
    assert isinstance(summary, dict)
    high = payload["high_hits"]
    info = payload["info_hits"]
    lines: list[str] = [
        "# INLINE-SCIENCE-SCAN — remediation item B-4",
        "",
        f"Generated by `tools/find_inline_science.py` on {payload['generated_utc']}.",
        "",
        "Every hit below is a published-formula skeleton copied into the business layer",
        "(`services/`, `runtime/`, `adapters/`) instead of being routed through the engine.",
        "Comments and docstrings are never matched, and test modules are excluded by default",
        "(`--include-tests` scans them): pinning a published value is what tests are *for*.",
        "",
        "## Summary",
        "",
        f"- Files scanned: **{payload['files_scanned']}**"
        f" (unreadable/skipped: {payload['files_skipped']})",
        f"- Roots: {', '.join(f'`{root}`' for root in payload['roots'])}",  # type: ignore[union-attr]
        f"- Total hits: **{payload['total_hits']}**"
        f" — **{high} HIGH**, **{info} INFO**",
        f"- Exit status: **{payload['exit_code']}**"
        " (0 = only INFO remains, 1 = at least one HIGH remains)",
        "",
        "### Hits by signature and severity",
        "",
        "| Signature | Family | Published source | HIGH | INFO | Total |",
        "|---|---|---|---:|---:|---:|",
    ]
    for signature in SIGNATURES:
        counts = summary.get(signature.sig_id, {SEVERITY_HIGH: 0, SEVERITY_INFO: 0})
        high_count = counts.get(SEVERITY_HIGH, 0)
        info_count = counts.get(SEVERITY_INFO, 0)
        lines.append(
            f"| `{signature.sig_id}` | {signature.family} | {signature.published} "
            f"| {high_count} | {info_count} | {high_count + info_count} |"
        )
    lines.extend(
        [
            "",
            "### Hits by file",
            "",
            "| File | HIGH | INFO | Total |",
            "|---|---:|---:|---:|",
        ]
    )
    by_file = payload["by_file"]
    assert isinstance(by_file, dict)
    for path, _count in by_file.items():
        file_hits = [hit for hit in hits if hit.path == path]
        file_high = sum(1 for hit in file_hits if hit.severity == SEVERITY_HIGH)
        file_info = len(file_hits) - file_high
        lines.append(f"| `{path}` | {file_high} | {file_info} | {len(file_hits)} |")
    lines.extend(
        [
            "",
            "## Full hit table",
            "",
            "| File:line | Severity | Signature | Family | Matched line |",
            "|---|---|---|---|---|",
        ]
    )
    for hit in hits:
        lines.append(
            f"| `{hit.path}:{hit.line}` | **{hit.severity}** | `{hit.signature}` "
            f"| {hit.family} | `{_snippet_cell(hit)}` |"
        )
    lines.extend(
        [
            "",
            "## Severity rule",
            "",
            f"- **HIGH** ({high}) — a re-implementation of a quantity the engine computes.",
            "  The copy can drift from the canonical value; the B-3 divergence register",
            "  records that it already has (the 0.48 Hargreaves exponent, a missing 0.408",
            "  MJ -> mm conversion, two different Penman-Monteith equations).",
            f"- **INFO** ({info}) — the same identifier in a schema, parameter spec or",
            "  default. No science is computed there, but a published parameter name belongs",
            "  in the model registry rather than in a hand-written declaration.",
            "",
            "## Canonical routes — where each signature must be routed",
            "",
            "Each offender above should be replaced by a call through the gateway facade",
            "(remediation items A-2 step 1 and B-3), never by a second implementation:",
            "",
        ]
    )
    for signature in SIGNATURES:
        counts = summary.get(signature.sig_id, {SEVERITY_HIGH: 0, SEVERITY_INFO: 0})
        total = counts.get(SEVERITY_HIGH, 0) + counts.get(SEVERITY_INFO, 0)
        marker = (
            "UNRESOLVED"
            if counts.get(SEVERITY_HIGH, 0)
            else ("declaration only" if total else "clean")
        )
        route = _route_cell(signature.route)
        lines.append(f"- `{signature.sig_id}` ({marker}, {_hit_count(total)}) → {route}")
    lines.extend(
        [
            "",
            "## Done when",
            "",
            "B-4 step 3 is met when this scan reports zero HIGH hits: no published formula",
            "skeleton survives inline in the business layer, only schema constants (INFO)",
            "remain, and `python tools/find_inline_science.py` exits 0.",
            "",
        ]
    )
    return "\n".join(lines)


def render_text(payload: dict[str, object], hits: list[Hit]) -> str:
    """The terminal report."""
    lines: list[str] = [
        "B-4 inline-science scan",
        f"  roots        : {', '.join(payload['roots'])}",  # type: ignore[arg-type]
        f"  files scanned: {payload['files_scanned']} (skipped {payload['files_skipped']})",
        f"  hits         : {payload['total_hits']}"
        f" (HIGH {payload['high_hits']}, INFO {payload['info_hits']})",
        "",
    ]
    if not hits:
        lines.append("no inline published-formula skeletons found")
    for hit in hits:
        lines.append(
            f"{hit.severity:4}  {hit.path}:{hit.line}  {hit.signature}  {hit.snippet}"
        )
    summary = payload["by_signature"]
    assert isinstance(summary, dict)
    lines.extend(["", "by signature:"])
    for signature in SIGNATURES:
        counts = summary.get(signature.sig_id, {SEVERITY_HIGH: 0, SEVERITY_INFO: 0})
        total = counts.get(SEVERITY_HIGH, 0) + counts.get(SEVERITY_INFO, 0)
        if not total:
            continue
        lines.append(
            f"  {signature.sig_id:28} {total:4} hits"
            f" ({counts.get(SEVERITY_HIGH, 0)} HIGH, {counts.get(SEVERITY_INFO, 0)} INFO)"
        )
    lines.append("")
    lines.append(f"exit status: {payload['exit_code']}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find inline copies of published formulas in the business layer (B-4).",
    )
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        metavar="DIR",
        help=(
            "directory to scan (repeatable); defaults to "
            + ", ".join(DEFAULT_ROOTS)
        ),
    )
    parser.add_argument(
        "--md",
        metavar="PATH",
        help="write the markdown report to PATH (B-4 deliverable)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable result instead of the text report",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="also scan test modules (excluded by default)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the scan; return 0 (only INFO), 1 (any HIGH) or 2 (cannot scan)."""
    args = _build_parser().parse_args(argv)
    if args.root:
        roots = [Path(item) for item in args.root]
    else:
        roots = [PROJECT_ROOT / name for name in DEFAULT_ROOTS]
    missing = [root for root in roots if not root.exists()]
    if missing:
        for root in missing:
            print(f"find_inline_science: no such directory: {root}", file=sys.stderr)
        return 2
    hits, scanned, skipped = scan_roots(roots, include_tests=args.include_tests)
    payload = build_payload(hits, roots, scanned, skipped)
    if args.md:
        report_path = Path(args.md)
        if report_path.parent and not report_path.parent.exists():
            report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_markdown(payload, hits), encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
    elif not args.md:
        print(render_text(payload, hits))
    else:
        print(render_text(payload, hits))
    return int(payload["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
