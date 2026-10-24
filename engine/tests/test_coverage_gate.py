"""Guards for ``tools/coverage_gate.py`` and the C-1/C-3 tooling around it.

The coverage gate is the tool that makes SB-08 ("coverage is unmeasured and
must never regress") enforceable. A gate that cannot be wrong is worthless, so
these tests pin the three things that would let it quietly become useless:

* **It reports without running the suite.** ``--json`` reads a report that
  already exists, so the number can be checked — by a test, or by a CI job that
  already produced it — without paying for the whole run again.
* **It refuses to regress.** A measured percentage below the floor exits 1 and
  says which floor was missed. A gate that only ever prints is a dashboard, not
  a gate.
* **It never mistakes "cannot measure" for "measured".** No plugin and no data
  are three distinct outcomes with three distinct exit codes, so a caller has
  to decide what an unmeasured tree means instead of inheriting a green.

The last two tests are not about coverage at all: they pin the pre-edit hook
(C-1 step 3) and the commit-landing order document (C-1 step 2), the other two
artefacts the programme needs in the tree before the 622 uncommitted changes
can be landed safely. A missing hook and a missing landing order are the same
class of problem as a missing coverage number: a claim that evidence exists.

Every check here runs against files in this repository and a fixture written
under ``tmp_path``; nothing is downloaded and the full suite is never invoked.
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "tools" / "coverage_gate.py"
HOOKS_DIR = REPO_ROOT / ".githooks"
LANDING_ORDER = REPO_ROOT / "reports" / "eco-nojin" / "COMMIT-LANDING-ORDER.md"

#: The five Rule-5 Quick-Scan commands, as a fragment each hook must contain.
#: The count is part of the contract: dropping one silently weakens the scan.
QUICK_SCAN_MARKERS = (
    "detect_imports.py",
    "ruff",
    "engine/tests",
    "services/",
    "phantom_path_check.py",
)

#: Exit codes the gate documents in its module docstring.
EXIT_OK = 0
EXIT_BELOW_FLOOR = 1
EXIT_PLUGIN_MISSING = 2
EXIT_NO_DATA = 3

#: The six landing groups of COMMIT-LANDING-ORDER.md, in landing order.
LANDING_GROUPS = ("a", "b", "c", "d", "e", "f")


def _load_gate():
    """Load ``tools/coverage_gate.py`` by path (``tools/`` is not a package)."""
    spec = importlib.util.spec_from_file_location("hydroma_coverage_gate", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["hydroma_coverage_gate"] = module
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def _run_gate(*argv: str) -> tuple[int, str]:
    """Run the gate as a subprocess; returns ``(exit code, stdout+stderr)``."""
    result = subprocess.run(
        [sys.executable, str(GATE_PATH), *argv],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    return result.returncode, result.stdout + result.stderr


def _write_fixture(path: Path, files: dict[str, tuple[int, int]]) -> Path:
    """Write a minimal coverage JSON report: ``{path: (covered, statements)}``.

    Only the keys the gate reads are emitted, so the fixture states exactly
    what the gate is expected to see and nothing the real ``coverage.py`` adds.
    """
    payload = {
        "meta": {"format": 3, "note": "test fixture, not a real run"},
        "files": {
            name: {
                "summary": {
                    "covered_lines": covered,
                    "num_statements": statements,
                    "percent_covered": (
                        100.0 * covered / statements if statements else 0.0
                    ),
                }
            }
            for name, (covered, statements) in files.items()
        },
        "totals": {
            "covered_lines": sum(c for c, _ in files.values()),
            "num_statements": sum(s for _, s in files.values()),
            "percent_covered": (
                100.0 * sum(c for c, _ in files.values())
                / sum(s for _, s in files.values())
                if sum(s for _, s in files.values())
                else 0.0
            ),
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 1. Report-only mode
# ---------------------------------------------------------------------------


def test_gate_reports_without_running_the_full_suite(tmp_path: Path) -> None:
    """``--print`` echoes the measured number and exits 0 without running pytest.

    The fixture is tiny on purpose: two files, twenty statements between them.
    If the gate needed the real suite to answer, a test like this could not
    exist — and the CI job would be the only place the number is ever seen.
    """
    fixture = _write_fixture(
        tmp_path / "coverage.json",
        {
            "engine/tests/test_gate_fixture.py": (8, 10),
            "services/tests/test_gate_fixture.py": (2, 10),
        },
    )
    code, output = _run_gate("--print", "--json", str(fixture))
    assert code == EXIT_OK
    assert "50.00" in output, output
    assert "80.00" in output, output
    assert "20.00" in output, output
    assert "no floor enforced" in output


def test_gate_reads_a_report_written_by_coverage_itself(tmp_path: Path) -> None:
    """The same numbers are read when ``totals`` disagrees with the per-file sums.

    ``coverage.py`` writes ``totals.percent_covered`` for every measured file,
    including any outside ``engine/`` and ``services/``. The gate therefore
    recomputes the area percentages from the per-file statement counts and
    never reuses ``totals`` as the engine figure — otherwise a number describing
    the whole run would be reported as the engine's.
    """
    fixture = tmp_path / "coverage.json"
    fixture.write_text(
        json.dumps(
            {
                "meta": {"format": 3},
                "files": {
                    "engine/hydroma/land/x.py": {
                        "summary": {
                            "covered_lines": 90,
                            "num_statements": 100,
                            "percent_covered": 90.0,
                        }
                    },
                    "conftest.py": {
                        "summary": {
                            "covered_lines": 0,
                            "num_statements": 100,
                            "percent_covered": 0.0,
                        }
                    },
                },
                "totals": {
                    "covered_lines": 90,
                    "num_statements": 200,
                    "percent_covered": 45.0,
                },
            }
        ),
        encoding="utf-8",
    )
    code, output = _run_gate("--print", "--json", str(fixture))
    assert code == EXIT_OK
    assert "engine   :      90.00 %" in output, output


# ---------------------------------------------------------------------------
# 2. Floor enforcement
# ---------------------------------------------------------------------------


def test_floor_is_enforced(tmp_path: Path) -> None:
    """40 % overall fails at ``--floor 55`` and passes at ``--floor 30``.

    The fixture is built so the overall figure is 40.00 % while the engine's own
    figure is 50.00 % — above the default engine floor of 45 %. That makes the
    overall floor the *only* thing that can fail, which is what the two
    assertions below are about: the floor is what changed, so the floor is what
    the result depends on.
    """
    fixture = _write_fixture(
        tmp_path / "coverage.json",
        {
            "engine/hydroma/x.py": (50, 100),
            "services/y.py": (10, 50),
        },
    )
    code, output = _run_gate("--json", str(fixture))
    assert code == EXIT_BELOW_FLOOR
    assert "40.00" in output
    assert "below floor" in output

    code, output = _run_gate("--json", str(fixture), "--floor", "30")
    assert code == EXIT_OK
    assert "READY" in output


def test_engine_floor_is_enforced_on_the_engine_alone(tmp_path: Path) -> None:
    """A services number lifted by thin router tests cannot rescue the engine.

    The engine sits at 30 % while the services sit at 70 %, so the overall
    figure clears an ordinary floor. The engine floor still fails, because it
    is computed over ``engine/`` files only — the whole point of SB-08's
    engine-side rung, and the reason the scientific split (A-1) must land
    before the two halves are allowed to share one number again.
    """
    fixture = _write_fixture(
        tmp_path / "coverage.json",
        {
            "engine/hydroma/a.py": (30, 100),
            "services/b.py": (70, 100),
        },
    )
    code, output = _run_gate(
        "--json", str(fixture), "--floor", "40", "--engine-floor", "45"
    )
    assert code == EXIT_BELOW_FLOOR
    assert "engine 30.00 %" in output


def test_engine_floor_is_waived_when_the_engine_is_not_measured() -> None:
    """No engine statements in the report is reported, not silently passed."""
    measurement = gate.read_measurement(
        {"files": {"services/a.py": {"summary": {"covered_lines": 10, "num_statements": 20}}}}
    )
    assert measurement.engine is None
    assert measurement.services == 50.0
    assert measurement.overall == 50.0


# ---------------------------------------------------------------------------
# 3. "Cannot measure" is not a pass
# ---------------------------------------------------------------------------


def test_missing_cov_plugin_skips_clearly(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Two unmeasurable states, two codes, neither of them green.

    * no coverage data at all (a report path that does not exist) exits
      :data:`EXIT_NO_DATA`;
    * the coverage plugin absent returns :data:`EXIT_PLUGIN_MISSING` and says
      so in words that rule out reading it as a pass.

    The plugin-absent path is exercised in-process with the probe patched out,
    because uninstalling ``pytest-cov`` from the environment a test suite runs
    in is not something a test may do to its host.
    """
    code, output = _run_gate("--json", str(tmp_path / "does-not-exist.json"))
    assert code == EXIT_NO_DATA
    assert "no coverage data" in output.lower()
    assert "does not exist" in output

    monkeypatch.setattr(gate, "_pytest_cov_present", lambda: False)
    returned = gate.main([])
    captured = capsys.readouterr()
    message = captured.out + captured.err
    assert returned == EXIT_PLUGIN_MISSING
    assert "pytest_cov" in message
    assert "NOT a pass" in message
    assert "install pytest-cov" in message.lower()


