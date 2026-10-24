# Stage 41-D — Repository test audit

## Result

`INCOMPLETE`: the full test suite did not finish, so the observed failures
cannot be named or classified from pytest's final summary.

## Attempts and evidence

1. `python -m pytest -q --timeout=300` was attempted with the configured
   repository venv. Pytest exited before collection because `--timeout` is not
   a recognized option in that environment; `pytest-timeout` is unavailable.
2. Installing `pytest-timeout` into `D:\eco_nojin\.venv` failed because the
   environment could not resolve `files.pythonhosted.org`.
3. A fallback `python -m pytest -q` started without the runbook's required
   `PYTHONPATH` and `SECRET_KEY` values. At 5% progress, the quiet output showed
   at least five `F` markers. No test names or tracebacks had been emitted.
   Progress then stalled while a child pytest process consumed CPU. The
   specific process IDs for that run were stopped; the run exited with code 1
   before pytest's failure summary.
4. The fallback run printed that the C++ extension was unavailable and Python
   kernels were used; it also printed that `gpytorch` was unavailable. Since
   the run had no final report and did not use the required environment, its
   failures are not reliable evidence of Stage 41 regressions.
5. The focused Stage 40/41 suite did complete: **25 passed** across
   `test_stage41_runner_failure_path.py`,
   `test_stage41_provenance_contract.py`,
   `test_stage41b_frozen_equivalence.py`, and
   `test_stage40_parameter_plumbing.py`.
   Ruff also passed for the runner and new regression test.

## Failure classification

| Test | File/module | Classification | Stage 42 blocker? |
|---|---|---|---|
| At least five failures observed by quiet progress markers; test IDs unavailable | Not recoverable from the interrupted run | UNCLASSIFIED; full run was interrupted before summary and lacked required environment variables | Yes, until a configured full-suite run identifies and classifies them |

No claim is made that these failures are pre-existing, Stage 41-caused,
other-agent, or real bugs. Do not infer test identity from the progress markers.

## Required follow-up

Repeat the full suite in the configured venv with `PYTHONPATH` and `SECRET_KEY`
set in the same shell, and with a working timeout mechanism. Save complete
pytest output so every failing test can be classified. Do not weaken or skip
tests to obtain a passing result.
