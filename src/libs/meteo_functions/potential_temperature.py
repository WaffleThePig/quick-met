"""
Atmospheric Potential Temperature Calculation Engine.

This module provides analytical formulations for calculating the potential 
temperature and equivalent potential temperature (Theta-E). It implements 
the standard Bolton (1980) equations, which are widely used in numerical 
weather prediction for their accuracy in representing moist thermodynamic 
processes.
"""

import numpy as np
import xarray as xr
from src.libs.meteo_functions.constants import meteo_constants


def calc_theta_e_basic(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the Equivalent Potential Temperature (Theta-E).

    This function implements the standard Bolton (1980) Equation 38 
    formulation, which accounts for the latent heat of condensation as air 
    is lifted to its Lifted Condensation Level (LCL).

    Args:
        inputs: A dictionary containing the input data arrays.
            - "temperature": Air temperature in Kelvin (K).
            - "dewpoint": Dew point temperature in Kelvin (K).
            - "pressure_level": Ambient air pressure (hPa).
            - "mixing_ratio": Water vapor mixing ratio (kg/kg).

    Returns:
        xr.DataArray: The equivalent potential temperature in Kelvin (K).

    References:
        - Bolton, D. (1980). "The Computation of Equivalent Potential Temperature". 
          Monthly Weather Review.
    """
    temperature_in_k = inputs["temperature"]
    dewpoint_in_k = inputs["dewpoint"]
    pressure = inputs["pressure_level"]
    mixing_ratio = inputs["mixing_ratio"]

    # Calculate dry potential temperature (Theta)
    #   Uses standard dry air approximation mapping to reference level (1000 mb)
    theta = temperature_in_k * (meteo_constants.P_BASE_MB / pressure) ** meteo_constants.KAPPA

    # Calculate Lifted Condensation Level (LCL) Temperature
    #   Analytical approximation via Bolton Eq. 22
    t_lcl = 56.0 + (1.0 / (1.0 / (dewpoint_in_k - 56.0) + np.log(temperature_in_k / dewpoint_in_k) / 800.0))

    # Resolve the Bolton latent phase change exponent
    t_lcl_c = t_lcl - meteo_constants.ZERO_C_K
    latent_heat_factor = 2697500.0 - 2554.5 * t_lcl_c
    moisture_mass_corr = mixing_ratio * 1.00081
    exponent = (latent_heat_factor * moisture_mass_corr) / (t_lcl * meteo_constants.C_P)

    # Compute final values
    theta_e = theta * np.exp(exponent)
    theta_e.attrs["units"] = "degK"
    return theta_e