def test_plugin_probe_agrees_with_the_import_system() -> None:
    """The probe asks the import system rather than hard-coding an answer.

    A probe pinned to ``True`` would make the plugin-absent branch untestable
    and, worse, would report SKIPPED as never reachable in an environment that
    genuinely lacks the plugin.
    """
    assert gate._pytest_cov_present() == (
        importlib.util.find_spec("pytest_cov") is not None
    )


def test_gate_documents_the_ratchet_and_the_a1_split() -> None:
    """SB-08's schedule and the A-1 caveat are in the docstring, not folklore.

    A floor whose schedule lives only in a chat message ratchets by accident:
    someone raises it, or someone forgets it was meant to rise. The docstring
    is the record, and this test refuses to let it be deleted.
    """
    docstring = GATE_PATH.read_text(encoding="utf-8")
    assert "+5 % per month" in docstring
    assert "80 %" in docstring
    assert "SB-08" in docstring
    assert "A-1" in docstring
    assert "separately" in docstring


# ---------------------------------------------------------------------------
# 4. The pre-edit hook (C-1 step 3)
# ---------------------------------------------------------------------------


def _hook_files() -> tuple[Path, Path]:
    powershell = HOOKS_DIR / "pre-edit.ps1"
    posix = HOOKS_DIR / "pre-edit.sh"
    assert powershell.is_file(), f"missing {powershell}"
    assert posix.is_file(), f"missing {posix}"
    return powershell, posix


