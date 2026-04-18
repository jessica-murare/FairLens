from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import ingest, audit, remediate

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest")
app.include_router(audit.router, prefix="/audit")
app.include_router(remediate.router, prefix="/remediate")

@app.get("/")
def root():
    return {"status": "FairLens API running"}
