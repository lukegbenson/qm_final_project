# This script loads and filters ACS Means of Transportation to Work data for the most recent year available (2023) at the US Census Block Group level.
#   - Requires having created the lot_features, city_boundaries, and car_share GeoJSONs

import os
from pyogrio.errors import DataSourceError
import pandas as pd
import geopandas as gpd

# The downloaded files are saved in the below file paths
LOTS_PATH = "data/lots/lot_features.geojson"
BOUNDARIES_PATH = "data/lots/city_boundaries.geojson"
CAR_SHARE_PATH = "data/filtered_block_groups/car_share.geojson"

def create_model_data():
    """
    
    Returns:
        model_data (DataFrame): the GeoPandas Data Frame used for modeling.
    """

    # Load the lot features
    lots = gpd.read_file(LOTS_PATH)

    # Load the parking lot boundaries
    boundaries = gpd.read_file(BOUNDARIES_PATH)
    boundaries.to_crs(epsg=5070, inplace=True)

    # Add a column for boundary area
    boundaries["boundary_area"] = boundaries.geometry.area

    # Load the car trip share data
    car_share = gpd.read_file(CAR_SHARE_PATH)

    # Overlay the car trip share data with the lot boundaries
    car_share_cities = gpd.overlay(car_share, boundaries, how='intersection')

    # We want an estimate for the car trip share within each boundary
    # First, find the intersection area between each block group and city boundary
    car_share_cities["intersection_area"] = car_share_cities.geometry.area

    # Second, find the percent overlap between the block group and the city boundary
    # Block groups contain land and water, but the city boundaries only outline the land
    car_share_cities["overlap_pct"] = car_share_cities["intersection_area"] / car_share_cities["boundary_area"]
    car_share_cities["land_ratio"] = (car_share_cities["land_area"] + car_share_cities["water_area"]) / car_share_cities["land_area"]

    # Within each block group, we want the total trips weighted by the % overlap between the block group and the city boundary, accounting for the land ratio of block group
    car_share_cities["weighted_total_trips"] = car_share_cities["total_trips"] * car_share_cities["overlap_pct"] * car_share_cities["land_ratio"]
    car_share_cities["weighted_car_trips"] = car_share_cities["car_trips"] * car_share_cities["overlap_pct"] * car_share_cities["land_ratio"]

    # The result is a weighted mean of trips for each city
    city_car_share = car_share_cities.groupby("id").agg({
        "weighted_total_trips": "sum",
        "weighted_car_trips": "sum",
    }).reset_index()

    city_car_share["car_trip_share"] = city_car_share["weighted_car_trips"] / city_car_share["weighted_total_trips"]

    model_data = lots.merge(
        city_car_share[["id", "car_trip_share"]], left_on="city", right_on="id", how="left"
    ).drop(["id"], axis=1)

    return model_data

def main():
    """
    Create the data for linear modeling.
    Save this file as a GeoJSON in data/modeling/
    """
    os.chdir('..')

    model_data = create_model_data()

    if model_data is not None and not model_data.empty:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'modeling')
        clean_path = os.path.normpath(output_path)
        car_share_file = os.path.join(clean_path, "model_data.geojson")

        # Create output folder if does not exist
        if not os.path.exists(clean_path):
            os.makedirs(clean_path)

        # Write the output to data folder   
        model_data.to_file(car_share_file, driver="GeoJSON")

if __name__ == "__main__":
    main()