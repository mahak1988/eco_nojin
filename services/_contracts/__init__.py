"""Canonical contracts for the ``services`` layer.

Each module here is the *reference implementation* of one standard from
``docs/standards/``. A standard without reference code is an intention; these
are what the phase 3 CI gates check against.

===================  ====================================================
Standard             Module
===================  ====================================================
S-HONEST             :mod:`services._contracts.status`
S-MONEY              :mod:`services._contracts.money`
S-SCI                :mod:`services._contracts.formula`
===================  ====================================================
"""

from __future__ import annotations

__all__ = ["formula", "money", "status"]
