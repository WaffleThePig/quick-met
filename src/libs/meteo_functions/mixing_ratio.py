"""
Atmospheric Mixing Ratio Calculation Engine.

This module provides functions for calculating various water vapor mixing 
ratios, including saturation mixing ratio over water and conversions from 
specific humidity or relative humidity. It also includes functions for 
deriving cloud water mixing ratio.

Formulations are consistent with Wallace & Hobbs (2006) and WMO standards.
"""

import numpy as np
import xarray as xr
from src.libs.meteo_functions.constants import meteo_constants


def calc_sat_mixing_ratio_water(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the saturation mixing ratio of water vapor.

    Derives the saturation mixing ratio from the ambient pressure and the 
    saturation vapor pressure over liquid water.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "pressure_level": Ambient air pressure (hPa or millibars).
            - "saturation_vapor_pressure": Saturation vapor pressure (hPa or millibars).

    Returns:
        xr.DataArray: The saturation mixing ratio (kg/kg).
    """
    pressure_in_mb = inputs["pressure_level"]
    vapor_pressure_in_mb = inputs["saturation_vapor_pressure"]

    pressure_diff = pressure_in_mb - vapor_pressure_in_mb
    invalid_cond = (np.abs(pressure_diff) < meteo_constants.DIVIDE_BY_ZERO_TOLERANCE)
    safe_pressure_diff = xr.where(invalid_cond, np.nan, pressure_diff)

    sat_mix_ratio = (meteo_constants.EPSILON * vapor_pressure_in_mb) / safe_pressure_diff

    sat_mix_ratio.attrs["units"] = "kg / kg"
    return sat_mix_ratio


def calc_mixing_ratio_from_q(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the water vapor mixing ratio from specific humidity.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "specific_humidity": Specific humidity (kg/kg).

    Returns:
        xr.DataArray: The water vapor mixing ratio (kg/kg).
    """
    q = inputs["specific_humidity"]  # (kg/kg)

    q_safe = q.clip(min=meteo_constants.DIVIDE_BY_ZERO_TOLERANCE, max=(1.0 - meteo_constants.DIVIDE_BY_ZERO_TOLERANCE))
    mixing_ratio = q_safe / (1.0 - q_safe)

    mixing_ratio.attrs["units"] = "kg / kg"
    return mixing_ratio


def calc_mixing_ratio_from_rh(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the water vapor mixing ratio from relative humidity.

    Uses the pressure and saturation vapor pressure to derive the mixing 
    ratio based on the relative humidity fraction.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "pressure_level": Ambient air pressure (hPa).
            - "saturation_vapor_pressure": Saturation vapor pressure (hPa).
            - "relative_humidity": Relative humidity as a fraction (0.0 to 1.0).

    Returns:
        xr.DataArray: The water vapor mixing ratio (kg/kg).

    References:
        - Wallace & Hobbs (2006), Atmospheric Science: An Introductory Survey.
        - WMO (2008) Guide to Meteorological Instruments and Methods of Observation.
    """
    pressure = inputs["pressure_level"]
    vp = inputs["saturation_vapor_pressure"]
    rh_fraction = inputs["relative_humidity"]

    rh_safe = rh_fraction.clip(min=meteo_constants.DIVIDE_BY_ZERO_TOLERANCE, max=1.0)
    mixing_ratio = meteo_constants.EPSILON * vp * rh_safe / (pressure - vp)  # Wallace&Hobbs (2006), WMO 2008

    mixing_ratio.attrs["units"] = "kg / kg"
    return mixing_ratio


def calc_cloud_water_mixing_ratio_from_mxr(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the cloud water mixing ratio from vapor mixing ratio.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "clwc": Specific cloud liquid water content (kg/kg).
            - "mixing_ratio": Water vapor mixing ratio (kg/kg).

    Returns:
        xr.DataArray: The cloud water mixing ratio (kg/kg).
    """
    spec_cloud_liquid = inputs["clwc"]
    mixing_ratio = inputs["mixing_ratio"]

    cwmr = spec_cloud_liquid * (1 + mixing_ratio)
    cwmr.attrs["units"] = "kg / kg"
    return cwmr


def calc_cloud_water_mixing_ratio_from_q(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the cloud water mixing ratio from specific humidity.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "clwc": Specific cloud liquid water content (kg/kg).
            - "specific_humidity": Specific humidity (kg/kg).

    Returns:
        xr.DataArray: The cloud water mixing ratio (kg/kg).
    """
    spec_cloud_liquid = inputs["clwc"]
    q = inputs["specific_humidity"]

    cwmr = spec_cloud_liquid / (1 - q)
    cwmr.attrs["units"] = "kg / kg"
    return cwmr