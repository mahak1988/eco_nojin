"""Internal, Docker-free runtime supervisor for Eco Nojin / HyDroMA (DP-2).

The runtime is supervised by :mod:`runtime.supervise` directly on the host:
no containers, no images, no registry and no compose files. The service map
lives as plain data in ``runtime/services.yaml`` and every service runs as an
ordinary child process under the same interpreter::

    python -m uvicorn <app> --host 127.0.0.1 --port <port> --workers <n>

The storage backend is chosen with the ``HYDROMA_STORAGE_TIER`` environment
variable; it is read by the services themselves, so this package documents the
contract and never rewrites or validates it.
"""

__all__ = ["supervise"]
