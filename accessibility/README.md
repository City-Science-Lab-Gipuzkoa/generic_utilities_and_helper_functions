# Auxiliary Data Processing Functions

This repository contains a set of auxiliary scripts for generating datasets related to population, cadastral references, land use, and workforce distribution in Gipuzkoa.

Each module includes:
- An `input_data` folder with the required datasets.
- An `output_data` folder with the generated results.

## 1. `assign_land_use_to_cadastral_references`

Assigns land-use information to each cadastral reference in Gipuzkoa.

**Output formats:** `.shp`, `.csv`

## 2. `assign_latlong_to_establishments`

Uses Google Maps and OpenStreetMap to assign geographic coordinates (latitude and longitude) to commercial establishments in Gipuzkoa.

**Output formats:** `.shp`, `.xlsx`, `.csv`

## 3. `assign_population_and_workers_to_cadastral_references`

Uses the outputs from the previous modules to assign population (based on residential floor area) and number of employees (based on establishment locations) to each cadastral reference in Gipuzkoa.

**Output formats:** `.shp`, `.csv`