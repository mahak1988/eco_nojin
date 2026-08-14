"""Configuration settings for the HyDroMa engine."""

from dataclasses import dataclass


@dataclass
class Settings:
    """Runtime settings for HyDroMa."""

    project_name: str = "Eco Nojin"
    engine_name: str = "HyDroMa"
    environment: str = "development"
