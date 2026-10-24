"""Helpers for serialising landscape entities to JSON-safe shapes.

Used by ``services/landscape/service.py`` and ``services/landscape/schemas/``
so that the response format is defined in exactly one place.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4


def _money(value: object) -> str | None:
    """Column ``Numeric`` -> exact decimal string. ``None`` stays ``None``.

    Per ``docs/standards/S-MONEY.md``: never float.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return str(Decimal(str(value)))
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def _to_iso(value: object) -> str | None:
    """DateTime / Date -> ISO 8601 string. ``None`` stays ``None``."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _uuid_str(value: object) -> str | None:
    """PG_UUID / UUIDString -> str. ``None`` stays ``None``."""
    return str(value) if value is not None else None


def _uuid(value: object) -> UUID:
    """UUID string/object -> UUID object."""
    if isinstance(value, UUID):
        return value
    if value is None:
        return None
    return UUID(str(value))


def _uuid4() -> UUID:
    """Random ``uuid4`` generator for model defaults."""
    return uuid4()
