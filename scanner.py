# -*- coding: utf-8 -*-
"""
Original created on Wed Mar 15 09:18:12 2017
Edited Dec 28 2018; January 8, 2019
@author: kerni016

Updated July 28, 2020
Updated by Yijing Zhou @YijingZhou33

Updated October 6, 2020
Updated by Ziying Cheng @Ziiiiing

Updated February 16, 2021
Updated by Yijing Zhou @YijingZhou33
-- populating spatial coverage based on bounding boxes

Updated February 24, 2021
Updated by Yijing Zhou @YijingZhou33
-- Handling download link errors for newly added items

Updated May 13, 2021
Updated by Ziying Cheng @Ziiiiing
-- Updating 'Genre' field

Updated May 13, 2021
Updated by Ziying Cheng @Ziiiiing
-- Updating the csv report for retired items

Updated Dec 31, 2021
Updated by Ziying Cheng @Ziiiiing
-- Updating the Provider, Member Of and Is Part Of fields

Updated Apr 17, 2022
Updated by Ziying Cheng @Ziiiiing
-- Updating the Theme, Duplicates, Title

Changed February 1, 2023
@karenmajewicz
removes complex functions in order to run more regularly

"""
# Need to define directory path (containing arcPortals.csv, folder "jsons" and "reports"), and list of fields desired in the printed report
# The script currently prints one combined report - one of new items
# The script also prints a status report giving the total number of resources in the portal

import json
import csv
from ssl import AlertDescription
import urllib
import urllib.request
from urllib.parse import urlparse, parse_qs
import os
from html.parser import HTMLParser
import decimal
import re
import time
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import numpy as np
from itertools import chain
from itertools import repeat
from functools import reduce
import requests

######################################

# SET UP YOUR PATHS

# names of the main directory containing folders named "jsons" and "reports"
# Windows:
# directory = r'D:\Library RA\dcat-metadata'
# MAC or Linux:
directory = r'.'


# csv file contaning portal list 
portalFile = 'arcPortals.csv'

# list of metadata fields from the DCAT json schema for open data portals desired in the final report
fieldnames = ['Title', 'Alternative Title', 'Description', 'Language', 'Creator', 'Title Source', 'Resource Class',
              'Theme', 'Keyword', 'Date Issued', 'Temporal Coverage', 'Date Range', 'Spatial Coverage',
              'Bounding Box', 'Resource Type', 'Format', 'Information', 'Download', 'MapServer',
              'FeatureServer', 'ImageServer', 'ID', 'Identifier', 'Provider', 'Code', 'Member Of', 'Is Part Of', 'Rights',
              'Accrual Method', 'Date Accessioned', 'Access Rights']

# list of fields to use for the deletedItems report
delFieldsReport = ['ID', 'document[b1g_dateRetired_s]', 'document[b1g_status_s]', 'document[publication_state]']

# list of fields to use for the portal status report
statusFieldsReport = ['portalName', 'total', 'new_items', 'deleted_items']

# dictionary using partial portal code to find out where the data portal belongs
statedict = {'01': 'Indiana', '02': 'Illinois', '03': 'Iowa', '04': 'Maryland', '04c-01': 'District of Columbia', 
             '04f-01': '04f-01', '05': 'Minnesota', '06': 'Michigan', '07': 'Michigan', '08': 'Pennsylvania', 
             '09': 'Indiana', '10': 'Wisconsin', '11': 'Ohio', '12': 'Illinois', '13': 'Nebraska', '14': 'New Jersey', '99': 'Esri'}
#######################################


# function to removes html tags from text
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def cleanData(value):
    fieldvalue = strip_tags(value)
    return fieldvalue

# function that prints metadata elements from the dictionary to a csv file (portal_status_report)
# with as specified fields list as the header row.


def printReport(report, dictionary, fields):
    with open(report, 'w', newline='', encoding='utf-8') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for keys in dictionary:
            allvalues = dictionary[keys]
            csvout.writerow(allvalues)

# Similar to the function above but generates two csv files (allNewItems & allDeletedItems)


def printItemReport(report, fields, dictionary):
    with open(report, 'w', newline='', encoding='utf-8') as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(fields)
        for portal in dictionary:
            for keys in portal:
                allvalues = portal[keys]
                csvout.writerow(allvalues)

# function that creates a dictionary with the position of a record in the data portal DCAT metadata json as the key
# and the identifier as the value.


def getIdentifiers(data):
    json_ids = {}
    for x in range(len(data["dataset"])):
        json_ids[x] = data["dataset"][x]["identifier"]
    return json_ids


