"""
NetCDF Data Extraction Facade.

This module provides a high-level interface for extracting meteorological 
metrics from NetCDF datasets. It orchestrates the process of pipeline 
validation, backtracking dependency resolution, and target metric slicing.
"""

import xarray as xr
from src.libs.netcdf_functions.dataset_inventory import DatasetInventory
from src.libs.netcdf_functions.pipeline_validator import PipelineValidator
from src.engine import BacktrackingExecutionEngine


class DataExtractor:
    """Facade for extracting processed metrics from NetCDF files.

    This class handles the complexity of coordinate selection, unit 
    conversions, and dependency resolution by utilizing the underlying 
    validation and execution engines.
    """
    def __init__(self, inventory: DatasetInventory):
        self.inventory = inventory
        self.validator = PipelineValidator(self.inventory)

    def extract_metric(
            self,
            target_metric: str,
            pressure_hpa: int | float | None = None,
            target_time: any = None
    ) -> xr.DataArray:
        """Extracts and processes a specific meteorological metric.

        Validates the file availability, maps out the required processing 
        pathway, handles unit corrections, and returns the requested 
        DataArray sliced by pressure and time if provided.

        Args:
            target_metric: The name of the metric to extract (e.g., 'icing').
            pressure_hpa: The target pressure level in hPa.
            target_time: The target timestamp.

        Returns:
            xr.DataArray: The processed and sliced data array.
        """
        var_name_map = self.validator.validate_pipeline_readiness([target_metric])

        selectors = {}

        if pressure_hpa is not None:
            pressure_keys = ["isobaricInhPa", "pressure_level", "plev", "level"]
            p_coord = next((k for k in pressure_keys if k in self.inventory.dimensions), None)
            if p_coord:
                selectors[p_coord] = pressure_hpa

        if target_time is not None:
            time_keys = ["time", "valid_time", "t", "times"]
            t_coord = next((k for k in time_keys if k in self.inventory.dimensions), None)
            if t_coord:
                selectors[t_coord] = target_time

        engine = BacktrackingExecutionEngine(
            inventory=self.inventory,
            variable_name_map=var_name_map,
            **selectors
        )

        return engine.get(target_metric)
