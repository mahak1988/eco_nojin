"""Connectors for the HyDroMA data pipeline.

This package holds the connectors that talk to external scientific data
providers which need their own credentials, protocol, or error semantics
and therefore do not fit inline in ``pipeline.py``:

* :class:`~engine.hydroma.data_pipeline.connectors.cds_connector.CDSEConnector`
  — Copernicus Data Space Ecosystem (Sentinel-1/2), STAC search + OData
  asset download.
* :class:`~engine.hydroma.data_pipeline.connectors.era5_connector.ERA5Connector`
  — ERA5-Land / ERA5 via the Climate Data Store retrieve API.
* :class:`~engine.hydroma.data_pipeline.connectors.wapor_connector.WaPORConnector`
  — FAO WaPOR v3 (GISMGR 2.0) water-productivity rasters.

Every connector in this package follows the same contract as the inline
connectors in ``pipeline.py``: it subclasses ``DataConnector``, exposes a
``DataSource``, returns ``DataAsset`` objects, and fails *honestly*. A
connector that cannot reach its source raises :class:`ConnectorUnavailable`
naming the missing credential or network condition. No connector in this
package ever fabricates, synthesises, or substitutes data.

Why the shared error type lives here
------------------------------------
The connector modules import ``DataAsset``/``DataConnector``/``DataSource``
from ``engine.hydroma.data_pipeline.pipeline``, and ``pipeline`` imports the
connector classes when it registers them. Defining ``ConnectorUnavailable``
in this ``__init__`` (and nowhere else) keeps that cycle one-directional:
the connector modules depend on the package's error contract, the package
does not depend on them at definition time.
"""

from __future__ import annotations


class ConnectorUnavailable(RuntimeError):
    """A connector cannot reach its source, and says why.

    Raised when a required credential is missing from the environment, when
    a configured endpoint cannot be reached, or when the remote service
    rejects the request (authentication, licence, quota). The message names
    the specific missing credential or network condition and, where one
    exists, the environment variable or file that would supply it.

    This is deliberately *not* a return of empty data: an empty result set
    is indistinguishable from "this source has no data", while this error
    says the source itself could not be consulted.
    """


__all__ = ["ConnectorUnavailable"]
