# Functions for exploratory analysis and modeling

import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
import numpy as np

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "axes.labelsize": 12,
    "axes.titlesize": 14,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10
})

def plot_city_lot_map(
    lots: gpd.GeoDataFrame,
    boundaries: gpd.GeoDataFrame,
    city: str,
    caption: str,
    buffer: float = 0.06,
):
    """
    Plot a parking lot map for a given city with a specific caption.

    Args:
        lots (DataFrame): the GeoPandas data frame with parking lot locations.
        boundaries (DataFrame): the GeoPandas data frame with city boundaries.
        city (str): the name of the city in the parking data.
        caption (str): the desired caption.
        buffer (float): the buffer at the bottom of the plot for the caption.

    Returns:
        Plot of parking lots and city boundary with the desired caption.
    """
    # Filter the data to the specific city
    lots_city = lots[lots["city"] == city]
    boundary_city = boundaries[boundaries["id"] == city]
    lots_city = lots_city.to_crs(epsg=3857)
    boundary_city = boundary_city.to_crs(epsg=3857)

    # plot on top of an ESRI base
    fig, ax = plt.subplots(figsize=(12, 12))

    boundary_city.plot(
        ax=ax,
        edgecolor="red",
        linewidth=2,
        facecolor="none",
        zorder=3
    )

    lots_city.plot(
        ax=ax,
        color="orange",
        alpha=0.6,
        zorder=4
    )

    ctx.add_basemap(
        ax,
        source=ctx.providers.Esri.WorldImagery,
        zoom=16
    )

    # Add the caption
    fig.text(
        0.5, buffer, 
        caption,
        ha="center", 
        fontsize=20, 
        style='italic',
        wrap=True
    )

    ax.set_axis_off()
    plt.tight_layout()
    plt.show()

def plot_rose_diagram(
    angles: list,
    caption: str
):
    """
    Create a polar histogram for polygon orientations.
    The angles will be a list of values between 0 and 90.

    Args:
        angles(list[float]): a list of angles between 0 and 90.
        caption (str): The caption for the diagram.

    Returns:
        Rose diagram showing the orientations of those angles. 
    """
    # Mirror the 0-90 angles for 90-360
    angles = np.asarray(angles)
    angles_360 = np.concatenate([
        angles,
        angles + 90,
        angles + 180,
        angles + 270
    ]) % 360

    # Each bin is 10 degrees and centered on cardinal directions
    bin_width = 10
    bins = np.arange(-bin_width/2, 360 + bin_width, bin_width)

    # Count the frequencies in each bin
    counts, bin_edges = np.histogram(angles_360, bins=bins)
    
    # Get the bin centers in radians for plotting
    bin_centers_deg = (bin_edges[:-1] + bin_edges[1:]) / 2
    theta = np.radians(bin_centers_deg)
    width = np.radians(bin_width)

    # Create rose diagram plot
    fig = plt.figure(figsize=(8, 8), dpi=200)
    ax = fig.add_subplot(111, projection='polar')
    bars = ax.bar(theta, counts, width=width, bottom=0.0, 
              color='orange', edgecolor='black', alpha=0.7)
    ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels(["E", "NE", "N", "NW", "W", "SW", "S", "SE"])

    fig.text(
        0.5, 0.04, 
        caption,
        ha="center", 
        fontsize=14, 
        style='italic',
        wrap=True
    )

    plt.show()