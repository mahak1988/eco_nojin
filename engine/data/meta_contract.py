"""The raw-data sidecar contract: every raw file ships a ``*.meta.json``.

Spec §4.2, layer A (داده خام / Raw Data) states the rule and its shape:

    **قرارداد:** هر فایل خام باید همراه با ``*.meta.json`` باشد
    *Contract: every raw file must be accompanied by a ``*.meta.json``.*

    {"dataset_id": ..., "source": ..., "url": ..., "license": ...,
     "retrieved_at": ..., "spatial_resolution": ..., "temporal_resolution": ...,
     "checksum_sha256": ..., "local_path": ...}

Spec §4.6 (قرارداد داده / Data Contract) then fixes the field vocabulary of a
dataset record: ``REQUIRED_DATASET_FIELDS`` and ``RECOMMENDED_DATASET_FIELDS``
below, spelled exactly as the spec lists them. The two sections name the same
things with different words, so the §4.2 sidecar spellings are registered as
aliases of the §4.6 canonical names in :data:`FIELD_ALIASES` and both spellings
validate. Nothing is invented on the caller's behalf: a field that was not
supplied stays absent from the record and is reported by the validator.

Severity
--------
A missing or malformed **required** field is an *error* — the sidecar is not
usable. A missing **recommended** field is a *warn* — the sidecar is usable but
incomplete. :func:`validate_meta` returns the blocking problems only, so an
empty list means "valid"; :func:`validate_meta_detailed` returns every finding
with its severity, field name and message.

Sidecar naming convention
-------------------------
``<path>.meta.json`` — the full raw file name with ``.meta.json`` appended::

    data/raw/climate/chirps_v3_daily_2024.tif
        -> data/raw/climate/chirps_v3_daily_2024.tif.meta.json

That is the single convention :func:`meta_path_for` returns, and it is what the
``*.meta.json`` glob of §4.2 matches exactly. The alternative ``<stem>.meta.json``
spelling (``chirps_v3_daily_2024.meta.json``) is deliberately **not** generated
here: one convention, documented and tested, beats two that differ only in
which reader happened to open the file.

No live download (ZED §2.2ج, قواعد داده)
-----------------------------------------
This module is offline by construction: it reads and hashes files that are
already mirrored locally, it imports nothing outside the standard library, and
it has no network code path to grow one. Per ZED §2.2ج the local mirror with a
checksum is mandatory, no live download is permitted inside the scientific
core, and ingestion may download only behind an explicit flag and outside that
core. ``sha256_of``/``content_hash``/``checksum_sha256`` exist so a mirrored
file can prove it is the file it claims to be.

Scope
-----
This contract governs **new** raw data. The pre-existing ``data/`` tree has no
``raw/`` layer and no sidecars at all (gap G-Z4); backfilling it is out of
scope here and stays a tracked P1 item.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Fields every dataset record must carry — spec §4.6, verbatim.
REQUIRED_DATASET_FIELDS: list[str] = [
    "dataset_id",
    "dataset_version",
    "source_id",
    "variable",
    "unit",
    "content_hash",
]

#: Fields a dataset record should carry — spec §4.6, verbatim.
RECOMMENDED_DATASET_FIELDS: list[str] = [
    "source_uri_or_reference",
    "provider",
    "license",
    "retrieved_at",
    "valid_time",
    "processing_time",
    "spatial_reference",
    "geometry_or_location",
    "temporal_resolution",
    "spatial_resolution",
    "quality_flag",
    "uncertainty",
    "processing_history",
]

#: §4.2 sidecar spelling -> §4.6 canonical field name.
FIELD_ALIASES: dict[str, str] = {
    "source": "source_id",
    "url": "source_uri_or_reference",
    "checksum_sha256": "content_hash",
    "local_path": "geometry_or_location",
}

#: Every field the contract knows, required or recommended.
KNOWN_FIELDS: tuple[str, ...] = (
    *REQUIRED_DATASET_FIELDS,
    *RECOMMENDED_DATASET_FIELDS,
)

#: Suffix of the sidecar file — see :func:`meta_path_for`.
META_SUFFIX = ".meta.json"

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")

#: Fields whose value must be 64 lowercase hex characters.
_HASH_FIELDS: tuple[str, ...] = ("content_hash",)

#: Fields the spec implies are single non-empty strings.
_STRING_FIELDS: tuple[str, ...] = (
    "dataset_id",
    "dataset_version",
    "source_id",
    "variable",
    "unit",
    "source_uri_or_reference",
    "provider",
    "license",
    "retrieved_at",
    "temporal_resolution",
    "spatial_resolution",
    "spatial_reference",
)

_CHUNK_SIZE = 1 << 20


@dataclass(frozen=True)
class MetaProblem:
    """One validation finding.

    ``severity`` is ``"error"`` for a blocking problem and ``"warn"`` for an
    advisory one, so a caller can sort, filter or count them without parsing
    the message text.
    """

    severity: str
    field: str
    message: str


def sha256_of(path: str | Path) -> str:
    """Lowercase hex sha256 of a file's bytes, read in chunks.

    Used to fill ``content_hash``/``checksum_sha256`` for a local mirror. The
    file is read from disk only; nothing is fetched.
    """
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def meta_path_for(data_path: str | Path) -> Path:
    """Sidecar path of a raw file under the ``<path>.meta.json`` convention.

    ``data/raw/climate/x.tif`` becomes ``data/raw/climate/x.tif.meta.json``.
    A path that already ends in ``.meta.json`` is returned unchanged, so the
    call is idempotent and can be used on either side of the pair.
    """
    path = Path(data_path)
    if path.name.endswith(META_SUFFIX):
        return path
    return path.with_name(path.name + META_SUFFIX)


def _canonical_keys(meta: dict[str, Any]) -> dict[str, str]:
    """Map canonical field name -> the key as spelled in *meta*.

    Only keys the contract knows are considered, and the canonical spelling
    wins when a record carries both, so an unknown extra key is ignored rather
    than rejected (forward compatibility) and never overwrites an explicit one.
    """
    view: dict[str, str] = {}
    for key in meta:
        canonical = FIELD_ALIASES.get(key, key)
        if canonical in KNOWN_FIELDS:
            view.setdefault(canonical, key)
    return view


def validate_meta_detailed(meta: dict[str, Any]) -> list[MetaProblem]:
    """Every finding of a sidecar, errors first, each with its severity.

    Checks performed: required fields present (spec §4.6); recommended fields
    present (spec §4.6, severity ``"warn"``); no known field holding ``None``;
    ``content_hash`` matching ``^[0-9a-f]{64}$``; and every string-like field
    being a non-empty string.
    """
    if not isinstance(meta, dict):
        return [
            MetaProblem(
                "error",
                "<meta>",
                f"expected a JSON object describing a dataset, got {type(meta).__name__}",
            )
        ]

    errors: list[MetaProblem] = []
    warnings: list[MetaProblem] = []
    present = _canonical_keys(meta)

    for canonical, key in present.items():
        value = meta[key]
        if value is None:
            errors.append(MetaProblem("error", canonical, f"{canonical!r} is present but null"))
            continue
        if canonical in _HASH_FIELDS:
            if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
                errors.append(
                    MetaProblem(
                        "error",
                        canonical,
                        f"{canonical!r} must be 64 lowercase hex characters, "
                        "the sha256 of the raw file",
                    )
                )
            continue
        if isinstance(value, str) and not value.strip():
            errors.append(
                MetaProblem("error", canonical, f"{canonical!r} must be a non-empty string")
            )
            continue
        if canonical in _STRING_FIELDS and not isinstance(value, str):
            errors.append(
                MetaProblem(
                    "error",
                    canonical,
                    f"{canonical!r} expected a string, got {type(value).__name__}",
                )
            )

    for field in REQUIRED_DATASET_FIELDS:
        if field not in present:
            errors.append(
                MetaProblem(
                    "error", field, f"missing required field {field!r} (spec §4.6 data contract)"
                )
            )

    for field in RECOMMENDED_DATASET_FIELDS:
        if field not in present:
            warnings.append(
                MetaProblem(
                    "warn",
                    field,
                    f"missing recommended field {field!r} (spec §4.6 data contract)",
                )
            )

    return errors + warnings


def validate_meta(meta: dict[str, Any]) -> list[str]:
    """Blocking problems of a sidecar; an empty list means the sidecar is valid.

    Only ``"error"``-severity findings are returned. A sidecar that omits
    recommended fields such as ``license`` is reported by
    :func:`validate_meta_detailed` as a warning instead, so an incomplete but
    honest record is not treated as a broken one.
    """
    return [p.message for p in validate_meta_detailed(meta) if p.severity == "error"]


def build_meta(
    dataset_id: str,
    source: str,
    variable: str,
    unit: str,
    content_hash: str,
    **optional: Any,
) -> dict[str, Any]:
    """Assemble a sidecar record from the values a caller actually has.

    ``source`` is stored under the canonical §4.6 name ``source_id``; the §4.2
    spelling ``source`` is accepted as an alias on read, so a hand-written
    sidecar may use either. ``dataset_version`` is required by §4.6 but is not
    a parameter here, because no honest default exists: pass it (and any
    recommended field) through ``**optional``, typically
    ``build_meta(..., dataset_version="1.0", license=...)``. Everything passed
    as ``None`` is dropped rather than written, since a null field is an error
    and an invented one is worse.

    Optional keys are canonicalised through :data:`FIELD_ALIASES`, so
    ``checksum_sha256=...`` lands on ``content_hash``.
    """
    meta: dict[str, Any] = {
        "dataset_id": dataset_id,
        "source_id": source,
        "variable": variable,
        "unit": unit,
        "content_hash": content_hash,
    }
    for key, value in optional.items():
        if value is None:
            continue
        meta[FIELD_ALIASES.get(key, key)] = value
    return meta
