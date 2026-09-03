"""
engine
======

Processing engine for Eco Nojin project.

Usage:
    from engine.data_connector import connector
    df = connector.get_climate_data(station_id=123)
"""

from .data_connector import DataConnector, connector

__all__ = ["DataConnector", "connector"]
