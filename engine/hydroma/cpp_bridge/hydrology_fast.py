"""Muskingum-Cunge flood routing - industry standard method.

This is the same method used in HEC-HMS, SWMM, and MIKE flood models.
It solves the continuity equation with a storage-displacement relationship.

Reference: 
- Cunge, J.A. (1969). "On the subject of a flood propagation computation method"
- Chow, V.T. et al. (1988). "Applied Hydrology"
- USACE HEC-HMS Technical Reference Manual

Advantages over Saint-Venant:
- Unconditionally stable (no CFL restriction)
- O(n) complexity per timestep
- Physically based attenuation and lag
"""
import numpy as np

try:
    from numba import njit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator


@njit(cache=True)
def _muskingum_cunge_route(
    inflow: np.ndarray,
    K: float,
    x: float,
    dt: float,
) -> np.ndarray:
    """Route inflow hydrograph using Muskingum-Cunge method.
    
    O(t+1) = C0*I(t+1) + C1*I(t) + C2*O(t)
    
    Args:
        inflow: Inflow hydrograph [m³/s]
        K: Storage time constant [s] = travel time
        x: Weighting factor [0, 0.5]
        dt: Time step [s]
    
    Returns:
        Outflow hydrograph [m³/s]
    """
    n = len(inflow)
    outflow = np.zeros(n, dtype=np.float64)
    
    # Muskingum-Cunge coefficients
    denom = K - K * x + 0.5 * dt
    if denom <= 0:
        # Fallback: K too small, just pass through
        return inflow.copy()
    
    C0 = (-K * x + 0.5 * dt) / denom
    C1 = (K * x + 0.5 * dt) / denom
    C2 = (K - K * x - 0.5 * dt) / denom
    
    # Initial outflow = initial inflow
    outflow[0] = inflow[0]
    
    # Route through time
    for t in range(1, n):
        outflow[t] = C0 * inflow[t] + C1 * inflow[t-1] + C2 * outflow[t-1]
        
        # Ensure non-negative
        if outflow[t] < 0:
            outflow[t] = 0.0
    
    return outflow


def compute_wave_parameters(
    channel_length: float,
    bed_slope: float,
    manning_n: float,
    channel_width: float,
    peak_flow: float,
) -> dict:
    """Compute wave celerity and K parameter from channel geometry.
    
    Uses kinematic wave approximation:
    - Normal depth from Manning's equation
    - Wave celerity c = dQ/dA ≈ (5/3) * v for wide channels
    - K = L / c (travel time)
    
    Args:
        channel_length: Channel length [m]
        bed_slope: Channel bed slope [m/m]
        manning_n: Manning's roughness coefficient
        channel_width: Channel width [m]
        peak_flow: Peak discharge [m³/s]
    
    Returns:
        Dictionary with K, x, celerity, normal_depth
    """
    # Unit-width discharge
    q = peak_flow / channel_width
    
    # Normal depth from Manning: q = (1/n) * h^(5/3) * S^(1/2)
    # h = (q * n / sqrt(S))^(3/5)
    if q > 0 and bed_slope > 0:
        h_normal = (q * manning_n / np.sqrt(bed_slope)) ** 0.6
    else:
        h_normal = 0.1
    
    # Mean velocity
    v = q / h_normal if h_normal > 0 else 0.1
    
    # Kinematic wave celerity: c = (5/3) * v for wide rectangular channel
    celerity = (5.0 / 3.0) * v
    
    # Travel time K
    K = channel_length / celerity if celerity > 0 else 100.0
    
    # Weighting factor x (0.0 to 0.5)
    # Lower x = more attenuation (diffusion)
    # Typical: 0.2 for natural channels
    x = 0.2
    
    return {
        "K": K,
        "x": x,
        "celerity": celerity,
        "normal_depth": h_normal,
        "velocity": v,
        "travel_time": K,
    }


def route_flood_wave(
    inflow_hydrograph: np.ndarray,
    channel_length: float = 1000.0,
    n_cells: int = 50,
    manning_n: float = 0.030,
    bed_slope: float = 0.002,
    dt: float = 10.0,
    channel_width: float = 5.0,
) -> dict:
    """Route a flood wave using Muskingum-Cunge method.
    
    This is the industry-standard method used in HEC-HMS and SWMM.
    
    Args:
        inflow_hydrograph: Inflow discharge [m³/s] over time
        channel_length: Channel length [m]
        n_cells: Number of routing reaches (for multi-reach routing)
        manning_n: Manning's roughness
        bed_slope: Channel bed slope
        dt: Time step [s]
        channel_width: Channel width [m]
    
    Returns:
        Routing statistics dictionary
    """
    inflow = np.asarray(inflow_hydrograph, dtype=np.float64)
    peak_in = float(np.max(inflow))
    
    # Compute wave parameters
    params = compute_wave_parameters(
        channel_length, bed_slope, manning_n,
        channel_width, peak_in
    )
    
    # Single-reach Muskingum-Cunge routing
    outflow = _muskingum_cunge_route(
        inflow, params["K"], params["x"], dt
    )
    
    # Compute statistics
    peak_out = float(np.max(outflow))
    peak_in_idx = int(np.argmax(inflow))
    peak_out_idx = int(np.argmax(outflow))
    
    # Mass conservation check (volume in vs volume out)
    volume_in = float(np.sum(inflow) * dt)
    volume_out = float(np.sum(outflow) * dt)
    mass_balance = volume_out / volume_in if volume_in > 0 else 0.0
    
    return {
        "outflow_hydrograph": outflow,
        "peak_inflow": peak_in,
        "peak_outflow": peak_out,
        "peak_attenuation": peak_in - peak_out,
        "attenuation_ratio": peak_out / peak_in if peak_in > 0 else 0.0,
        "time_lag": (peak_out_idx - peak_in_idx) * dt,
        "time_to_peak_out": peak_out_idx * dt,
        "travel_time": params["travel_time"],
        "celerity": params["celerity"],
        "normal_depth": params["normal_depth"],
        "volume_in": volume_in,
        "volume_out": volume_out,
        "mass_balance": mass_balance,
    }


def route_multi_reach(
    inflow_hydrograph: np.ndarray,
    channel_length: float,
    n_reaches: int,
    manning_n: float = 0.030,
    bed_slope: float = 0.002,
    dt: float = 10.0,
    channel_width: float = 5.0,
) -> dict:
    """Route through multiple reaches for more accurate attenuation.
    
    Each reach is routed independently, with outflow of reach i
    becoming inflow of reach i+1.
    """
    inflow = np.asarray(inflow_hydrograph, dtype=np.float64)
    reach_length = channel_length / n_reaches
    
    current_inflow = inflow.copy()
    total_K = 0.0
    
    for _ in range(n_reaches):
        params = compute_wave_parameters(
            reach_length, bed_slope, manning_n,
            channel_width, float(np.max(current_inflow))
        )
        total_K += params["K"]
        
        current_inflow = _muskingum_cunge_route(
            current_inflow, params["K"], params["x"], dt
        )
    
    outflow = current_inflow
    
    peak_in = float(np.max(inflow))
    peak_out = float(np.max(outflow))
    
    return {
        "outflow_hydrograph": outflow,
        "peak_inflow": peak_in,
        "peak_outflow": peak_out,
        "attenuation_ratio": peak_out / peak_in if peak_in > 0 else 0.0,
        "total_travel_time": total_K,
        "n_reaches": n_reaches,
    }
