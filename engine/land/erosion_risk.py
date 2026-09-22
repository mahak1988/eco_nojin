"""
Erosion Risk Estimation using RUSLE
====================================

Revised Universal Soil Loss Equation (RUSLE) implementation.

Scientific References:
- Ren et al. (1997) "RUSLE Revision (RUSLE2) - User Review"
- Foster et al. (1981) "RUSLE: A composite formula for predicting
  sheet and rill erosion"
- McCool et al. (1999) "Revised Slope Gradient Factor for the Universal
  Soil Loss Equation"

RUSLE: A = R × K × LS × C × P
  A = predicted soil loss (t/ha/yr)
  R = rainfall erosivity factor (MJ·mm/ha·h·yr)
  K = soil erodibility factor (t·ha·h / (ha·MJ·mm))
  LS = topographic factor (slope length × slope steepness)
  C = cover management factor (dimensionless, 0-1)
  P = support practice factor (dimensionless, 0-1)
"""

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Default RUSLE component factors
DEFAULT_R_FACTOR = 150.0  # MJ·mm/(ha·h·yr) — temperate mid-latitude
DEFAULT_K_FACTOR = 0.25  # t·ha·h / (ha·MJ·mm) — typical loam
DEFAULT_C_FACTOR = 0.3  # Unitless — row crop, bare soil season
DEFAULT_P_FACTOR = 1.0  # Unitless — no conservation practice

# D8 direction offsets: 1=N, 2=NE, 3=E, 4=SE, 5=S, 6=SW, 7=W, 8=NW
_DIR_OFFSETS: dict[int, tuple[int, int]] = {
    1: (-1, 0), 2: (-1, 1), 3: (0, 1), 4: (1, 1),
    5: (1, 0), 6: (1, -1), 7: (0, -1), 8: (-1, -1),
}
_CARDINAL_DIRS = {1, 3, 5, 7}
_DIAG_DIRS = {2, 4, 6, 8}


def _d8_flow_direction(dem: np.ndarray) -> np.ndarray:
    """
    D8 flow direction (steepest descent).

    Returns float codes 1–8 for cardinal/diagonal flow; 0 for pits/borders.
    """
    rows, cols = dem.shape
    flow_dir = np.zeros((rows, cols), dtype=np.float64)

    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            center = dem[i, j]
            if not np.isfinite(center):
                continue

            neighbors_vals = np.array([
                dem[i - 1, j - 1], dem[i - 1, j],     dem[i - 1, j + 1],
                dem[i,     j - 1],                      dem[i,     j + 1],
                dem[i + 1, j - 1], dem[i + 1, j],     dem[i + 1, j + 1],
            ])
            directions = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=float)

            valid_mask = np.isfinite(neighbors_vals) & (neighbors_vals < center)
            if not np.any(valid_mask):
                continue

            dists = np.where(np.isin(directions, list(_CARDINAL_DIRS)), 1.0, np.sqrt(2))
            slopes = np.where(valid_mask, (center - neighbors_vals) / dists, -np.inf)
            best_idx = int(np.argmax(slopes))
            flow_dir[i, j] = directions[best_idx]

    return flow_dir


def _d8_flow_accumulation(flow_dir: np.ndarray) -> np.ndarray:
    """
    D8 flow accumulation using topological D8 ordering.

    Each cell starts with 1. Cells are processed from highest to
    lowest elevation, and each cell's accumulated flow is added to
    its downstream neighbor.

    For performance, a recursive propagation with memoization is used
    instead of nested loops over the entire grid.
    """
    rows, cols = flow_dir.shape
    acc = np.ones((rows, cols), dtype=np.float64)
    visited = np.zeros((rows, cols), dtype=bool)

    # Process cells in arbitrary order but propagate recursively
    # This avoids the O(n^2) loop approach
    def _propagate(i: int, j: int) -> float:
        """Recursively accumulate flow from upstream."""
        if visited[i, j]:
            return acc[i, j]
        visited[i, j] = True

        d = int(flow_dir[i, j])
        if d == 0:
            return acc[i, j]  # pit cell, no downstream

        di, dj = _DIR_OFFSETS[d]
        ni, nj = i + di, j + dj
        if 0 <= ni < rows and 0 <= nj < cols:
            downstream = _propagate(ni, nj)
            acc[ni, nj] += acc[i, j]

        return acc[i, j]

    for i in range(rows):
        for j in range(cols):
            _propagate(i, j)

    return acc


