# Applied AI Builder - DDR Report Generator

This project is a technical tool that automates the creation of Detailed Diagnostic Reports (DDR). It takes raw data from two different sources—a site inspection report and a thermal imaging document—and merges them into a single, professional report for clients.

## Visual Demo & Workflow

The system follows a specific logical path to handle the documents:

1. Ingestion: The user uploads two PDF files.
2. Processing: The system reads these files either as raw multimodal data (Node.js version) or by converting every page into a high-resolution image (Python version).
3. Extraction: The AI identifies site observations from the first document and temperature anomalies from the second.
4. Reasoning: The core of the project is where the AI matches these two datasets. For example, it looks for a site observation about a damp wall and searches the thermal report for a corresponding cold spot.
5. Assessment: The AI then determines the severity of the issue and suggests a root cause and recommended actions.
6. Formatting: The final output is structured as a clean JSON object that the frontend renders into a professional dashboard.

## Core AI Logic

The project uses two different approaches to solve the problem of merging disconnected data.

### 1. Multimodal Reasoning (Node.js Backend)
In the file backend/index.js, the system uses the Gemini 1.5 Flash model. The logic here is built around a SYSTEM_PROMPT that instructs the AI to act as a Technical Diagnostic Engineer. 

Instead of just summarizing text, the AI is told to look at both documents simultaneously. It treats the PDFs as direct inputs, allowing the model to see images and text at the same time. This prevents the loss of context that usually happens when you convert a PDF to plain text. The prompt forces the AI to handle conflicts (e.g., if the reports disagree) and explicitly state "Not Available" if data or images are missing, ensuring the report is honest and reliable.

### 2. Vision-Based Extraction (Python Backend)
In the file backend_python/main.py, the system uses a more granular multi-stage workflow:

- Vision Stage: It uses llama-3.2-90b-vision-preview to look at each page of the reports as an image. This is necessary because technical reports often have data inside tables or text next to specific photos that traditional text-extractors fail to read correctly.
- Extraction Stage: The vision model extracts specific findings and thermal anomalies into two separate lists.
- Merging Stage: A second model (llama-3.3-70b-versatile) takes these two lists and performs a logical join. It uses reasoning to determine which thermal anomaly belongs to which site observation based on the location and description.

## Code Logic and Key Files

The following files contain the primary logic for the system:

- backend/index.js: Contains the multimodal prompt logic. It handles the direct upload to Gemini and the cleaning of the JSON response. The SYSTEM_PROMPT here is the most important part, as it defines the rules for how the AI should reason about the severity and root causes.
- backend_python/main.py: Contains the image processing pipeline. It uses PyMuPDF (fitz) to convert PDFs to JPEGs and manages the two-stage AI call (Vision for extraction, Text for merging).
- frontend/src/App.jsx: Manages the report presentation. It takes the complex JSON output from the AI and maps it to specific UI components, including the logic to display evidence images based on page numbers extracted by the AI.

## Handling Imperfect Data

One of the main goals of this system is to handle real-world reports that might be incomplete. The AI is programmed with strict rules:

- No Hallucination: If the documents do not mention a cause, the AI is not allowed to invent one.
- Explicit Missing Data: If a thermal reading is expected but not found for a specific area, the report will explicitly state "Not Available" in that section.
- Evidence Linking: Every finding is linked to a specific page number in the original report to provide a clear audit trail for the client.

## Setup Instructions

### Backend Setup
cd backend
npm install
node index.js
(Note: Add your GOOGLE_API_KEY to the .env file)

### Frontend Setup
cd frontend
npm install
npm run dev
