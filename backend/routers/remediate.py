from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.remediator import remediate
from core.gemini import explain_remediation
from routers.ingest import upload_datasets

router = APIRouter()

class RemediateRequest(BaseModel):
    dataset_id: str
    protected_column: str
    target_column: str

@router.post("/")
def run_remediation(req: RemediateRequest):
    df = upload_datasets.get(req.dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found. Re-upload.")

    if req.protected_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{req.protected_column}' not found")
    if req.target_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{req.target_column}' not found")

    try:
        result = remediate(df, req.protected_column, req.target_column)
        
        # gemini explains what changed
        try:
            explanation = explain_remediation(result["before"], result["best_result"])
            result["gemini_explanation"] = explanation
        except Exception as e:
            result["gemini_explanation"] = f"Explanation unavailable: {str(e)}"

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Remediation failed: {str(e)}")