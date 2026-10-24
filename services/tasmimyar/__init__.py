"""
Tasmimyar Service Package
=========================

Service layer for the Decision Engine. Routes all engine access through
the Engine Gateway per INV-003.
"""

from .decision_service import DecisionRequest, ServiceResponse, TasmimyarService

__all__ = [
    "TasmimyarService",
    "DecisionRequest", 
    "ServiceResponse",
    "HAS_ROUTER",
    "router",
]