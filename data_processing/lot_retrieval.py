# This script retrieves the "Central City" boundaries and parking lot polygons for the 100+ cities analyzed by the Parking Reform Network
# The map and methodology for the data can be found at https://parkingreform.org/resources/parking-lot-map/

# The resulting boundaries and lots are saved into data/lots/

import os
import re
import json
import requests

PRN_URL = "https://parkingreform.org/parking-lot-map/"

def extract_geojson_from_js(text: str):
    """
    Find all JSON.parse() calls in a JS block, decode the JSON, and returns only the JSONs where type is 'FeatureCollection' or 'Feature'.

    Args:
        text (str): the JS text block.

    Returns:
        data (dict): GeoJSON object.
    """

    # Initialize the list of features
    features = []

    # Set regex for JSON parse expression
    pattern = re.compile(r"JSON\.parse\(\s*(['\"])(?P<json>.*?)\1\s*\)")

    # Loop through text chunks which match the pattern
    for match in pattern.finditer(text):
        json_text = match.group("json")
        try:
            json_text = json_text.encode("utf-8").decode("unicode_escape")
        except Exception:
            pass

        # If the JSON type is a Feature or FeatureCollection, add to the list
        try:
            data = json.loads(json_text)
            if isinstance(data, dict) and data.get("type") in ["FeatureCollection", "Feature"]:
                features.append(data)
        except json.JSONDecodeError:
            continue

    return features

def flatten_coords(coords: list):
    """
    Flatten geographic coordinates from X,Y,Z to X,Y. Operates recursively.

    Args:
        coords (list): a list of X,Y,Z coordinates. May include multiple nested lists.

    Returns:
        list: A list of flattened X,Y coordinates.
    """

    # Return X and Y if X is a float or integer
    if isinstance(coords[0], (float, int)):
        return coords[:2]
    
    # If X is not numeric, go a level down
    else:
        return [flatten_coords(c) for c in coords]

def flatten_geojson(geojson: dict):
    """
    Take a GeoJSON dict and flatten all coordinates objects. Operates recursively.

    Args:
        geojson (dict): a GeoJSON dict.
    
    Returns:
        geojson (dict): the same GeoJSON with all coordinates flattened from X,Y,Z to X,Y.
    """

    # Flatten the corrdinates for each possible geometry type
    if geojson["type"] in ["Polygon", "MultiPolygon", "LineString", "MultiLineString", "Point", "MultiPoint"]:
        geojson["coordinates"] = flatten_coords(geojson["coordinates"])

    # If JSON is a Feature, go one level down
    elif geojson["type"] == "Feature":
            flatten_geojson(geojson["geometry"])

    # If JSON is a FeatureCollection, go one level down
    elif geojson["type"] == "FeatureCollection":
        for feature in geojson["features"]:
            flatten_geojson(feature)

    return geojson

def retrieve_lots(text: str):
    """
    Retrieve the parking lot polygons for each city analyzed by the Parking Reform Network (PRN).

    Args:
        text (str): The JS text block.
    
    Returns:
        geojson (dict): the GeoJSON with parking lot polygons for each city.
    """

    # Initialize lots list for each city
    lots = []

    # Set regex for the parking lot JSON imports 
    pattern = r'import\("\./(.*?\.js)"\)'
    matches = re.findall(pattern, text)
    print(f"Found {len(matches)} city lot maps.")

    # For each city, request the specific URL and append the extracted GeoJSON to the list
    for filename in matches:
        url = f"{PRN_URL.rstrip('/')}/{filename}"

        city_name = filename.split('.')[0]
        print(f"Processing {city_name}...")

        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error in JSON request: HTTP {response.status_code}")
                continue

            geojson_data = extract_geojson_from_js(response.text)

            if geojson_data:
                lots.append(geojson_data)
            else:
                print(f"Error in JSON data: Could not parse JSON from JS file.")

        except Exception as e:
            print(f"Error {e}")

    # Flatten the list since each extract_geojson_from_js() call returns a list
    flattened_lots = [geo for sublist in lots for geo in sublist]

    # Create one large GeoJSON for saving output
    geojson = {
        "type": "FeatureCollection",
        "features": flattened_lots
    }

    return geojson

def main():
    """
    Retrieve the Central City boundaries and parking lot locations for each city.
    Save these files as GeoJSONs in data/lots/
    """
    os.chdir('..')

    # Get the HTML response from the PRN URL
    response = requests.get(PRN_URL)
    response.raise_for_status()
    html = response.text

    # Retrieve the city bouncaries
    city_boundaries_geojson = []
    for data in extract_geojson_from_js(html):
        city_boundaries_geojson.append(data)

    # Retrieve parking lot polygons
    lots_geojson = retrieve_lots(html)

    # Flatten the coordinates from X,Y,Z to X,Y
    output_boundaries = flatten_geojson(city_boundaries_geojson[0])
    output_lots = flatten_geojson(lots_geojson)

    # Write the outputs to data folder
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lots')
    clean_path = os.path.normpath(output_path)
    boundaries_file = os.path.join(clean_path, "city_boundaries.geojson")
    lots_file = os.path.join(clean_path, "city_lots.geojson")

    # Write the boundaries file
    with open(boundaries_file, 'w') as f:
        json.dump(output_boundaries, f, indent=4)

    # Write the lots file
    with open(lots_file, 'w') as f:
        json.dump(output_lots, f, indent=4)

if __name__ == "__main__":
    main()