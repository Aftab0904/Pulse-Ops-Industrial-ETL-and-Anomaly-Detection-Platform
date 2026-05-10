import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2, Info, ChevronRight, Download } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE_URL = 'http://localhost:5000';

function App() {
  const [inspectionFile, setInspectionFile] = useState(null);
  const [thermalFile, setThermalFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async () => {
    if (!inspectionFile || !thermalFile) {
      setError('Please select both reports.');
      return;
    }

    setLoading(true);
    setError(null);
    setReport(null);

    const formData = new FormData();
    formData.append('inspectionReport', inspectionFile);
    formData.append('thermalReport', thermalFile);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate-ddr`, formData);
      setReport(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred during report generation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <header className="max-w-6xl mx-auto mb-12 text-center">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">Applied AI Builder</h1>
        <p className="text-slate-600">Detailed Diagnostic Report (DDR) Generator</p>
      </header>

      <main className="max-w-6xl mx-auto">
        {!report ? (
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              {/* Inspection Report Upload */}
              <div className="space-y-4">
                <label className="block text-sm font-semibold text-slate-700 uppercase tracking-wider">
                  1. Site Inspection Report
                </label>
                <div 
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                    inspectionFile ? 'border-emerald-500 bg-emerald-50' : 'border-slate-300 hover:border-indigo-500'
                  }`}
                >
                  <input 
                    type="file" 
                    id="inspection" 
                    className="hidden" 
                    accept="application/pdf"
                    onChange={(e) => setInspectionFile(e.target.files[0])}
                  />
                  <label htmlFor="inspection" className="cursor-pointer">
                    {inspectionFile ? (
                      <div className="flex flex-col items-center text-emerald-600">
                        <CheckCircle2 size={48} className="mb-2" />
                        <span className="font-medium">{inspectionFile.name}</span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center text-slate-500">
                        <Upload size={48} className="mb-2" />
                        <span className="font-medium">Upload Inspection PDF</span>
                      </div>
                    )}
                  </label>
                </div>
              </div>

              {/* Thermal Report Upload */}
              <div className="space-y-4">
                <label className="block text-sm font-semibold text-slate-700 uppercase tracking-wider">
                  2. Thermal Images Document
                </label>
                <div 
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                    thermalFile ? 'border-emerald-500 bg-emerald-50' : 'border-slate-300 hover:border-indigo-500'
                  }`}
                >
                  <input 
                    type="file" 
                    id="thermal" 
                    className="hidden" 
                    accept="application/pdf"
                    onChange={(e) => setThermalFile(e.target.files[0])}
                  />
                  <label htmlFor="thermal" className="cursor-pointer">
                    {thermalFile ? (
                      <div className="flex flex-col items-center text-emerald-600">
                        <CheckCircle2 size={48} className="mb-2" />
                        <span className="font-medium">{thermalFile.name}</span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center text-slate-500">
                        <Upload size={48} className="mb-2" />
                        <span className="font-medium">Upload Thermal PDF</span>
                      </div>
                    )}
                  </label>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg flex items-center gap-3 mb-6">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={loading || !inspectionFile || !thermalFile}
              className={`w-full py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-3 ${
                loading 
                  ? 'bg-slate-200 text-slate-500 cursor-not-allowed' 
                  : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-200'
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" />
                  Analyzing Reports...
                </>
              ) : (
                <>
                  <FileText />
                  Generate DDR Report
                </>
              )}
            </button>
          </div>
        ) : (
          <ReportView data={report} onReset={() => setReport(null)} />
        )}
      </main>
    </div>
  );
}

