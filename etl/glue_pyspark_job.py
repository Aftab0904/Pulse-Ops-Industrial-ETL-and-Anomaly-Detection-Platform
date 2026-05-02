import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, input_file_name, regexp_extract, lit, mean, stddev, sqrt, pow
from pyspark.sql.types import DoubleType, StructType, StructField, StringType, TimestampType
from datetime import datetime
import pandas as pd
from scipy.stats import kurtosis, skew

# Initialize Spark Session (Simulating AWS Glue Spark Context)
spark = SparkSession.builder \
    .appName("PulseOps-Glue-ETL") \
    .config("spark.sql.parquet.compression.codec", "snappy") \
    .getOrCreate()

# Schema for NASA Bearing Data (4 columns for the most common experiments)
schema = StructType([
    StructField("b1", DoubleType(), True),
    StructField("b2", DoubleType(), True),
    StructField("b3", DoubleType(), True),
    StructField("b4", DoubleType(), True)
])

LANDING_PATH = "data_lake/landing/year=*/month=*/day=*"
FEATURE_STORE_PATH = "data_lake/feature_store"

def extract_timestamp_from_path(path):
    # Extract filename from path (e.g., 2003.10.22.12.06.24)
    filename = os.path.basename(path)
    try:
        dt = datetime.strptime(filename, "%Y.%m.%d.%H.%M.%S")
        return dt
    except:
        return None

# Register UDFs for Kurtosis and Skewness (using Pandas UDF for efficiency)
@udf(returnType=DoubleType())
def calculate_kurtosis(values):
    return float(kurtosis(values))

@udf(returnType=DoubleType())
def calculate_skewness(values):
    return float(skew(values))

def process_etl():
    print("[*] [Glue ETL] Starting PySpark Job...")
    
    # 1. Read Landing Data
    df = spark.read.option("header", "true").csv(LANDING_PATH)
    
    # Add metadata: filename and timestamp
    df = df.withColumn("file_path", input_file_name())
    
    # Convert string columns to double (they might be strings if there are nulls)
    for c in ["0", "1", "2", "3"]: # In landing, columns were saved without headers by lambda
        df = df.withColumn(c, col(c).cast(DoubleType()))

    # 2. Data Cleaning (Forward Fill / Mean Imputation)
    # For industrial data, we often fill nulls with mean or previous value
    # df = df.fillna(0.0) # Simple fill for now
    
    # 3. Feature Engineering (Aggregations per file/timestamp)
    # Each file represents a 1-second snapshot. We aggregate features for each bearing.
    
    feature_dfs = []
    
    for i in range(4):
        col_name = str(i)
        bearing_id = f"bearing_{i+1}"
        
        bearing_features = df.groupBy("file_path").agg(
            mean(col(col_name)).alias("mean"),
            stddev(col(col_name)).alias("std"),
            sqrt(mean(pow(col(col_name), 2))).alias("rms"),
            # We can't easily do Kurtosis/Skew in standard Spark without complex UDFs or Window
            # So we stick to these for the Spark part or use a trick
        ).withColumn("bearing_id", lit(bearing_id))
        
        feature_dfs.append(bearing_features)
    
    # Union all bearing features
    final_features_df = feature_dfs[0]
    for i in range(1, 4):
        final_features_df = final_features_df.union(feature_dfs[i])
    
    # 4. Save to Feature Store (Parquet Partitioned)
    print(f"[*] [Glue ETL] Writing to Feature Store: {FEATURE_STORE_PATH}")
    
    final_features_df.write.mode("overwrite").partitionBy("bearing_id").parquet(FEATURE_STORE_PATH)
    
    print("[+] [Glue ETL] Job Completed Successfully.")

if __name__ == "__main__":
    process_etl()
    spark.stop()
