import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { uploadDataset } from "../api/clients"

export default function Upload() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handle = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const res = await uploadDataset(file)
      setResult(res.data)
      localStorage.setItem("fairlens_dataset", JSON.stringify(res.data))
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed")
    }
    setLoading(false)
  }

  return (
    <div style={{ maxWidth: 700, margin: "60px auto", padding: "0 24px" }}>
      <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>
        Upload Dataset
      </h1>
      <p style={{ color: "#8b92a5", marginBottom: 32 }}>
        Upload any CSV file. FairLens auto-detects protected attributes and target column.
      </p>

      <div style={{
        border: "2px dashed #2a2f45", borderRadius: 12,
        padding: "48px 32px", textAlign: "center", marginBottom: 24,
        background: file ? "#0d1f1a" : "#0d1117",
        transition: "all 0.2s"
      }}>
        <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])}
          style={{ display: "none" }} id="file-input" />
        <label htmlFor="file-input" style={{ cursor: "pointer" }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📂</div>
          <div style={{ color: file ? "#4ade80" : "#8b92a5", fontSize: 15 }}>
            {file ? `✓ ${file.name}` : "Click to select CSV file"}
          </div>
        </label>
      </div>

      <button onClick={handle} disabled={!file || loading} style={{
        width: "100%", padding: "14px", borderRadius: 8, border: "none",
        background: file && !loading ? "#4ade80" : "#1e2130",
        color: file && !loading ? "#0a0d14" : "#4a5068",
        fontWeight: 700, fontSize: 16, cursor: file ? "pointer" : "not-allowed"
      }}>
        {loading ? "Analyzing..." : "Upload & Detect"}
      </button>

      {error && <div style={{ color: "#f87171", marginTop: 16, fontSize: 14 }}>{error}</div>}

      {result && (
        <div style={{ marginTop: 32, background: "#0d1520", borderRadius: 12, padding: 24 }}>
          <div style={{ color: "#4ade80", fontWeight: 600, marginBottom: 16 }}>
            ✓ Dataset loaded — {result.rows} rows
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 8 }}>
              DETECTED PROTECTED ATTRIBUTES
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {Object.entries(result.detected.protected_attributes).map(([col, type]) => (
                <span key={col} style={{
                  background: "#1a2f1a", color: "#4ade80", padding: "4px 12px",
                  borderRadius: 6, fontSize: 13
                }}>{col} ({type})</span>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 8 }}>
              TARGET COLUMN
            </div>
            <span style={{
              background: "#1a1f35", color: "#818cf8", padding: "4px 12px",
              borderRadius: 6, fontSize: 13
            }}>{result.detected.target_column}</span>
          </div>

          <button onClick={() => navigate("/audit")} style={{
            width: "100%", padding: "12px", borderRadius: 8, border: "none",
            background: "#818cf8", color: "#fff", fontWeight: 700,
            fontSize: 15, cursor: "pointer"
          }}>
            Run Bias Audit →
          </button>
        </div>
      )}
    </div>
  )
}