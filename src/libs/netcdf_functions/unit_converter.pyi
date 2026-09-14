"""
Meteorological Unit Conversion Engine.

This module provides the `UnitConverter` class, which handles automated unit 
transformations for Xarray DataArrays.
"""

import xarray as xr

class UnitConverter:
    """Automated unit transformation handler for Xarray DataArrays.

    Uses a Pint Registry to perform physical unit conversions while 
    preserving Xarray metadata and dimensions. Includes specialized 
    handling for common NetCDF unit strings and temperature scale shifts.
    """
    
    @staticmethod
    def convert(da: xr.DataArray, target_unit: str) -> xr.DataArray:
        """Converts a DataArray to a target physical unit.

        Compares the DataArray's 'units' attribute to the target unit and 
        applies the necessary transformation. Safely handles common NetCDF 
        shorthands (e.g., 'kg kg**-1' to 'kg/kg') and temperature scale 
        shifts (e.g., Kelvin to Celsius).

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
        ...
