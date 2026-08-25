"""
Economic Engine - Employment Generation Module.

Estimates direct, indirect, and induced employment effects of projects.
"""
from typing import Dict, Any, List


def estimate_direct_employment(
    activity_type: str,
    scale_of_activity: float,
    employment_intensity_per_unit: float, # Jobs per unit of activity (e.g., jobs per hectare, jobs per MLD water)
    job_type: str = "full_time_equivalent", # e.g., "full_time", "part_time", "seasonal"
    duration_months: float = 12.0 # Average duration of employment
) -> Dict[str, Any]:
    """
    Estimates direct employment created by a specific activity.

    Args:
        activity_type: Type of activity (e.g., 'cultivation', 'construction', 'operation').
        scale_of_activity: Scale of the activity (e.g., hectares cultivated, km of channel built).
        employment_intensity_per_unit: Number of jobs created per unit of activity.
        job_type: Type of employment contract.
        duration_months: Average duration of the job.

    Returns:
        Dictionary containing employment estimates.
    """
    direct_jobs = scale_of_activity * employment_intensity_per_unit

    return {
        "activity_type": activity_type,
        "scale_of_activity": scale_of_activity,
        "employment_intensity_per_unit": employment_intensity_per_unit,
        "job_type": job_type,
        "duration_months": duration_months,
        "direct_employment_person_months": direct_jobs * duration_months,
        "direct_employment_full_time_equivalent": direct_jobs * (duration_months / 12.0)
    }


def estimate_induced_employment(
    direct_employment_fte: float,
    household_size: float,
    income_spent_locally_fraction: float,
    local_multiplier: float # Jobs created per unit of spending in the local economy
) -> Dict[str, Any]:
    """
    Estimates induced employment (jobs created in local economy due to spending by direct employees).

    Args:
        direct_employment_fte: Direct full-time equivalent jobs.
        household_size: Average number of people supported per job.
        income_spent_locally_fraction: Fraction of income spent in the local economy.
        local_multiplier: Number of additional jobs created per unit of local spending.

    Returns:
        Dictionary containing induced employment estimates.
    """
    # Simplified model: Induced jobs = Direct jobs * household_size * income_spent_locally_fraction * local_multiplier
    # The local multiplier itself is a complex economic indicator.
    induced_jobs = direct_employment_fte * household_size * income_spent_locally_fraction * local_multiplier

    return {
        "direct_employment_full_time_equivalent": direct_employment_fte,
        "household_size": household_size,
        "income_spent_locally_fraction": income_spent_locally_fraction,
        "local_multiplier": local_multiplier,
        "induced_employment_full_time_equivalent": induced_jobs
    }


def calculate_total_employment_impact(
    direct_employment_data: List[Dict[str, Any]],
    indirect_employment_data: List[Dict[str, Any]], # e.g., from supply chain models
    induced_employment_data: Dict[str, Any] # Calculated from direct employment
) -> Dict[str, Any]:
    """
    Aggregates direct, indirect, and induced employment impacts.

    Args:
        direct_employment_data: List of direct employment estimates.
        indirect_employment_data: List of indirect employment estimates.
        induced_employment_data: Calculated induced employment.

    Returns:
        Dictionary containing total employment impact.
    """
    total_direct_fte = sum(d.get("direct_employment_full_time_equivalent", 0) for d in direct_employment_data)
    total_indirect_fte = sum(i.get("indirect_employment_full_time_equivalent", 0) for i in indirect_employment_data)
    total_induced_fte = induced_employment_data.get("induced_employment_full_time_equivalent", 0)

    total_fte = total_direct_fte + total_indirect_fte + total_induced_fte

    return {
        "total_employment_full_time_equivalent": total_fte,
        "breakdown": {
            "direct_fte": total_direct_fte,
            "indirect_fte": total_indirect_fte,
            "induced_fte": total_induced_fte
        },
        "details": {
            "direct": direct_employment_data,
            "indirect": indirect_employment_data,
            "induced": induced_employment_data
        }
    }
