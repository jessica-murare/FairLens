from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.metrics import compute_fairness_metrics
from routers.ingest import upload_datasets
from core.metrics import compute_fairness_metrics, compute_intersectional_bias
from core.gemini import explain_bias_report
from core.explainer import compute_shap_explanation


router = APIRouter()

class AuditRequest(BaseModel):
    dataset_id: str
    protected_column: str
    target_column: str

@router.post("/")
def run_audit(req: AuditRequest):
    df = upload_datasets.get(req.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found. Re-upload.")
    
    if req.protected_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{req.protected_column}' not found")
    
    if req.target_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{req.target_column}' not found")
    
    try:
        result = compute_fairness_metrics(df, req.protected_column, req.target_column)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics computation failed: {str(e)}")
    

class IntersectionalRequest(BaseModel):
    dataset_id: str
    protected_columns: list[str]
    target_column: str

@router.post("/intersectional")
def run_intersectional(req: IntersectionalRequest):
    df = upload_datasets.get(req.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found. Re-upload.")
    
    missing = [c for c in req.protected_columns if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Columns not found: {missing}")

    result = compute_intersectional_bias(df, req.protected_columns, req.target_column)
    return result

class FullAuditRequest(BaseModel):
    dataset_id: str
    protected_columns: list[str]
    target_column: str

@router.post("/full")
def run_full_audit(req: FullAuditRequest):
    df = upload_datasets.get(req.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found. Re-upload.")

    primary_col = req.protected_columns[0]
    metrics = compute_fairness_metrics(df, primary_col, req.target_column)

    intersectional = None
    if len(req.protected_columns) > 1:
        intersectional = compute_intersectional_bias(
            df, req.protected_columns, req.target_column
        )

    shap_result = compute_shap_explanation(df, primary_col, req.target_column)
    explanation = explain_bias_report(metrics, intersectional)

    return {
        "metrics": metrics,
        "intersectional": intersectional,
        "shap": shap_result,
        "explanation": explanation
    }

class ExplainRequest(BaseModel):
    dataset_id: str
    protected_column: str
    target_column: str

@router.post("/explain")
def run_explanation(req: ExplainRequest):
    df = upload_datasets.get(req.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found. Re-upload.")
    
    result = compute_shap_explanation(df, req.protected_column, req.target_column)
    return result