def getTitles(data):
    json_titles = {}
    for x in range(len(data["dataset"])):
        json_titles[x] = data["dataset"][x]["title"]
    return json_titles

'''Auto-generate Title field be like alternativeTitle [titleSource(place name)] {year if exist in alternative title}'''
def format_title(alternativeTitle, titleSource):
    # find if year exist in alternativeTitle
    year = ''  
    year_range = re.findall(r'(\d{4})-(\d{4})', alternativeTitle)
#     single_year = re.match(r'.*([1-3][0-9]{3})', alternativeTitle)  
    single_year = re.match(r'.*(17\d{2}|18\d{2}|19\d{2}|20\d{2})', alternativeTitle)    
    if year_range:   # if a 'yyyy-yyyy' exists
        year = '-'.join(year_range[0])
        alternativeTitle = alternativeTitle.replace(year, '').strip().rstrip(',')
    elif single_year:  # or if a 'yyyy' exists
        year = single_year.group(1)




        alternativeTitle = alternativeTitle.replace(year, '').strip().rstrip(',')
        
    title = alternativeTitle + ' [{}]'.format(titleSource)
    
    if year:
        title += ' {' + year +'}'
        
    return title


# function that returns a dictionary of selected metadata elements into a dictionary of new items (newItemDict) for each new item in a data portal.
# This includes blank fields '' for columns that will be filled in manually later.
def metadataNewItems(newdata, newitem_ids):
    newItemDict = {}
    # y = position of the dataset in the DCAT metadata json, v = landing page URLs
    for y, v in newitem_ids.items():
        identifier = v
        metadata = []

#ALTERNATIVE TITLE
        alternativeTitle = ""
        try:
            alternativeTitle = cleanData(newdata["dataset"][y]['title'])
        except:
            alternativeTitle = newdata["dataset"][y]['title']
            
#DESCRIPTION
        description = cleanData(newdata["dataset"][y]['description'])
        # Remove newline, whitespace, defalut description and replace singe quote, double quote
        if description == "{{default.description}}":
            description = description.replace("{{default.description}}", "")
        elif description == "{{description}}":
            description = description.replace("{{description}}", "")
        else:
            description = re.sub(r'[\n]+|[\r\n]+', ' ',
                                 description, flags=re.S)
            description = re.sub(r'\s{2,}', ' ', description)
            description = description.replace(u"\u2019", "'").replace(u"\u201c", "\"").replace(u"\u201d", "\"").replace(
                u"\u00a0", "").replace(u"\u00b7", "").replace(u"\u2022", "").replace(u"\u2013", "-").replace(u"\u200b", "")

 #CREATOR
        creator = newdata["dataset"][y]["publisher"]
        for pub in creator.values():
            try:
                creator = pub.replace(u"\u2019", "'")
            except:
                creator = pub


# DISTRIBUTION

        format_types = []
        resourceClass = ""
        formatElement = ""
        downloadURL = ""
        resourceType = ""
        webService = ""

        distribution = newdata["dataset"][y]["distribution"]
        for dictionary in distribution:
            try:
                # If one of the distributions is a shapefile, change genre/format and get the downloadURL
                format_types.append(dictionary["title"])
                if dictionary["title"] == "Shapefile":
                    resourceClass = "Datasets|Web services"
                    formatElement = "Shapefile"
                    if 'downloadURL' in dictionary.keys():
                        downloadURL = dictionary["downloadURL"].split('?')[0]
                    else:
                        downloadURL = dictionary["accessURL"].split('?')[0]

                    resourceType = "Vector data"

                # If the Rest API is based on an ImageServer, change genre, type, and format to relate to imagery
                if dictionary["title"] == "ArcGIS GeoService":
                    if 'accessURL' in dictionary.keys():
                        webService = dictionary['accessURL']

                        if webService.rsplit('/', 1)[-1] == 'ImageServer':
                            resourceClass = "Imagery|Web services"
                            formatElement = 'Imagery'
                            resourceType = "Satellite imagery"
                    else:
                        resourceClass = ""
                        formatElement = ""
                        downloadURL = ""

            # If the distribution section of the metadata is not structured in a typical way
            except:
                resourceClass = ""
                formatElement = ""
                downloadURL = ""
                continue


        try:
            bboxList = []
            bbox = ''
            spatial = cleanData(newdata["dataset"][y]['spatial'])
            typeDmal = decimal.Decimal
            fix4 = typeDmal("0.0001")
            for coord in spatial.split(","):
                coordFix = typeDmal(coord).quantize(fix4)
                bboxList.append(str(coordFix))
            bbox = ','.join(bboxList)
        except:
            spatial = ""

        theme = ""
        keyword = newdata["dataset"][y]["keyword"]
        keyword_list = []
        keyword_list = '|'.join(keyword).replace(' ', '')

        dateIssued = cleanData(newdata["dataset"][y]['issued']).split('T', 1)[0] 
        temporalCoverage = ""
        dateRange = ""

        information = cleanData(newdata["dataset"][y]['landingPage'])
        
        try:
            rights = cleanData(newdata["dataset"][y]['license'])
        except:
            rights = ""   

        featureServer = ""
        mapServer = ""
        imageServer = ""

        try:
            if "FeatureServer" in webService:
                featureServer = webService
            if "MapServer" in webService:
                mapServer = webService
            if "ImageServer" in webService:
                imageServer = webService
        except:
            print(identifier)

