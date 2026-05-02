import os
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
LANDING_PATH = "data_lake/landing"
FEATURE_STORE_PATH = "data_lake/feature_store"

def process_etl_duckdb():
    print("[*] [Glue ETL - DuckDB] Starting Lightweight ETL Job...")
    
    # Initialize DuckDB
    con = duckdb.connect(database=':memory:')
    
    # 1. Read all CSV files from Landing Zone
    csv_pattern = os.path.join(LANDING_PATH, "year=*", "month=*", "day=*", "*.txt")
    
    try:
        # Load data using DuckDB's fast CSV reader
        df = con.execute(f"""
            SELECT *, regexp_extract(filename, '([^\\\\/]+)$', 1) as file_id
            FROM read_csv_auto('{csv_pattern}', filename=True, header=True)
        """).df()
        
        print(f"[+] Loaded {len(df)} rows from landing zone.")

        # 2. Feature Engineering
        # We need to calculate RMS, Mean, Std per file_id for each bearing (cols 0, 1, 2, 3)
        features_list = []
        
        for i in range(4):
            col_name = str(i)
            bearing_id = f"bearing_{i+1}"
            
            # Group by filename and calculate features
            bearing_features = con.execute(f"""
                SELECT 
                    filename as file_path,
                    '{bearing_id}' as bearing_id,
                    AVG("{col_name}") as mean,
                    STDDEV("{col_name}") as std,
                    SQRT(AVG(POWER("{col_name}", 2))) as rms
                FROM read_csv_auto('{csv_pattern}', filename=True, header=True)
                GROUP BY filename
            """).df()
            
            features_list.append(bearing_features)
        
        final_features_df = pd.concat(features_list)
        
        # 3. Save to Feature Store as Parquet
        if not os.path.exists(FEATURE_STORE_PATH):
            os.makedirs(FEATURE_STORE_PATH)
            
        # For simplicity in this demo, we save as a single parquet or partitioned manually
        for b_id in final_features_df['bearing_id'].unique():
            b_path = os.path.join(FEATURE_STORE_PATH, f"bearing_id={b_id}")
            if not os.path.exists(b_path):
                os.makedirs(b_path)
            
            b_df = final_features_df[final_features_df['bearing_id'] == b_id]
            b_df.to_parquet(os.path.join(b_path, "features.parquet"))

        print(f"[+] [Glue ETL] Successfully wrote features to {FEATURE_STORE_PATH}")
        
    except Exception as e:
        print(f"[x] ETL Job Failed: {e}")

if __name__ == "__main__":
    process_etl_duckdb()
