"""
Atmospheric Relative Humidity Calculation Engine.

This module provides functions for calculating relative humidity (RH) from 
other hygrometric variables, such as specific humidity. The calculations 
ensure that RH values are bounded within the physical range of 0% to 100%.
"""

import xarray as xr
from src.libs.meteo_functions.constants import meteo_constants


def calculate_rh_from_specific_humidity(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the relative humidity from specific humidity.

    This function derives the mixing ratio from the specific humidity and 
    then calculates the relative humidity by comparing it to the saturation 
    mixing ratio.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "specific_humidity": Specific humidity (kg/kg).
            - "saturation_mixing_ratio": Saturation mixing ratio (kg/kg).

    Returns:
        xr.DataArray: The relative humidity in percent (%).

    References:
        - Wallace & Hobbs (2006) Equation 3.64.
    """
    q = inputs["specific_humidity"]
    sat_mxr = inputs["saturation_mixing_ratio"]
    mxr = q / (1.0 - q)
    rh = 100.0 * mxr / sat_mxr  # Wallace&Hobbs (2006) eq. 3.64
    bound_rh = rh.clip(min=0, max=100)
    bound_rh.attrs["units"] = "%"

    return bound_rh


import numpy as np
import xarray as xr

def calc_rh_from_temp_dewpoint(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the relative humidity from air temperature and dew point.

    This function uses the inverse Magnus-Tetens approximation to derive 
    relative humidity directly from temperature and dew point.

    The calculation follows:
    gamma_t = (SVP_A * T) / (SVP_B + T)
    gamma_td = (SVP_A * Td) / (SVP_B + Td)
    RH = 100 * exp(gamma_td - gamma_t)

    Args:
        inputs: A dictionary containing the input data arrays.
            - "temperature": Air temperature in degrees Celsius (°C).
            - "dewpoint": Dew point temperature in degrees Celsius (°C).

    Returns:
        xr.DataArray: The relative humidity as a percent (0.0 to 100.0).

    References:
        - Lawrence, M. G. (2005). "The relationship between relative humidity and the dewpoint 
          temperature in moist air." Bulletin of the American Meteorological Society.
    """
    temperature_in_c = inputs["temperature"]
    dewpoint_in_c = inputs["dewpoint"]

    # Calculate gamma for both temperature and dew point
    gamma_t = (meteo_constants.SVP_A * temperature_in_c) / (meteo_constants.SVP_B + temperature_in_c)
    gamma_td = (meteo_constants.SVP_A * dewpoint_in_c) / (meteo_constants.SVP_B + dewpoint_in_c)

    # The difference in gamma values gives the log of RH
    log_rh = gamma_td - gamma_t

    # Exponentiate to get the fraction and clip between 0.0 and 100.0 % to ensure physical limits
    rh = np.exp(log_rh) * 100.0
    rh = rh.clip(min=0.0, max=100.0)
    rh.attrs["units"] = "%"
    return rh