def _is_executable(path: Path) -> bool:
    """Executable where the platform can express it (POSIX: the mode bit).

    On Windows the POSIX mode bit does not exist; git carries the executable
    bit in the index instead (``git update-index --chmod=+x``), which is what
    ``.githooks/README.md`` records as the install step.
    """
    return os.access(path, os.X_OK)


def test_hook_scripts_exist_and_are_executable() -> None:
    """Both Quick-Scan entry points exist, are executable, and run five checks.

    The five markers are the commands themselves, not a summary of them: a hook
    that stops running the import guard, or the ruff statistics, would still
    print READY and would still be wrong.

    The first line is read as ``utf-8-sig`` so a byte-order mark does not look
    like part of the shebang; ``test_powershell_hook_survives_windows_powershell_parsing``
    explains why the mark must be there at all.
    """
    powershell, posix = _hook_files()
    for path in (powershell, posix):
        assert _is_executable(path), f"{path} is not executable"
        first_line = path.read_text(encoding="utf-8-sig").splitlines()[0]
        assert first_line.startswith("#!"), (path, first_line)

    for marker in QUICK_SCAN_MARKERS:
        for path in (powershell, posix):
            text = path.read_text(encoding="utf-8-sig")
            assert marker in text, f"{path} does not run the {marker!r} check"

    for path in (powershell, posix):
        text = path.read_text(encoding="utf-8-sig")
        assert "READY" in text
        assert "NOT-READY" in text
        assert "PYTHONPATH" in text
        assert "SECRET_KEY" in text

    launcher = HOOKS_DIR / "pre-edit"
    assert launcher.is_file(), f"missing {launcher}"
    assert _is_executable(launcher), f"{launcher} is not executable"


