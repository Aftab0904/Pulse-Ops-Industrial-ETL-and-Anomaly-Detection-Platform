const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
require('dotenv').config();
const { GoogleGenerativeAI } = require('@google/generative-ai');

const app = express();
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + file.originalname);
  },
});

const upload = multer({ storage });

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);

// Helper function to convert file to GoogleGenerativeAI.Part
function fileToGenerativePart(path, mimeType) {
  return {
    inlineData: {
      data: Buffer.from(fs.readFileSync(path)).toString('base64'),
      mimeType,
    },
  };
}

const SYSTEM_PROMPT = `
You are a professional Technical Diagnostic Engineer specializing in building inspections and thermal analysis.
Your task is to generate a Detailed Diagnostic Report (DDR) by analyzing two provided documents: 
1. An Inspection Report (site observations and issue descriptions)
2. A Thermal Report (temperature readings and thermal images)

Your goal is to extract relevant observations, combine information logically, avoid duplicates, handle missing/conflicting details, and present a client-friendly report.

STRUCTURE YOUR OUTPUT AS A JSON OBJECT WITH THE FOLLOWING KEYS:
1. propertyIssueSummary: A high-level overview of the issues found.
2. areaWiseObservations: An array of objects, each containing:
    - area: The location name.
    - findings: A description of what was observed.
    - thermalData: Associated temperature readings or thermal findings from the thermal report.
    - imageRef: An object with { reportType: 'inspection'|'thermal', pageNumber: number, description: string } identifying the most relevant image for this observation.
3. probableRootCause: A logical deduction of why these issues are occurring.
4. severityAssessment: 
    - level: "High", "Medium", or "Low".
    - reasoning: Detailed explanation for the assigned severity.
5. recommendedActions: A list of clear, actionable steps for the client.
6. additionalNotes: Any other relevant information.
7. missingOrUnclearInformation: Explicitly mention "Not Available" for specific data points if they are missing or if there are conflicts.

GUIDELINES:
- Do NOT invent facts.
- If information conflicts, mention the conflict.
- If information is missing, use "Not Available".
- Use simple, client-friendly language.
- Ensure images (referenced by page number) support the findings.
- Generalize your logic so it works on any similar inspection data.
`;

app.post('/api/generate-ddr', upload.fields([
  { name: 'inspectionReport', maxCount: 1 },
  { name: 'thermalReport', maxCount: 1 }
]), async (req, res) => {
  try {
    const inspectionFile = req.files['inspectionReport'][0];
    const thermalFile = req.files['thermalReport'][0];

    if (!inspectionFile || !thermalFile) {
      return res.status(400).json({ error: 'Both Inspection and Thermal reports are required.' });
    }

    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' }, { apiVersion: 'v1' });

    const prompt = "Please analyze the attached Inspection Report and Thermal Report and generate the Detailed Diagnostic Report (DDR) JSON as per the system instructions.";

    const result = await model.generateContent([
      SYSTEM_PROMPT,
      prompt,
      fileToGenerativePart(inspectionFile.path, 'application/pdf'),
      fileToGenerativePart(thermalFile.path, 'application/pdf'),
    ]);

    const response = await result.response;
    let text = response.text();
    
    // Clean JSON response if it's wrapped in markdown code blocks
    text = text.replace(/```json/g, '').replace(/```/g, '').trim();
    
    const ddrData = JSON.parse(text);

    // Add file paths to the response so the frontend can display them
    ddrData.files = {
      inspectionReport: inspectionFile.filename,
      thermalReport: thermalFile.filename
    };

    res.json(ddrData);
  } catch (error) {
    console.error('Error generating DDR:', error);
    res.status(500).json({ error: 'Failed to generate report. ' + error.message });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
