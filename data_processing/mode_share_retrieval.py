# This script loads and filters ACS Means of Transportation to Work data for the most recent year available (2023) at the US Census Block Group level.
#   - The data is available for download at: https://data.census.gov/table?q=b08301&g=010XX00US$1500000
#   - This data has to be joined to the 2020 Block Group shapefiles: https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html
#   - Requires having loaded in the parking lot boundaries

import os
from pyogrio.errors import DataSourceError
import pandas as pd
import geopandas as gpd

# The downloaded files are saved in the below file paths
MODE_SHARE_PATH = "data/source_data/mode_share/ACSDT5Y2023.B08301-Data.csv"
BLOCK_GROUP_PATH = "data/source_data/cb_2024_us_bg_500k/cb_2024_us_bg_500k.shp"
PARKING_BOUNDARY_PATH = "data/lots/city_boundaries.geojson"

def load_mode_share():
    """
    Load the mode share data, add desired columns, and merge it to 2020 Block Group geographies.
    Filter the resulting data to the block groups overlapping the parking lot boundaries.
    
    Returns:
        car_share_filtered (Data.Frame): the GeoPandas Data Frame of car share and total trips for each Census Block Group.
    """

    # Load transportation to work data
    mode_share = pd.read_csv(MODE_SHARE_PATH, header=1)

    # Create car trip share column
    mode_share.rename(columns = {"Estimate!!Total:": "total_trips", "Geography": "geo_id"} , inplace=True)
    mode_share["car_trip_share"] = mode_share["Estimate!!Total:!!Car, truck, or van:"] / mode_share["total_trips"]

    # Load Block Group data
    bgs = gpd.read_file(BLOCK_GROUP_PATH)

    # Merge data sets
    car_share = bgs.merge(mode_share, left_on='GEOIDFQ', right_on="geo_id", how='left')

    # Filter the block groups to only those which overlap the parking lot boundaries
    try:
        boundaries = gpd.read_file(PARKING_BOUNDARY_PATH)

        # Project to same CRS
        car_share = car_share.to_crs(epsg=5070)
        boundaries = boundaries.to_crs(epsg=5070)

        car_share_filtered = gpd.sjoin(car_share, boundaries, how='inner', predicate='intersects')

        # Select the needed columns
        car_share_filtered = car_share_filtered[["geo_id", "total_trips", "car_trip_share", "geometry"]]

        return car_share_filtered

    except DataSourceError:
        print("No parking boundaries data. Load this data first.")

def main():
    """
    Retrieve the car trip share data for each block group overlapping with the Central City boundaries.
    Save this file as a GeoJSON in data/filtered_block_groups/
    """
    os.chdir('..')

    car_share = load_mode_share()

    if car_share is not None and not car_share.empty:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'filtered_block_groups')
        clean_path = os.path.normpath(output_path)
        car_share_file = os.path.join(clean_path, "car_share.geojson")

        # Create output folder if does not exist
        if not os.path.exists(clean_path):
            os.makedirs(clean_path)

        # Write the output to data folder   
        car_share.to_file(car_share_file, driver="GeoJSON")

if __name__ == "__main__":
    main()