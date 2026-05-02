import pandas as pd
import numpy as np
import os
from datetime import datetime

def generate_mock_data():
    print("[*] Generating Mock Industrial Sensor Data...")
    landing_dir = "data_lake/landing"
    now = datetime.now()
    partition_path = os.path.join(landing_dir, f"year={now.year}", f"month={now.month:02d}", f"day={now.day:02d}")
    
    if not os.path.exists(partition_path):
        os.makedirs(partition_path)
    
    # Generate 10 mock sensor snapshots
    for i in range(10):
        # 4 columns for 4 bearings
        data = np.random.normal(0, 0.1, (1000, 4))
        # Add a slight trend to bearing 1 to simulate degradation
        data[:, 0] += (i * 0.05)
        
        df = pd.DataFrame(data)
        file_name = f"2026.05.01.12.00.{i:02d}.txt"
        df.to_csv(os.path.join(partition_path, file_name), index=False)
        print(f"[+] Generated: {file_name}")

if __name__ == "__main__":
    generate_mock_data()
