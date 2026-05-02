import os
import requests
import zipfile
import shutil

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    else:
        print(f"Failed to download. Status code: {response.status_code}")

def extract_zip(zip_path, extract_to):
    print(f"Extracting {zip_path} to {extract_to}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print("Extraction complete.")

if __name__ == "__main__":
    DATA_URL = "https://phm-datasets.s3.amazonaws.com/NASA/4.+Bearings.zip"
    ZIP_NAME = "bearings.zip"
    INGESTION_DIR = "data_lake/ingestion_temp"
    
    if not os.path.exists(INGESTION_DIR):
        os.makedirs(INGESTION_DIR)
    
    zip_path = os.path.join(INGESTION_DIR, ZIP_NAME)
    
    # Download
    if not os.path.exists(zip_path):
        download_file(DATA_URL, zip_path)
    
    # Extract
    extract_zip(zip_path, INGESTION_DIR)
    
    print("Phase 1: Download and Extraction complete.")
