# DCAT Maintenance
This repository is for tracking the BTAA GDP harvesting activities from ArcGIS Hub data portals




## Environment Setup

We We will be using **Anaconda 3** to edit and run scripts. Information on Anaconda installation can be found [here](https://docs.anaconda.com/anaconda/install/).  All packages available for 64-bit Windows with Python 3.7 in the Anaconda can be found [here](https://docs.anaconda.com/anaconda/packages/py3.7_win-64/). Please note that all scripts are running on Python 3 (**3.7.6**).

Here are all dependencies needed to be installed properly: 

- [geopandas](https://geopandas.org/getting_started/install.html) [Version: 0.7.0]

- [shapely](https://pypi.org/project/Shapely/) [Version: 1.7.0]

- [requests](https://requests.readthedocs.io/en/master/user/install/#install) [Version: 2.22.0]

- [numpy](https://numpy.org/install/) [Version: 1.18.1]



## Python Scripts
- ### scanner.py

This script can be run regularly to find new portals.  

 



## CSV Lists
These list the current and historical portal URL. The scripts above that harvest from hosted JSONS require accompanying lists of where to harvest from. These are referenced in the section of the script commented as *"Manual items to change!"*

- ### arcPortals.csv

    This file should have five columns *(portalName, URL, provenance, publisher, and spatialCoverage)* with details about ESRI open data portals to be checked for new records.



## Folders

- ### jsons

    This holds all harvested JSONs with the naming convention of **portalName_YYYYMMDD.json**. Once running the python scripts, newly generated JSON files need to be uploaded. The date in the latest JSON filename is used to define *PreviousActionDate*. These are referenced in the section of the script commented as *"Manual items to change!"*


- ### reports
  
    This holds all CSV reports of new and deleted items and portal status reports :
    - **allNewItems_YYYYMMDD.csv**
    - **allDeletedItems_YYYYMMDD.csv**
    - **portal_status_report_YYYYMMDD.csv**
    
    Once running the python scripts, newly generated CSV files need to be uploaded. Like JSONs, the date in the latest CSV filename is used to define *PreviousActionDate*. These are referenced in the section of the script commented as *"Manual items to change!"*