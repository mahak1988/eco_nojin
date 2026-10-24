"""Shared approver-role policy for the tourism surface.

Both ``services.tourism.api.router`` and ``services.tourism.api.safety`` need the
same approver set: admin + landscape_manager. Defining it here (instead of in
``router.py``) breaks the circular dependency between the two modules.
"""
from __future__ import annotations

from services.api_gateway.auth import ROLE_ADMIN, require_roles

_APPROVER_ROLES = {ROLE_ADMIN, "landscape_manager"}
APPROVER_ROLES = _APPROVER_ROLES
require_tourism_approver = require_roles(ROLE_ADMIN, "landscape_manager")