# GET CLEAN IDENTIFIER
        slug = identifier.split('=', 1)[-1].replace("&sublayer=", "_")
        querystring = parse_qs(urlparse(identifier).query)
        identifier_new = "https://hub.arcgis.com/datasets/" + "" + querystring["id"][0]

        # auto-generate Title as alternativeTitle [titleSource] {YEAR if it exists in alternativeTitle}
        title = format_title(alternativeTitle, titleSource)
        # auto-generate Temporal Coverage and Date Range
        if re.search(r"\{(.*?)\}", title):     # if title has {YYYY} or {YYYY-YYYY}
            temporalCoverage = re.search(r"\{(.*?)\}", title).group(1)
            dateRange = temporalCoverage[:4] + '-' + temporalCoverage[-4:]
        else:
            temporalCoverage = 'Continually updated resource'

        # if 'LiDAR' exists in Title or Description, add it to Resource Type
        if 'LiDAR' in title or 'LiDAR' in description:
            resourceType = 'LiDAR'
        if 'imagery' in title or 'imagery' in description or 'imagery' in keyword_list:
            resourceClass = 'Imagery'

        metadataList = [title, alternativeTitle, description, language, creator, titleSource,
                        resourceClass, theme, keyword_list, dateIssued, temporalCoverage,
                        dateRange, spatialCoverage, bbox, resourceType,
                        formatElement, information, downloadURL, mapServer, featureServer,
                        imageServer, slug, identifier_new, provider, portalName, memberOf, isPartOf, rights,
                        accrualMethod, dateAccessioned, accessRights]

        # deletes data portols except genere = 'Geospatial data' or 'Aerial imagery'
        for i in range(len(metadataList)):
            if metadataList[6] != "":
                metadata.append(metadataList[i])

        newItemDict[slug] = metadata

        for k in list(newItemDict.keys()):
            if not newItemDict[k]:
                del newItemDict[k]

    return newItemDict


All_New_Items = []
All_Deleted_Items = []
Status_Report = {}

# Generate the current local time with the format like 'YYYYMMDD' and save to the variable named 'ActionDate'
ActionDate = time.strftime('%Y%m%d')

# List all files in the 'jsons' folder under the current directory and store file names in the 'filenames' list
filenames = os.listdir('jsons')

