"""Alerting Service for Eco Nojin.

Provides alert rules, notifications, and alert management.
"""

# ``Alert`` and ``AlertRule`` are SQLAlchemy models in ``.models``; only the
# request/response envelopes are Pydantic and live in ``.schemas``. Importing
# the models from ``.schemas`` made every module in this package unimportable,
# which is exactly what the phase 3 G1 import gate is for.
from .models import Alert, AlertRule
from .schemas import (
    AlertResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertSummary,
)
from .service import AlertService

__all__ = [
    "Alert",
    "AlertResponse",
    "AlertRule",
    "AlertRuleCreate",
    "AlertRuleResponse",
    "AlertRuleUpdate",
    "AlertService",
    "AlertSummary",
]
