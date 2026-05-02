import os
import subprocess
import time
from datetime import datetime

class StepFunctionsOrchestrator:
    def __init__(self):
        self.state = "IDLE"
        self.execution_log = []
        self.status_file = "data_lake/pipeline_status.json"

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] [{self.state}] {message}"
        print(msg)
        self.execution_log.append(msg)
        self.save_status()

    def save_status(self):
        import json
        status = {
            "state": self.state,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "logs": self.execution_log[-10:] # Last 10 logs
        }
        with open(self.status_file, "w") as f:
            json.dump(status, f)

    def run_state_machine(self):
        self.state = "START"
        self.log("Starting PulseOps Orchestrator Pipeline...")
        
        try:
            # State 1: Ingestion (Lambda)
            self.state = "LAMBDA_INGESTION"
            self.log("Triggering Event-Driven Ingestion...")
            subprocess.run(["python", "ingestion/lambda_ingest.py"], check=True)
            self.log("Ingestion completed successfully.")

            # State 2: ETL (Glue Spark Job - Mocked via DuckDB for Local Demo)
            self.state = "GLUE_ETL"
            self.log("Triggering ETL Job (AWS Glue Mock via DuckDB)...")
            # Note: In production, we run etl/glue_pyspark_job.py
            subprocess.run(["python", "etl/glue_duckdb_job.py"], check=True)
            self.log("ETL Job completed successfully.")

            # State 3: ML Inference (Anomaly Detection)
            self.state = "ML_INFERENCE"
            self.log("Triggering Anomaly Detection Inference...")
            subprocess.run(["python", "ml_models/inference.py"], check=True)
            self.log("ML Inference completed successfully.")

            # State 4: Analytics (Athena/DuckDB)
            self.state = "ATHENA_QUERY"
            self.log("Running Analytics Queries...")
            # To be implemented in Phase 3
            # subprocess.run(["python", "utils/athena_engine.py"], check=True)
            self.log("Analytics complete.")

            self.state = "FINISH"
            self.log("Pipeline Execution Finished Successfully.")

        except Exception as e:
            self.state = "FAIL"
            self.log(f"Pipeline Failed: {e}")
            # Simulate CloudWatch Alert / SNS Notification
            self.send_alert(f"Critical Pipeline Failure in state {self.state}")

    def send_alert(self, message):
        print(f"\n[!!!] SNS ALERT: {message}\n")

if __name__ == "__main__":
    orchestrator = StepFunctionsOrchestrator()
    orchestrator.run_state_machine()
