# This script loads and filters EPA National Walkability Index data at the US Census Block Group level.
#   - The data is available for download at: https://catalog.data.gov/dataset/walkability-index8
#   - The methodology used to score each block group is provided at: https://www.epa.gov/sites/default/files/2021-06/documents/national_walkability_index_methodology_and_user_guide_june2021.pdf
#   - Requires having loaded in the parking lot boundaries

import os
from pyogrio.errors import DataSourceError
import geopandas as gpd

# The downloaded files are saved in the below file path
WALKABILITY_PATH = "data/source_data/WalkabilityIndex/Natl_WI.gdb"
PARKING_BOUNDARY_PATH = "data/lots/city_boundaries.geojson"

def load_walkability_index():
    """
    Load the walkability data. Filter the resulting data to the block groups overlapping the parking lot boundaries.
    
    Returns:
        walk_index_filtered (DataFrame): the GeoPandas Data Frame of walk index data for each Census Block Group.
    """

    # Load data
    walk_index = gpd.read_file(WALKABILITY_PATH, layer='NationalWalkabilityIndex')

    # Filter the block groups to only those which overlap the parking lot boundaries
    try:
        boundaries = gpd.read_file(PARKING_BOUNDARY_PATH)

        # Project to same CRS
        walk_index = walk_index.to_crs(epsg=5070)
        boundaries = boundaries.to_crs(epsg=5070)

        walk_index_filtered = gpd.sjoin(walk_index, boundaries, how='inner', predicate='intersects')

        return walk_index_filtered

    except DataSourceError:
        print("No parking boundaries data. Load this data first.")

def main():
    """
    Retrieve the walkability index data for each block group overlapping with the Central City boundaries.
    Save this file as a GeoJSON in data/filtered_block_groups/
    """
    os.chdir('..')

    walk_index = load_walkability_index()

    if walk_index is not None and not walk_index.empty:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'filtered_block_groups')
        clean_path = os.path.normpath(output_path)
        walk_index_file = os.path.join(clean_path, "walk_index.geojson")

        # Create output folder if does not exist
        if not os.path.exists(clean_path):
            os.makedirs(clean_path)

        # Write the output to data folder   
        walk_index.to_file(walk_index_file, driver="GeoJSON")

if __name__ == "__main__":
    main()