function ReportView({ data, onReset }) {
  const [selectedImage, setSelectedImage] = useState(null);

  const getSeverityColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'bg-rose-100 text-rose-700 border-rose-200';
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'low': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8 pb-20"
    >
      <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Generated DDR</h2>
          <p className="text-slate-500">Diagnostic Summary & Actions</p>
        </div>
        <button 
          onClick={onReset}
          className="px-6 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
        >
          New Analysis
        </button>
      </div>

      {/* Property Issue Summary */}
      <section className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Info className="text-indigo-600" size={20} />
          Property Issue Summary
        </h3>
        <p className="text-slate-700 leading-relaxed">
          {data.propertyIssueSummary}
        </p>
      </section>

      {/* Area-wise Observations */}
      <section className="space-y-6">
        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <ChevronRight className="text-indigo-600" size={20} />
          Area-wise Observations
        </h3>
        <div className="grid grid-cols-1 gap-6">
          {data.areaWiseObservations.map((obs, idx) => (
            <div key={idx} className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col md:flex-row">
              <div className="p-6 flex-1">
                <div className="flex justify-between items-start mb-4">
                  <h4 className="font-bold text-indigo-700 text-lg">{obs.area}</h4>
                </div>
                <div className="space-y-4">
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-tighter">Findings</span>
                    <p className="text-slate-700">{obs.findings}</p>
                  </div>
                  {obs.thermalData && obs.thermalData !== "Not Available" && (
                    <div className="bg-orange-50 p-4 rounded-xl border border-orange-100">
                      <span className="text-xs font-bold text-orange-400 uppercase tracking-tighter">Thermal Data</span>
                      <p className="text-orange-900 text-sm">{obs.thermalData}</p>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Image Rendering */}
              {obs.imageRef && obs.imageRef.pageNumber ? (
                <div className="w-full md:w-64 bg-slate-100 p-4 flex flex-col items-center justify-center border-l border-slate-100">
                  <div className="text-xs text-slate-400 mb-2 uppercase font-bold">
                    Ref: {obs.imageRef.reportType} Report (Pg {obs.imageRef.pageNumber})
                  </div>
                  <div className="w-full aspect-[4/3] bg-white rounded shadow-inner overflow-hidden flex items-center justify-center cursor-pointer hover:ring-2 hover:ring-indigo-500 transition-all">
                     <img 
                        src={`${API_BASE_URL}/images/${data.sessionId}_${obs.imageRef.reportType === 'inspection' ? 'ins' : 'thr'}_page_${obs.imageRef.pageNumber}.jpg`}
                        alt={`Observation from ${obs.area}`}
                        className="w-full h-full object-contain"
                     />
                  </div>
                  <p className="text-[10px] text-slate-500 mt-2 text-center italic">{obs.imageRef.description}</p>
                </div>
              ) : (
                <div className="w-full md:w-64 bg-slate-50 p-4 flex items-center justify-center border-l border-slate-100 text-slate-300 text-xs italic">
                  Image Not Available
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Severity */}
        <section className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Severity Assessment</h3>
          <div className={`inline-flex px-4 py-1 rounded-full text-sm font-bold border mb-4 ${getSeverityColor(data.severityAssessment.level)}`}>
            {data.severityAssessment.level} Severity
          </div>
          <p className="text-slate-700 text-sm">{data.severityAssessment.reasoning}</p>
        </section>

        {/* Root Cause */}
        <section className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Probable Root Cause</h3>
          <p className="text-slate-700 text-sm leading-relaxed">{data.probableRootCause}</p>
        </section>
      </div>

      {/* Recommendations */}
      <section className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h3 className="text-lg font-bold text-slate-900 mb-4">Recommended Actions</h3>
        <ul className="space-y-3">
          {data.recommendedActions.map((action, i) => (
            <li key={i} className="flex gap-3 text-slate-700 text-sm">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center text-xs font-bold">
                {i + 1}
              </span>
              {action}
            </li>
          ))}
        </ul>
      </section>

      {/* Missing Info */}
      {data.missingOrUnclearInformation && data.missingOrUnclearInformation !== "Not Available" && (
         <section className="bg-rose-50 p-8 rounded-2xl shadow-sm border border-rose-100">
            <h3 className="text-lg font-bold text-rose-900 mb-4">Missing or Unclear Information</h3>
            <p className="text-rose-800 text-sm italic">{data.missingOrUnclearInformation}</p>
         </section>
      )}

      {/* Footer Notes */}
      <footer className="text-center text-slate-400 text-xs pb-10">
        Generated by Applied AI Builder • {new Date().toLocaleDateString()}
      </footer>
    </motion.div>
  );
}

export default App;
