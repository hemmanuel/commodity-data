import requests
from bs4 import BeautifulSoup
import os

# ERCOT Base URL
BASE_URL = "https://www.ercot.com"

# Product IDs
# NP6-785-ER: Historical RTM Load Zone and Hub Prices
# NP6-86-CD: SCED Shadow Prices and Binding Transmission Constraints

# We need to find the actual download links from these pages.
# Let's inspect the page for NP6-785-ER first.

url = "https://www.ercot.com/mp/data-products/data-product-details?id=NP6-785-ER"

print(f"Fetching {url}...")
try:
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    
    soup = BeautifulSoup(r.content, 'html.parser')
    
    # Look for download links (usually in a table or list)
    # They often have 'doc' in the href
    
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/content/' in href or '.zip' in href:
            full_url = href if href.startswith('http') else BASE_URL + href
            links.append((a.text.strip(), full_url))
            
    print(f"Found {len(links)} potential download links:")
    for text, link in links[:10]:
        print(f"- {text}: {link}")
        
except Exception as e:
    print(f"Error: {e}")
