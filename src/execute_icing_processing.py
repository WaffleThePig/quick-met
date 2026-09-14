from config import DATA_DIR, OUTPUT_DIR
import xarray as xr
from src.libs.netcdf_functions.data_extractor import DataExtractor
from src.libs.netcdf_functions.dataset_inventory import DatasetInventory
from src.libs.netcdf_functions.get_datetime_list import get_datetime_list


def main(package_name: str):
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # set the NetCDF path and extract the raw variables #
        netcdf_path = DATA_DIR / package_name
        print(f'-------------------------------------------\nUtilizing {package_name} for icing generation...')
        inventory = DatasetInventory(netcdf_path)
        extractor = DataExtractor(inventory)
        data_times = get_datetime_list(inventory)
        pressure_levels = inventory.pressure_mapping
        # Initialize a storage buffer for time slices
        time_slices = []

        # Loop through dimensions and capture results
        for valid_time in data_times:
            level_arrays = []
            # Sort levels descending (e.g., 700 down to 500) to keep the spatial structure uniform
            sorted_levels = sorted(pressure_levels, reverse=True)

            for pressure_level in sorted_levels:
                print(f"\tGenerating icing @ {pressure_level}mb for {valid_time}UTC")
                # Capture the resulting horizontal DataArray from the extractor
                layer_da = extractor.extract_metric(
                    target_metric="icing",
                    pressure_hpa=pressure_level,
                    target_time=valid_time
                )
                level_arrays.append(layer_da)
                print(f"\t\t✅ Successfully generated icing @ {pressure_level}mb")

            # Bundle all horizontal levels for this specific timestamp into a 3D block
            time_block_3d = xr.concat(level_arrays, dim="level")
            time_block_3d = time_block_3d.assign_coords(level=sorted_levels)

            time_slices.append(time_block_3d)

        # Stack all time blocks along the time dimension axis to build the final 4D Cube
        final_4d_cube = xr.concat(time_slices, dim="time")
        final_4d_cube = final_4d_cube.assign_coords(time=data_times)
        final_4d_cube.name = "icing"

        # 5. Pack into a Dataset and preserve original level coordinate attributes
        output_ds = final_4d_cube.to_dataset(name="icing")
        if "level" in output_ds.coords:
            output_ds["level"].attrs = inventory.level_attrs
        if "time" in output_ds.coords:
            output_ds["time"].attrs = inventory.time_attrs

        # 6. Save out to the final file destination
        output_path = OUTPUT_DIR / f'icing_from_{package_name}'
        output_ds.to_netcdf(output_path, format="NETCDF4")
        print(f"\n📁 Successfully exported complete 4D Icing Cube to: {output_path}")
    except IOError as ioe:
        print(ioe)
    except ValueError as ve:
        print(ve)
    except TypeError as te:
        print(te)
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    for package in ["era5_ua_package_spec_hum.nc", "era5_ua_package_rh.nc", "era5_ua_package_no_hum.nc"]:
        main(package)