def test_powershell_hook_survives_windows_powershell_parsing() -> None:
    """``.githooks/pre-edit.ps1`` must be UTF-8 **with** a byte-order mark.

    Windows PowerShell 5.1 has no UTF-8 default: a ``.ps1`` without a BOM is
    decoded as the machine's ANSI code page, where the three UTF-8 bytes of an
    em dash (``E2 80 94``) include ``0x94`` — a right double quotation mark in
    cp1252. A single em dash inside a double-quoted string therefore terminates
    that string early, and the file fails to parse at all rather than running
    wrong. The parser is the authority here, so this test asserts both that the
    mark is present and that the file still parses.

    A BOM is the standard encoding for a ``.ps1`` for exactly this reason; the
    bash and Python entry points stay BOM-less, because ``sh`` and CPython both
    default to UTF-8.
    """
    powershell = HOOKS_DIR / "pre-edit.ps1"
    assert powershell.is_file(), f"missing {powershell}"
    raw = powershell.read_bytes()
    assert raw[:3] == b"\xef\xbb\xbf", "pre-edit.ps1 must be saved as UTF-8 with BOM"

    if sys.platform != "win32":  # pragma: no cover - POSIX checkout
        return
    # ``-Command`` in Windows PowerShell 5.1 concatenates any trailing argument
    # onto the command text instead of binding it to ``$args``, so the script is
    # passed as an encoded command — the documented form that avoids shell
    # quoting entirely.
    ps_command = (
        "$errors = $null; $tokens = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        "'{path}', [ref]$tokens, [ref]$errors); "
        "if ($errors.Count -gt 0) {{ "
        "$errors | ForEach-Object {{ Write-Output $_.Message }}; exit 1 }}; "
        "exit 0"
    ).format(path=str(powershell).replace("'", "''"))
    encoded = base64.b64encode(ps_command.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-EncodedCommand",
            encoded,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, (
        "pre-edit.ps1 does not parse under Windows PowerShell; a BOM-less "
        "UTF-8 .ps1 is read as the ANSI code page and the em dash breaks any "
        f"string literal: {result.stdout}{result.stderr}"
    )


def test_hook_quick_flag_skips_the_slow_suite() -> None:
    """``--quick`` must skip the services suite in both implementations.

    The quick flag exists so an edit loop is not minutes long; a flag that runs
    the same five checks would be a trap rather than a shortcut.
    """
    for path in _hook_files():
        text = path.read_text(encoding="utf-8-sig")
        assert re.search(r"--?[Qq]uick", text), path
        assert re.search(r"[Ss]kip[^.]*services|services[^.]*[Ss]kip", text), path
        assert "services/" in text, path
        assert "no:cacheprovider" in text, path


# ---------------------------------------------------------------------------
# 5. The landing order (C-1 step 2)
# ---------------------------------------------------------------------------


def test_landing_order_document_is_complete() -> None:
    """The landing plan names all six groups and the per-group ``git add -p``.

    The order is the safety argument: each group leaves the tree greener than
    the last. A document that names four of the six groups, or that forgets the
    incremental-add recipe, cannot be followed by the next person, and the
    landing degrades back into one 622-file commit — the failure C-1 exists to
    remove.
    """
    assert LANDING_ORDER.is_file(), f"missing {LANDING_ORDER}"
    text = LANDING_ORDER.read_text(encoding="utf-8")

    headings = re.findall(r"^##\s+Group \(([a-f])\)", text, flags=re.MULTILINE)
    assert sorted(headings) == sorted(LANDING_GROUPS), headings

    for group in LANDING_GROUPS:
        assert text.count(f"Group ({group})") >= 1

    assert "git add -p" in text
    assert text.count("git add -p") >= len(LANDING_GROUPS)
    assert "data/" in text
    assert ".mypy_cache" in text
    assert "git status --short" in text