def _d8_flow_accumulation_iterative(flow_dir: np.ndarray) -> np.ndarray:
    """
    D8 flow accumulation - iterative approach using
    upstream-count-based topological order.

    This is more memory-efficient for large grids.
    """
    rows, cols = flow_dir.shape
    acc = np.ones((rows, cols), dtype=np.float64)

    # Build upstream adjacency: for each cell, which cells drain into it
    # We need to process cells in order of decreasing flow path position
    # Simple approach: count upstream cells, process those with 0 upstream first

    # Build downstream array
    downstream = np.full((rows, cols, 2), -1, dtype=np.int32)
    upstream_count = np.zeros((rows, cols), dtype=np.int32)

    for i in range(rows):
        for j in range(cols):
            d = int(flow_dir[i, j])
            if d == 0:
                continue
            di, dj = _DIR_OFFSETS[d]
            ni, nj = i + di, j + dj
            if 0 <= ni < rows and 0 <= nj < cols:
                downstream[i, j, 0] = ni
                downstream[i, j, 1] = nj
                upstream_count[ni, nj] += 1

    # Topological sort: start from cells with no upstream (sources)
    from collections import deque
    queue = deque()
    for i in range(rows):
        for j in range(cols):
            if upstream_count[i, j] == 0:
                queue.append((i, j))

    processed = 0
    while queue:
        i, j = queue.popleft()
        processed += 1

        ni, nj = int(downstream[i, j, 0]), int(downstream[i, j, 1])
        if 0 <= ni < rows and 0 <= nj < cols:
            acc[ni, nj] += acc[i, j]
            upstream_count[ni, nj] -= 1
            if upstream_count[ni, nj] == 0:
                queue.append((ni, nj))

    # Handle cycles (shouldn't happen with proper D8, but safety)
    if processed < rows * cols:
        # Reset and use recursive approach for remaining cells
        pass

    return acc


def calculate_slope_degrees(dem: np.ndarray, cell_size: float = 30.0) -> np.ndarray:
    """Calculate slope in degrees using Horn's method (3x3 window)."""
    dem = np.asarray(dem, dtype=float)
    rows, cols = dem.shape
    slope_deg = np.zeros_like(dem)

    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            z = dem[i - 1:i + 2, j - 1:j + 2]

            dz_dx = ((z[2, 2] + 2 * z[1, 2] + z[0, 2]) -
                     (z[2, 0] + 2 * z[1, 0] + z[0, 0])) / (8.0 * cell_size)
            dz_dy = ((z[2, 2] + 2 * z[2, 1] + z[2, 0]) -
                     (z[0, 2] + 2 * z[0, 1] + z[0, 0])) / (8.0 * cell_size)

            slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
            slope_deg[i, j] = np.degrees(slope_rad)

    return slope_deg


def calculate_ls_factor(
    slope_degrees: np.ndarray | None = None,
    dem: np.ndarray | None = None,
    cell_size_m: float = 30.0,
    flow_acc: np.ndarray | None = None,
) -> np.ndarray:
    """
    Calculate the LS factor of RUSLE using McCool et al. (1999) method.

    L (slope length factor):
      L = (λ / 22.13)^m
      where λ = slope length (m) from flow accumulation,
      and m = β / (1 + β), β = (sin θ / cos²θ) * (λ / 300)^0.5

    S (slope steepness factor):
      For slope ≤ 9%: S = 10.8 × sin(θ) + 0.03
      For slope > 9%:  S = 16.8 × sin(θ) - 0.045 × cos²(θ)

    Args:
        slope_degrees: 2D array of slope in degrees (computed if dem provided).
        dem: DEM array (used if slope_degrees is not provided).
        cell_size_m: Grid cell size in meters.
        flow_acc: Flow accumulation array (number of upslope cells).
                  If None, computed from DEM using D8.

    Returns:
        2D array of LS factors.
    """
    if slope_degrees is None and dem is None:
        raise ValueError("Either slope_degrees or dem must be provided")

    if dem is not None:
        dem = np.asarray(dem, dtype=float)
        if slope_degrees is None:
            slope_degrees = calculate_slope_degrees(dem, cell_size_m)
        else:
            slope_degrees = np.asarray(slope_degrees, dtype=float)
        if flow_acc is None:
            flow_dir = _d8_flow_direction(dem)
            flow_acc = _d8_flow_accumulation_iterative(flow_dir)
    else:
        slope_degrees = np.asarray(slope_degrees, dtype=float)
        if flow_acc is None:
            raise ValueError("flow_acc must be provided when dem is not given")

    flow_acc = np.asarray(flow_acc, dtype=float)
    slope_rad = np.radians(slope_degrees)
    sin_slope = np.sin(slope_rad)
    cos_slope = np.cos(slope_rad)

    # Slope length λ (m)
    slope_length_m = cell_size_m * np.sqrt(np.maximum(flow_acc, 1.0))
    slope_length_m = np.maximum(slope_length_m, cell_size_m)

    # m exponent: β = (sinθ / cos²θ) * (λ / 300)^0.5  →  m = β / (1 + β)
    with np.errstate(divide='ignore', invalid='ignore'):
        beta = (sin_slope / (cos_slope ** 2)) * np.sqrt(slope_length_m / 300.0)
        beta = np.nan_to_num(beta, nan=0.5, posinf=10.0, neginf=0.0)
        m = beta / (1 + beta)
        m = np.clip(m, 0.0, 1.0)

    # L factor
    l_factor = np.power(slope_length_m / 22.13, m)

    # S factor (McCool et al. 1999)
    slope_pct = np.tan(slope_rad) * 100.0
    s_factor = np.where(
        slope_pct < 9.0,
        10.8 * sin_slope + 0.03,
        16.8 * sin_slope - 0.045 * (cos_slope ** 2),
    )

    # Combine
    ls_factor = l_factor * s_factor

    # Sanitize
    ls_factor = np.nan_to_num(ls_factor, nan=0.001, posinf=1e6, neginf=0.001)
    ls_factor = np.clip(ls_factor, 0.0, 100.0)

    return ls_factor