# Open a list of portals and urls ending in /data.json from input CSV
# using column headers 'portalName', 'URL', 'provider', 'SpatialCoverage'
with open(portalFile, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Read in values from the portals list to be used within the script or as part of the metadata report
        portalName = row['ID']
        url = row['Identifier']
        provider = row['Title']
        titleSource = row['Publisher']
        spatialCoverage = row['Spatial Coverage']
        isPartOf  = row['ID']
        memberOf = row['Member Of']
        print(portalName, url)
        accrualMethod = "ArcGIS Hub"
        dateAccessioned = time.strftime('%Y-%m-%d')
        accessRights = "Public"
        language = "eng"

        # For each open data portal in the csv list...
        # create an empty list to extract all previous action dates only from file names
        dates = []

        # loop over all file names in 'filenames' list and find the json files for the selected portal
        # extract the previous action dates only from these files and store in the 'dates' list
        for filename in filenames:
            if filename.startswith(portalName):
                # format of filename is 'portalName_YYYYMMDD.json'
                # 'YYYYMMDD' is located from index -13(included) to index -5(excluded)
                dates.append(filename[-13:-5])

        # remove action date from previous dates if any
        # in case the script is run several times in one single day
        # so the actionDate JSONs can overwrite those generated earlier on the same day 
        if ActionDate in dates:
            dates.remove(ActionDate)

        # find the latest action date from the 'dates' list
        if dates:
            PreviousActionDate = max(dates)
        else:  # for brand new portals
            PreviousActionDate='00000000'

        # renames file paths based on portalName and manually provided dates
        oldjson = directory + \
            '/jsons/%s_%s.json' % (portalName, PreviousActionDate)
        newjson = directory + '/jsons/%s_%s.json' % (portalName, ActionDate)

        # if newjson already exists, do not need to request again
        if os.path.exists(newjson):
            with open(newjson, 'r') as fr:
                newdata = json.load(fr)
        else:
            response = urllib.request.urlopen(url)
            # check if data portal URL is broken
            if response.headers['content-type'] != 'application/json; charset=utf-8':
                print("\n--------------------- Data portal URL does not exist --------------------\n",
                      portalName, url,  "\n--------------------------------------------------------------------------\n")
                continue
            else:
                newdata = json.load(response)

            # Saves a copy of the json to be used for the next round of comparison/reporting
            with open(newjson, 'w', encoding='utf-8') as outfile:
                json.dump(newdata, outfile)

        # collects information about number of resources (total, new, and old) in each portal
        status_metadata = []
        status_metadata.append(portalName)

        # Opens older copy of data/json downloaded from the specified Esri Open Data Portal.
        # If this file does not exist, treats every item in the portal as new.
        if os.path.exists(oldjson):
            with open(oldjson) as data_file:
                older_data = json.load(data_file)

            # Makes a list of dataset identifiers in the older json
            older_ids = getIdentifiers(older_data)
            # UPDATE: Makes a list of dataset title in the older json
            older_titles = getTitles(older_data)

            # compares identifiers in the older json harvest of the data portal with identifiers in the new json,
            # creating dictionaries with
            # 1) a complete list of new json identifiers
            # 2) a list of just the items that appear in the new json but not the older one
            newjson_ids = {}
            newitem_ids = {}

            for y in range(len(newdata["dataset"])):
                identifier = newdata["dataset"][y]["identifier"]
                newjson_ids[y] = identifier
                if identifier not in older_ids.values():
                    newitem_ids[y] = identifier
            
            # UPDATE
            newjson_titles = {}
            newitem_ids = {}
            for y in range(len(newdata["dataset"])):
                identifier = newdata["dataset"][y]["identifier"]
                title = newdata["dataset"][y]["title"]
                newjson_titles[y] = title
                if title not in older_titles.values():
                    newitem_ids[y] = identifier

            # Creates a dictionary of metadata elements for each new data portal item.
            # Includes an option to print a csv report of new items for each data portal.
            # Puts dictionary of identifiers (key), metadata elements (values) for each data portal into a list
            # (to be used printing the combined report)
            # i.e. [portal1{identifier:[metadataElement1, metadataElement2, ... ],
            # portal2{identifier:[metadataElement1, metadataElement2, ... ], ...}]
            All_New_Items.append(metadataNewItems(newdata, newitem_ids))

            # Compares identifiers in the older json to the list of identifiers from the newer json.
            # If the record no longer exists, adds selected fields into a dictionary of deleted items (deletedItemDict)
            deletedItemDict = {}


            # UPDATE: check deleted item's landing page, if it is broken, delete it
            for z in range(len(older_data["dataset"])):
                # identifier = older_data["dataset"][z]["identifier"]
                title = older_data["dataset"][z]["title"]
                if title not in newjson_titles.values():
                    distribution = older_data["dataset"][z]["distribution"]
                    for dictionary in distribution:
                        if dictionary["title"] == "Shapefile":
                            slug = identifier.rsplit('/', 1)[-1]
                        elif dictionary["title"] == "ArcGIS GeoService":  # TODO:UPDATE HERE
                            if 'accessURL' in dictionary.keys():
                                webService = dictionary['accessURL']
                                if webService.rsplit('/', 1)[-1] == 'ImageServer':
                                    slug = identifier.rsplit('/', 1)[-1]
                        else:
                            slug = ''

                    # only include records whose download link is either Shapefile or ImageServer
                    if len(slug):
                        deletedItemDict[slug] = [slug, time.strftime('%Y-%m-%d'), "Inactive", "['unpublished']"]

            All_Deleted_Items.append(deletedItemDict)

            # collects information for the status report
            status_metalist = [len(newjson_titles), len(
                newitem_ids), len(deletedItemDict)]
            for value in status_metalist:
                status_metadata.append(value)

        # if there is no older json for comparions....
        else:
            print("There is no comparison json for %s" % (portalName))
            # Makes a list of dataset identifiers in the new json
            newjson_ids = getIdentifiers(newdata)

            All_New_Items.append(metadataNewItems(newdata, newjson_ids))

            # collects information for the status report
            status_metalist = [len(newjson_ids), len(newjson_ids), '0']
            for value in status_metalist:
                status_metadata.append(value)

        Status_Report[portalName] = status_metadata

# prints two csv spreadsheets with all items that are new or deleted since the last time the data portals were harvested
newItemsReport = directory + \
    "/reports/allNewItems_%s.csv" % (ActionDate)
printItemReport(newItemsReport, fieldnames, All_New_Items)

# delItemsReport = directory + "/reports/allDeletedItems_%s.csv" % (ActionDate)
# printItemReport(delItemsReport, delFieldsReport, All_Deleted_Items)

reportStatus = directory + \
    "/reports/portal_status_report_%s.csv" % (ActionDate)
printReport(reportStatus, Status_Report, statusFieldsReport)


# ---------- Populating Spatial Coverage -----------

""" set file path """
# df_csv = pd.read_csv(newItemsReport, encoding='unicode_escape')
df_csv = pd.read_csv(newItemsReport)

""" split csv file if necessary """
# if records come from Esri, the spatial coverage is considered as United States
df_esri = df_csv[df_csv['Title Source'] == 'Esri'].reset_index(drop=True)
df_csv = df_csv[df_csv['Title Source'] != 'Esri'].reset_index(drop=True)


""" split state from column 'Title Source' """
# -----------------------------------------
# The portal code is the main indicator:
# - 01 - Indiana
# - 02 - Illinois
# - 03 - Iowa
# - 04 - Maryland
# - 04c-01 - District of Columbia
# - 04f-01 - Delaware, Philadelphia, Maryland, New Jersey
# - 05 - Minnesota
# - 06 - Michigan
# - 07 - Michigan
# - 08 - Pennsylvania
# - 09 - Indiana
# - 10 - Wisconsin
# - 11 - Ohio
# - 12 - Illinois
# - 13 - Nebraska
# - 99 - Esri
# -----------------------------------------

df_csv['State'] = [statedict[row['Code']] if row['Code'] in statedict.keys(
) else statedict[row['Code'][0:2]] for _, row in df_csv.iterrows()]

""" create bounding boxes for csv file """


def format_coordinates(df, identifier):
    # create regular bouding box coordinate pairs and round them to 2 decimal places
    # manually generates the buffering zone
    df = pd.concat([df, df['Bounding Box'].str.split(',', expand=True).astype(float).round(2)], axis=1).rename(
        columns={0: 'minX', 1: 'minY', 2: 'maxX', 3: 'maxY'})

    # check if there exists wrong coordinates and drop them
    coordslist = ['minX', 'minY', 'maxX', 'maxY']
    idlist = []
    for _, row in df.iterrows():
        for coord in coordslist:
            # e.g. [-180.0000,-90.0000,180.0000,90.0000]
            if abs(row[coord]) == 0 or abs(row[coord]) == 180:
                idlist.append(row[identifier])
        if (row.maxX - row.minX) > 10 or (row.maxY - row.minY) > 10:
            idlist.append(row[identifier])    

    # create bounding box 
    df['Coordinates'] = df.apply(lambda row: box(
        row.minX, row.minY, row.maxX, row.maxY) if str(row['Bounding Box']) != 'nan' else None, axis=1)
    df['Roundcoords'] = df.apply(lambda row: ', '.join(
        [str(i) for i in [row.minX, row.minY, row.maxX, row.maxY]]), axis=1)

    # clean up unnecessary columns
    df = df.drop(columns=coordslist).reset_index(drop=True)

    df_clean = df[~df[identifier].isin(idlist)]
    # remove records with wrong coordinates into a new dataframe
    df_wrongcoords = df[df[identifier].isin(idlist)].drop(
        columns=['State', 'Coordinates'])

    return [df_clean, df_wrongcoords]


df_csvlist = format_coordinates(df_csv, 'ID')
df_clean = df_csvlist[0]
df_wrongcoords = df_csvlist[1]


df_newitems = pd.read_csv(newItemsReport)
df_newitems.to_csv(newItemsReport, index=False)


print("\n--------------------- Congrats! ╰(￣▽￣)╯ --------------------\n")