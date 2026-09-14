"""
NetCDF Dataset Metadata Inventory and Discovery.

This module provides tools for extracting, indexing, and caching metadata 
from NetCDF files using Xarray. It simplifies access to variable 
properties, temporal coordinates, and vertical pressure levels, facilitating 
automated pipeline validation and data extraction.
"""

from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

@dataclass(frozen=True)
class VariableMetadata:
    """Structured container for NetCDF variable metadata.

    Attributes:
        name: The primary name of the variable.
        dimensions: Tuple of dimension names associated with the variable.
        shape: Tuple of dimension sizes.
        data_type: String representation of the data type (e.g., 'float32').
        attributes: Dictionary of variable-specific NetCDF attributes.
    """
    name: str
    dimensions: tuple[str, ...]
    shape: tuple[int, ...]
    data_type: str
    attributes: dict[str, Any] = field(default_factory=dict)

class DatasetInventory:
    """Structured inventory of a NetCDF dataset's metadata.

    Crawls an xarray Dataset in a single pass to build a structured 
    metadata inventory. Caches time and pressure coordinates to eliminate 
    repetitive file I/O operations and provides synonym mapping for common 
    meteorological variables.

    Attributes:
        filepath: Path to the underlying NetCDF file.
        dimensions: Dictionary mapping dimension names to their sizes.
        variables: Dictionary mapping variable names to their metadata.
        timestamps: List of datetime objects representing the temporal axis.
        pressure_mapping: List of pressure levels found in the dataset.
        time_attrs: Attributes associated with the time coordinate.
        level_attrs: Attributes associated with the level/pressure coordinate.
    """
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)

        with xr.open_dataset(self.filepath) as ds:
            self.dimensions: dict[str, int] = {str(k): v for k, v in ds.sizes.items()}
            self.variables: dict[str, VariableMetadata] = self._build_variable_inventory(ds)
            self.timestamps: list[datetime] = self._extract_timestamps(ds)
            self.pressure_mapping: list[int | float] = self._extract_pressure_levels(ds)

            # --- NEW: Cache axis-specific metadata attributes directly ---
            self.time_attrs: dict[str, Any] = dict(ds.coords["time"].attrs) if "time" in ds.coords else {}
            self.level_attrs: dict[str, Any] = dict(ds.coords["level"].attrs) if "level" in ds.coords else {}


    @staticmethod
    def _build_variable_inventory(ds: xr.Dataset) -> dict[str, VariableMetadata]:
        """Iterates through data variables to isolate their properties and handles synonyms.

        Args:
            ds: The input Xarray Dataset.

        Returns:
            dict[str, VariableMetadata]: A mapping of variable tokens to their metadata.
        """
        inventory = {}

        for var_name, da in ds.data_vars.items():
            inventory[str(var_name)] = VariableMetadata(
                name=str(var_name),
                dimensions=tuple(str(d) for d in da.dims),
                shape=da.shape,
                data_type=str(da.dtype),
                attributes=dict(da.attrs)
            )

        # Dictionary mapping target keys to their exact name aliases or long_name substring rules
        synonym_rules = {
            "temperature": {
                "names": ["t2m", "t", "temp"],
                "substrings": ["2 metre temperature", "2m temperature", "temperature"]
            },
            "dewpoint": {
                "names": ["d2m", "td", "dew"],
                "substrings": ["2 metre dewpoint", "2m dewpoint", "dew point temperature"]
            },
            "pvv": {
                "names": ["Vertical velocity", "omega", "vvel", "w"],
                "substrings": ["vertical velocity"]
            },
            "cloud_cover": {
                "names": ["cc", "tcc"],
                "substrings": ["cloud cover", "total cloud cover"]
            }
        }

        # Dynamically find and map missing keys based on name aliases or long_name contents
        for target_key, rules in synonym_rules.items():
            if target_key in inventory:
                continue

            found_var_name = None

            # Step 1: Try finding by direct variable name matches first
            for name in rules["names"]:
                if name in inventory:
                    found_var_name = name
                    break

            # Step 2: Fall back to searching inside the 'long_name' attribute lowercase text
            if not found_var_name:
                for var_name, meta in inventory.items():
                    long_name = meta.attributes.get("long_name", "").lower()
                    if any(sub in long_name for sub in rules["substrings"]):
                        found_var_name = var_name
                        break

            # If a match was found via either method, alias it in the inventory
            if found_var_name:
                inventory[target_key] = inventory[found_var_name]

        return inventory


    @staticmethod
    def _extract_timestamps(ds: xr.Dataset) -> list[datetime]:
        """Finds the temporal coordinate and converts it to native Python datetimes.

        Args:
            ds: The input Xarray Dataset.

        Returns:
            list[datetime]: A list of extracted timestamps.
        """
        time_keys = ["time", "valid_time", "t", "times"]
        time_coord_name = next((k for k in time_keys if k in ds.coords), None)
        if not time_coord_name:
            return []
        time_data = ds[time_coord_name].values
        if isinstance(time_data, (np.datetime64, datetime)):
            time_array = np.array([time_data])
        else:
            time_array = time_data
        return [dt for dt in time_array.astype("datetime64[s]").tolist()]

    @staticmethod
    def _extract_pressure_levels(ds: xr.Dataset) -> list[int | float]:
        """Maps array indices to their corresponding pressure level coordinate values.

        Args:
            ds: The input Xarray Dataset.

        Returns:
            list[int | float]: A list of pressure level values.
        """
        # Detect common pressure/vertical coordinate identifiers based on your schema
        pressure_keys = ["isobaricInhPa", "pressure_level", "plev", "level"]
        p_coord_name = next((k for k in pressure_keys if k in ds.coords), None)

        if not p_coord_name:
            return []

        return ds[p_coord_name].values.tolist()
