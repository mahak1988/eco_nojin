"""Ingestion and quality-control layer for field observation data.

Reads CSV and JSON files into :class:`~engine.hydroma.eval.field_data.EvaluationDataset`
records, performing validation, duplicate detection, outlier flagging, and
preserving raw data for audit.  No network imports — this module is
import-safe under the ``ENGINE_NO_SERVICES`` guard.

Quality-control pipeline (in order):
    1. Schema validation (column names, types, required fields).
    2. Unit normalisation for known variables.
    3. Duplicate detection (same site + season + variable + date).
    4. Outlier flag via the IQR rule (Tukey) on numeric fields.
    5. Raw-data preservation: every row that passes schema validation is
       stored with its original values in ``raw_rows`` for audit.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engine.hydroma.eval.field_data import (
    EvaluationDataset,
    FieldObservation,
    ObservationSource,
    SeasonInfo,
    SiteInfo,
    VariableType,
)

CSV_REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {"site_id", "date", "variable", "value"}
)

JSON_REQUIRED_KEYS: frozenset[str] = frozenset(
    {"site_id", "date", "variable", "value"}
)


@dataclass
class QualityReport:
    """Summary of quality-control events during ingestion."""

    total_rows: int = 0
    rows_accepted: int = 0
    rows_rejected: int = 0
    duplicates: int = 0
    outliers: int = 0
    errors: list[str] = field(default_factory=list)
    outliers_detail: list[str] = field(default_factory=list)
    duplicates_detail: list[str] = field(default_factory=list)

    @property
    def acceptance_rate(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return self.rows_accepted / self.total_rows


@dataclass
class IngestionResult:
    """Result of an ingestion run.

    Attributes:
        dataset: The populated :class:`EvaluationDataset`.
        quality_report: QA summary of the ingestion.
        raw_rows: Every row that passed schema validation, in original form.
    """

    dataset: EvaluationDataset
    quality_report: QualityReport
    raw_rows: list[dict[str, Any]]


def _coerce_date(value: str | Any) -> str:
    """Normalise a date-like value to an ISO date string."""
    if isinstance(value, str):
        return value.strip()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _is_outlier(value: float, q1: float, q3: float) -> bool:
    """Tukey IQR outlier test."""
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return value < lower or value > upper


def _detect_outliers(values: list[float]) -> tuple[int, float, float]:
    """Return (count, q1, q3) for outlier detection."""
    if len(values) < 4:
        return 0, 0.0, 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1_idx = n * 0.25
    q3_idx = n * 0.75

    def _interp_q(idx: float) -> float:
        lo = int(idx)
        if idx == lo:
            return sorted_vals[lo]
        frac = idx - lo
        return sorted_vals[lo] + (sorted_vals[lo + 1] - sorted_vals[lo]) * frac

    q1 = _interp_q(q1_idx)
    q3 = _interp_q(q3_idx)
    count = sum(1 for v in values if _is_outlier(v, q1, q3))
    return count, q1, q3


class CSVIngester:
    """Read field observations from a CSV file into an EvaluationDataset."""

    def __init__(
        self,
        dataset_name: str,
        dataset_version: str = "1.0.0",
        citation: str | None = None,
        license: str | None = None,
    ):
        self.dataset_name = dataset_name
        self.dataset_version = dataset_version
        self.citation = citation
        self.license = license

    def ingest(
        self,
        file_path: str | Path,
        *,
        encoding: str = "utf-8",
        has_header: bool = True,
        site_metadata: dict[str, dict[str, Any]] | None = None,
        season_metadata: dict[str, dict[str, Any]] | None = None,
    ) -> IngestionResult:
        """Parse a CSV file into an :class:`IngestionResult`.

        Parameters
        ----------
        file_path:
            Path to the CSV file.
        encoding:
            File encoding (default utf-8).
        has_header:
            Whether the file has a header row.
        site_metadata:
            Optional dict mapping site_id to SiteInfo fields.
        season_metadata:
            Optional dict mapping season_id to SeasonInfo fields.
        """
        path = Path(file_path)
        raw_rows: list[dict[str, Any]] = []
        observations: list[FieldObservation] = []
        sites: dict[str, SiteInfo] = {}
        seasons: dict[str, SeasonInfo] = {}
        report = QualityReport()

        seen_keys: set[tuple[str, str, str, str]] = set()

        with open(path, encoding=encoding, newline="") as f:
            if has_header:
                reader: csv.DictReader[str] = csv.DictReader(f)
                fieldnames: Sequence[str] = reader.fieldnames or []
            else:
                first_line = f.readline().strip()
                fieldnames = [c.strip() for c in first_line.split(",")]
                f.seek(0)
                reader = csv.DictReader(f, fieldnames=fieldnames)

            missing = CSV_REQUIRED_COLUMNS - set(fieldnames)
            if missing:
                report.errors.append(
                    f"Missing required columns: {missing}"
                )
                return IngestionResult(
                    dataset=EvaluationDataset(
                        name=self.dataset_name,
                        version=self.dataset_version,
                    ),
                    quality_report=report,
                    raw_rows=[],
                )

            all_values: dict[str, list[float]] = {}

            for i, row in enumerate(reader):
                report.total_rows += 1
                try:
                    site_id = str(row["site_id"]).strip()
                    obs_date = _coerce_date(row["date"])
                    variable = VariableType(row["variable"].strip().lower())
                    value = float(row["value"])
                    unit = str(row.get("unit", "")).strip() or self._default_unit(variable)
                    season_id = str(row.get("season_id", "")).strip() or site_id
                    source_str = str(row.get("source", "field_measured")).strip()
                    quality_flag = str(row.get("quality_flag", "good")).strip()
                    method = str(row.get("method", "")).strip() or None
                    uncertainty = row.get("uncertainty", "")
                    uncertainty_val = float(uncertainty) if uncertainty else None
                    uncertainty_unit = str(row.get("uncertainty_unit", "")).strip() or None
                except (ValueError, KeyError) as exc:
                    report.rows_rejected += 1
                    report.errors.append(f"Row {i+1}: {exc}")
                    continue

                raw_rows.append(dict(row))

                dedup_key = (site_id, season_id, variable.value, obs_date)
                if dedup_key in seen_keys:
                    report.duplicates += 1
                    report.duplicates_detail.append(
                        f"Row {i+1}: duplicate {site_id}/{season_id}/{variable.value}/{obs_date}"
                    )
                    continue
                seen_keys.add(dedup_key)

                try:
                    obs = FieldObservation(
                        site=site_id,
                        season=season_id,
                        observation_id=f"{site_id}_{season_id}_{variable.value}_{obs_date}_{i}",
                        variable=variable,
                        value=value,
                        unit=unit,
                        observation_date=obs_date,
                        source=ObservationSource.from_label(source_str)
                        if isinstance(source_str, str)
                        else source_str,
                        method=method,
                        uncertainty=uncertainty_val,
                        uncertainty_unit=uncertainty_unit,
                        quality_flag=quality_flag,
                        metadata={
                            k: v for k, v in row.items()
                            if k not in CSV_REQUIRED_COLUMNS and v
                        },
                    )
                except Exception as exc:
                    report.rows_rejected += 1
                    report.errors.append(f"Row {i+1}: validation error - {exc}")
                    continue

                observations.append(obs)
                report.rows_accepted += 1

                var_key = variable.value
                all_values.setdefault(var_key, []).append(value)

                if site_id not in sites and site_metadata and site_id in site_metadata:
                    meta = dict(site_metadata[site_id])
                    meta.pop("site_id", None)
                    try:
                        sites[site_id] = SiteInfo(site_id=site_id, **meta)
                    except Exception as exc:
                        report.errors.append(f"Site {site_id}: {exc}")

                if season_id not in seasons and season_metadata and season_id in season_metadata:
                    meta = dict(season_metadata[season_id])
                    try:
                        seasons[season_id] = SeasonInfo(**meta)
                    except Exception as exc:
                        report.errors.append(f"Season {season_id}: {exc}")

        # Outlier detection per variable
        for var_key, vals in all_values.items():
            count, q1, q3 = _detect_outliers(vals)
            report.outliers += count
            if count > 0:
                report.outliers_detail.append(
                    f"variable={var_key}: {count} outliers (Q1={q1:.2f}, Q3={q3:.2f})"
                )

        dataset = EvaluationDataset(
            name=self.dataset_name,
            version=self.dataset_version,
            citation=self.citation,
            license=self.license,
            sites=sites,
            seasons=seasons,
            observations=observations,
        )

        return IngestionResult(
            dataset=dataset,
            quality_report=report,
            raw_rows=raw_rows,
        )

    @staticmethod
    def _default_unit(variable: VariableType) -> str:
        defaults = {
            VariableType.YIELD: "t/ha",
            VariableType.BIOMASS: "t/ha",
            VariableType.LAI: "index",
            VariableType.PAR: "MJ/m2/day",
            VariableType.VPD: "kPa",
            VariableType.SHORTWAVE: "MJ/m2/day",
            VariableType.TEMPERATURE: "degC",
            VariableType.EWSI: "index",
            VariableType.ET: "mm/day",
            VariableType.SOIL_MOISTURE: "m3/m3",
            VariableType.PRECIPITATION: "mm/day",
        }
        return defaults.get(variable, "")


class JSONIngester:
    """Read field observations from a JSON file (array of records)."""

    def __init__(
        self,
        dataset_name: str,
        dataset_version: str = "1.0.0",
        citation: str | None = None,
        license: str | None = None,
    ):
        self.dataset_name = dataset_name
        self.dataset_version = dataset_version
        self.citation = citation
        self.license = license

    def ingest(
        self,
        file_path: str | Path,
        *,
        encoding: str = "utf-8",
        site_metadata: dict[str, dict[str, Any]] | None = None,
        season_metadata: dict[str, dict[str, Any]] | None = None,
    ) -> IngestionResult:
        """Parse a JSON file (array of observation objects) into a dataset."""
        path = Path(file_path)
        with open(path, encoding=encoding) as f:
            raw_data = json.load(f)

        if not isinstance(raw_data, list):
            raise ValueError("JSON ingester expects a top-level array of observation records")

        report = QualityReport()
        observations: list[FieldObservation] = []
        sites: dict[str, SiteInfo] = {}
        seasons: dict[str, SeasonInfo] = {}
        seen_keys: set[tuple[str, str, str, str]] = set()
        all_values: dict[str, list[float]] = {}
        raw_rows: list[dict[str, Any]] = []

        for i, record in enumerate(raw_data):
            report.total_rows += 1
            if not isinstance(record, dict):
                report.rows_rejected += 1
                report.errors.append(f"Row {i+1}: expected a JSON object")
                continue

            missing_keys = JSON_REQUIRED_KEYS - set(record.keys())
            if missing_keys:
                report.rows_rejected += 1
                report.errors.append(f"Row {i+1}: missing keys {missing_keys}")
                continue

            raw_rows.append(record)

            try:
                site_id = str(record["site_id"]).strip()
                obs_date = _coerce_date(record["date"])
                variable = VariableType(str(record["variable"]).strip().lower())
                value = float(record["value"])
                unit = str(record.get("unit", "")).strip() or CSVIngester._default_unit(variable)
                season_id = str(record.get("season_id", "")).strip() or site_id
                source_str = str(record.get("source", "field_measured")).strip()
                quality_flag = str(record.get("quality_flag", "good")).strip()
                method = str(record.get("method", "")).strip() or None
                uncertainty = record.get("uncertainty")
                uncertainty_val = float(uncertainty) if uncertainty else None
                uncertainty_unit = str(record.get("uncertainty_unit", "")).strip() or None
                metadata = {
                    k: v for k, v in record.items()
                    if k not in JSON_REQUIRED_KEYS and v is not None
                }
            except (ValueError, TypeError) as exc:
                report.rows_rejected += 1
                report.errors.append(f"Row {i+1}: {exc}")
                continue

            dedup_key = (site_id, season_id, variable.value, obs_date)
            if dedup_key in seen_keys:
                report.duplicates += 1
                report.duplicates_detail.append(
                    f"Row {i+1}: duplicate {site_id}/{season_id}/{variable.value}/{obs_date}"
                )
                continue
            seen_keys.add(dedup_key)

            try:
                obs = FieldObservation(
                    site=site_id,
                    season=season_id,
                    observation_id=f"{site_id}_{season_id}_{variable.value}_{obs_date}_{i}",
                    variable=variable,
                    value=value,
                    unit=unit,
                    observation_date=obs_date,
                    source=ObservationSource.from_label(source_str)
                    if isinstance(source_str, str)
                    else source_str,
                    method=method,
                    uncertainty=uncertainty_val,
                    uncertainty_unit=uncertainty_unit,
                    quality_flag=quality_flag,
                    metadata=metadata or None,
                )
            except Exception as exc:
                report.rows_rejected += 1
                report.errors.append(f"Row {i+1}: validation error - {exc}")
                continue

            observations.append(obs)
            report.rows_accepted += 1
            all_values.setdefault(variable.value, []).append(value)

            if site_id not in sites and site_metadata and site_id in site_metadata:
                    meta = dict(site_metadata[site_id])
                    meta.pop("site_id", None)
                    try:
                        sites[site_id] = SiteInfo(site_id=site_id, **meta)
                    except Exception as exc:
                        report.errors.append(f"Site {site_id}: {exc}")

            if season_id not in seasons and season_metadata and season_id in season_metadata:
                meta = dict(season_metadata[season_id])
                try:
                    seasons[season_id] = SeasonInfo(**meta)
                except Exception as exc:
                    report.errors.append(f"Season {season_id}: {exc}")

        for var_key, vals in all_values.items():
            count, q1, q3 = _detect_outliers(vals)
            report.outliers += count
            if count > 0:
                report.outliers_detail.append(
                    f"variable={var_key}: {count} outliers (Q1={q1:.2f}, Q3={q3:.2f})"
                )

        dataset = EvaluationDataset(
            name=self.dataset_name,
            version=self.dataset_version,
            citation=self.citation,
            license=self.license,
            sites=sites,
            seasons=seasons,
            observations=observations,
        )

        return IngestionResult(
            dataset=dataset,
            quality_report=report,
            raw_rows=raw_rows,
        )


def ingest_csv(
    file_path: str | Path,
    *,
    dataset_name: str,
    dataset_version: str = "1.0.0",
    citation: str | None = None,
    license: str | None = None,
    encoding: str = "utf-8",
    has_header: bool = True,
    site_metadata: dict[str, dict[str, Any]] | None = None,
    season_metadata: dict[str, dict[str, Any]] | None = None,
) -> IngestionResult:
    """Convenience wrapper around :class:`CSVIngester`."""
    ingester = CSVIngester(
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        citation=citation,
        license=license,
    )
    return ingester.ingest(
        file_path,
        encoding=encoding,
        has_header=has_header,
        site_metadata=site_metadata,
        season_metadata=season_metadata,
    )


def ingest_json(
    file_path: str | Path,
    *,
    dataset_name: str,
    dataset_version: str = "1.0.0",
    citation: str | None = None,
    license: str | None = None,
    encoding: str = "utf-8",
    site_metadata: dict[str, dict[str, Any]] | None = None,
    season_metadata: dict[str, dict[str, Any]] | None = None,
) -> IngestionResult:
    """Convenience wrapper around :class:`JSONIngester`."""
    ingester = JSONIngester(
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        citation=citation,
        license=license,
    )
    return ingester.ingest(
        file_path,
        encoding=encoding,
        site_metadata=site_metadata,
        season_metadata=season_metadata,
    )
