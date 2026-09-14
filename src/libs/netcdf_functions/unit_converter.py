"""
Meteorological Unit Conversion Engine.

This module provides the `UnitConverter` class, which handles automated unit 
transformations for Xarray DataArrays using the Pint unit registry. It 
ensures that variables are in the correct units before being passed to 
meteorological calculation functions.
"""

import xarray as xr
from pint import UnitRegistry

# Instantiate a single global unit registry matching your other project's setup
_unit_reg = UnitRegistry()

class UnitConverter:
    """Automated unit transformation handler for Xarray DataArrays.

    Uses a Pint Registry to perform physical unit conversions while
    preserving Xarray metadata and dimensions. Includes specialized
    handling for common NetCDF unit strings and space-stripping conventions.
    """

    @staticmethod
    def convert(da: xr.DataArray, target_unit: str) -> xr.DataArray:
        """Converts a DataArray to a target physical unit.

        Compares the DataArray's 'units' attribute to the target unit and
        applies the necessary transformation. Safely handles common NetCDF
        shorthands and temperature scale shifts (e.g., Kelvin to Celsius).

        Args:
            da: The input Xarray DataArray with a 'units' attribute.
            target_unit: The desired unit string (e.g., 'degC', 'hPa').

        Returns:
            xr.DataArray: A copy of the input array with data converted to
                the target unit and updated 'units' attribute.

        Raises:
            ValueError: If the conversion fails due to incompatible units
                or parsing errors.
        """
        raw_unit = da.attrs.get("units", "dimensionless").strip()

        # 1. DEFENSIVE SANITIZATION: Map complex raw NetCDF syntax strings
        # to clear, standard explicit formats before stripping spaces
        sanitized_mapping = {
            "K": "kelvin",
            "C": "degC",
            "Pa": "pascal",
            "%": "percent",
            "(0 - 1)": "dimensionless",
            "kg kg**-1": "kg / kg",
            "kg/kg": "kg / kg",
            "m s**-1": "m / s",
            "Pa s**-1": "pascal / s",
            "m of water equivalent": "m"
        }

        # Match exactly against the raw metadata string
        current_unit = sanitized_mapping.get(raw_unit, raw_unit)

        # 2. Normalize Celsius name strings to avoid Pint parsing typos
        if target_unit in ["degC", "degree_Celsius", "degree_C"]:
            target_unit = "degC"

        # 3. Apply your space-stripping optimization rules
        current_unit = current_unit.replace(" ", "")
        target_unit = target_unit.replace(" ", "")

        # 4. Optimization: Exit early if the normalized target strings match
        if current_unit == target_unit:
            return da

        try:
            # 5. Build the Pint Quantity using the raw array values
            quantity = _unit_reg.Quantity(da.values, current_unit)
            converted_quantity = quantity.to(target_unit)

            # 6. Reconstruct a clean Xarray DataArray keeping all your original dimensions
            converted_da = da.copy(data=converted_quantity.magnitude)
            converted_da.attrs["units"] = target_unit

            return converted_da

        except Exception as e:
            raise ValueError(
                f"UnitConverter failed on '{da.name}': "
                f"Cannot transform from '{raw_unit}' (interpreted as '{current_unit}') to target '{target_unit}'. "
                f"Error details: {e}"
            )
