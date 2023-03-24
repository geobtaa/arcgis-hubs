This repository is for tracking the BTAA GDP harvesting activities from ArcGIS Hub data portals


### Step 1. Get the active portal list by downloading them from GEOMG. 

1. Look for sites with these parameters:
   -  Resource Class: Websites
   - Accrual Method: DCAT US 1.1
   - This link should work: https://geomg.lib.umn.edu/documents?f%5Bb1g_dct_accrualMethod_s%5D%5B%5D=DCAT+US+1.1&f%5Bgbl_resourceClass_sm%5D%5B%5D=Websites&rows=20&sort=score+desc

2. Rename the downloaded file arcPortals.csv

Note: we will no longer maintain a separate list as a CSV in these repos. It has been too hard to keep them in sync.  Any changes or updates to the Hub sites should be done in GEOMG. Once the CSV has been downloaded, we don't need to adjust the field names, because I updated the script to find them as is.

### Step 2: Prepare the repo

1. Make a new branch for the scan and name it by date. (ex 2023-02-08)
2. Clear out the documents in the JSONS and REPORTS folders
3. Put the downloaded arcPortals.csv in the repo next to the folders

I did not completely disable the comparison feature in the script yet, but we do not want to use it for our regular scans. Clear out the folders so that the script has nothing to compare to. It will download the full JSONs and create a CSV of all items.

note: the current script still looks for dates. If you have already downloaded a JSON from a portal with today's date in the filename, it will just use that one. Otherwise, it will download a new one.

### Step 3: Run scanner.py

1. Open Terminal
2. CD into directory
3. type python scanner.py
4. Troubleshoot!

The Hub sites are fairly unstable and it is likely that one or more of them will fail and interrupt the script. Check and see if the site is down, moved, etc. Make any updates to GEOMG directly. For tracking problems, the Status field in GEOMG is plain text and can be used for admin notes.

- If a site is missing, Unpublish it from GEOMG and indicate the Date Retired, and make a note in the Status field.  
- If a site just isn't working, Remove the value "DCAT US 1.1" from the Accrual Method field and make a note in the Status field.

Edit the arcPortals.csv (or re-download it) and keep running until it works.

### Step 4: Inspect the results and make edits as needed

1. Open the CSV in the Reports folder. (currently called allNewItems  - we may change this)
2. Remove duplicate items using a spreadsheet function to keep only the first instances of these values:
- ID
- Title (optional)

There may be other things to check for.  Removing duplicates could also be added back into the script.

### Step 5: Upload to GEOMG

1. Uploaded new batch, making sure the Date Accessioned was filled in with today's date
2. Searched for the previous harvest date [example for 2023-03-07](https://geomg.lib.umn.edu/documents?f%5Bb1g_dct_accrualMethod_s%5D%5B%5D=ArcGIS+Hub&q=%222023-03-07%22&rows=20&sort=score+desc)
3. Unpublished the ones that have the old date in the Date Accessioned field - record this number in the ticket under Number Deleted
4. Look for records in the uploaded batch that are still "Draft" - these are new records. Publish them and record this number in the GitHub issue ticked under Number Added

### Step 6: Publish your branch to GitHub

This will just be for tracking purposes. Do not open a pull request to update the main branch.

If you edit the scanner script, create a different branch with a name related to the work (ex. fix-date-scan) and create a pull request for that. Mainly, we want to avoid merging all of the JSON and CSV files we create in each branch.