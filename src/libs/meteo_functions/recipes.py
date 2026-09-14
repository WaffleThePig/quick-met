"""
Meteorological Calculation Pipeline Recipes.

This module defines the computational pathways (recipes) used by the 
execution engine to derive meteorological metrics. Each recipe specifies its 
dependencies, target units, and the corresponding implementation function.

The `PIPELINE_RECIPES` dictionary serves as a configuration for a 
backtracking dependency resolver, allowing the system to automatically 
determine how to calculate a requested variable (e.g., 'icing') based on 
available data in a NetCDF file.
"""

PIPELINE_RECIPES = {
    "saturation_vapor_pressure": [
        {
            "description": "Calculate Saturation Vapor Pressure",
            "depends_on": {
                "temperature": "degC"
            },
            "target_unit": "hPa",
            "compute_func": "calc_saturation_vapor_pressure"
        }
    ],
    "saturation_mixing_ratio": [
        {
            "description": "Calculate Saturation Mixing Ratio from SVP",
            "depends_on": {
                "pressure_level": "hPa",
                "saturation_vapor_pressure": "hPa"
            },
            "target_unit": "kg/kg",
            "compute_func": "calc_sat_mixing_ratio_water"
        }
    ],
    "mixing_ratio": [
        {
            "description": "Calculate Mixing Ratio from Specific Humidity",
            "depends_on": {
                "specific_humidity": "kg/kg"
            },
            "target_unit": "kg/kg",
            "compute_func": "calc_mixing_ratio_from_q"
        },
        {
            "description": "Calculate Mixing Ratio from Relative Humidity",
            "depends_on": {
                "pressure_level": "hPa",
                "saturation_vapor_pressure": "hPa",
                "relative_humidity": "dimensionless"
            },
            "target_unit": "kg/kg",
            "compute_func": "calc_mixing_ratio_from_rh"
        }
    ],
    "relative_humidity": [
        {
            "description": "Calculate Relative Humidity from Specific Humidity",
            "depends_on": {
                "specific_humidity": "kg/kg",
                "saturation_mixing_ratio": "kg/kg"
            },
            "target_unit": "%",
            "compute_func": "calculate_rh_from_specific_humidity"
        },
        {
            "description": "Calculate Relative Humidity from dewpoint and temperature",
            "depends_on": {
                "temperature": "degC",
                "dewpoint": "degC"
            },
            "target_unit": "%",
            "compute_func": "calc_rh_from_temp_dewpoint"
        }
    ],
    "dewpoint": [
        {
            "description": "Calculate Dewpoint from Specific Humidity",
            "depends_on": {
                "pressure_level": "kPa",
                "specific_humidity": "kg/kg"
            },
            "target_unit": "degK",
            "compute_func": "calc_dew_point_from_q"
        },
        {
            "description": "Calculate Dewpoint from Relative Humidity",
            "depends_on": {
                "temperature": "degC",
                "relative_humidity": "dimensionless"
            },
            "target_unit": "degK",
            "compute_func": "calc_dew_point_from_rh"
        }
    ],
    "theta_e": [
        {
            "description": "Calculate Equivalent Potential Temperature (Basic)",
            "depends_on": {
                "pressure_level": "hPa",
                "mixing_ratio": "kg/kg",
                "temperature": "degK",
                "dewpoint": "degK"
            },
            "target_unit": "degK",
            "compute_func": "calc_theta_e_basic"
        }
    ],
    "theta_e_adv": [
        {
            "description": "Calculate Equivalent Potential Temperature Advection",
            "depends_on": {
                "theta_e": "degK",
                "eastward_wind": "m/s",
                "northward_wind": "m/s"
            },
            "target_unit": "K/m/s",
            "compute_func": "calc_theta_e_advection"
        }
    ],
    "cloud_water_mixing_ratio": [
        {
            "description": "Calculate Cloud Water Mixing Ratio from MXR",
            "depends_on": {
                "clwc": "kg/kg",
                "mixing_ratio": "kg/kg"
            },
            "target_unit": "g/kg",
            "compute_func": "calc_cloud_water_mixing_ratio_from_mxr"
        },
        {
            "description": "Calculate Cloud Water Mixing Ratio from Q",
            "depends_on": {
                "clwc": "kg/kg",
                "specific_humidity": "kg/kg"
            },
            "target_unit": "g/kg",
            "compute_func": "calc_cloud_water_mixing_ratio_from_q"
        }
    ],
    "icing": [
        {
            "description": "Calculate Icing Type-Intensity Code",
            "depends_on": {
                "temperature": "degK",
                "theta_e_adv": "K/m/h",
                "relative_humidity": "%",
                "cloud_water_mixing_ratio": "g/kg",
                "cloud_cover": "%",
                "pvv": "Pa/s"
            },
            "target_unit": "dimensionless",
            "compute_func": "calc_icing_type_intensity"
        }
    ],
    "visibility": [
        {
            "description": "Calculate Visibility Robust",
            "depends_on": {
                "relative_humidity": "dimensionless",
                "temperature": "degC",
                "skt": "degC",
                "u10": "m/s",
                "v10": "m/s",
                "tp": "mm",
                "sf": "mm"  # pint has issues recognizing "m of equivalent water" as a unit
            },
            "target_unit": "km",
            "compute_func": "calc_visibility_complex"
        },
        {
            "description": "Calculate Visibility from Relative Humidity",
            "depends_on": {
                "relative_humidity": "dimensionless"
            },
            "target_unit": "km",
            "compute_func": "calc_visibility_from_rh"
        }
    ],
}