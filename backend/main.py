from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import json
from datetime import datetime
import sys

# Add root directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.athena_engine import AthenaEngine
from pipelines.step_functions_orchestrator import StepFunctionsOrchestrator

app = FastAPI(title="PulseOps Intelligent Backend")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INGESTION_TEMP = "data_lake/ingestion_temp"
STATUS_FILE = "data_lake/pipeline_status.json"

@app.get("/")
def read_root():
    return {"message": "PulseOps V2 API is operational"}

@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not os.path.exists(INGESTION_TEMP):
        os.makedirs(INGESTION_TEMP)
        
    file_path = os.path.join(INGESTION_TEMP, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Trigger orchestrator in the background
    background_tasks.add_task(run_pipeline)
    
    return {"filename": file.filename, "status": "Uploaded. Pipeline triggered."}

@app.post("/ingest/nasa-auto")
async def ingest_nasa_auto(background_tasks: BackgroundTasks):
    """Automatically ingest NASA data from the local archive/temp."""
    source = "data_lake/ingestion_temp/4. Bearings"
    if not os.path.exists(source):
        # Fallback to ingestion_temp root
        source = "data_lake/ingestion_temp"
        
    # Trigger orchestrator
    background_tasks.add_task(run_pipeline)
    return {"status": "NASA Auto-Ingestion triggered."}

def run_pipeline():
    orchestrator = StepFunctionsOrchestrator()
    orchestrator.run_state_machine()

@app.get("/status")
def get_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {"state": "IDLE", "logs": []}

@app.get("/analytics/summary")
def get_summary():
    try:
        engine = AthenaEngine()
        df = engine.get_summary_stats()
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

@app.get("/analytics/anomalies")
def get_anomalies(bearing_id: str = None):
    try:
        engine = AthenaEngine()
        df = engine.get_anomalies(bearing_id)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

@app.get("/analytics/features")
def get_features(bearing_id: str = None):
    try:
        engine = AthenaEngine()
        sql = "SELECT * FROM bearing_features"
        if bearing_id:
            sql += f" WHERE bearing_id = '{bearing_id}'"
        sql += " ORDER BY bearing_id"
        df = engine.query(sql)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
