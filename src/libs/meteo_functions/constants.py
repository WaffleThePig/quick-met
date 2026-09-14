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
        ES_0: Saturation vapor pressure at 0°C (273.15 K) in kilopascals (kPa).
        R_D: Gas constant for dry air in Joules per kilogram per Kelvin [J/(kg*K)].
        C_P: Specific heat of dry air at constant pressure in Joules per 
            kilogram per Kelvin [J/(kg*K)].
        KAPPA: Poisson constant (R_D / C_P), dimensionless.
        EPSILON: Ratio of the gas constant for dry air to that for water vapor 
            (approx. 0.62197), dimensionless.
        ZERO_C_K: Offset to convert degrees Celsius to Kelvin [K].
        P_BASE_MB: Reference baseline pressure for potential temperature 
            calculations in millibars [mb] or hectopascals [hPa].
        SVP_A: Dimensionless Magnus exponent multiplier for saturation vapor 
            pressure calculations over liquid water.
        SVP_B: Temperature scaling offset parameter in degrees Celsius (°C) 
            for Magnus-type equations.
        EARTH_RADIUS: Mean radius of the Earth in meters [m].
        DIVIDE_BY_ZERO_TOLERANCE: Minimal threshold used to prevent 
            mathematical singularities in reciprocal calculations.
    """
    ES_0: float = 0.611205              # Saturation vapor pressure at 0°C (kPa)
    R_D: float = 287.053                # Gas constant for dry air [J/(kg*K)]
    C_P: float = 1005.7                 # Specific heat of dry air at constant pressure [J/(kg*K)]
    KAPPA: float = 0.2854               # Poisson constant (R_D / C_P)
    EPSILON: float = 0.62197            # Ratio of dry air to water vapor molecular mass
    ZERO_C_K: float = 273.15            # Zero degrees Celsius in Kelvin [K]
    P_BASE_MB: float = 1000.0           # Reference baseline pressure for potential temperature [mb]
    SVP_A: float = 17.7548              # Dimensionless Magnus exponent multiplier
    SVP_B: float = 244.55               # Temperature scaling offset parameter (°C)
    BETA_AIR: float = 3.912             # Air visibility baseline (Koschmieder, 1924)
    EARTH_RADIUS: float = 6371000.0     # Earth's radius in meters


    # Validation tolerance
    DIVIDE_BY_ZERO_TOLERANCE: float = 1e-10


# Instantiate ONCE as a singleton reference for the whole module space
meteo_constants = MeteoConstants()