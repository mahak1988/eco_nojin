"""Risk assessment layer: aggregation of the economic risk primitives.

Re-exports :func:`perform_comprehensive_risk_analysis`, the scenario-level
aggregator over the Value-at-Risk primitives that already exist in
:mod:`engine.hydroma.economics.risk`.
"""

from engine.hydroma.risk.assessment import perform_comprehensive_risk_analysis

__all__ = ["perform_comprehensive_risk_analysis"]
