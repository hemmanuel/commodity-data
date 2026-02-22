# FERC Form 552 Master Table Download Instructions

The FERC data portal at data.ferc.gov uses a JavaScript-heavy interface that requires browser interaction to download CSV files. Automated downloads are challenging due to the dynamic nature of the site.

## Manual Download Instructions

1. Navigate to: https://data.ferc.gov/form-no.-552-download-data/form-552-master-table/

2. Click the blue **"Download"** button on the right side of the page

3. In the modal that appears:
   - Select **"Dataset"** radio button (not "Data Dictionary")
   - Wait for additional options to load
   - Select **"All Data"** radio button (not "Filtered Data")
   - Check the **".csv"** checkbox under "Select File Type"
   - Click the **"Download"** button at the bottom

4. The CSV file will be generated and downloaded to your Downloads folder

5. Move the downloaded file to: `data/raw/ferc/Form552_Master.csv`

## Dataset Information

- **Title**: Form 552 Master Table
- **Description**: Database of Page 1 (Identification of Respondent) and Page 4 (Purchase and Sales Information) of Annual Report of Natural Gas Transactions Form (FERC No. 552)
- **Industry**: Natural Gas
- **Last Updated**: 2/16/2026 2:08 PM
- **Security Level**: Public
- **Rows**: ~12,606 records

## Automated Download Attempts

Several automated download methods were attempted:

1. **Direct API calls** - FERC's new portal doesn't expose simple REST API endpoints
2. **Selenium browser automation** - The download button triggers a backend job that doesn't immediately download the file
3. **Request library with proper headers** - 403/404 errors on guessed endpoints

The FERC portal appears to generate CSV exports on-demand server-side, which may take time and requires maintaining a browser session.

## Alternative: Use Selenium Script

A Selenium automation script has been created at `scripts/ingestion/download_ferc_552_selenium.py` that automates the browser interaction. However, it requires Chrome/Chromium to be installed and may need adjustments based on your system.

To use it:
```bash
python scripts/ingestion/download_ferc_552_selenium.py
```

Note: The script may need debugging based on timing issues with the FERC portal's dynamic content loading.