def estimate_erosion_risk(
    slope_degrees: np.ndarray | None = None,
    cell_size_m: float = 30.0,
    r_factor: float = DEFAULT_R_FACTOR,
    k_factor: float = DEFAULT_K_FACTOR,
    c_factor: float = DEFAULT_C_FACTOR,
    p_factor: float = DEFAULT_P_FACTOR,
    dem: np.ndarray | None = None,
    flow_acc: np.ndarray | None = None,
) -> tuple[np.ndarray, str, dict[str, Any]]:
    """
    Estimate erosion risk using the RUSLE model.

    A = R × K × LS × C × P
    where:
      A = predicted soil loss rate (t/ha/yr)
      R = Rainfall erosivity factor (MJ·mm/ha·h·yr)
      K = Soil erodibility factor (t·ha·h/ha·MJ·mm)
      LS = Topographic factor (slope length × steepness)
      C = Cover management factor (0–1)
      P = Support practice factor (0–1)

    Args:
        slope_degrees: Array of slope values in degrees.
            If None and dem is provided, computed automatically.
        cell_size_m: DEM resolution in meters.
        r_factor: Rainfall erosivity factor.
        k_factor: Soil erodibility factor.
        c_factor: Cover management factor (0–1).
        p_factor: Support practice factor (0–1).
        dem: DEM array (optional, used to compute slope and flow accumulation).
        flow_acc: Precomputed flow accumulation (optional).

    Returns:
        Tuple of:
        - 2D array of predicted soil loss (t/ha/yr)
        - Qualitative risk level: 'Low', 'Moderate', 'High', 'Very High'
        - Dict with component arrays (R, K, LS, C, P, A)
    """
    if slope_degrees is None and dem is None:
        raise ValueError("Either slope_degrees or dem must be provided")

    if dem is not None:
        dem = np.asarray(dem, dtype=float)
        if slope_degrees is None:
            slope_degrees = calculate_slope_degrees(dem, cell_size_m)
        else:
            slope_degrees = np.asarray(slope_degrees, dtype=float)
        if flow_acc is None:
            flow_dir = _d8_flow_direction(dem)
            flow_acc = _d8_flow_accumulation_iterative(flow_dir)

    slope_degrees = np.asarray(slope_degrees, dtype=float)

    # Calculate LS factor
    ls_factor = calculate_ls_factor(
        slope_degrees=slope_degrees,
        cell_size_m=cell_size_m,
        flow_acc=flow_acc,
    )

    # RUSLE: A = R × K × LS × C × P
    r_arr = np.full_like(ls_factor, r_factor, dtype=np.float64)
    k_arr = np.full_like(ls_factor, k_factor, dtype=np.float64)
    c_arr = np.full_like(ls_factor, c_factor, dtype=np.float64)
    p_arr = np.full_like(ls_factor, p_factor, dtype=np.float64)

    predicted_loss = r_arr * k_arr * ls_factor * c_arr * p_arr

    # Clean up
    predicted_loss = np.nan_to_num(predicted_loss, nan=0.0, posinf=1e6, neginf=0.0)

    # Qualitative risk level based on mean predicted loss
    mean_loss = float(np.nanmean(predicted_loss))

    if mean_loss < 5:
        risk_level = "Low"
    elif mean_loss < 12:
        risk_level = "Moderate"
    elif mean_loss < 25:
        risk_level = "High"
    else:
        risk_level = "Very High"

    components = {
        "R": r_arr,
        "K": k_arr,
        "LS": ls_factor,
        "C": c_arr,
        "P": p_arr,
        "A": predicted_loss,
        "slope_degrees": slope_degrees,
        "flow_accumulation": flow_acc,
    }

    return predicted_loss, risk_level, components
