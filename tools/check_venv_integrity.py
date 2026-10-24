"""Site-packages integrity audit against wheel RECORD hashes.

Why this exists
---------------
On 2026-10-10 two packages in the working venv were found to have been
modified after installation (``passlib`` carried an environment-variable read
that upstream does not have; ``huggingface_hub`` had an injected import).
Neither showed up in any test: the project's own suites never import them on
the paths that were changed. This audit is the mechanical check that does.

Every wheel ships a ``dist-info/RECORD`` listing a sha256 for each installed
file. A file whose content no longer matches its RECORD hash was modified after
installation -- that is what this reports.

Known false positives, handled explicitly:

* packages upgraded in place leave the *previous* version's ``dist-info``
  behind (``ruff-0.11.2`` next to ``ruff-0.16.4``). The stale RECORD's hashes
  describe the old build, so its entries mismatch the current files. A file is
  only reported when NO RECORD that lists it matches (the stale RECORD's
  entries are covered by the current build's RECORD). Per package name the
  audit treats the ``dist-info`` whose RECORD actually matches the installed
  tree as active and lists the remainder under ``stale_dist_info``; picking
  the active one by name sort instead mislabeled all five real stale
  directories when this was measured on 2026-10-10.
* ``Scripts/*.exe`` launchers are recorded relative to the venv root; paths
  are resolved from ``Lib/site-packages`` upwards, which lands there.

Usage::

    python tools/check_venv_integrity.py [--venv PATH] [--json PATH]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path

DEFAULT_VENV = Path(r"D:\eco_nojin\.venv")


def _dist_version(dist_info: Path) -> str:
    metadata = dist_info / "METADATA"
    if not metadata.is_file():
        return ""
    match = re.search(r"^Version:\s*(\S+)", metadata.read_text(encoding="utf-8", errors="replace"), re.M)
    return match.group(1) if match else ""


def _version_key(version: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", version)[:4]
    return tuple(int(p) for p in parts) or (0,)


def audit(venv: Path) -> dict:
    site = venv / "Lib" / "site-packages"
    if not site.is_dir():
        raise SystemExit(f"no site-packages under {venv}")

    # Collect every RECORD once per package name. A file is only reported when
    # NO RECORD that lists it matches: packages upgraded in place leave the
    # previous version's dist-info behind, and a stale RECORD's hashes describe
    # the old build -- treating a single-RECORD mismatch as tampering produced
    # 15 false positives in a pristine venv on 2026-10-10.
    by_package: dict[str, list[Path]] = {}
    for record in sorted(site.glob("*.dist-info/RECORD")):
        name = record.parent.name.split("-")[0].lower()
        by_package.setdefault(name, []).append(record)

    # path -> (expected hash, recorded size, package, dist-info) for every
    # RECORD entry that names it
    entries: dict[str, list[tuple[str, str, str, str]]] = {}
    for records in by_package.values():
        for record in records:
            package = record.parent.name.split("-")[0]
            for line in record.read_text(encoding="utf-8", errors="replace").splitlines():
                parts = line.rsplit(",", 2)
                if len(parts) != 3 or not parts[1].startswith("sha256="):
                    continue
                relpath, hashspec, size = parts[0], parts[1][len("sha256="):], parts[2]
                entries.setdefault(str(site / relpath), []).append(
                    (hashspec, size, package, record.parent.name)
                )

    checked = missing = unreadable = 0
    mismatches: list[dict[str, str]] = []
    # Per dist-info: how many of its listed files are present on disk, and how
    # many of those hash-match its RECORD. The dist-info whose RECORD actually
    # describes the installed tree is the active one; the rest is upgrade
    # residue (see the module docstring).
    dist_present: dict[str, int] = {}
    dist_matched: dict[str, int] = {}
    for path, candidates in entries.items():
        target = Path(path)
        if not target.is_file():
            missing += 1
            continue
        try:
            payload = target.read_bytes()
        except OSError:
            unreadable += 1
            continue
        checked += 1
        digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()
        for _expected, _size, _pkg, dist in candidates:
            dist_present[dist] = dist_present.get(dist, 0) + 1
        matched = False
        for expected, _size, _pkg, dist in candidates:
            if digest == expected:
                matched = True
                dist_matched[dist] = dist_matched.get(dist, 0) + 1
        if matched:
            continue
        try:
            relative = str(target.relative_to(site))
        except ValueError:
            relative = str(target)
        package, dist_info = candidates[0][2], candidates[0][3]
        mismatches.append(
            {
                "package": package,
                "dist_info": dist_info,
                "path": relative,
                "recorded_size": candidates[0][1],
                "actual_size": str(len(payload)),
                "size_matches": str(len(payload)) == candidates[0][1],
                "sibling_dist_info": str(len(candidates)),
            }
        )

    stale: list[str] = []
    for records in by_package.values():
        if len(records) < 2:
            continue
        active = max(
            records,
            key=lambda r: (
                dist_matched.get(r.parent.name, 0),
                dist_matched.get(r.parent.name, 0) == dist_present.get(r.parent.name, 0),
                _version_key(_dist_version(r.parent)),
                r.parent.name,
            ),
        )
        stale.extend(r.parent.name for r in records if r is not active)

    return {
        "venv": str(venv),
        "packages_audited": len(by_package),
        "files_checked": checked,
        "missing": missing,
        "unreadable": unreadable,
        "mismatches": mismatches,
        "mismatch_count": len(mismatches),
        "stale_dist_info": sorted(stale),
        "status": "FAIL" if mismatches else "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", type=Path, default=DEFAULT_VENV)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    result = audit(args.venv)
    print(f"venv                : {result['venv']}")
    print(f"packages audited    : {result['packages_audited']}")
    print(f"files checked       : {result['files_checked']}")
    print(f"stale dist-info     : {len(result['stale_dist_info'])} "
          f"(upgrade residue: {', '.join(result['stale_dist_info'][:6])})")
    print(f"MISMATCHED          : {result['mismatch_count']}")
    for entry in result["mismatches"]:
        print(f"  {entry['package']:16s} {entry['path']} "
              f"(size matches RECORD: {entry['size_matches']})")
    print(f"status              : {result['status']}")

    if args.json is not None:
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"report              : {args.json}")

    if args.json is None and result["mismatch_count"]:
        print("\nA size match with a hash mismatch means the content changed after")
        print("installation; a size mismatch usually means a stale dist-info from an")
        print("upgrade. Compare against a known-good venv before concluding.")
    return 2 if result["mismatch_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
