"""
Standardized Physical and Meteorological Constants.

This module provides a centralized, immutable repository of physical constants, 
thermodynamic parameters, and conversion factors used throughout the 
meteorological library. These constants ensure mathematical consistency 
across different calculation engines (e.g., vapor pressure, icing, potential 
temperature).

The implementation uses a frozen dataclass to guarantee thread-safety and 
prevent runtime modification of fundamental physical values.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class MeteoConstants:
    """Immutable physical and meteorological constants.

    This class serves as a singleton container for fundamental atmospheric 
    constants. All values are sourced from WMO (World Meteorological 
    Organization) and standard atmospheric physics references (e.g., 
    Wallace & Hobbs).

    Attributes:
        ES_0 (float): Saturation vapor pressure at 0°C (273.15 K) in kilopascals (kPa).
        R_D (float): Gas constant for dry air in Joules per kilogram per Kelvin [J/(kg*K)].
        C_P (float): Specific heat of dry air at constant pressure in Joules per 
            kilogram per Kelvin [J/(kg*K)].
        KAPPA (float): Poisson constant (R_D / C_P), dimensionless.
        EPSILON (float): Ratio of the gas constant for dry air to that for water vapor 
            (approx. 0.62197), dimensionless.
        ZERO_C_K (float): Offset to convert degrees Celsius to Kelvin [K].
        P_BASE_MB (float): Reference baseline pressure for potential temperature 
            calculations in millibars [mb] or hectopascals [hPa].
        SVP_A (float): Dimensionless Magnus exponent multiplier for saturation vapor 
            pressure calculations over liquid water.
        SVP_B (float): Temperature scaling offset parameter in degrees Celsius (°C) 
            for Magnus-type equations.
        EARTH_RADIUS (float): Mean radius of the Earth in meters [m].
        BETA_AIR (float): Sea-level atmospheric extinction coefficient (approx. 0.012 km^-1).
        DIVIDE_BY_ZERO_TOLERANCE (float): Minimal threshold used to prevent 
            mathematical singularities in reciprocal calculations.
    """
    ES_0: float
    R_D: float
    C_P: float
    KAPPA: float
    EPSILON: float
    ZERO_C_K: float
    P_BASE_MB: float
    SVP_A: float
    SVP_B: float
    EARTH_RADIUS: float
    BETA_AIR: float
    DIVIDE_BY_ZERO_TOLERANCE: float

meteo_constants: MeteoConstants
