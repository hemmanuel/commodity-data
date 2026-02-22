"""
Download FERC Form 552 Master Table CSV file using Selenium.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import glob

def download_ferc_552_master():
    """Download the FERC Form 552 Master Table CSV file using Selenium."""
    
    # Set up download directory
    download_dir = os.path.abspath("data/raw/ferc")
    os.makedirs(download_dir, exist_ok=True)
    
    # Configure Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Run in background - DISABLED for debugging
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Set download preferences
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    print(f"Starting browser automation...")
    print(f"Download directory: {download_dir}")
    
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        
        # Navigate to the page
        url = "https://data.ferc.gov/form-no.-552-download-data/form-552-master-table/"
        print(f"\nNavigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(3)
        
        # Find and click the Download button
        print("Looking for Download button...")
        wait = WebDriverWait(driver, 20)
        download_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download')]"))
        )
        
        # Scroll into view and click using JavaScript
        driver.execute_script("arguments[0].scrollIntoView(true);", download_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", download_btn)
        print("Clicked Download button")
        
        time.sleep(2)
        
        # Save screenshot to debug
        driver.save_screenshot("debug_after_download_click.png")
        print("Saved screenshot: debug_after_download_click.png")
        
        # Check if modal appeared
        print("Checking for modal...")
        try:
            modal = driver.find_element(By.ID, "downloadModal")
            print(f"Modal found: {modal.is_displayed()}")
            
            # Save page source to see what's in the modal
            with open("modal_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Saved modal HTML to modal_source.html")
            
            # List all input elements in modal
            inputs = modal.find_elements(By.TAG_NAME, "input")
            print(f"\nFound {len(inputs)} input elements in modal:")
            for inp in inputs[:10]:
                print(f"  - type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}, value={inp.get_attribute('value')}")
        except Exception as e:
            print(f"Modal error: {e}")
            time.sleep(2)
        
        # First, select "Dataset" option (not "Data Dictionary")
        print("Selecting 'Dataset' option...")
        time.sleep(1)
        dataset_radio = wait.until(
            EC.element_to_be_clickable((By.ID, "chooseFiles1"))
        )
        driver.execute_script("arguments[0].click();", dataset_radio)
        print("Selected 'Dataset'")
        
        # Wait for additional options to load
        time.sleep(2)
        
        # Now the modal should show file size and format options
        print("Waiting for file size options to appear...")
        
        # Select "All Data" radio button
        print("Selecting 'All Data' option...")
        all_data_radio = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='full']"))
        )
        driver.execute_script("arguments[0].checked = true;", all_data_radio)
        print("Selected 'All Data'")
        
        time.sleep(1)
        
        # Check the CSV checkbox
        print("Selecting CSV format...")
        csv_checkbox = wait.until(
            EC.presence_of_element_located((By.NAME, "datasetcsv"))
        )
        driver.execute_script("arguments[0].checked = true;", csv_checkbox)
        print("Selected CSV format")
        
        time.sleep(1)
        
        # Click the Download button in the modal
        print("Clicking final Download button...")
        modal_download_btn = wait.until(
            EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Download Button']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", modal_download_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", modal_download_btn)
        print("Clicked Download - file should be downloading...")
        
        # Wait for download to complete
        print("\nWaiting for download to complete...")
        max_wait = 120  # 2 minutes max
        elapsed = 0
        while elapsed < max_wait:
            # Look for CSV files in download directory
            csv_files = glob.glob(os.path.join(download_dir, "*.csv"))
            crdownload_files = glob.glob(os.path.join(download_dir, "*.crdownload"))
            
            if csv_files and not crdownload_files:
                print(f"\nDownload complete!")
                for csv_file in csv_files:
                    print(f"Found: {csv_file}")
                    file_size = os.path.getsize(csv_file)
                    print(f"File size: {file_size:,} bytes")
                    
                    # Rename to expected filename if different
                    expected_name = os.path.join(download_dir, "Form552_Master.csv")
                    if csv_file != expected_name:
                        if os.path.exists(expected_name):
                            os.remove(expected_name)
                        os.rename(csv_file, expected_name)
                        print(f"Renamed to: {expected_name}")
                        csv_file = expected_name
                    
                    # Show first few lines
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:5]
                        print("\nFirst 5 lines:")
                        for i, line in enumerate(lines, 1):
                            print(f"{i}: {line.rstrip()}")
                    
                    return csv_file
            
            time.sleep(2)
            elapsed += 2
            if elapsed % 10 == 0:
                print(f"Still waiting... ({elapsed}s elapsed)")
        
        print("\nTimeout waiting for download")
        return None
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        print("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    download_ferc_552_master()
