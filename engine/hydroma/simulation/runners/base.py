"""Common runner interface for the simulation chain (Phase 3)."""

from abc import ABC, abstractmethod
from typing import Any


class ModelRunner(ABC):
    """A validated external model wrapped behind a uniform interface.

    Subclasses declare ``name`` and ``version`` and implement ``run`` so the
    orchestrator can execute any model with the same call shape.
    """

    name: str = "abstract"
    version: str = "0"

    @abstractmethod
    def run(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the model and return a provenance-labeled result dict."""
        raise NotImplementedError
