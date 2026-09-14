"""
Atmospheric Dew Point Temperature Calculation Engine.

This module provides analytical formulations for deriving the dew point 
temperature from diverse hygrometric inputs, such as specific humidity or 
relative humidity. It utilizes Magnus-type approximations consistent with 
WMO standards and provides a unified interface for vectorized Xarray processing.
"""

import numpy as np
import xarray as xr
from src.libs.meteo_functions.constants import meteo_constants


def calc_dew_point_from_q(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the dew point temperature from specific humidity and pressure.

    This function first derives the actual water vapor pressure (e) from the 
    specific humidity and then applies the inverse Magnus formula to solve 
    for the dew point.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "specific_humidity": Mass fraction of water vapor in the air (kg/kg).
            - "pressure_level": Ambient air pressure, typically in kPa.

    Returns:
        xr.DataArray: The dew point temperature in degrees Celsius (°C).
    """
    q = inputs["specific_humidity"]  # (kg/kg)
    pressure_in_kpa = inputs["pressure_level"]

    # Calculate actual water vapor pressure field (e) in kPa
    e = (q * pressure_in_kpa) / (meteo_constants.EPSILON + (1.0 - meteo_constants.EPSILON) * q)
    ln_e_ratio = np.log(np.clip(e / meteo_constants.ES_0, meteo_constants.DIVIDE_BY_ZERO_TOLERANCE, None))

    dewpoint = meteo_constants.SVP_B * (ln_e_ratio / (meteo_constants.SVP_A - ln_e_ratio))
    dewpoint.attrs["units"] = "degC"
    return dewpoint


def calc_dew_point_from_rh(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the dew point temperature from relative humidity and temperature.

    This function utilizes the Magnus-Tetens approximation to derive the dew 
    point temperature based on the air temperature and the relative humidity 
    fraction.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "temperature": Air temperature in degrees Celsius (°C).
            - "relative_humidity": Relative humidity as a fraction (0.0 to 1.0).

    Returns:
        xr.DataArray: The dew point temperature in degrees Celsius (°C).
    """
    temperature_in_c = inputs["temperature"]
    rh_fraction = inputs["relative_humidity"]

    log_rh = np.log(rh_fraction.clip(min=meteo_constants.DIVIDE_BY_ZERO_TOLERANCE))
    gamma = ((meteo_constants.SVP_A * temperature_in_c) / (meteo_constants.SVP_B + temperature_in_c)) + log_rh

    dewpoint = (meteo_constants.SVP_B * gamma) / (meteo_constants.SVP_A - gamma)
    dewpoint.attrs["units"] = "degC"
    return dewpoint