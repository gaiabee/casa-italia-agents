from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.orchestrator import run_session

app = FastAPI(title="Casa Italia Agents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionRequest(BaseModel):
    design_mode: str = "rustic-italian"
    total_budget: int = 20000
    rooms: list[str] = ["kitchen", "living", "bedroom", "bathroom"]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/run-session")
async def run_session_endpoint(req: SessionRequest):
    async def event_stream() -> AsyncGenerator[str, None]:
        async for msg in run_session(req.design_mode, req.total_budget, req.rooms):
            yield json.dumps(msg) + "\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
