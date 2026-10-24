# services/carbon/rothc_service.py
"""RothC soil-carbon forecast service (wrapper around the ``pyRothC`` backend).

Honesty note (why this module degrades instead of computing):

* The module historically did ``from pyRothC import rothc`` and called
  ``rothc.run(years=..., init=..., climate=..., management=...)``.
* The ``pyRothC`` package installed in this environment is an EMPTY namespace
  package (``dir(pyRothC) == []``), so that import fails and no RothC-26.3
  engine exists behind it.
* The only working RothC contract in this repository is
  ``services/scientific_motors/rothc_real.py``::

      from pyRothC.RothC import RothC
      model = RothC(temperature=..., precip=..., evaporation=..., years=...,
                    C0=..., input_carbon=..., farmyard_manure=..., clay=...,
                    soil_thickness=..., DR=..., pE=..., bare=...)
      df = model.compute()

This module is an orphan (zero importers, zero tests). Rather than invent a
synthetic RothC engine, it imports cleanly and raises a typed, documented
error at call time until the product owner decides which pyRothC contract is
authoritative.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

try:  # pyRothC is a declared project dependency (package name: pyRothC)
    from pyRothC import rothc as _rothc_module

    # ``rothc.run`` is the legacy contract this module was written against;
    # verify the backend actually exposes it before promising anything.
    PYROTHC_AVAILABLE = callable(getattr(_rothc_module, "run", None))
except Exception:  # pragma: no cover - import guard
    _rothc_module = None  # type: ignore[assignment]
    PYROTHC_AVAILABLE = False


class CarbonSequestrationForecast(BaseModel):
    """RothC soil-carbon forecast result (local response contract).

    Defined here — not imported from ``services.carbon.schemas`` — because
    that module has never defined this model; the original
    ``from services.carbon.schemas import CarbonSequestrationForecast`` line
    was a second latent ImportError hidden behind the pyRothC failure. Adding
    it to the shared schemas module is outside this service's scope.
    """

    total_tonnes_co2e: float
    yearly_projection: list[float]
    credits_eligible: float
    confidence_interval: float


class RothCServiceUnavailable(RuntimeError):
    """The pyRothC backend cannot serve RothC-26.3 runs right now.

    Raised instead of computing a fabricated carbon trajectory.
    """


_PYROTHC_CONTRACT_MESSAGE = (
    "RothC forecast unavailable: the installed 'pyRothC' package is an EMPTY "
    "namespace package (dir(pyRothC) == []), so neither "
    "'from pyRothC import rothc' nor 'from pyRothC.RothC import RothC' resolves. "
    "This module historically called rothc.run(years=..., init=..., climate=..., "
    "management=...); the only working RothC contract in this repository is "
    "services/scientific_motors/rothc_real.py, which uses "
    "pyRothC.RothC.RothC(...).compute(). The product owner must decide which "
    "pyRothC contract is authoritative before this service can run; no "
    "substitute RothC engine is provided by design (anti-fabrication rule)."
)


class RothCService:
    """
    پیش‌بینی ترشح کربن خاک به‌مدت ۲۰ سال
    برای محاسبه Carbon Credits قابل معامله
    """

    async def forecast_sequestration(
        self,
        soil_profile: dict,
        management_scenario: str,
        years: int = 20,
    ) -> CarbonSequestrationForecast:

        if not PYROTHC_AVAILABLE:
            raise RothCServiceUnavailable(_PYROTHC_CONTRACT_MESSAGE)

        # پارامترهای اولیه
        init = {
            "pC": soil_profile["initial_soc"],  # کربن اولیه
            "sC": 0.0,
            "bC": 0.0,
            "hC": 0.0,
            "iC": 0.0,
        }

        # اجرای مدل
        result: dict[str, Any] = _rothc_module.run(
            years=years,
            init=init,
            climate=soil_profile["climate"],
            management=management_scenario,
        )

        # محاسبه اعتبار کربن (هر تن CO2e = 1 credit)
        total_sequestered = result["SOC"][-1] - result["SOC"][0]
        co2e = total_sequestered * 44 / 12  # تبدیل C به CO2

        return CarbonSequestrationForecast(
            total_tonnes_co2e=co2e,
            yearly_projection=result["SOC"],
            credits_eligible=co2e * 0.85,  # 15% buffer
            confidence_interval=0.92,
        )
