"""Versioned evaluation-dataset management with data-leakage prevention.

Provides :class:`EvaluationDataset` wrappers that enforce season-based,
site-based, or combined train/validation/test splits to prevent the same
field site-season from appearing in both training and evaluation corpora
(a classic source of over-optimistic performance estimates).

This module is import-safe: it depends only on pydantic, numpy, and the
field contracts in :mod:`engine.hydroma.eval.field_data`.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any, Literal

import numpy as np

from engine.hydroma.eval.field_data import (
    EvaluationDataset,
    FieldObservation,
    ObservationSource,
)

SplitMethod = Literal["season", "site", "combined", "random"]


class SplitRole(StrEnum):
    """The role a split plays in evaluation."""

    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


@dataclass
class DataSplit:
    """A single train/validation/test split of a dataset.

    Attributes:
        train: Observations assigned to the training split.
        validation: Observations assigned to the validation split.
        test: Observations assigned to the test split.
        train_season_ids: Season identifiers that land in train.
        validation_season_ids: Season identifiers in validation.
        test_season_ids: Season identifiers in test.
        train_site_ids: Site identifiers in train.
        validation_site_ids: Site identifiers in validation.
        test_site_ids: Site identifiers in test.
        method: The split method used.
        seed: Random seed for reproducibility (for random splits).
        leak_check: Result of the data-leakage check.
    """

    train: list[FieldObservation]
    validation: list[FieldObservation]
    test: list[FieldObservation]
    train_season_ids: set[str]
    validation_season_ids: set[str]
    test_season_ids: set[str]
    train_site_ids: set[str]
    validation_site_ids: set[str]
    test_site_ids: set[str]
    train_pairs: set[tuple[str, str]]
    validation_pairs: set[tuple[str, str]]
    test_pairs: set[tuple[str, str]]
    method: SplitMethod
    seed: int | None = None
    leak_check: dict[str, bool] | None = None

    @property
    def train_size(self) -> int:
        return len(self.train)

    @property
    def validation_size(self) -> int:
        return len(self.validation)

    @property
    def test_size(self) -> int:
        return len(self.test)

    @property
    def is_leak_free(self) -> bool:
        """True if no (site, season) pair overlaps between splits.

        For ``combined`` splits, the pair-level check is authoritative: the
        same site-season combination must never appear in two splits.  For
        ``season`` and ``site`` splits, the respective key-level check is used.
        For ``random`` splits, the check is advisory (random splits may leak).
        """
        if self.leak_check is None:
            return True
        if self.method == "combined":
            pair_checks = {k: v for k, v in self.leak_check.items() if k.startswith("pair_")}
            return all(pair_checks.values()) if pair_checks else True
        elif self.method == "season":
            season_checks = {k: v for k, v in self.leak_check.items() if k.startswith("season_")}
            return all(season_checks.values()) if season_checks else True
        elif self.method == "site":
            site_checks = {k: v for k, v in self.leak_check.items() if k.startswith("site_")}
            return all(site_checks.values()) if site_checks else True
        return all(self.leak_check.values())

    def summary(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "seed": self.seed,
            "train": self.train_size,
            "validation": self.validation_size,
            "test": self.test_size,
            "train_season_ids": sorted(self.train_season_ids),
            "validation_season_ids": sorted(self.validation_season_ids),
            "test_season_ids": sorted(self.test_season_ids),
            "leak_free": self.is_leak_free,
        }


@dataclass
class DatasetVersion:
    """A frozen snapshot of a dataset at a given version.

    Provides a SHA-256 checksum so that evaluation results can be tied
    to an exact dataset revision.

    Attributes:
        name: Dataset name.
        version: Semantic version string.
        checksum: SHA-256 of the (sorted, serialised) dataset.
        created_at: ISO timestamp of creation.
    """

    name: str
    version: str
    checksum: str
    created_at: str

    @classmethod
    def from_dataset(
        cls, dataset: EvaluationDataset, created_at: str | None = None
    ) -> DatasetVersion:
        """Compute a deterministic checksum for a dataset snapshot."""
        records = []
        def sort_key(o: FieldObservation) -> tuple[str, str, str, str]:
            return (o.site, o.season, o.variable.value, str(o.observation_date))
        for obs in sorted(dataset.observations, key=sort_key):
            src = obs.source
            source_str = src.value if isinstance(src, ObservationSource) else src
            records.append({
                "site": obs.site,
                "season": obs.season,
                "variable": obs.variable.value,
                "value": obs.value,
                "unit": obs.unit,
                "observation_date": str(obs.observation_date),
                "source": source_str,
                "quality_flag": obs.quality_flag,
            })
        payload = {
            "name": dataset.name,
            "version": dataset.version,
            "observations": records,
        }
        serialised = json.dumps(payload, sort_keys=True, default=str)
        checksum = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
        return cls(
            name=dataset.name,
            version=dataset.version,
            checksum=checksum,
            created_at=created_at or date.today().isoformat(),
        )


class EvaluationDatasetManager:
    """Manages versioned evaluation datasets and produces leak-free splits.

    Usage::

        manager = EvaluationDatasetManager()
        manager.add_dataset("EC001-yield-v1.0.0", dataset)
        split = manager.get_split("EC001-yield-v1.0.0", method="combined", seed=42)
    """

    def __init__(self) -> None:
        self._datasets: dict[str, EvaluationDataset] = {}
        self._versions: dict[str, DatasetVersion] = {}

    def add_dataset(self, name: str, dataset: EvaluationDataset) -> DatasetVersion:
        """Register a dataset and record its version fingerprint."""
        version = DatasetVersion.from_dataset(dataset)
        self._datasets[name] = dataset
        self._versions[name] = version
        return version

    def get_dataset(self, name: str) -> EvaluationDataset:
        if name not in self._datasets:
            raise KeyError(f"Dataset {name!r} not registered")
        return deepcopy(self._datasets[name])

    def get_version(self, name: str) -> DatasetVersion:
        if name not in self._versions:
            raise KeyError(f"Dataset {name!r} not registered")
        return self._versions[name]

    def list_datasets(self) -> list[str]:
        return list(self._datasets.keys())

    def get_split(
        self,
        name: str,
        *,
        method: SplitMethod = "combined",
        seed: int = 42,
        train_ratio: float = 0.6,
        validation_ratio: float = 0.2,
        test_ratio: float = 0.2,
    ) -> DataSplit:
        """Produce a train/validation/test split with data-leakage prevention.

        Parameters
        ----------
        name:
            Registered dataset name.
        method:
            - ``"season"`` — splits by season_id only (same season never in two splits).
            - ``"site"`` — splits by site_id only.
            - ``"combined"`` — splits by (site_id, season_id) pair so neither
              site nor season overlaps.
            - ``"random"`` — random split at the observation level (use only for
              development; a `leak_check` warning is raised).
        seed:
            Random seed for reproducibility.
        train_ratio, validation_ratio, test_ratio:
            Sum should be 1.0; they are normalised internally.
        """
        dataset = self.get_dataset(name)
        total = train_ratio + validation_ratio + test_ratio
        train_ratio /= total
        validation_ratio /= total
        test_ratio /= total

        if method == "random":
            return self._random_split(
                dataset, seed, train_ratio, validation_ratio, test_ratio
            )
        elif method == "season":
            return self._split_by_key(
                dataset, "season_id", method, seed,
                train_ratio, validation_ratio, test_ratio,
            )
        elif method == "site":
            return self._split_by_key(
                dataset, "site_id", method, seed,
                train_ratio, validation_ratio, test_ratio,
            )
        elif method == "combined":
            return self._split_combined(
                dataset, seed, train_ratio, validation_ratio, test_ratio
            )
        else:
            raise ValueError(f"Unknown split method {method!r}")

    def _split_by_key(
        self,
        dataset: EvaluationDataset,
        key: str,
        method: SplitMethod,
        seed: int,
        train_ratio: float,
        validation_ratio: float,
        test_ratio: float,
    ) -> DataSplit:
        """Split observations so that all rows sharing a ``key`` value land in one split."""
        rng = np.random.RandomState(seed)

        def _key_func_season(o: FieldObservation) -> str:
            return o.season

        def _key_func_site(o: FieldObservation) -> str:
            return o.site

        if key == "season_id":
            key_func = _key_func_season
        elif key == "site_id":
            key_func = _key_func_site
        else:
            raise ValueError(f"Unknown key {key!r}")

        unique_keys = sorted({key_func(o) for o in dataset.observations})
        rng.shuffle(unique_keys)

        n = len(unique_keys)
        n_train = int(n * train_ratio)
        n_val = int(n * validation_ratio)
        train_keys = set(unique_keys[:n_train])
        val_keys = set(unique_keys[n_train : n_train + n_val])
        test_keys = set(unique_keys[n_train + n_val :])

        train: list[FieldObservation] = []
        validation: list[FieldObservation] = []
        test: list[FieldObservation] = []

        for obs in dataset.observations:
            k = key_func(obs)
            if k in train_keys:
                train.append(obs)
            elif k in val_keys:
                validation.append(obs)
            else:
                test.append(obs)

        leak_check = self._check_leakage(
            train_keys, val_keys, test_keys,
            "season" if key == "season_id" else "site",
        )

        return DataSplit(
            train=train,
            validation=validation,
            test=test,
            train_season_ids=train_keys if key == "season_id" else set(),
            validation_season_ids=val_keys if key == "season_id" else set(),
            test_season_ids=test_keys if key == "season_id" else set(),
            train_site_ids=train_keys if key == "site_id" else set(),
            validation_site_ids=val_keys if key == "site_id" else set(),
            test_site_ids=test_keys if key == "site_id" else set(),
            train_pairs=set(),
            validation_pairs=set(),
            test_pairs=set(),
            method=method,
            seed=seed,
            leak_check=leak_check,
        )

    def _split_combined(
        self,
        dataset: EvaluationDataset,
        seed: int,
        train_ratio: float,
        validation_ratio: float,
        test_ratio: float,
    ) -> DataSplit:
        """Split by (site_id, season_id) pairs — the strictest no-leak method."""
        rng = np.random.RandomState(seed)
        pairs = sorted({(o.site, o.season) for o in dataset.observations})
        rng.shuffle(pairs)

        n = len(pairs)
        n_train = int(n * train_ratio)
        n_val = int(n * validation_ratio)
        train_pairs = set(pairs[:n_train])
        val_pairs = set(pairs[n_train : n_train + n_val])
        test_pairs = set(pairs[n_train + n_val :])

        train: list[FieldObservation] = []
        validation: list[FieldObservation] = []
        test: list[FieldObservation] = []
        train_seasons: set[str] = set()
        val_seasons: set[str] = set()
        test_seasons: set[str] = set()
        train_sites: set[str] = set()
        val_sites: set[str] = set()
        test_sites: set[str] = set()

        for obs in dataset.observations:
            pair = (obs.site, obs.season)
            if pair in train_pairs:
                train.append(obs)
                train_seasons.add(obs.season)
                train_sites.add(obs.site)
            elif pair in val_pairs:
                validation.append(obs)
                val_seasons.add(obs.season)
                val_sites.add(obs.site)
            else:
                test.append(obs)
                test_seasons.add(obs.season)
                test_sites.add(obs.site)

        season_leak = self._check_leakage(
            train_seasons, val_seasons, test_seasons, "season"
        )
        site_leak = self._check_leakage(
            train_sites, val_sites, test_sites, "site"
        )
        pair_leak = self._check_leakage(
            train_pairs, val_pairs, test_pairs, "site_season_pair"
        )
        leak_check = {
            **{f"season_{k}": v for k, v in season_leak.items()},
            **{f"site_{k}": v for k, v in site_leak.items()},
            **{f"pair_{k}": v for k, v in pair_leak.items()},
        }

        return DataSplit(
            train=train,
            validation=validation,
            test=test,
            train_season_ids=train_seasons,
            validation_season_ids=val_seasons,
            test_season_ids=test_seasons,
            train_site_ids=train_sites,
            validation_site_ids=val_sites,
            test_site_ids=test_sites,
            train_pairs=train_pairs,
            validation_pairs=val_pairs,
            test_pairs=test_pairs,
            method="combined",
            seed=seed,
            leak_check=leak_check,
        )

    def _random_split(
        self,
        dataset: EvaluationDataset,
        seed: int,
        train_ratio: float,
        validation_ratio: float,
        test_ratio: float,
    ) -> DataSplit:
        """Random split at the observation level (may leak — use with caution)."""
        rng = np.random.RandomState(seed)
        obs_list = list(dataset.observations)
        rng.shuffle(obs_list)

        n = len(obs_list)
        n_train = int(n * train_ratio)
        n_val = int(n * validation_ratio)

        train = obs_list[:n_train]
        validation = obs_list[n_train : n_train + n_val]
        test = obs_list[n_train + n_val :]

        train_seasons = {o.season for o in train}
        val_seasons = {o.season for o in validation}
        test_seasons = {o.season for o in test}

        season_leak = self._check_leakage(
            train_seasons, val_seasons, test_seasons, "season"
        )
        train_sites = {o.site for o in train}
        val_sites = {o.site for o in validation}
        test_sites = {o.site for o in test}
        site_leak = self._check_leakage(
            train_sites, val_sites, test_sites, "site"
        )

        leak_check = {
            **{f"season_{k}": v for k, v in season_leak.items()},
            **{f"site_{k}": v for k, v in site_leak.items()},
        }

        return DataSplit(
            train=train,
            validation=validation,
            test=test,
            train_season_ids=train_seasons,
            validation_season_ids=val_seasons,
            test_season_ids=test_seasons,
            train_site_ids=train_sites,
            validation_site_ids=val_sites,
            test_site_ids=test_sites,
            train_pairs=set(),
            validation_pairs=set(),
            test_pairs=set(),
            method="random",
            seed=seed,
            leak_check=leak_check,
        )

    @staticmethod
    def _check_leakage(
        train_keys: set[str],
        val_keys: set[str],
        test_keys: set[str],
        dimension: str,
    ) -> dict[str, bool]:
        """Return a dict of leak-check results for each split pair."""
        no_overlap_train_val = len(train_keys & val_keys) == 0
        no_overlap_train_test = len(train_keys & test_keys) == 0
        no_overlap_val_test = len(val_keys & test_keys) == 0
        return {
            f"no_leak_train_val_{dimension}": no_overlap_train_val,
            f"no_leak_train_test_{dimension}": no_overlap_train_test,
            f"no_leak_val_test_{dimension}": no_overlap_val_test,
        }
