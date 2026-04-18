# FairLens 🔍
### AI Bias Detection, Explanation & Remediation Platform

> Built for the Google AI Solution Challenge — *Unbiased AI Decision* track

[![Live Demo](https://img.shields.io/badge/Live%20Demo-fair--lens--alpha.vercel.app-4ade80?style=for-the-badge)](https://fair-lens-alpha.vercel.app/)
[![API](https://img.shields.io/badge/API-HuggingFace%20Spaces-f97316?style=for-the-badge)](https://jessica-murare-fairlens-api.hf.space)
[![License](https://img.shields.io/badge/License-MIT-818cf8?style=for-the-badge)](LICENSE)

---

## The Problem

AI systems make life-changing decisions in hiring, lending, and healthcare — yet most are trained on historical data that reflects decades of human bias. When these systems learn from flawed data, they silently amplify discrimination at scale, affecting millions of people without any transparency or recourse.

**Existing tools only detect bias. FairLens detects, explains, and fixes it.**

---

## What is FairLens?

FairLens is an end-to-end AI bias auditing and remediation platform. Upload any tabular dataset, instantly receive a full fairness audit across protected attributes, understand *why* bias exists through explainable AI, and apply automated remediation — all before your model goes live.

---

## Features

### 🔎 Auto Detection
Automatically identifies protected attributes (gender, race, age, religion, disability) and target columns from any uploaded CSV — no manual configuration needed.

### 📊 Fairness Metrics Engine
Computes four industry-standard fairness metrics across all demographic groups:
- **Demographic Parity Gap** — are positive outcomes equally distributed?
- **Equalized Odds (TPR + FPR Gap)** — are error rates equal across groups?
- **Disparate Impact Ratio** — does the model meet the 80% rule?

### 🔗 Intersectional Bias Analysis
Goes beyond single-attribute analysis to detect compounded bias across combinations (e.g. race × gender). Identifies the most privileged and most disadvantaged subgroup — a capability missing from most existing tools.

### 🧠 SHAP Explainability
Uses SHAP (SHapley Additive exPlanations) to identify which features drive bias, showing feature importance scores and correlation with protected attributes with HIGH/MEDIUM risk tagging.

### ✦ Gemini AI Explanations
Converts technical metrics into plain-language insights using Google Gemini 1.5 Flash — structured into Summary, Who Is Affected, Real World Impact, Root Cause, and Recommended Fixes. Built for non-technical compliance and HR teams.

### ⚙️ Automated Remediation
Applies two debiasing techniques and selects the best result:
- **Reweighing** — adjusts sample weights to balance group representation
- **Fairness-Constrained Modeling** — penalizes features correlated with protected attributes

Outputs a full before/after comparison with improvement percentages across all fairness metrics.

---

## How It Works

```
Upload CSV → Auto-detect attributes → Run fairness audit
→ SHAP analysis → Gemini explanation → Apply remediation → Verify improvement
```

---

## Demo

| Step | Screenshot |
|------|-----------|
| Upload dataset | Auto-detects protected attributes + target column |
| Bias audit | Metrics, radar chart, group comparison, SHAP drivers |
| AI explanation | Gemini-powered plain language breakdown |
| Remediation | Before/after verdict, improvement %, group rate comparison |

---

## Competitive Advantage

| Feature | IBM AIF360 | Microsoft Fairlearn | Google What-If | **FairLens** |
|--------|-----------|-------------------|----------------|-------------|
| Auto attribute detection | ❌ | ❌ | ❌ | ✅ |
| Intersectional bias | ❌ | ❌ | Limited | ✅ |
| Plain language explanation | ❌ | ❌ | ❌ | ✅ Gemini |
| Auto remediation | ✅ | Partial | ❌ | ✅ |
| Before/after proof | ❌ | ❌ | ❌ | ✅ |
| No-code UI | ❌ | ❌ | ✅ | ✅ |
| Free & open source | ✅ | ✅ | ✅ | ✅ |

---

## Tech Stack

### Backend
- **FastAPI** — REST API framework
- **scikit-learn** — model training and evaluation
- **AIF360** — fairness metrics (IBM)
- **Fairlearn** — fairness constraints (Microsoft)
- **SHAP** — explainability
- **Google Gemini 1.5 Flash** — AI explanations
- **Deployed on:** Hugging Face Spaces (Docker)

### Frontend
- **React + Vite** — UI framework
- **Recharts** — data visualizations (bar, radar charts)
- **React Router** — page navigation
- **Deployed on:** Vercel

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest/` | Upload CSV, auto-detect columns |
| `POST` | `/audit/full` | Full bias audit + SHAP + Gemini |
| `POST` | `/audit/intersectional` | Intersectional bias analysis |
| `POST` | `/remediate/` | Apply debiasing + before/after |

---

## Run Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### Backend
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

# create .env file
echo "GEMINI_API_KEY=your_key_here" > .env

uvicorn main:app --reload
# API running at http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install

# create .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
# UI running at http://localhost:5173
```

---

## Sample Dataset

Test with the COMPAS Recidivism dataset — a well-known example of racial bias in criminal justice AI:

```bash
curl -o sample.csv https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv
```

Upload `sample.csv` → protected columns: `race`, `sex` → target: `two_year_recid`

Expected result: **BIASED** verdict with ~26% intersectional gap between African-American males and Caucasian females.

---

## Project Structure

```
fairlens/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── routers/
│   │   ├── ingest.py        # upload + detection
│   │   ├── audit.py         # metrics + SHAP + Gemini
│   │   └── remediate.py     # debiasing
│   ├── core/
│   │   ├── metrics.py       # fairness metrics engine
│   │   ├── explainer.py     # SHAP analysis
│   │   ├── remediator.py    # reweighing + constrained model
│   │   └── gemini.py        # Gemini API integration
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── pages/           # Upload, Audit, Remediate
│       ├── components/      # Navbar, charts
│       └── api/client.js    # API calls
└── README.md
```

---

## Real World Impact

FairLens directly addresses bias in:
- **Hiring** — resume screening and candidate scoring
- **Lending** — loan approval and credit scoring  
- **Healthcare** — treatment recommendations and risk scoring
- **Criminal Justice** — recidivism prediction (COMPAS)

Organizations subject to the **EU AI Act** and **US Equal Credit Opportunity Act** can use FairLens as a compliance audit tool before model deployment.

---

## Built With ❤️ for Google AI Solution Challenge

*FairLens — because fair AI isn't optional, it's essential.*