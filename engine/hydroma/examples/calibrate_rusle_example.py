"""Example of calibrating RUSLE model parameters."""
from engine.hydroma.calibration.model_calibrator import CalibrationInput, Calibrator
from engine.hydroma.simulation.contracts import (  # Assuming RUSLEInput exists or is similar to ChainInputs
    ChainInputs,
    RUSLEInput,
)
from engine.hydroma.simulation.orchestrator import _run_rusle  # Assuming the internal runner exists


# Define a wrapper for the RUSLE model to fit the ModelRunner protocol
class RUSLERunnerAdapter:
    def __init__(self, base_inputs: ChainInputs):
        self.base_inputs = base_inputs

    def run(self, parameters: dict):
        # Update base inputs with calibrated parameters
        rusle_in = RUSLEInput(
            land_profile_id=self.base_inputs.site_id,
            rainfall_erosivity=parameters.get('r_factor', self.base_inputs.r_factor),
            soil_erodibility=parameters.get('k_factor', self.base_inputs.k_factor),
            slope_length_factor=parameters.get('ls_factor', self.base_inputs.ls_factor),
            slope_steepness_factor=parameters.get('s_factor', 1.0), # Assuming this was missing and needs calibration
            cover_factor=parameters.get('c_factor', self.base_inputs.c_factor_base),
            management_factor=parameters.get('p_factor', 1.0),
        )
        result = _run_rusle(rusle_in)
        # Return simulated values (e.g., erosion rate)
        return result # Assuming result has an attribute like .erosion_rate_t_ha_yr

def run_example():
    # Example base inputs and observed data
    base_inputs = ChainInputs(
        site_id="example_site_1",
        area_ha=10.0,
        scenario=None, # Not used here
        r_factor=100.0, k_factor=0.2, ls_factor=1.0, c_factor_base=0.3
        # ... other required fields for ChainInputs ...
    )
    observed_erosion = [5.0, 7.2, 4.8] # Example observed rates
    # Assuming the model runs for 3 periods and returns 3 simulated rates

    model_adapter = RUSLERunnerAdapter(base_inputs)

    cal_input = CalibrationInput(
        model_runner=model_adapter,
        observed_data=observed_erosion,
        parameter_bounds={
            "k_factor": (0.1, 0.5),
            "c_factor": (0.1, 0.5),
            # Add other parameters to calibrate
        },
        objective_function="rmse"
    )

    calibrator = Calibrator()
    result = calibrator.execute(cal_input)

    print(f"Calibrated Parameters: {result.calibrated_parameters}")
    print(f"Best Objective Value (RMSE): {result.best_objective_value}")

if __name__ == "__main__":
    run_example()
