# This script creates model features based solely on parking lot locations and Central City boundaries
#   - Requires having loaded in the parking lot boundaries

import os
from pyogrio.errors import DataSourceError
import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.stats import entropy

# The downloaded files are saved in the below file path
PARKING_LOT_PATH = "data/lots/city_lots.geojson"
PARKING_BOUNDARY_PATH = "data/lots/city_boundaries.geojson"

def load_lot_data():
    """
    Load the lot polygons and central city boundaries. Add basic geographic features.
    
    Returns:
        lot_data (DataFrame): GeoPandas Data Frame merged from lots and boundaries.
    """

    try:
        lots = gpd.read_file(PARKING_LOT_PATH)
        boundaries = gpd.read_file(PARKING_BOUNDARY_PATH)

        # Project to same CRS
        lots = lots.to_crs(epsg=5070)
        boundaries = boundaries.to_crs(epsg=5070)

        # Add area in m^2
        lots["total_lot_area"] = lots.geometry.area
        boundaries["boundary_area"] = boundaries.geometry.area

        # Add number of lots
        lots["num_lots"] = lots.geometry.apply(lambda x: len(x.geoms) if x.geom_type == "MultiPolygon" else 1)

        # Creta new dataframe which contains lot features for each city
        lot_data = lots.merge(pd.DataFrame(boundaries.drop(columns='geometry')), on='id', how='left')
        lot_data.rename(columns={'id': 'city'}, inplace=True)

        return lot_data

    except DataSourceError:
        print("No parking boundaries data. Load this data first.")

def add_geo_features(lot_data: gpd.GeoDataFrame):
    """
    Load the lot polygons and central city boundaries. Add basic geographic features.
    
    Args:
        lot_data (DataFrame): GeoPandas Data Frame merged from lots and boundaries.
    
    Returns:
        lot_data (DataFrame): GeoPandas Data Frame with a few basic geographic features.
    """

    # Add feature: % of central city taken up by parking
    lot_data["pct_lot_area"] = lot_data["total_lot_area"] / lot_data["boundary_area"]

    # Add feature: number of parking lots per km^2
    lot_data["lots_per_sq_km"] = 1000 * lot_data["num_lots"] / lot_data["boundary_area"]

    # Add feature: average lot area
    lot_data["avg_lot_area"] = lot_data.geometry.apply(lambda geom: np.mean([poly.area for poly in geom.geoms]) if hasattr(geom, 'geoms') else geom.area) / 1000

    return lot_data

def gini_coefficient(x: list):
    """
    Calculate the Gini coefficient of an array.

    Args:
        x (list): array of values.
    
    Returns:
        gini_coef (float): The Gini coefficient value for the array.
    """
    x = np.array(x, dtype=np.float64)
    if x.size <= 1 or np.sum(x) == 0:
        return 0.0 
    
    x = np.sort(x)
    n = len(x)
    index = np.arange(1, n + 1)
    
    # Formula for Gini coefficient
    gini_coef = (np.sum((2 * index - n - 1) * x)) / (n * np.sum(x))

    return gini_coef

def get_orientation(poly):
    """
    Return the angle of the minimum area rotated rectangle in degrees.

    Args:
        poly (Polygon): geometric polygon.
    
    Returns:
        angle (float): The orientation of the miminum area rotated rectangle in degrees, measured symmetrically between 0 and 90.
    """

    # Get the minimum rotated rectangle
    mbr = poly.minimum_rotated_rectangle

    # Get coordinates of the rectangle
    x, y = mbr.exterior.coords.xy

    # Calculate the angle between the first two points
    edge_angle = np.arctan2(y[1] - y[0], x[1] - x[0])

    # Normalize the angle to 0-90 degrees (we don't care about long side vs short side)
    angle = np.degrees(edge_angle) % 90

    return angle

def calculate_orientation_entropy(geoms, bins=36):
    """
    Calculate Shannon entropy of orientations for a list of polygons.

    Args:
        geoms (list[Polygon]): geometric polygon.
    
    Returns:
        orientation_entropy (float): The entropy of the orientations, from 0 to 1.
    """
    if not geoms or len(geoms) <= 1:
        return 0.0
    
    # Get orientation for each geom
    angles = [get_orientation(p) for p in geoms]
    
    # 2. Create a distribution of angles
    hist, _ = np.histogram(angles, bins=bins, range=(0, 90))
    
    # Calculate the Shannon entropy and normalize by log(bins) to get a value between 0 and 1
    orientation_entropy = entropy(hist) / np.log(bins)

    return orientation_entropy

def main():
    """
    Create lot features for modelling.
    Save this file as a GeoJSON in data/lots/
    """
    os.chdir('..')

    initial_lots = load_lot_data()

    # Add basic geographic features
    lot_data = add_geo_features(initial_lots)

    # Add gini coefficient
    lot_data["gini_coef"] = [
        gini_coefficient([poly.area for poly in geom.geoms]) 
        if hasattr(geom, 'geoms') else 0.0 
        for geom in lot_data.geometry
    ]

    # Add orientation entropy
    lot_data["orientation_entropy"] = [
        calculate_orientation_entropy(list(geom.geoms)) 
        if hasattr(geom, 'geoms') else 0.0 
        for geom in lot_data.geometry
    ]

    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lots')
    clean_path = os.path.normpath(output_path)
    lot_data_file = os.path.join(clean_path, "lot_features.geojson")

    # Write the output to data folder   
    lot_data.to_file(lot_data_file, driver="GeoJSON")

if __name__ == "__main__":
    main()