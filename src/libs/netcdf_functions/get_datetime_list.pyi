"""
NetCDF Temporal Coordinate Extraction.

This module provides a utility function to retrieve the list of timestamps 
cached within a `DatasetInventory`.
"""

from datetime import datetime
from .dataset_inventory import DatasetInventory

def get_datetime_list(inventory: DatasetInventory) -> list[datetime]:
    """Returns the cached list of datetime objects from the inventory.

    Args:
        inventory: The DatasetInventory object to query.

    Returns:
        list[datetime]: A list of timestamps found in the dataset.

    Raises:
        ValueError: If no temporal coordinate is present in the dataset.
    """
    ...
