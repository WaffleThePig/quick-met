"""
Aircraft Icing Type and Intensity Diagnostic Engine.

This module implements a heuristic multi-threshold algorithm for diagnosing 
in-flight icing hazards. It utilizes thermodynamic and microphysical fields 
to categorize icing risk by physical type (Rime vs. Mixed) and severity.
"""

import numpy as np
import xarray as xr


def calc_icing_type_intensity(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the aircraft icing type and intensity indicator.

    This diagnostic algorithm follows the heuristic multi-threshold approach 
    derived from the AFWA/NCAR RAL algorithms. It evaluates atmospheric 
    variables to identify potential icing hazards, categorized by type (Rime, 
    Mixed) and intensity (Trace, Light, Moderate).

    The algorithm considers:
    1. Solid cloud deck scaling (RH-based).
    2. Dynamic updraft convective curves (Vertical velocity-based).
    3. Supercooled Large Droplet (SCLD) potential.
    4. Structural icing window (-15°C to 0°C).

    Args:
        inputs: A dictionary containing the input data arrays.
            - "temperature": Air temperature in Kelvin (K).
            - "theta_e_adv": Equivalent potential temperature advection (K/s).
            - "relative_humidity": Relative humidity (0 to 100).
            - "cloud_cover": Fractional horizontal coverage (0 to 100).
            - "cloud_water_mixing_ratio": Cloud Water Mixing Ratio (g/kg).
            - "pvv": Positive Vertical Velocity (Pa/s or similar, will be converted).

    Returns:
        xr.DataArray: Integer codes representing icing type and intensity:
            - 0: None
            - 1: Rime Ice - Trace
            - 2: Rime Ice - Light
            - 3: Mixed Ice - Light
            - 5: Rime Ice - Moderate
            - 6: Mixed Ice - Moderate

    References:
        - Bernstein, B. C., et al. (2005). "The Current Icing Potential (CIP)
            Algorithm: Description and Comparison with Aircraft Observations."
            Journal of Applied Meteorology, 44(7), 969-985.
        - Air Force Weather Agency (AFWA) Technical Note 98/002: "Meteorological
            Diagnostics for Aviation Icing Forecasts."
        - National Center for Atmospheric Research (NCAR) RAL In-flight Icing
            Product Development Team / Prototype Documentation.
    """
    temp_in_k = inputs["temperature"]
    theta_e_adv = inputs["theta_e_adv"]
    rh = inputs["relative_humidity"]
    cloud_cover = inputs["cloud_cover"]
    cwmr = inputs["cloud_water_mixing_ratio"]
    pvv = inputs["pvv"]  # convert to negative microbars /second

    # Define a missing value mask across any alignment coordinates
    is_missing = (
            temp_in_k.isnull()
            | cloud_cover.isnull()
            | rh.isnull()
            | cwmr.isnull()
            | theta_e_adv.isnull()
            | pvv.isnull()
    )
    pvv *= -10.0  # convert Pa/s to -ub/s

    # Solid Deck Scaling: Determines if advection operates on a solid cloud deck
    #   Bounded linearly between 80% rh (factor=1.0) and 90% rh (factor=1.25)
    #   Values under 40% rh are locked to 1.0 rather than dropping to 0.
    rh_factor = ((rh - 40.0) / 40.0).clip(1.0, 1.25)
    #   Apply rh_factor directly to the equivalent thermal advection intensity
    advfx = xr.where(
        theta_e_adv >= -0.1,
        abs(0.67 * theta_e_adv * rh_factor),
        abs(1.25 * theta_e_adv * rh_factor),
        )

    # Dynamic Updraft Curve (Convective vertical velocity mapping)
    cloud_poly = -0.0063 * (pvv**2) + 0.2825 * pvv - 1.0286
    cloud_type = cloud_poly.clip(0.0, 2.0) * (advfx / 1.5).clip(0.0, 1.0)

    # Supercooled Large Drop (scld/SLD) Potential
    scld_inner1 = (cwmr / 0.15).clip(0.0, 1.0)
    scld_inner2 = (pvv / 18.0).clip(0.0, 1.0) * (
            (rh - 80.0) / 20.0
    ).clip(0.0, 1.0)
    scld_potential = xr.where(
        scld_inner1 > scld_inner2, scld_inner1, scld_inner2
    )

    # SCLD only activates in standard kinetic icing temperatures (0C to -15C)
    scld = xr.where(
        (temp_in_k < 273.15) & (temp_in_k >= 258.15), scld_potential, 0.0
    )

    # 5. Type-Intensity Condition Masks
    # TI Code 6: Moderate Mixed (Vigorous CU and High SLD Potential)
    cond_6 = (
            (cloud_cover >= 87)
            & (rh >= 90)
            & (temp_in_k <= 271.15)
            & (temp_in_k >= 258.15)
            & (advfx >= 1.5)
            & (cloud_type >= 1.0)
            & (scld >= 0.7)
    )

    # TI Code 5: Moderate Rime (Overcast layer and Intense Cold Advection)
    cond_5 = (
                     (cloud_cover >= 87)
                     & (rh >= 90)
                     & (temp_in_k <= 271.15)
                     & (temp_in_k >= 258.15)
                     & (advfx >= 1.5)
             ) | (
                     (cloud_cover >= 87)
                     & (rh >= 90)
                     & (temp_in_k < 258.15)
                     & (temp_in_k >= 251.15)
                     & (advfx >= 1.5)
                     & (cloud_type >= 1.0)
             )

    # TI Code 3: Light Mixed (Broken/Overcast cloud deck and Weak SLD Potential)
    cond_3 = (
            (cloud_cover >= 62)
            & (temp_in_k <= 271.15)
            & (temp_in_k >= 258.15)
            & (scld >= 0.3)
            & ((cloud_type >= 0.25) | (advfx >= 1.1))
    )

    # TI Code 2: Light Rime (Broken deck and Light macro-lift)
    cond_2 = (
                     (cloud_cover >= 62)
                     & (temp_in_k <= 271.15)
                     & (temp_in_k >= 258.15)
                     & ((advfx >= 0.1) | (pvv >= 5.0))
             ) | (
                     (cloud_cover >= 62)
                     & (temp_in_k < 258.15)
                     & (temp_in_k >= 251.15)
                     & (advfx >= 1.1)
                     & (cloud_type >= 0.25)
             ) | (
                     (cloud_cover >= 62)
                     & (temp_in_k < 251.15)
                     & (temp_in_k >= 241.15)
                     & (advfx >= 1.5)
             )

    # TI Code 1: Trace Rime
    cond_1 = (
                     (cloud_cover >= 62) & (temp_in_k <= 273.15) & (temp_in_k >= 258.15)
             ) | (
                     (cloud_cover >= 62)
                     & (temp_in_k < 258.15)
                     & (temp_in_k >= 251.15)
                     & (advfx >= 1.1)
             ) | (
                     (cloud_cover >= 62)
                     & (temp_in_k < 251.15)
                     & (temp_in_k >= 241.15)
                     & (advfx >= 1.5)
             )

    # Hierarchical assignment using top-down prioritization overrides
    ti_output = xr.where(cond_6, 6, 0)
    ti_output = xr.where(cond_5 & (ti_output == 0), 5, ti_output)
    ti_output = xr.where(cond_3 & (ti_output == 0), 3, ti_output)
    ti_output = xr.where(cond_2 & (ti_output == 0), 2, ti_output)
    ti_output = xr.where(cond_1 & (ti_output == 0), 1, ti_output)

    # Preserve missing data points as NaN flags
    ti_output = xr.where(is_missing, np.nan, ti_output)
    # =========================================================================
    # GIS & CF-CONVENTIONS METADATA INJECTION
    # =========================================================================
    # Ensure the list elements match your array's data type (typically int or int8)
    values = [0, 1, 2, 3, 4, 5, 6, 7]

    # FIX: Added clear, trailing spaces to every line so it splits properly [1, 2]
    meanings = (
        "none "
        "rime_trace "
        "rime_light "
        "mixed_light "
        "clear_light "
        "rime_moderate "
        "mixed_moderate "
        "clear_moderate"
    )

    ti_output.attrs.update({
        "long_name": "Aircraft Icing Type-Intensity Code",
        "standard_name": "aircraft_icing_type_intensity_indicator",
        "units": "1",  # "1" or "dimensionless" is CF-compliant for integer codes
        "valid_range": [0, 7],

        # CF-Conventions recognized by ArcGIS Pro, QGIS, and GDAL/GeoTIFF tools:
        "flag_values": values,
    "flag_meanings": meanings,

    # Embedded fallback string mapping for custom web map application parsers
    "code_legend": str({v: m for v, m in zip(values, meanings.split())})
    })

    return ti_output