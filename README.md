# Parking and Car Usage

How well can we explain car usage in US cities using solely the footprint of their parking lots?

## Source Datasets

[Parking Reform Network](https://parkingreform.org/): Parking lot locations and city boundaries. The foundational dataset for this analysis.

[ACS Means of Transporation to Work](https://data.census.gov/table?q=b08301&g=010XX00US$1500000): Data for car trip shares.

[US Census Shapefiles](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html): Geometries for the 2020 US Census block groups.

[EPA Walkability Metric](https://catalog.data.gov/dataset/walkability-index8): Walk scores for 2010 US Census block groups. Not ultimately used for analysis given that the logic fopr walk scores breaks down at smaller geographic areas.

## Folder Structure
```text
├── data/               # All data engineered from the source datasets
├── data_processing/    # Data processing and engineering scripts
├── analysis/           # Notebooks and util functions for analysis and modeling
└── README.md