"""Response models for the two satellite store-status routes.

Added 2026-10-04. Both declared ``response_model=dict``.

Field sets measured from the live calls on 2026-10-04, not read off the source:

* ``all_stores_status()`` -> ``{"stores": {...}}``, whose values are themselves
  store-status dicts.
* ``CdsClient().status()`` -> ``store``, ``name``, ``configured``, ``api_url``,
  ``key_url``, ``auth``, ``note``.

One model serves both, with ``extra="allow"``, because the two shapes are the
same record at two scopes: a single store and the map of all stores. Two models
would document the overlap twice and drift.

``configured: False`` and the ``note`` are load-bearing. These routes exist to
report that Copernicus is *not* wired, and a client that renders "available"
because the key is absent is exactly the dishonesty S-HONEST.md forbids.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StoreStatusOut(BaseModel):
    """One Copernicus store. `configured` is measured, never assumed."""

    model_config = ConfigDict(extra="allow")

    store: str | None = None
    name: str | None = None
    configured: bool = Field(
        default=False,
        description="Whether credentials are present. False means the source is "
        "unavailable, and a client must not render it as usable.",
    )
    api_url: str | None = None
    key_url: str | None = None
    auth: str | None = Field(default=None, description="Auth scheme, e.g. bearer.")
    note: str | None = Field(
        default=None, description="Why it is unavailable, in the server's own words."
    )


class AllStoresStatusOut(BaseModel):
    """`{"stores": {store_name: StoreStatusOut}}`."""

    model_config = ConfigDict(extra="allow")

    stores: dict[str, Any] = Field(
        default_factory=dict,
        description="Keyed by store id (cds, ewds, ads, sepal, ...).",
    )
