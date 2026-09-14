# Meteorological Calculation Pipeline

A pull-based data execution engine for meteorological data processing. This project dynamically resolves requested variables (like icing and visibility) from NetCDF files using a recursive backtracking engine and predefined physical recipes.

## Prerequisites

- **Python 3.13** (Required)
- NetCDF data files (ERA5 UA/Land packages)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd CodingTest
   ```

2. **Set up a virtual environment:**
   ```powershell
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   This project requires `xarray`, `pint`, `pint-xarray`, `netCDF4`, and `numpy`.
   ```bash
   pip install xarray pint pint-xarray netCDF4 numpy
   ```

## Project Structure

- `src/`: Core implementation.
  - `engine.py`: The `BacktrackingExecutionEngine` that resolves data dependencies.
  - `libs/meteo_functions/`: Physical formulas and recipes (e.g., `icing.py`, `visibility.py`, `recipes.py`).
  - `libs/netcdf_functions/`: Utilities for NetCDF extraction, unit conversion, and validation.
- `data/`: Input NetCDF files (e.g., ERA5 UA and Land packages).
- `output/`: Generated processing results.
- `styling/`: QML files for visualization (e.g., icing intensity).

## Usage

The project provides entry points for different meteorological metrics:

### Icing Processing
Calculates icing type and intensity across multiple pressure levels and time steps.
```bash
python src/execute_icing_processing.py
```

### Visibility Processing
Calculates surface visibility based on meteorological parameters.
```bash
python src/execute_visibility_processing.py
```

## How It Works

1. **Inventory**: The `DatasetInventory` scans input NetCDF files to identify available primitive variables.
2. **Recipe Resolution**: When a metric (e.g., `icing`) is requested, the `PipelineValidator` finds a valid "recipe" path based on available data.
3. **Execution**: The `BacktrackingExecutionEngine` recursively pulls or calculates dependencies, ensuring units are normalized using `pint-xarray` before applying formulas.
4. **Output**: Results are exported as 4D (time, level, lat, lon) or 3D (time, lat, lon) NetCDF cubes.

## 🗺️ Visualization & GIS Integration

Because the generated icing risk output is a discrete categorical indicator, viewing it with default linear color ramps will obscure the data structure.

A dedicated **QGIS Layer Style file** has been provided to map the categorical flags cleanly.

### To view the data with proper symbology:
1. Load the generated `.nc` output file into **QGIS**.
2. Right-click the layer and go to **Properties** -> **Symbology**.
3. In the lower-left corner, click **Style** -> **Load Style...**
4. Select `styling/icing_type_intensity.qml` from this repository.

This will automatically configure a discrete qualitative color palette mapped directly to the official CF-Convention meanings (e.g., *Rime Trace*, *Clear Moderate*).
