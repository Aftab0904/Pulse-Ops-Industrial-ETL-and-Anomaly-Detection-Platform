import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import pyarrow.parquet as pq
import glob

FEATURE_STORE_PATH = "data_lake/feature_store"
MODEL_OUTPUT_PATH = "data_lake/model_output"

def run_inference():
    print("[*] [ML Inference] Starting Anomaly Detection (Isolation Forest)...")
    
    # 1. Load data from Feature Store (Parquet)
    # Using glob to find all parquet files in partitions
    parquet_files = glob.glob(f"{FEATURE_STORE_PATH}/**/*.parquet", recursive=True)
    
    if not parquet_files:
        print("[!] No feature data found. Skipping inference.")
        return

    # Read all partitioned parquet files into a single DataFrame
    df_list = [pd.read_parquet(f) for f in parquet_files]
    df = pd.concat(df_list, ignore_index=True)
    
    # 2. Preprocessing
    # Features for the model: rms, std, mean
    X = df[['rms', 'std', 'mean']].values
    
    # 3. Model Logic (Isolation Forest)
    # contamination=0.05 assumes 5% of data points are anomalies
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    df['anomaly_score'] = model.fit_predict(X)
    
    # Convert scores: -1 (anomaly) -> 1, 1 (normal) -> 0
    df['is_anomaly'] = df['anomaly_score'].apply(lambda x: 1 if x == -1 else 0)
    
    # 4. Save results to Model Output layer
    if not os.path.exists(MODEL_OUTPUT_PATH):
        os.makedirs(MODEL_OUTPUT_PATH)
        
    output_file = os.path.join(MODEL_OUTPUT_PATH, "anomaly_predictions.parquet")
    df.to_parquet(output_file, index=False)
    
    print(f"[+] [ML Inference] Anomaly detection complete. Results saved to {output_file}")

if __name__ == "__main__":
    run_inference()
