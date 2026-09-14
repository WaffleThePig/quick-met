import xarray as xr
from src.libs.netcdf_functions.dataset_inventory import DatasetInventory
from src.libs.netcdf_functions.pipeline_validator import PipelineValidator

class BacktrackingExecutionEngine:
    """
    A pull-based data execution engine that resolves missing variable arrays
    dynamically by backtracking through a predefined functional recipe tree.
    Enforces automatic on-the-fly unit normalization using pint-xarray.
    """

    inventory: DatasetInventory
    var_name_map: dict[str, str]
    selectors: dict
    validator: PipelineValidator
    _runtime_cache: dict[str, xr.DataArray]

    def __init__(self, inventory: DatasetInventory, variable_name_map: dict[str, str], **selectors) -> None:
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
        ...

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
        ...
