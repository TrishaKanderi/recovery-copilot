import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .data_gen import generate_batch
from .pipeline import run_batch, summarize

app = FastAPI(title="Recovery Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory store of the last run (fine for a demo/prototype)
STATE = {"cases": [], "summary": {}}


@app.post("/api/run")
def run(n: int = 80):
    """Generates a fresh synthetic batch and runs the full recovery
    pipeline end to end. n = batch size (held-out synthetic test set)."""
    records = generate_batch(n=n)
    cases = run_batch(records)
    STATE["cases"] = cases
    STATE["summary"] = summarize(cases)
    return {"summary": STATE["summary"], "case_count": len(cases)}


@app.get("/api/summary")
def get_summary():
    if not STATE["cases"]:
        raise HTTPException(400, "No run yet. POST /api/run first.")
    return STATE["summary"]


@app.get("/api/cases")
def get_cases():
    if not STATE["cases"]:
        raise HTTPException(400, "No run yet. POST /api/run first.")
    # lightweight list for the dashboard table
    return [
        {
            "id": c["id"],
            "type": c["type"],
            "amount": c["amount"],
            "customer_name": c["customer_name"],
            "customer_language": c["customer_language"],
            "root_cause": c["root_cause"],
            "action": c["action"],
            "status": c["status"],
            "attempts": c["attempts"],
        }
        for c in STATE["cases"]
    ]


@app.get("/api/case/{case_id}")
def get_case(case_id: str):
    for c in STATE["cases"]:
        if c["id"] == case_id:
            return c
    raise HTTPException(404, "Case not found")


# serve the dashboard
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
