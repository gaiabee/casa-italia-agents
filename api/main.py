from __future__ import annotations

import base64
import json
from typing import AsyncGenerator

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agents.orchestrator import run_session

app = FastAPI(title="Casa Italia Agents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/run-session")
async def run_session_endpoint(
    pdf: UploadFile = File(...),
    budget: int = Form(30000),
    design_style: str = Form("warm-rustic"),
    priorities: str = Form("kitchen,entertaining,bedroom"),
):
    """
    Accepts:
      - pdf: property brochure PDF (used for Claude Vision analysis)
      - budget: total budget in EUR (integer)
      - design_style: warm-rustic | contemporary-minimal | bold-layered | organic-modern
      - priorities: comma-separated ranked list e.g. "kitchen,entertaining,bedroom"
    Streams back newline-delimited JSON messages.
    """
    pdf_bytes = await pdf.read()
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    priority_list = [p.strip() for p in priorities.split(",") if p.strip()]

    async def event_stream() -> AsyncGenerator[str, None]:
        async for msg in run_session(
            pdf_b64=pdf_b64,
            design_style=design_style,
            total_budget=budget,
            priorities=priority_list,
        ):
            yield json.dumps(msg) + "\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
