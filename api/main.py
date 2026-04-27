from __future__ import annotations
import base64, json
from typing import AsyncGenerator
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from agents.orchestrator import run_session

app = FastAPI(title="Casa Italia Agents API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/run-session")
async def run_session_endpoint(
    pdf: UploadFile = File(...),
    budget: int = Form(20000),
    design_mode: str = Form("rustic-italian"),
    rooms: str = Form("living,kitchen,bedroom"),
):
    pdf_bytes = await pdf.read()
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    room_list = [r.strip() for r in rooms.split(",") if r.strip()]
    async def event_stream() -> AsyncGenerator[str, None]:
        async for msg in run_session(pdf_b64=pdf_b64, design_mode=design_mode, total_budget=budget, rooms=room_list):
            yield json.dumps(msg) + "\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")
