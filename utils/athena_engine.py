import duckdb
import os

class AthenaEngine:
    def __init__(self, feature_store_path="data_lake/feature_store", model_output_path="data_lake/model_output"):
        self.feature_store_path = feature_store_path
        self.model_output_path = model_output_path
        # Use a persistent file or shared memory for the backend
        self.db_path = "data_lake/pulseops_analytics.db"
        self.conn = duckdb.connect(database=self.db_path)
        self.create_view()
        
    def create_view(self):
        """Simulates creating an external table in Athena over S3 Parquet."""
        parquet_path = os.path.join(self.feature_store_path, "*/*.parquet")
        model_path = os.path.join(self.model_output_path, "*.parquet")
        try:
            self.conn.execute(f"CREATE OR REPLACE VIEW bearing_features AS SELECT * FROM read_parquet('{parquet_path}')")
            print(f"[*] [Athena Engine] View 'bearing_features' created successfully.")
            
            if os.path.exists(self.model_output_path):
                self.conn.execute(f"CREATE OR REPLACE VIEW anomaly_results AS SELECT * FROM read_parquet('{model_path}')")
                print(f"[*] [Athena Engine] View 'anomaly_results' created successfully.")
        except Exception as e:
            print(f"[x] Error creating Athena view: {e}")

    def query(self, sql):
        """Execute SQL query and return results as a Pandas DataFrame."""
        print(f"[*] [Athena Engine] Executing Query: {sql}")
        return self.conn.execute(sql).fetchdf()

    def get_anomalies(self, bearing_id=None):
        """Fetch anomaly detection results."""
        sql = "SELECT * FROM anomaly_results"
        if bearing_id:
            sql += f" WHERE bearing_id = '{bearing_id}'"
        return self.query(sql)

    def get_summary_stats(self):
        """Example analytical query."""
        sql = """
        SELECT 
            bearing_id, 
            AVG(rms) as avg_rms, 
            MAX(rms) as max_rms, 
            STDDEV(rms) as std_rms 
        FROM bearing_features 
        GROUP BY bearing_id
        """
        return self.query(sql)

if __name__ == "__main__":
    # Test Athena Engine
    engine = AthenaEngine()
    engine.create_view()
    
    # Try a sample query if data exists
    if os.path.exists("data_lake/feature_store"):
        stats = engine.get_summary_stats()
        print(stats)
    else:
        print("[!] Feature store not found. Run the ETL job first.")
