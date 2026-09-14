from config import DATA_DIR, OUTPUT_DIR
import xarray as xr
from src.libs.netcdf_functions.data_extractor import DataExtractor
from src.libs.netcdf_functions.dataset_inventory import DatasetInventory
from src.libs.netcdf_functions.get_datetime_list import get_datetime_list


def main(package_name: str):
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # set the NetCDF path and extract the raw variables
        netcdf_path = DATA_DIR / package_name
        print(f'-------------------------------------------\nUtilizing {package_name} for surface visibility generation...')

        inventory = DatasetInventory(netcdf_path)
        extractor = DataExtractor(inventory)
        data_times = get_datetime_list(inventory)

        # Initialize a storage buffer for time slices
        time_slices = []

        # Loop through dimensions and capture results
        for valid_time in data_times:
            print(f"\tGenerating surface visibility for {valid_time}UTC")

            # Capture the resulting horizontal DataArray from the extractor for the surface level
            surface_da = extractor.extract_metric(
                target_metric="visibility",
                target_time=valid_time
            )

            time_slices.append(surface_da)
            print(f"\t\t✅ Successfully generated surface visibility")

        # Stack all time blocks along the time dimension axis to build the final 3D Cube
        final_3d_cube = xr.concat(time_slices, dim="time")
        final_3d_cube = final_3d_cube.assign_coords(time=data_times)
        final_3d_cube.name = "visibility"

        # 5. Pack into a Dataset and preserve original coordinate attributes
        output_ds = final_3d_cube.to_dataset(name="visibility")

        if "time" in output_ds.coords:
            output_ds["time"].attrs = inventory.time_attrs

        # Optional: Clean up level attributes if they are no longer applicable
        if "level" in output_ds.coords:
            output_ds = output_ds.drop_vars("level")

        # 6. Save out to the final file destination
        output_path = OUTPUT_DIR / f'surface_visibility_from_{package_name}'
        output_ds.to_netcdf(output_path, format="NETCDF4")
        print(f"\n📁 Successfully exported complete 2D Surface Visibility to: {output_path}")

    except IOError as ioe:
        print(ioe)
    except ValueError as ve:
        print(ve)
    except TypeError as te:
        print(te)
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    for package in ["era5_land_package_simple.nc", "era5_land_package_robust.nc"]:
        main(package)