# FairLens — AI Bias Detection & Remediation Platform

FairLens is an end-to-end bias auditing platform that helps organizations 
detect, explain, and fix bias in their AI models before deployment.

## Live Demo
- Frontend: https://fairlens.vercel.app
- API: https://YOUR_USERNAME-fairlens-api.hf.space

## Features
- Auto-detects protected attributes from any CSV
- Computes 4 fairness metrics (demographic parity, equalized odds, disparate impact)
- Intersectional bias analysis across combined attributes
- SHAP-powered feature importance
- Gemini AI plain-language explanations
- Automated bias remediation with before/after proof

## Tech Stack
- Frontend: React + Vite + Recharts → Vercel
- Backend: FastAPI → Hugging Face Spaces
- ML: scikit-learn, AIF360, Fairlearn, SHAP
- AI: Google Gemini 1.5 Flash

## Run Locally
### Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

### Frontend
cd frontend
npm install
npm run dev

jessica