#!/usr/bin/env python3
"""Citation-link checker (EXTERNAL-ALIGNMENT-PLAN item X-10).

Extracts DOIs from the model cards (``engine/models/cards/*.md``) and the
indicator records (``indicators/*.yaml``), then resolves each one against
doi.org with a HEAD request.

Why doi.org and not only Crossref: our cards cite Zenodo (DataCite) records
too, and a Crossref-only resolution would false-negative every one of them.

Rules:
* CI/dev-layer only. It is never imported by ``engine/`` and never runs at
  model-execution time (ZED §2.2ج concerns the scientific core, not the audit
  layer).
* A resolvable DOI returns 2xx/3xx; an unresolvable one is reported DEAD.
* A network failure is reported ERROR and exits 3, so a broken CI network can
  never be mistaken for a citation defect.
* ISBNs are only reported as unverifiable-offline; they never gate.

Exit codes: 0 = all resolvable, 1 = at least one DEAD, 2 = no DOIs found,
3 = network error while resolving.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]

#: 10.xxxx/... DOI registrant/suffix form. Parentheses are allowed inside the
#: suffix (publisher DOIs use them); the balance is resolved in _clean_doi.
DOI_PATTERN = re.compile(
    r"(?<![0-9])(10\.\d{4,9}/[^\s\"'<>\}\],;]+)",
)

SCAN_TARGETS = [
    "engine/models/cards/*.md",
    "indicators/*.yaml",
    "reports/eco-nojin/FORMULA-VALIDATION-REGISTER.md",
    "reports/hydroma/HYDROMA_REFERENCE_DATA_CATALOG.md",
    "reports/hydroma/HYDROMA_SCIENTIFIC_CRITERIA.md",
]


def _clean_doi(raw: str) -> str:
    """Strip prose punctuation without breaking parenthesised DOIs.

    ScienceDirect DOIs carry balanced parentheses in the suffix
    (``10.1016/S0022-1694(01)00466-8``), while prose puts DOIs inside its own
    parentheses (``see (10.5281/zenodo.123)``). The rule is therefore
    balance-aware: drop surplus closing parentheses, and truncate at the last
    unmatched opening parenthesis.
    """
    doi = raw.rstrip(r""". , ; : } ] " '""")
    while doi.count(")") > doi.count("(") and doi.endswith(")"):
        doi = doi[:-1]
    if doi.count("(") > doi.count(")"):
        doi = doi[: doi.rfind("(")]
    return doi.rstrip(".")


def extract_dois(text: str) -> list[str]:
    """Return the unique, cleaned DOIs found in *text*, in first-seen order."""
    seen: dict[str, None] = {}
    for match in DOI_PATTERN.finditer(text):
        doi = _clean_doi(match.group(1))
        seen.setdefault(doi, None)
    return list(seen)


def resolve_doi(doi: str, timeout: float = 20.0) -> str:
    """Resolve one DOI against doi.org: OK / DEAD / ERROR.

    Two operational facts shape this rule (both measured on 2026-10-10):

    * A GET is required, not a HEAD: Atypon/Wiley, T&F, AMS, AGU and ASCE all
      answer HEAD with 403, which a HEAD-only checker misreports as dead.
    * Registration, not publisher bot policy, is what a citation check can
      assert: AGU/Wiley and T&F return 403 to automated GETs on the landing
      page they redirected to. So a DOI that resolved away from doi.org to a
      publisher record is OK; only a 4xx/5xx *from doi.org itself* (no
      redirect happened) means the DOI is unregistered.

    ERROR means the network failed, never a citation defect.
    """
    try:
        response = requests.get(
            f"https://doi.org/{doi}",
            allow_redirects=True,
            timeout=timeout,
            stream=True,
            headers={
                "User-Agent": "eco-nojin-citation-checker/1.0 (mailto:audit@eco-nojin.local)",
                "Accept": "text/html",
            },
        )
        final_host = urlparse(response.url).netloc
        status = response.status_code
        response.close()
    except requests.RequestException:
        return "ERROR"
    if "doi.org" not in final_host:
        return "OK"  # resolved to a publisher record (403/401 = bot block)
    return "OK" if status < 400 else "DEAD"


def collect_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in SCAN_TARGETS:
        files.extend(sorted(root.glob(pattern)))
    return files


def scan(root: Path, timeout: float = 10.0) -> dict[str, dict[str, str]]:
    """Resolve every DOI in the scan targets.

    Returns ``{doi: {"status": ..., "sources": "path[:path]"}}``.
    """
    results: dict[str, dict[str, str]] = {}
    for path in collect_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for doi in extract_dois(text):
            entry = results.setdefault(doi, {"status": "PENDING", "sources": []})
            entry["sources"].append(str(path.relative_to(root)))
    for doi, entry in results.items():
        entry["status"] = resolve_doi(doi, timeout=timeout)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args(argv)

    results = scan(Path(args.root), timeout=args.timeout)
    if not results:
        print("NO_DOIS_FOUND — nothing to check")
        return 2

    dead = [d for d, e in results.items() if e["status"] == "DEAD"]
    errors = [d for d, e in results.items() if e["status"] == "ERROR"]

    for doi, entry in sorted(results.items()):
        sources = ", ".join(sorted(set(entry["sources"])))
        print(f"{entry['status']:5s} {doi}  <- {sources}")

    print(f"SUMMARY total={len(results)} ok={len(results) - len(dead) - len(errors)} dead={len(dead)} error={len(errors)}")
    if dead:
        print("DEAD: " + ", ".join(sorted(dead)))
    if errors:
        print("ERROR: " + ", ".join(sorted(errors)) + " (network — not a citation defect)")
    if errors:
        return 3
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
