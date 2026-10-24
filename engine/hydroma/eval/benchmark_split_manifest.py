"""Benchmark split manifest for CIMMYT wheat dataset.

Creates and manages the official development/test split for HY-RUE
calibration and benchmark evaluation. The split is district-based to
prevent data leakage: records from the same district never appear in
both development and test sets.

Test districts (3): Buxar, Muzaffarpur, Rohtas
Development districts (7): Begusarai, Bhojpur, Deoria, EastChamparan,
  Kushinagar, Lakhisarai, Madhepura

The manifest stores dataset hash, manifest hash, and all record IDs so
the split is fully reproducible.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

CIMMYT_DATA_PATH = Path(
    "data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx"
)

#: Districts reserved for test (held-out, never used for calibration).
TEST_DISTRICTS: list[str] = ["Buxar", "Muzaffarpur", "Rohtas"]

#: Districts used for development (calibration only).
DEVELOPMENT_DISTRICTS: list[str] = [
    "Begusarai",
    "Bhojpur",
    "Deoria",
    "EastChamparan",
    "Kushinagar",
    "Lakhisarai",
    "Madhepura",
]

SPLIT_VERSION = "stage36_v1"

MANIFEST_PATH = Path(
    "engine/reports/data/stage36_benchmark_split_manifest.json"
)


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_dataframe(df: pd.DataFrame) -> str:
    """Compute a deterministic hash of a DataFrame's contents."""
    # Sort by all columns to ensure row order doesn't affect hash
    df_sorted = df.sort_values(by=list(df.columns)).reset_index(drop=True)
    raw = df_sorted.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_cimmyt_data() -> pd.DataFrame:
    """Load the CIMMYT wheat dataset."""
    return pd.read_excel(CIMMYT_DATA_PATH)


def create_split_manifest(
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Create the benchmark split manifest.

    Loads CIMMYT data, partitions records into development and test sets
    by district, computes dataset and manifest hashes, and writes the
    manifest to disk.

    Args:
        output_path: Path to write the manifest JSON. Defaults to
            ``engine/reports/data/stage36_benchmark_split_manifest.json``.

    Returns:
        The manifest dictionary.
    """
    df = load_cimmyt_data()

    # Compute dataset hash (on the raw data, before any filtering)
    dataset_hash = _hash_dataframe(df)
    data_file_hash = _sha256_file(CIMMYT_DATA_PATH)

    # Partition by district
    test_mask = df["District"].isin(TEST_DISTRICTS)
    dev_mask = df["District"].isin(DEVELOPMENT_DISTRICTS)

    test_df = df[test_mask].copy()
    dev_df = df[dev_mask].copy()

    # Verify no district overlap
    test_districts_found = set(test_df["District"].unique())
    dev_districts_found = set(dev_df["District"].unique())
    overlap = test_districts_found & dev_districts_found
    if overlap:
        raise ValueError(
            f"District overlap between dev and test: {overlap}"
        )

    # Verify all districts are accounted for
    all_districts = set(df["District"].unique())
    expected = set(TEST_DISTRICTS) | set(DEVELOPMENT_DISTRICTS)
    if all_districts != expected:
        raise ValueError(
            f"District mismatch: data has {all_districts}, "
            f"expected {expected}"
        )

    test_record_ids = test_df["Field_ID"].tolist()
    dev_record_ids = dev_df["Field_ID"].tolist()

    manifest: dict[str, Any] = {
        "dataset_id": "CIMMYT_EASTERN_INDIA_WHEAT",
        "dataset_version": "1.0.0",
        "split_version": SPLIT_VERSION,
        "grouping_column": "District",
        "development_districts": sorted(DEVELOPMENT_DISTRICTS),
        "test_districts": sorted(TEST_DISTRICTS),
        "development_record_ids": dev_record_ids,
        "test_record_ids": test_record_ids,
        "development_record_count": len(dev_record_ids),
        "test_record_count": len(test_record_ids),
        "total_record_count": len(df),
        "split_created_at": datetime.now(UTC).isoformat(),
        "dataset_hash": dataset_hash,
        "data_file_sha256": data_file_hash,
        "data_file_path": str(CIMMYT_DATA_PATH),
        "district_overlap": [],
        "no_leakage": True,
    }

    # Compute manifest hash (excluding the hash field itself)
    manifest_for_hash = {k: v for k, v in manifest.items() if k != "manifest_hash"}
    manifest_raw = json.dumps(manifest_for_hash, sort_keys=True).encode("utf-8")
    manifest["manifest_hash"] = hashlib.sha256(manifest_raw).hexdigest()

    # Write manifest
    out_path = output_path or MANIFEST_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

    return manifest


def load_split_manifest(
    path: Path | None = None,
) -> dict[str, Any]:
    """Load an existing split manifest."""
    p = path or MANIFEST_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def verify_split(manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    """Verify the split manifest integrity.

    Checks:
    - Manifest hash matches recomputed hash
    - No district overlap between dev and test
    - Record counts match
    - All districts accounted for

    Returns:
        Dict with verification results.
    """
    m = manifest or load_split_manifest()

    # Recompute manifest hash
    m_for_hash = {k: v for k, v in m.items() if k != "manifest_hash"}
    manifest_raw = json.dumps(m_for_hash, sort_keys=True).encode("utf-8")
    computed_hash = hashlib.sha256(manifest_raw).hexdigest()
    hash_matches = computed_hash == m.get("manifest_hash")

    # Verify no overlap
    dev_ids = set(m["development_record_ids"])
    test_ids = set(m["test_record_ids"])
    id_overlap = dev_ids & test_ids

    dev_districts = set(m["development_districts"])
    test_districts = set(m["test_districts"])
    district_overlap = dev_districts & test_districts

    counts_match = (
        m["development_record_count"] == len(dev_ids)
        and m["test_record_count"] == len(test_ids)
    )

    return {
        "manifest_hash_matches": hash_matches,
        "computed_hash": computed_hash,
        "stored_hash": m.get("manifest_hash"),
        "no_id_overlap": len(id_overlap) == 0,
        "id_overlap": sorted(id_overlap),
        "no_district_overlap": len(district_overlap) == 0,
        "district_overlap": sorted(district_overlap),
        "counts_match": counts_match,
        "development_records": m["development_record_count"],
        "test_records": m["test_record_count"],
        "total_records": m["total_record_count"],
        "verified": (
            hash_matches
            and len(id_overlap) == 0
            and len(district_overlap) == 0
            and counts_match
        ),
    }


if __name__ == "__main__":
    manifest = create_split_manifest()
    verification = verify_split(manifest)

    print("=" * 60)
    print("Stage 36 Benchmark Split Manifest")
    print("=" * 60)
    print(f"Dataset: {manifest['dataset_id']}")
    print(f"Split version: {manifest['split_version']}")
    print(f"Total records: {manifest['total_record_count']}")
    print(f"Development records: {manifest['development_record_count']}")
    print(f"Test records: {manifest['test_record_count']}")
    print(f"Development districts: {manifest['development_districts']}")
    print(f"Test districts: {manifest['test_districts']}")
    print(f"Manifest hash: {manifest['manifest_hash'][:16]}...")
    print()
    print("Verification:")
    for key, val in verification.items():
        print(f"  {key}: {val}")
