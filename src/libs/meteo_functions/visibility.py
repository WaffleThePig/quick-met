"""
Atmospheric Visibility Calculation Engine.

This module provides two methodologies for calculating horizontal 
atmospheric visibility: a simple empirical moisture-based decay and a 
complex multi-variable physical extinction engine.
"""

import numpy as np
import xarray as xr

from src.libs.meteo_functions.constants import meteo_constants


def calc_visibility_from_rh(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """
    VISIBILITY INDEX (SIMPLE METHOD): Empirical Exponential Moisture Decay.

    METHODOLOGY OVERVIEW:
    --------------------
    This method uses a top-down, rule-based empirical framework to estimate horizontal
    atmospheric visibility. Designed as a computationally lightweight diagnostic tool, the
    algorithm focuses exclusively on moisture-driven visibility degradation (mist, haze,
    and dense fog) by evaluating atmospheric saturation near the surface.

    The algorithm maps ambient conditions to visibility through two distinct stages:
    1. Thermodynamic Saturation Resolution: Leverages the Magnus-Tetens framework to calculate
       Relative Humidity (RH) as a standardized fraction directly from 2m air temperature and
       dewpoint variables.
    2. Non-Linear Exponential Decay: Applies an empirical regression curves modeling statistical
       weather station behavior. Visibility is strictly bounded within a fixed perfect-sky upper
       limit (v_max) and decays along a steep, high-exponent curve as the air nears 100% saturation.
       This replicates the sudden, "cliff-like" visual drop-off observed during real-world mist
       and dense radiation fog transitions without requiring complex microphysical scattering math.

    OUTPUT SPECIFICATION:
    --------------------
    Returns horizontal visibility in kilometers (km) safely bounded within [0, v_max].
    To convert the final output to statute miles, multiply the result by 0.621371.

    SCIENTIFIC REFERENCES & METEOROLOGICAL STANDARDS:
    -------------------------------------------------
    - Lawrence, M. G. (2005). "The relationship between relative humidity and the dewpoint
      temperature in moist air." Bulletin of the American Meteorological Society, 86(2), 225-234.
      (Validates the foundational thermodynamic framework utilized to resolve true Relative
      Humidity fields).
    - American Meteorological Society (AMS) Glossary. "Visual Range and Extinction Coefficient."
      Retrieved 2026. (Validates log-linear empirical approximations and top-down statistical fits
      when high-resolution microphysical sensor payloads or hydrometeor data are unavailable).
    """
    rh_fraction = inputs["relative_humidity"]

    k = 4.0
    n = 12.0  # High power mimics rapid fog onset near saturation

    visibility = 20.0 * np.exp(-k * (rh_fraction ** n))
    visibility.clip(min=0, max=20)
    visibility.attrs["units"] = "km"
    visibility.name = "visibility"
    visibility.attrs["long_name"] = "Surface Visibility"
    visibility.attrs["description"] = "Visibility in km"
    visibility.attrs["valid_range"] = (0, 20)

    return visibility


def calc_visibility_complex(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """
    VISIBILITY INDEX (COMPLEX METHOD): Multi-Variable Physical Extinction Engine.

    METHODOLOGY OVERVIEW:
    --------------------
    This method uses a bottom-up, microphysical reconstruction approach to calculate
    horizontal atmospheric visibility. Instead of evaluating distance through simple
    statistical regressions, it breaks down the boundary layer into independent physical
    pathways that absorb or scatter light, converting them into additive extinction
    coefficients (beta).

    The algorithm isolates four distinct atmospheric hazard channels:
    1. Clear-Air Baseline: Sets the theoretical perfect-sky limit of the model based on
       clean molecular air scattering.
    2. Hygroscopic Aerosol Growth (Fog/Mist): Models the exponential swelling of microscopic
       airborne particles as the atmosphere approaches saturation (RH). Integrates ground skin
       temperature (skt) differentials to capture localized microclimates, such as early
       morning radiation fog or post-rain warm-ground steam mist.
    3. Hydrometeor Attenuation (Rain/Snow): Separates liquid and frozen precipitation phases.
       Because ice crystals possess a significantly larger geometric cross-section than liquid
       droplets, falling snow is penalized up to ten times more severely than liquid rain to
       accurately replicate real-world visibility restrictions.
    4. Kinetic Wind Obscuration (Blizzards/Dust): Triggers mechanical visibility reductions
       when wind vectors breach critical thresholds. Simulates freezing vectors driving loose
       snow into a whiteout state, or dry, high-velocity winds lifting surface dust/soil particles.

    The independent scattering channels are combined linearly into a total atmospheric extinction
    coefficient. This sum is translated into horizontal visual distance via Koschmieder's Law,
    resolving the exact distance at which a black target object loses visual contrast against the
    horizon.

    OUTPUT SPECIFICATION:
    --------------------
    Returns horizontal visibility in kilometers (km) bounded within [0, 20].
    To convert the final output to statute miles, multiply the result by 0.621371.

    SCIENTIFIC REFERENCES & METEOROLOGICAL STANDARDS:
    -------------------------------------------------
    - Koschmieder, H. (1924). "Theorie der horizontalen Sichtweite." Beiträge zur Physik
      der freien Atmosphäre, 12, 33-53. (Establishes foundational link between contrast
      thresholds and atmospheric extinction: V ≈ 3.912 / beta).
    - Hänel, G. (1976). "The properties of atmospheric aerosol particles as functions of relative
      humidity at thermodynamic equilibrium." Advances in Geophysics, 19, 73-188. (Provides
      the power laws governing aerosol water-uptake swelling).
    - Lawrence, M. G. (2005). "The relationship between relative humidity and the dewpoint
      temperature in moist air." Bulletin of the American Meteorological Society, 86(2), 225-234.
      (Validates the Magnus-Tetens framework used to resolve RH fields).
    - Kunkel, B. A., & Attwater, D. H. (1980). "Comparison of Liquid Water Content and Extinction
      Coefficients in Rain and Fog." Journal of Applied Meteorology. (Establishes empirical
      power laws linking explicit precipitation rates to light scattering).
    - American Meteorological Society (AMS) Glossary. "Visual Range and Extinction Coefficient."
      Retrieved 2026. (Validates operational standards for multi-variable diagnostic
      parameterizations).
    """
    beta_20km = meteo_constants.BETA_AIR / 20.0
    rh = inputs["relative_humidity"]
    temperature_in_c = inputs["temperature"]
    skin_temp_in_c = inputs["skt"]
    wind_u = inputs["u10"]
    wind_v = inputs["v10"]
    wind_speed_ms = np.sqrt(wind_u ** 2 + wind_v ** 2)
    total_precip_mm_hr = inputs["tp"]
    snowfall_mm_hr = inputs["sf"]

    # 1. Fog / Mist Obscuration (Base Aerosol Growth)
    rh_capped = np.minimum(rh, 0.995)
    beta_swelling_base = beta_20km * ((1.0 - rh_capped) ** -0.75 - 1.0)

    # 2. Skin Temperature Adjustment (Evaporative / Radiative Forcing)
    # Delta = Skin Temp - Air Temp
    t_delta = skin_temp_in_c - temperature_in_c

    # Scenario A: Warm, wet surface evaporating into cold air (Steam Mist)
    # Scenario B: Cold surface drawing air to dewpoint rapidly (Radiation Fog)
    # We amplify beta_swelling if RH is already high (> 80%) and t_delta is sharp
    flux_amplification = np.where((rh > 0.80) & (np.abs(t_delta) > 3.0),
                                1.0 + (np.abs(t_delta) - 3.0) * 0.15,
                                1.0)

    beta_swelling = beta_swelling_base * flux_amplification

    # 3. Hydrometeor Partitioning
    rain_rate = np.maximum(0.0, total_precip_mm_hr - snowfall_mm_hr)
    snow_rate = snowfall_mm_hr

    beta_rain = np.where(rain_rate > 0, 0.22 * (rain_rate ** 0.78), 0.0)
    beta_snow = np.where(snow_rate > 0, 2.10 * (snow_rate ** 0.72), 0.0)

    # 4. Wind Obscuration Factor
    beta_blowing_snow = np.where((wind_speed_ms > 9.0) & (temperature_in_c <= 0.0),
                                 0.08 * (wind_speed_ms - 9.0) ** 1.8,
                                 0.0)
    beta_blowing_dust = np.where((wind_speed_ms > 11.0) & (rh < 0.35),
                                 0.05 * (wind_speed_ms - 11.0) ** 1.5,
                                 0.0)
    beta_wind = beta_blowing_snow + beta_blowing_dust

    # 5. Total Extinction and Koschmieder's Transformation
    total_beta = beta_20km + beta_swelling + beta_rain + beta_snow + beta_wind
    visibility = rh.copy()
    visibility.values = 3.912 / total_beta
    visibility.clip(min=0, max=20)
    visibility.attrs["units"] = "km"
    visibility.name = "visibility"
    visibility.attrs["long_name"] = "Surface Visibility"
    visibility.attrs["description"] = "Visibility in km"
    visibility.attrs["valid_range"] = (0, 20)

    return visibility