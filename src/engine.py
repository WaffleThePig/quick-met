"""
Dynamic Execution Engine for Meteorological Data Processing.

This module provides the core logic for a pull-based data execution engine. 
It resolves requested variables by either retrieving them directly from 
NetCDF data files or by recursively calculating them using a tree of 
meteorological recipes. The engine handles unit conversion and caching 
to ensure efficiency and physical consistency across all calculations.
"""

import xarray as xr
from libs.meteo_functions import *  # noqa : Dynamically unpacks your formula strings into callable functions
from src.libs.netcdf_functions.dataset_inventory import DatasetInventory
from src.libs.netcdf_functions.pipeline_validator import PipelineValidator
from src.libs.netcdf_functions.unit_converter import UnitConverter


class BacktrackingExecutionEngine:
    """
    A pull-based data execution engine that resolves missing variable arrays
    dynamically by backtracking through a predefined functional recipe tree.
    Enforces automatic on-the-fly unit normalization using pint-xarray.
    """
    def __init__(self, inventory: DatasetInventory, variable_name_map: dict[str, str], **selectors):
        """
        Initializes the Backtracking Execution Engine.

        Args:
            inventory (DatasetInventory): An inventory object containing metadata 
                about the available variables in the NetCDF dataset.
            variable_name_map (dict[str, str]): A mapping of logical variable 
                tokens to their expected names in the source files.
            **selectors: Dimensional selectors (e.g., latitude, longitude, time) 
                used to slice the data during extraction.
        """
        self.inventory = inventory
        self.var_name_map = variable_name_map
        self.selectors = selectors
        self.validator = PipelineValidator(inventory)

        # Memory-backed cache tracking execution states to enforce single-run calculations
        self._runtime_cache: dict[str, xr.DataArray] = {}

    def get(self, variable_token: str, desired_unit: str | None = None) -> xr.DataArray:
        """
        Retrieves a DataArray for a specific variable, computing it if necessary.

        This method follows a three-step resolution process:
        1.  **Cache Check**: Returns the variable from the internal runtime 
            cache if it has already been resolved or computed.
        2.  **Raw Extraction**: If the variable is defined as a primitive in 
            the name map, it is pulled directly from the NetCDF file, 
            sliced according to the engine's selectors, and loaded into memory.
        3.  **Recipe Execution**: If the variable is not primitive, the engine 
            backtracks through the recipe tree. It recursively resolves all 
            dependencies, performs unit conversion to match the recipe's 
            requirements, and executes the appropriate meteorological function.

        Args:
            variable_token (str): The unique identifier for the variable to retrieve.
            desired_unit (str | None, optional): The target physical unit for the 
                returned DataArray. If provided, the engine performs automatic 
                unit conversion. Defaults to None.

        Returns:
            xr.DataArray: The resolved data array, normalized to the desired units.

        Raises:
            ValueError: If a required dependency for a recipe calculation cannot 
                be resolved.
            AttributeError: If a function specified in a recipe is not found in 
                the meteorological function library.
            KeyError: If no path (raw or recipe) can be determined for the 
                requested variable token.
        """
        # 1. Check in-memory memoization cache
        if variable_token in self._runtime_cache:
            da = self._runtime_cache[variable_token]
            return UnitConverter.convert(da, desired_unit) if desired_unit else da

        # 2. Extract primitive variable raw from disk
        if variable_token in self.var_name_map:
            # FIX: Look up the metadata inside inventory to get the true NetCDF variable name
            if variable_token in self.inventory.variables:
                actual_nc_name = self.inventory.variables[variable_token].name
            else:
                actual_nc_name = self.var_name_map[variable_token]

            with xr.open_dataset(self.inventory.filepath) as ds:
                raw_da = ds[actual_nc_name] # Dynamically opens 'cc' or 'Vertical velocity'
                active_selectors = {k: v for k, v in self.selectors.items() if k in raw_da.dims}

                if active_selectors:
                    sliced_da = raw_da.sel(active_selectors, method="nearest")
                else:
                    sliced_da = raw_da
                sliced_da.load()  # Pull values into RAM safely

            self._runtime_cache[variable_token] = sliced_da
            raw_units = sliced_da.attrs.get("units", "")
            sliced_da["units"] = raw_units.replace(" of equivalent water", "")
            return UnitConverter.convert(sliced_da, desired_unit) if desired_unit else sliced_da

        # 3. Dynamic Pathway Execution
        recipe = self.validator.resolve_valid_recipe_tree(variable_token)
        if recipe and recipe.get("type") != "raw_file":
            dependencies_dict = recipe["depends_on"]
            func_name = recipe["compute_func"]
            recipe_unit = recipe["target_unit"]
            print(f"\t\t⚙️ Selected Recipe Path: {recipe['description']}")

            # Resolve dependent arguments recursively, demanding exact target units
            injected_inputs = {}
            missing_inputs = []

            for dep_token, required_unit in dependencies_dict.items():
                try:
                    resolved_val = self.get(dep_token, desired_unit=required_unit)
                    if resolved_val is None:
                        missing_inputs.append(dep_token)
                    else:
                        injected_inputs[dep_token] = resolved_val
                except Exception:
                    # Catch cases where self.get explicitly raises an error for missing data
                    missing_inputs.append(dep_token)

            # If any inputs are missing, halt execution and report exactly what is missing
            if missing_inputs:
                raise ValueError(
                    f"Cannot execute '{func_name}' for variable '{variable_token}'. "
                    f"Missing required inputs: {missing_inputs}"
                )

            # Look up the string function pointer out of the unpacked thermodynamic module globals
            if func_name not in globals():
                raise AttributeError(f"Mathematical function '{func_name}' is not defined in meteo_functions library.")

            compute_callable = globals()[func_name]
            raw_computed_da = compute_callable(injected_inputs)

            final_converted_da = UnitConverter.convert(raw_computed_da, recipe_unit)
            final_converted_da.name = variable_token
            final_converted_da.attrs["units"] = recipe_unit

            self._runtime_cache[variable_token] = final_converted_da
            return UnitConverter.convert(final_converted_da, desired_unit) if desired_unit else final_converted_da

        raise KeyError(f"Unable to determine processing path for variable '{variable_token}'.")
