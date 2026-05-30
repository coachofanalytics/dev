from fastapi import FastAPI
from typing import Optional
from datetime import datetime
from decimal import Decimal

app = FastAPI(
    title="Inflow Management API - main2",
    description="Path and query parameters for inflow records.",
    version="1.0.0"
)

# ✅ Paste the mock inflows here
mock_inflows = [
    {
        "id": i,
        "sender": (i % 5) + 1,
        "receiver": f"Receiver {i}",
        "amount": Decimal(100*i),
        "transaction_date": datetime(2026, 5, 23, (8 + i) % 24),
        "description": f"Inflow {i}"
    }
    for i in range(1, 21)
]

# Now define your routes
@app.get("/")
def home():
    return {"message": "main2 - path and query parameters"}

@app.get("/inflows/{inflow_id}")
def get_inflow(inflow_id: int):
    inflow = next((x for x in mock_inflows if x["id"] == inflow_id), None)
    if inflow is None:
        return {"error": "Inflow not found"}
    return inflow

@app.get("/inflows/")
def list_inflows(skip: int = 0, limit: int = 10, sender: Optional[int] = None):
    results = mock_inflows
    if sender is not None:
        results = [x for x in results if x["sender"] == sender]
    return results[skip : skip + limit]