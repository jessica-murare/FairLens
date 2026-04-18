from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
from core.detector import detect_columns

router = APIRouter()

upload_datasets = {} #in-memory storage for uploaded datasets

@router.post("/")
async def ingest_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty.")
    
    detection = detect_columns(df)

    dataset_id = file.filename.replace('.csv', '').replace(' ', '_')
    upload_datasets[dataset_id] = df

    return{
        "dataset_id": dataset_id,
        "rows": len(df),
        "columns": list(df.columns),
        "detected": detection
    }
    