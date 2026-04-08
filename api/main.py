from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from agents.orchestrator import Orchestrator


app = FastAPI(title="Casa Italia", version="0.1.0")


class RunRequest(BaseModel):
    design_mode: str = Field(..., description="e.g. 'italian-modern', 'budget-refresh', 'luxury'")
    budget: int = Field(..., ge=0, description="Total budget in USD (or chosen currency unit).")


class RunResponse(BaseModel):
    agent_messages: list[dict]
    allocations: dict
    items: dict


@app.post("/api/run", response_model=RunResponse)
async def run_design(req: RunRequest) -> RunResponse:
    orchestrator = Orchestrator()
    result = await orchestrator.run(design_mode=req.design_mode, budget=req.budget)
    return RunResponse(**result)
