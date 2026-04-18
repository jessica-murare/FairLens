import { useState, useEffect } from "react"
import { runRemediation } from "../api/clients"
import { BarChart, Bar, XAxis, YAxis, Tooltip,
         ResponsiveContainer, Legend } from "recharts"

export default function Remediate() {
  const [dataset, setDataset] = useState(null)
  const [audit, setAudit] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const d = localStorage.getItem("fairlens_dataset")
    const a = localStorage.getItem("fairlens_audit")
    if (d) setDataset(JSON.parse(d))
    if (a) setAudit(JSON.parse(a))
  }, [])

  const run = async () => {
    if (!dataset || !audit) return
    setLoading(true)
    const protected_col = Object.keys(dataset.detected.protected_attributes)[0]
    const target = dataset.detected.target_column
    try {
      const res = await runRemediation(dataset.dataset_id, protected_col, target)
      setResult(res.data)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const compareData = result
    ? Object.keys(result.before.group_metrics).map(group => ({
        name: group,
        before: result.before.group_metrics[group]?.positive_rate,
        after: result.best_result.group_metrics[group]?.positive_rate
      }))
    : []

  return (
    <div style={{ maxWidth: 900, margin: "60px auto", padding: "0 24px" }}>
      <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>Bias Remediation</h1>
      <p style={{ color: "#8b92a5", marginBottom: 32 }}>
        Automatically fix detected bias and verify improvement
      </p>

      {!result && (
        <button onClick={run} disabled={loading} style={{
          padding: "14px 32px", borderRadius: 8, border: "none",
          background: loading ? "#1e2130" : "#4ade80",
          color: loading ? "#4a5068" : "#0a0d14",
          fontWeight: 700, fontSize: 16, cursor: "pointer"
        }}>
          {loading ? "Applying fixes..." : "Fix Bias Automatically"}
        </button>
      )}

      {result && (
        <div>
          {/* Before / After verdict */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
            {[
              { label: "BEFORE", data: result.before, color: "#f87171" },
              { label: "AFTER", data: result.best_result, color: "#4ade80" }
            ].map(({ label, data, color }) => (
              <div key={label} style={{
                background: "#0d1520", borderRadius: 12, padding: 24,
                borderTop: `3px solid ${color}`
              }}>
                <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 12 }}>{label}</div>
                <div style={{ fontSize: 24, fontWeight: 700, color, marginBottom: 16 }}>
                  {data.fairness_scores.bias_verdict}
                </div>
                <div style={{ fontSize: 13, color: "#8b92a5" }}>
                  Parity gap: <span style={{ color: "#e8eaf0" }}>
                    {data.fairness_scores.demographic_parity_gap}
                  </span>
                </div>
                <div style={{ fontSize: 13, color: "#8b92a5", marginTop: 4 }}>
                  Accuracy: <span style={{ color: "#e8eaf0" }}>
                    {(data.model_accuracy * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Improvement stats */}
          <div style={{
            background: "#0d1f1a", borderRadius: 12, padding: 24,
            marginBottom: 24, border: "1px solid #1a3a2a"
          }}>
            <div style={{ color: "#4ade80", fontSize: 13, fontWeight: 600, marginBottom: 16 }}>
              ✓ IMPROVEMENT SUMMARY — Method: {result.best_method}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
              {[
                { label: "Parity Gap Reduced", value: result.improvement.demographic_parity_gap_reduced_by },
                { label: "Disparate Impact Improved", value: result.improvement.disparate_impact_improved_by },
                { label: "Accuracy Change", value: result.improvement.accuracy_change }
              ].map(s => (
                <div key={s.label}>
                  <div style={{ color: "#8b92a5", fontSize: 11, marginBottom: 4 }}>{s.label}</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: "#4ade80" }}>{s.value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Before/After chart */}
          <div style={{ background: "#0d1520", borderRadius: 12, padding: 24, marginBottom: 24 }}>
            <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 16 }}>
              GROUP POSITIVE RATES — BEFORE vs AFTER
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={compareData} barGap={4}>
                <XAxis dataKey="name" stroke="#4a5068" tick={{ fontSize: 11 }} />
                <YAxis stroke="#4a5068" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#0a0d14", border: "1px solid #1e2130" }} />
                <Legend />
                <Bar dataKey="before" fill="#f87171" radius={[4, 4, 0, 0]} />
                <Bar dataKey="after" fill="#4ade80" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Gemini explanation */}
          {result.gemini_explanation && (
            <div style={{ background: "#0d1520", borderRadius: 12, padding: 24 }}>
              <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 12 }}>✦ AI EXPLANATION</div>
              <div style={{ color: "#c8ccd8", fontSize: 14, lineHeight: 1.7 }}>
                {result.gemini_explanation}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}