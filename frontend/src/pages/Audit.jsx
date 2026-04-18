import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { runFullAudit } from "../api/clients"
import {
    RadarChart, Radar, PolarGrid, PolarAngleAxis,
    BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, Legend
} from "recharts"

export default function Audit() {
    const [dataset, setDataset] = useState(null)
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const navigate = useNavigate()

    useEffect(() => {
        const d = localStorage.getItem("fairlens_dataset")
        if (d) {
            try {
                setDataset(JSON.parse(d))
            } catch (_err) {
                console.error("Failed to parse dataset from localStorage", _err)
            }
        }

        const cachedAudit = localStorage.getItem("fairlens_audit")
        if (cachedAudit) {
            try {
                setResult(JSON.parse(cachedAudit))
            } catch (_err) {
                console.error("Failed to parse cached audit from localStorage", _err)
            }
        }
    }, [])

    const run = async () => {
        if (!dataset) return
        setError(null)
        setLoading(true)
        const protected_cols = Object.keys(dataset.detected.protected_attributes)
        const target = dataset.detected.target_column
        try {
            const res = await runFullAudit(dataset.dataset_id, protected_cols, target)
            setResult(res.data)
            localStorage.setItem("fairlens_audit", JSON.stringify(res.data))
        } catch (e) {
            console.error(e)
            setError(e.response?.data?.detail || e.message || "Audit failed")
        }
        setLoading(false)
    }

    const verdictColor = (v) =>
        v === "BIASED" ? "#f87171" : v === "MODERATE BIAS" ? "#fbbf24" : "#4ade80"

    const groupChartData = result
        ? Object.entries(result.metrics.group_metrics).map(([k, v]) => ({
            name: k, positive_rate: v.positive_rate,
            tpr: v.tpr, accuracy: v.accuracy
        }))
        : []

    const fairnessRadar = result
        ? [
            { metric: "Dem. Parity", score: 1 - result.metrics.fairness_scores.demographic_parity_gap },
            { metric: "Eq. Odds TPR", score: 1 - result.metrics.fairness_scores.equalized_odds_tpr_gap },
            { metric: "Eq. Odds FPR", score: 1 - result.metrics.fairness_scores.equalized_odds_fpr_gap },
            { metric: "Disp. Impact", score: result.metrics.fairness_scores.disparate_impact_ratio },
        ]
        : []

    return (
        <div style={{ maxWidth: 900, margin: "60px auto", padding: "0 24px" }}>
            <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>Bias Audit</h1>
            <p style={{ color: "#8b92a5", marginBottom: 32 }}>
                Full fairness analysis across all protected attributes
            </p>

            {!dataset && (
                <div style={{ color: "#f87171" }}>
                    No dataset found. Go back and upload first.
                    <div style={{ marginTop: 12 }}>
                        <button onClick={() => navigate("/")} style={{
                            padding: "10px 18px",
                            borderRadius: 8,
                            border: "none",
                            background: "#818cf8",
                            color: "#fff",
                            cursor: "pointer"
                        }}>
                            Upload Dataset
                        </button>
                    </div>
                </div>
            )}

            {error && (
                <div style={{ color: "#f87171", marginBottom: 20 }}>{error}</div>
            )}

            {dataset && !result && (
                <>
                    <button
                        onClick={run}
                        disabled={loading}
                        style={{
                            padding: "14px 32px",
                            borderRadius: 8,
                            border: "none",
                            background: loading ? "#1e2130" : "#818cf8",
                            color: loading ? "#4a5068" : "#fff",
                            fontWeight: 700,
                            fontSize: 16,
                            cursor: "pointer"
                        }}
                    >
                        {loading ? "Processing..." : "Run Audit"}
                    </button>

                    {loading && (
                        <div style={{ marginTop: 32 }}>
                            {[
                                "Loading dataset...",
                                "Computing fairness metrics...",
                                "Running SHAP analysis...",
                                "Generating AI explanation..."
                            ].map((msg, i) => (
                                <div
                                    key={i}
                                    style={{
                                        padding: "12px 16px",
                                        background: "#0d1520",
                                        borderRadius: 8,
                                        marginBottom: 8,
                                        color: "#4a5068",
                                        fontSize: 13,
                                        animation: "pulse 1.5s infinite"
                                    }}
                                >
                                    {msg}
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}

            {result && (
                <div>
                    {/* Verdict banner */}
                    <div style={{
                        background: "#0d1520", borderRadius: 12, padding: 24,
                        marginBottom: 24, borderLeft: `4px solid ${verdictColor(result.metrics.fairness_scores.bias_verdict)}`
                    }}>
                        <div style={{ fontSize: 13, color: "#8b92a5", marginBottom: 4 }}>OVERALL VERDICT</div>
                        <div style={{ fontSize: 28, fontWeight: 700, color: verdictColor(result.metrics.fairness_scores.bias_verdict) }}>
                            {result.metrics.fairness_scores.bias_verdict}
                        </div>
                        <div style={{ color: "#8b92a5", fontSize: 14, marginTop: 8 }}>
                            Model accuracy: {(result.metrics.model_accuracy * 100).toFixed(1)}%
                        </div>
                    </div>

                    {/* Metric cards */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
                        {[
                            { label: "Demographic Parity Gap", value: result.metrics.fairness_scores.demographic_parity_gap, ideal: "0" },
                            { label: "Disparate Impact Ratio", value: result.metrics.fairness_scores.disparate_impact_ratio, ideal: "1.0" },
                            { label: "Equalized Odds TPR Gap", value: result.metrics.fairness_scores.equalized_odds_tpr_gap, ideal: "0" },
                            { label: "Equalized Odds FPR Gap", value: result.metrics.fairness_scores.equalized_odds_fpr_gap, ideal: "0" },
                        ].map(m => (
                            <div key={m.label} style={{ background: "#0d1520", borderRadius: 10, padding: 20 }}>
                                <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 6 }}>{m.label.toUpperCase()}</div>
                                <div style={{ fontSize: 28, fontWeight: 700 }}>{m.value}</div>
                                <div style={{ color: "#4a5068", fontSize: 12, marginTop: 4 }}>ideal: {m.ideal}</div>
                            </div>
                        ))}
                    </div>

                    {/* Charts */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
                        <div style={{ background: "#0d1520", borderRadius: 10, padding: 20 }}>
                            <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 16 }}>GROUP POSITIVE RATES</div>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={groupChartData}>
                                    <XAxis dataKey="name" stroke="#4a5068" tick={{ fontSize: 11 }} />
                                    <YAxis stroke="#4a5068" tick={{ fontSize: 11 }} />
                                    <Tooltip contentStyle={{ background: "#0a0d14", border: "1px solid #1e2130" }} />
                                    <Bar dataKey="positive_rate" fill="#818cf8" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        <div style={{ background: "#0d1520", borderRadius: 10, padding: 20 }}>
                            <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 16 }}>FAIRNESS RADAR</div>
                            <ResponsiveContainer width="100%" height={200}>
                                <RadarChart data={fairnessRadar}>
                                    <PolarGrid stroke="#1e2130" />
                                    <PolarAngleAxis dataKey="metric" tick={{ fill: "#8b92a5", fontSize: 11 }} />
                                    <Radar dataKey="score" stroke="#4ade80" fill="#4ade80" fillOpacity={0.2} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* SHAP Feature Importance */}
                    {result.shap && (
                        <div style={{ background: "#0d1520", borderRadius: 12, padding: 24, marginBottom: 24 }}>
                            <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 16 }}>
                                FEATURE BIAS DRIVERS (SHAP)
                            </div>

                            {/* top features bar */}
                            <ResponsiveContainer width="100%" height={180}>
                                <BarChart
                                    data={result.shap.top_features}
                                    layout="vertical"
                                    margin={{ left: 80 }}
                                >
                                    <XAxis type="number" stroke="#4a5068" tick={{ fontSize: 11 }} />
                                    <YAxis dataKey="feature" type="category" stroke="#4a5068" tick={{ fontSize: 11 }} />
                                    <Tooltip contentStyle={{ background: "#0a0d14", border: "1px solid #1e2130" }} />
                                    <Bar dataKey="importance" fill="#fbbf24" radius={[0, 4, 4, 0]} />
                                </BarChart>
                            </ResponsiveContainer>

                            {/* bias drivers table */}
                            {result.shap.bias_drivers?.length > 0 && (
                                <div style={{ marginTop: 20 }}>
                                    <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 10 }}>
                                        FEATURES CORRELATED WITH PROTECTED ATTRIBUTE
                                    </div>
                                    {result.shap.bias_drivers.map(d => (
                                        <div key={d.feature} style={{
                                            display: "flex", justifyContent: "space-between",
                                            alignItems: "center", padding: "10px 0",
                                            borderBottom: "1px solid #1e2130"
                                        }}>
                                            <span style={{ fontSize: 14, color: "#e8eaf0" }}>{d.feature}</span>
                                            <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
                                                <span style={{ fontSize: 12, color: "#8b92a5" }}>
                                                    corr: {d.protected_correlation}
                                                </span>
                                                <span style={{
                                                    fontSize: 11, padding: "2px 8px", borderRadius: 4,
                                                    background: d.bias_risk === "HIGH" ? "#2d1515" : "#2d2510",
                                                    color: d.bias_risk === "HIGH" ? "#f87171" : "#fbbf24"
                                                }}>
                                                    {d.bias_risk}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div style={{ marginTop: 16, padding: 12, background: "#0a0d14", borderRadius: 8 }}>
                                <div style={{ fontSize: 13, color: "#c8ccd8" }}>
                                    💡 {result.shap.summary}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Gemini explanation */}
                    {result.explanation?.sections && (
                        <div style={{ background: "#0d1520", borderRadius: 12, padding: 24, marginBottom: 24 }}>
                            <div style={{ color: "#8b92a5", fontSize: 12, marginBottom: 16 }}>
                                ✦ AI EXPLANATION
                            </div>
                            {Object.entries(result.explanation.sections).map(([k, v]) => (
                                <div key={k} style={{ marginBottom: 16 }}>
                                    <div style={{ color: "#818cf8", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{k}</div>
                                    <div style={{ color: "#c8ccd8", fontSize: 14, lineHeight: 1.6 }}>{v}</div>
                                </div>
                            ))}
                        </div>
                    )}

                    <button onClick={() => navigate("/remediate")} style={{
                        width: "100%", padding: "14px", borderRadius: 8, border: "none",
                        background: "#4ade80", color: "#0a0d14",
                        fontWeight: 700, fontSize: 16, cursor: "pointer"
                    }}>
                        Fix Bias Now →
                    </button>
                </div>
            )}
        </div>
    )
}