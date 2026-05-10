import os
import fitz  # PyMuPDF
import json
import base64
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from groq import Groq
from dotenv import load_dotenv
import uuid
import time

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
UPLOAD_DIR = "uploads"
EXTRACT_DIR = "extracted_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)

app.mount("/images", StaticFiles(directory=EXTRACT_DIR), name="images")

@app.get("/")
async def root():
    return {"status": "online", "message": "Applied AI Builder API (Groq Vision Edition) is running"}

# Configure Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def pdf_to_images(pdf_path, output_folder, prefix):
    doc = fitz.open(pdf_path)
    image_paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # High res
        img_name = f"{prefix}_page_{i+1}.jpg"
        img_path = os.path.join(output_folder, img_name)
        pix.save(img_path)
        image_paths.append(img_path)
    return image_paths

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def call_groq_with_retry(model_name, messages, response_format=None):
    max_retries = 3
    for i in range(max_retries):
        try:
            params = {
                "model": model_name,
                "messages": messages,
            }
            if response_format:
                params["response_format"] = response_format
            
            completion = client.chat.completions.create(**params)
            return completion.choices[0].message.content
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "rate limit" in err_str or "503" in err_str:
                wait_time = (i + 1) * 5
                print(f"Groq Rate Limit/Busy. Retry {i+1} in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise e
    raise Exception("Groq failed after multiple retries.")

@app.post("/api/generate-ddr")
async def generate_ddr(
    inspectionReport: UploadFile = File(...),
    thermalReport: UploadFile = File(...)
):
    session_id = str(uuid.uuid4())
    
    # Save files
    ins_path = os.path.join(UPLOAD_DIR, f"{session_id}_ins.pdf")
    thr_path = os.path.join(UPLOAD_DIR, f"{session_id}_thr.pdf")
    
    with open(ins_path, "wb") as f:
        f.write(await inspectionReport.read())
    with open(thr_path, "wb") as f:
        f.write(await thermalReport.read())

    # Stage 1: Convert PDFs to Images
    ins_images = pdf_to_images(ins_path, EXTRACT_DIR, f"{session_id}_ins")
    thr_images = pdf_to_images(thr_path, EXTRACT_DIR, f"{session_id}_thr")

    # Stage 2: Analysis with Groq (Updated Models)
    VISION_MODEL = "llama-3.2-90b-vision-preview" 
    TEXT_MODEL = "llama-3.3-70b-versatile" 

    try:
        print(f"Analyzing with Groq...")

        # Analyze Inspection
        print("-> Analyzing Inspection Report (Vision)...")
        ins_content = [{"type": "text", "text": "Analyze these inspection report pages. Extract issues into a JSON list: [{\"area\": \"Location\", \"findings\": \"Observation\", \"page_number\": number}]. Output ONLY raw JSON."}]
        for path in ins_images[:10]: # Limit to first 10 pages for free tier safety
            base64_image = encode_image(path)
            ins_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        
        ins_data_raw = await call_groq_with_retry(VISION_MODEL, [{"role": "user", "content": ins_content}])
        
        # Analyze Thermal
        print("-> Analyzing Thermal Report (Vision)...")
        thr_content = [{"type": "text", "text": "Analyze these thermal report pages. Extract anomalies into a JSON list: [{\"area\": \"Location\", \"thermalData\": \"Anomalies\", \"page_number\": number}]. Output ONLY raw JSON."}]
        for path in thr_images[:10]:
            base64_image = encode_image(path)
            thr_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        
        thr_data_raw = await call_groq_with_retry(VISION_MODEL, [{"role": "user", "content": thr_content}])

        # Merge Data
        print("-> Merging data...")
        merge_prompt = f"""
        Merge these two datasets into a single Detailed Diagnostic Report (DDR) JSON object.
        
        Inspection Data: {ins_data_raw}
        Thermal Data: {thr_data_raw}
        
        Output MUST be a JSON object with:
        - propertyIssueSummary: Overall Summary
        - areaWiseObservations: List of {{area, findings, thermalData, imageRef: {{reportType: 'inspection'|'thermal', pageNumber}}}}
        - probableRootCause: Reasoning
        - severityAssessment: {{level: "High"|"Medium"|"Low", reasoning: string}}
        - recommendedActions: List of strings
        """
        
        final_json_str = await call_groq_with_retry(
            TEXT_MODEL, 
            [{"role": "user", "content": merge_prompt}],
            response_format={"type": "json_object"}
        )
        
        report_data = json.loads(final_json_str)
        report_data["sessionId"] = session_id
        
        print("Success! Report generated via Groq.")
        return report_data

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
