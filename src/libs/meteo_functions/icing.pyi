"""
Aircraft Icing Type-Intensity Diagnostic (Vectorized Xarray Implementation)

This module implements a diagnostic algorithm to identify potential aircraft 
icing hazards based on heuristic multi-threshold logic derived from legacy 
AFWA/NCAR RAL algorithms. Co-developed with Cory Wolff (NCAR), this method
uses 4D fluid mechanics and thermodynamics to evaluate the potential impact
of aircraft icing on the aircraft's environment.

Scientific Foundations & Logic Breakdown:
    1. Solid Cloud Deck Scaling (rh_factor):
       Evaluates whether equivalent potential temperature (ThetaE) advection is
       acting on a broken vs. overcast/solid deck. The scaling targets the
       80% to 90% RH boundary range.

    2. Updraft Convective Curve (cloud_type):
       A 2nd-order polynomial mapping of Positive Vertical Velocity (PVV)
       designed to index updraft vigorously. It peaks around ~22.4 -ub/s, which
       empirically models continuous generation of Supercooled Liquid Water
       (SLW) via strong upward mechanical lift, compensating for precipitation
       depletion.

    3. Supercooled Large Droplet (SCLD) Potential:
       Evaluated strictly in the classical Stallabrass/NCAR structural icing
       window (258.15K to 273.15K, or -15°C to 0°C). It calculates
       kinetic severity by taking the envelope maximum of microphysical mass
       density (Cloud Water Mixing Ratio) and dynamic convective scaling.

Output Interpretation (Type-Intensity Codes):
* 0 = None
* 1 = Rime Ice - Trace
* 2 = Rime Ice - Light
* 3 = Mixed Ice - Light
* 5 = Rime Ice - Moderate
* 6 = Mixed Ice - Moderate

References:
    [1] Bernstein, B. C., et al. (2005). "The Current Icing Potential (CIP)
        Algorithm: Description and Comparison with Aircraft Observations."
        Journal of Applied Meteorology, 44(7), 969-985.
    [2] Air Force Weather Agency (AFWA) Technical Note 98/002: "Meteorological
        Diagnostics for Aviation Icing Forecasts."
    [3] National Center for Atmospheric Research (NCAR) RAL In-flight Icing
        Product Development Team / Prototype Documentation.
"""

import xarray as xr

def calc_icing_type_intensity(inputs: dict[str, xr.DataArray]) -> xr.DataArray:
    """Calculates the aircraft icing type and intensity indicator.

    The algorithm uses a combination of thermodynamic and microphysical 
    thresholds to diagnose icing risk:
    1. Temperature check: Must be in the supercooled range (T < 0°C).
    2. Cloud liquid water content: Thresholds for trace, light, and moderate icing.
    3. Convective scaling: PVV is used to amplify icing intensity in updrafts.
    4. Theta-E advection: Used to scale the cloud deck factor.

    Args:
        inputs: A dictionary containing the input data arrays.
            - "temperature": Air temperature in Kelvin (K).
            - "theta_e_adv": Equivalent potential temperature advection (K/s).
            - "relative_humidity": Relative humidity (0 to 100).
            - "cloud_cover": Fractional horizontal coverage (0 to 100).
            - "cloud_water_mixing_ratio": Cloud Water Mixing Ratio (g/kg).
            - "pvv": Positive Vertical Velocity (Pa/s).

    Returns:
        xr.DataArray: Integer codes representing icing type and intensity.
            - 0: None
            - 1: Rime Ice - Trace
            - 2: Rime Ice - Light
            - 3: Mixed Ice - Light
            - 5: Rime Ice - Moderate
            - 6: Mixed Ice - Moderate

    References:
        - Bernstein, B. C., et al. (2005). "The Current Icing Potential (CIP) 
          Algorithm." Journal of Applied Meteorology.
    """
    ...