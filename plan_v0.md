# Abstract
This project is a bridge from Garmin Connect to grafana.
The purpose of this project is to provide visualizations of health and fitness data and allow for more through analysis than the garmin connect app.
Right now, the goal is to start smaller and work up --- not going from 0 to 100 right off the bat

# Architecture 
python script (garf) -> postgresql -> grafana

Where the python script pulls data, writes to postres, and then grafana reads from postgres.
Note that postgres may be subsituted for timescaledb if that fits the project needs better.
Postgresql and grafana should be managed through docker, although they shouldn't be part of the same stack.
Grafana will need to be used for other projects as well, and I want to avoid running multiple instances if possible. 

## Schema
While I don't have an exact schema in mind, the data pulled should live in multiple tables, not just one.
Time series data such as heart rate, hrv, pulse ox, stress, etc should be in one table.
Workouts should be stored in their own table, as it is harder to put them on a time series.
This will be expanded later. Build to be extensible.

## File structure
The file structure isn't massively important, but it should similarly be built for modification. 
Classes should each have their own files, and everything should be designed using proper object-oriented programming principles.
### Required Base Classes
Workouts and time series data should both have their own abstract base classes that specific variants build off of.

## Authentication
I will handle this myself. Leave it as a placeholder

# Research 
the directory `../garmin-research/` includes an example project if you need more information.

