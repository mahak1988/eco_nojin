# services/carbon/rothc_service.py
from pyRothC import rothc

from services.carbon.schemas import CarbonSequestrationForecast


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

        # پارامترهای اولیه
        init = {
            "pC": soil_profile["initial_soc"],  # کربن اولیه
            "sC": 0.0,
            "bC": 0.0,
            "hC": 0.0,
            "iC": 0.0,
        }

        # اجرای مدل
        result = rothc.run(
            years=years,
            init=init,
            climate=soil_profile["climate"],
            management=management_scenario,
        )

        # محاسبه اعتبار کربن (هر تن CO2e = 1 credit)
        total_sequestered = result["SOC"][-1] - result["SOC"][0]
        co2e = total_sequestered * 44/12  # تبدیل C به CO2

        return CarbonSequestrationForecast(
            total_tonnes_co2e=co2e,
            yearly_projection=result["SOC"],
            credits_eligible=co2e * 0.85,  # 15% buffer
            confidence_interval=0.92,
        )
