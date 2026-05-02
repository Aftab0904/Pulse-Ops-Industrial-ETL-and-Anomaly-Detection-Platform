import os
import time
import shutil
import pandas as pd
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

# Configuration
SOURCE_DIR = "data_lake/ingestion_temp"
RAW_DIR = "data_lake/raw"
LANDING_DIR = "data_lake/landing"

class IngestionHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def process_file(self, file_path):
        # Handle .txt files (unpacked) or .csv if present
        if not (file_path.endswith('.txt') or file_path.endswith('.csv')):
            return
        
        print(f"[*] [Lambda Ingest] Processing: {file_path}")
        
        try:
            # --- 1. S3 RAW ARCHIVE SIMULATION ---
            # In a real AWS setup, we save the UNTOUCHED file to a 'raw' bucket first.
            if not os.path.exists(RAW_DIR):
                os.makedirs(RAW_DIR)
            shutil.copy(file_path, os.path.join(RAW_DIR, os.path.basename(file_path)))
            print(f"[+] [S3 Raw] Original file archived to: {RAW_DIR}")

            # --- 2. PROCESSING FOR LANDING ---
            df = pd.read_csv(file_path, sep='\t', header=None)
            
            # 1. Validation: Check column count (should be 4 or 8)
            if df.shape[1] not in [4, 8]:
                print(f"[!] Validation failed for {file_path}: Expected 4 or 8 columns, got {df.shape[1]}")
                return

            # 2. Noise Injection (simulate messy data)
            # Inject 1% null values
            for col in df.columns:
                mask = np.random.random(df.shape[0]) < 0.01
                df.loc[mask, col] = np.nan
            
            # 3. Partitioning logic (Simulating S3 partitioning)
            # We use the current date for partitioning in this simulation
            now = datetime.now()
            partition_path = os.path.join(
                LANDING_DIR, 
                f"year={now.year}", 
                f"month={now.month:02d}", 
                f"day={now.day:02d}"
            )
            
            if not os.path.exists(partition_path):
                os.makedirs(partition_path)
            
            dest_file = os.path.join(partition_path, os.path.basename(file_path))
            
            # Save as CSV in landing zone
            df.to_csv(dest_file, index=False)
            print(f"[+] [Lambda Ingest] Processed and moved to: {dest_file}")
            
            # Optionally remove source file to simulate "ingestion"
            # os.remove(file_path)

        except Exception as e:
            print(f"[x] Error processing {file_path}: {e}")

def run_manual_ingest():
    """Process existing files in the source directory."""
    handler = IngestionHandler()
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith('.txt'):
                handler.process_file(os.path.join(root, file))

if __name__ == "__main__":
    if not os.path.exists(LANDING_DIR):
        os.makedirs(LANDING_DIR)
        
    print("[*] Starting Lambda-style Ingestion Service...")
    
    # Run manual ingest first to catch existing files
    print("[*] Processing existing files...")
    run_manual_ingest()
    
    # Start watching for new files
    # event_handler = IngestionHandler()
    # observer = Observer()
    # observer.schedule(event_handler, SOURCE_DIR, recursive=True)
    # observer.start()
    
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     observer.stop()
    # observer.join()
