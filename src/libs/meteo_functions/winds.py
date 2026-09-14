"""
Atmospheric Wind Dynamics and Advection Engine.

This module provides tools for calculating vector-based atmospheric 
processes, specifically horizontal advection on a spherical Earth. It 
includes specialized handling for ERA5 global grids, including polar 
padding to ensure accurate gradient calculations across the North and South 
poles.
"""

import numpy as np
import xarray as xr
from src.libs.meteo_functions.constants import meteo_constants


def calc_theta_e_advection(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the horizontal advection of Equivalent Potential Temperature.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "theta_e": Equivalent potential temperature (K).
            - "eastward_wind": Zonal wind component (u) in m/s.
            - "northward_wind": Meridional wind component (v) in m/s.

    Returns:
        xr.DataArray: The advection of Theta-E (K/m/s).
    """
    theta_e = inputs["theta_e"]
    wind_u = inputs["eastward_wind"]
    wind_v = inputs["northward_wind"]

    theta_e_adv = calculate_era5_advection(theta_e, wind_u, wind_v)
    theta_e_adv.attrs["units"] = "K/m/s"
    return theta_e_adv


def pad_era5_poles(da: xr.DataArray, lat_dim: str = "latitude", lon_dim: str = "longitude") -> xr.DataArray:
    """Pads an ERA5 DataArray over the poles to allow for continuous gradients.

    This specialized padding rolls the opposite side of the globe by 180 
    degrees at the poles, creating ghost rows that maintain physical 
    continuity for differentiation.

    Args:
        da: The input DataArray (typically 1440x721).
        lat_dim: Name of the latitude dimension.
        lon_dim: Name of the longitude dimension.

    Returns:
        xr.DataArray: The padded DataArray with ghost rows at 90.25°N and -90.25°S.
    """
    # 1. Grab rows adjacent to the poles (ERA5 is typically North to South)
    # Index 1 is 89.75°N, Index -2 is -89.75°S
    row_near_np = da.isel(**{lat_dim: 1})
    row_near_sp = da.isel(**{lat_dim: -2})

    # 2. Shift longitudes by 180 degrees (exactly 720 points on a 1440 grid)
    ghost_np = row_near_np.roll(**{lon_dim: 720}, roll_coords=False)
    ghost_sp = row_near_sp.roll(**{lon_dim: 720}, roll_coords=False)

    # 3. Assign out-of-bounds coordinates (90 + 0.25 and -90 - 0.25)
    ghost_np = ghost_np.assign_coords(**{lat_dim: 90.25})
    ghost_sp = ghost_sp.assign_coords(**{lat_dim: -90.25})

    # 4. Concatenate back onto the array in North-to-South order
    padded_da = xr.concat([ghost_np, da, ghost_sp], dim=lat_dim)

    return padded_da


def calculate_era5_advection(
        scalar_da: xr.DataArray, 
        u_da: xr.DataArray, 
        v_da: xr.DataArray, 
        lat_name: str = "latitude", 
        lon_name: str = "longitude"
) -> xr.DataArray:
    """Calculates horizontal scalar advection for global ERA5 grids.

    This function performs vector calculus on a spherical coordinate system, 
    accounting for the convergence of meridians at high latitudes and 
    applying polar padding for gradient accuracy.

    Args:
        scalar_da: The scalar field to be advected (e.g., temperature, Theta-E).
        u_da: Zonal wind component (m/s).
        v_da: Meridional wind component (m/s).
        lat_name: Name of the latitude coordinate.
        lon_name: Name of the longitude coordinate.

    Returns:
        xr.DataArray: The advection field (-V • ∇C).
    """
    # 1. Pad over the poles
    c_pad = pad_era5_poles(scalar_da, lat_dim=lat_name, lon_dim=lon_name)
    u_pad = pad_era5_poles(u_da, lat_dim=lat_name, lon_dim=lon_name)
    v_pad = pad_era5_poles(v_da, lat_dim=lat_name, lon_dim=lon_name)

    # 2. Compute raw gradients per degree
    dc_dlon_deg = c_pad.differentiate(lon_name)
    dc_dlat_deg = c_pad.differentiate(lat_name)

    # 3. Scale to meters using spherical geometry
    deg_to_rad = np.pi / 180
    lat_rad = np.deg2rad(c_pad[lat_name])

    # Zonal conversion: Force exact pole points to 0 gradient to avoid 1/cos(90) infinity
    cos_lat = np.cos(lat_rad)
    dc_dx = dc_dlon_deg / (meteo_constants.EARTH_RADIUS * cos_lat * deg_to_rad)
    dc_dx = xr.where(np.abs(c_pad[lat_name]) >= 90.0, 0.0, dc_dx)

    # Meridional conversion: Safely continuous due to the padding rows
    dc_dy = dc_dlat_deg / (meteo_constants.EARTH_RADIUS * deg_to_rad)

    # 4. Compute advection (-V • ∇C)
    advection_padded = -(u_pad * dc_dx + v_pad * dc_dy)

    # 5. Extract original 721 latitudes, dropping the temporary ghost rows
    return advection_padded.sel(**{lat_name: scalar_da[lat_name].values})
