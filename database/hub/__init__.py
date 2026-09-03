"""
database.hub
============

Central data access hub for Eco Nojin project.

Usage:
    from database.hub import hub

    with hub.get_session() as session:
        users = session.query(User).all()
"""

from .hub import DataHub, hub

__all__ = ["DataHub", "hub"]
