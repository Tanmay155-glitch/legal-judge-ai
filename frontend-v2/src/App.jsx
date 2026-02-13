import { useState } from 'react'
import axios from 'axios'
import { Upload, FileText, CheckCircle, Clock } from 'lucide-react'

function App() {
    const [file, setFile] = useState(null)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [steps, setSteps] = useState([])

    const handleFileChange = (e) => {
        if (e.target.files) {
            setFile(e.target.files[0])
        }
    }

    const handleAnalyze = async () => {
        if (!file) return

        setLoading(true)
        setResult(null)
        setSteps([
            { name: "Uploading PDF", status: "processing" },
            { name: "Running OCR Extraction", status: "pending" },
            { name: "Searching 10,000+ Cases (Vector DB)", status: "pending" },
            { name: "Predicting Outcome (Burn ML)", status: "pending" },
            { name: "Generating Opinion", status: "pending" }
        ])

        const formData = new FormData()
        formData.append('file', file)

        // Simulate step progress for demo effect (since backend is fast/mocked for now)
        const updateStep = (index, status) => {
            setSteps(prev => prev.map((s, i) => i === index ? { ...s, status } : s))
            if (index + 1 < steps.length && status === 'completed') {
                setSteps(prev => prev.map((s, i) => i === index + 1 ? { ...s, status: 'processing' } : s))
            }
        }

        try {
            // Step 1: Upload & OCR
            updateStep(0, 'completed')
            updateStep(1, 'processing')

            const response = await axios.post('http://localhost:8080/api/analyze-brief', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })

            // Simulate the rest of the pipeline visualization
            setTimeout(() => updateStep(1, 'completed'), 1000)
            setTimeout(() => updateStep(2, 'completed'), 2000)
            setTimeout(() => updateStep(3, 'completed'), 3000)
            setTimeout(() => {
                updateStep(4, 'completed')
                setResult(response.data)
                setLoading(false)
            }, 4000)

        } catch (error) {
            console.error("Analysis failed:", error)
            setSteps(prev => prev.map(s => s.status === 'processing' ? { ...s, status: 'error' } : s))
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen pb-12">
            <div className="max-w-5xl mx-auto px-6 py-8">

                {/* Header */}
                <header className="mb-12 pb-6 border-b border-green-200">
                    <h1 className="text-4xl font-serif font-bold text-green-900 mb-2">
                        Legal Judge AI <span className="text-sm font-sans font-normal text-green-600 bg-green-100 px-2 py-1 rounded ml-2">Phase 2 Demo</span>
                    </h1>
                    <p className="text-gray-600">
                        Automated brief analysis, outcome prediction, and opinion generation.
                    </p>
                </header>

                {/* Upload Section */}
                <div className="bg-white rounded-xl shadow-sm border border-green-100 p-8 mb-8">
                    <div className="flex flex-col items-center justify-center border-2 border-dashed border-green-200 rounded-lg p-10 bg-green-50/30">
                        <Upload className="w-12 h-12 text-green-600 mb-4" />
                        <h3 className="text-xl font-medium text-green-900 mb-2">Upload Legal Brief (PDF)</h3>
                        <p className="text-gray-500 mb-6 text-center max-w-md">
                            Drag and drop your PDF here, or click to browse. System will extract text, find precedents, and predict the ruling.
                        </p>
                        <input
                            type="file"
                            accept=".pdf"
                            onChange={handleFileChange}
                            className="hidden"
                            id="file-upload"
                        />
                        <label
                            htmlFor="file-upload"
                            className="px-6 py-3 bg-green-700 text-white rounded-lg font-medium hover:bg-green-800 transition-colors cursor-pointer"
                        >
                            {file ? file.name : "Select PDF File"}
                        </label>
                    </div>

                    {file && (
                        <div className="mt-6 flex justify-center">
                            <button
                                onClick={handleAnalyze}
                                disabled={loading}
                                className="px-8 py-3 bg-green-600 text-white rounded-lg font-bold shadow-lg shadow-green-600/20 hover:bg-green-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            >
                                {loading ? 'Analyzing Case...' : 'Analyze Brief & Predict Outcome'}
                            </button>
                        </div>
                    )}
                </div>

                {/* Processing Steps */}
                {loading && (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
                        <h3 className="font-bold text-gray-900 mb-4">Analysis Pipeline</h3>
                        <div className="space-y-4">
                            {steps.map((step, idx) => (
                                <div key={idx} className="flex items-center gap-3">
                                    {step.status === 'completed' ? (
                                        <CheckCircle className="w-5 h-5 text-green-600" />
                                    ) : step.status === 'processing' ? (
                                        <div className="w-5 h-5 border-2 border-green-600 border-t-transparent rounded-full animate-spin" />
                                    ) : (
                                        <div className="w-5 h-5 border-2 border-gray-200 rounded-full" />
                                    )}
                                    <span className={`${step.status === 'completed' ? 'text-green-900 font-medium' : step.status === 'processing' ? 'text-green-700 font-bold' : 'text-gray-400'}`}>
                                        {step.name}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Results */}
                {result && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">

                        {/* Outcome Prediction */}
                        <div className="bg-white rounded-xl shadow-sm border border-green-200 p-8 overflow-hidden relative">
                            <div className="absolute top-0 left-0 w-2 h-full bg-green-600"></div>
                            <h2 className="text-2xl font-serif font-bold text-gray-900 mb-6">Predicted Outcome</h2>

                            <div className="flex items-center gap-8 mb-8">
                                <div className="text-5xl font-bold text-green-700 tracking-tight">
                                    {result.predicted_outcome.label.replace('_', ' ')}
                                </div>
                                <div className="flex-1">
                                    {Object.entries(result.predicted_outcome.probabilities).map(([label, prob]) => (
                                        <div key={label} className="mb-2">
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="font-medium text-gray-700">{label}</span>
                                                <span className="text-gray-500">{(prob * 100).toFixed(1)}%</span>
                                            </div>
                                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-green-600 transition-all duration-1000"
                                                    style={{ width: `${prob * 100}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Generated Opinion */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
                            <h2 className="text-2xl font-serif font-bold text-gray-900 mb-6 flex items-center gap-2">
                                <FileText className="w-6 h-6 text-green-700" />
                                Generated Judicial Opinion
                            </h2>
                            <div className="prose prose-green max-w-none text-gray-800 font-serif leading-relaxed bg-gray-50/50 p-6 rounded-lg border border-gray-100">
                                <p>{result.judge_opinion}</p>
                                <div className="mt-4 text-sm text-gray-500 font-sans italic border-t pt-4">
                                    * This opinion was generated by AI based on the provided brief and retrieved precedents.
                                </div>
                            </div>
                        </div>

                        {/* Top Precedents */}
                        <div>
                            <h2 className="text-2xl font-serif font-bold text-gray-900 mb-6">Cited Precedents (Vector Search)</h2>
                            <div className="grid gap-4">
                                {result.top_cases.map((item, idx) => (
                                    <div key={idx} className="bg-white p-6 rounded-lg border border-gray-200 hover:border-green-400 transition-colors shadow-sm">
                                        <div className="flex justify-between items-start mb-2">
                                            <h3 className="text-lg font-bold text-green-900">{item.case_name}</h3>
                                            <span className="bg-green-50 text-green-700 px-3 py-1 rounded-full text-xs font-medium border border-green-100">
                                                Match: {(item.relevance_score * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                        <p className="text-sm font-mono text-gray-500 mb-3">{item.citation}</p>
                                        <p className="text-gray-700 text-sm leading-relaxed border-l-2 border-green-200 pl-4">
                                            "{item.snippet}"
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* OCR Text Debug */}
                        <div className="mt-8 border-t pt-8">
                            <details className="cursor-pointer text-gray-500">
                                <summary className="text-sm font-medium hover:text-green-700">View Extracted OCR Text</summary>
                                <pre className="mt-4 p-4 bg-gray-900 text-gray-100 rounded text-xs overflow-auto max-h-60">
                                    {result.ocr_text}
                                </pre>
                            </details>
                        </div>

                    </div>
                )}

            </div>
        </div>
    )
}

export default App
