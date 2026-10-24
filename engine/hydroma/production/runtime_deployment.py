"""Docker-free runtime deployment descriptor (DP-2, ``ECO-DP2-RUNTIME``).

Replaces the container-era Kubernetes/Helm descriptor (``deployment.py``) for the
default ``local`` storage tier: one in-process Python runtime driven by
``runtime/services.yaml``, with no image registry, no orchestrator, no service
mesh and no PostgreSQL server. The ``scaled`` tier keeps the PostgreSQL escape
hatch, expressed here as a plain config that points at an external server rather
than an in-cluster Helm value.

Pure stdlib plus the storage-tier helper (:func:`storage_tier`) from
``engine.hydroma.config.rules``.
"""

from __future__ import annotations

from typing import Any

from engine.hydroma.config.rules import storage_tier


def runtime_descriptor() -> dict[str, Any]:
    """Return the internal-runtime deployment spec for the active storage tier.

    In the ``local`` tier (the default) this is fully Docker- and
    orchestrator-free: ``docker`` is ``False``, ``orchestrator`` is ``None`` and
    no key mentions Kubernetes, Helm or an image. In the ``scaled`` tier a
    ``postgresql`` escape-hatch block is added (opt-in PostgreSQL).
    """
    tier = storage_tier()
    descriptor: dict[str, Any] = {
        "runtime": "hydroma-runtime",
        "docker": False,
        "orchestrator": None,
        "storage_tier": tier,
        "services_source": "runtime/services.yaml",
        "logs_dir": "data/logs",
        "backup": "runtime.backup",
        "secrets": ["env"],
    }
    if tier == "scaled":
        descriptor["postgresql"] = {
            "enabled": True,
            "host": "postgresql",
            "port": 5432,
            "auth": {"existing_secret": "postgresql-auth"},
            "primary": {"persistence": {"enabled": True, "size": "50Gi"}},
        }
    return descriptor


__all__ = ["runtime_descriptor"]
