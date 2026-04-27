from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import AsyncGenerator

import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

ROOM_LABELS = {
    "living": "Reception Room / Soggiorno",
    "kitchen": "Kitchen / La Cucina",
    "bedroom": "Master Bedroom / La Camera",
    "bathroom": "Bathroom / Il Bagno",
    "dining": "Dining Room / La Sala da Pranzo",
    "terrace": "Terrace / La Terrazza",
}

DESIGN_MODES = {
    "rustic-italian": "Rustic Italian — preserve original stone, terracotta, and beams; layer with linen, aged oak, and artisan ceramics",
    "modern-minimal": "Modern Minimal — clean lines, neutral palette, hide structural elements behind plaster; Boffi kitchen, Poliform wardrobes",
    "entertaining": "Grand Entertaining — maximise reception space, statement lighting, large dining table, hospitality-grade kitchen",
    "feng-shui": "Feng Shui / Harmony — energy flow, natural materials, declutter, plants, water features, balanced yin/yang",
}


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _msg(agent: str, role: str, content: str) -> dict:
    return {"agent": agent, "role": role, "content": content, "ts": _ts()}


def _call(system: str, user: str, max_tokens: int = 400) -> str:
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def _call_vision(system: str, user_text: str, pdf_b64: str, max_tokens: int = 600) -> str:
    """Call Claude with a PDF document for vision analysis."""
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=max_tokens,
        system=system,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )
    return resp.content[0].text.strip()


async def run_session(
    pdf_b64: str,
    design_mode: str,
    total_budget: int,
    rooms: list[str],
) -> AsyncGenerator[dict, None]:
    mode_desc = DESIGN_MODES.get(design_mode, DESIGN_MODES["rustic-italian"])
    room_names = [ROOM_LABELS.get(r, r.title()) for r in rooms]
    budget_per_room = total_budget // len(rooms)

    # ── PHASE 1: Space Planner analyses the PDF ──────────────────────────────
    yield _msg("Space Planner", "analyst", "📐 Analysing property layout and spatial constraints from the brochure...")

    property_summary = _call_vision(
        system=(
            "You are a professional space planner specialising in Italian rural properties. "
            "Analyse the property brochure and extract: property name/location, total sqm, "
            "key rooms and their approximate sizes, architectural features (stone walls, beams, "
            "fireplaces, arches), current condition, and any spatial constraints. "
            "Be specific and concise. Max 150 words."
        ),
        user_text=(
            f"Analyse this property brochure. Focus on the following rooms: {', '.join(room_names)}. "
            "Describe the spatial layout, architectural character, and what a designer would need to know."
        ),
        pdf_b64=pdf_b64,
        max_tokens=300,
    )

    yield _msg("Space Planner", "analyst", f"🏛️ Property analysis complete: {property_summary}")

    # ── PHASE 2: Style Agent sets the design brief ───────────────────────────
    yield _msg("Style Agent", "designer", f"🎨 Establishing design brief: {mode_desc}")

    style_brief = _call(
        system=(
            "You are a luxury Italian interior designer. Given a design mode and property description, "
            "write a concise design brief (3 sentences max) covering: colour palette, key materials, "
            "and the emotional atmosphere to create. Be specific to Italian craftsmanship."
        ),
        user_text=f"Design mode: {mode_desc}\nProperty: {property_summary}\nWrite the design brief.",
        max_tokens=200,
    )

    yield _msg("Style Agent", "designer", f"✨ Design brief: {style_brief}")

    # ── PHASE 3: Room Agents propose budgets ─────────────────────────────────
    room_proposals: dict[str, dict] = {}

    for room_key, room_name in zip(rooms, room_names):
        yield _msg(f"{room_name} Agent", "room-agent", f"💬 Analysing {room_name} and preparing budget proposal...")

        proposal_text = _call_vision(
            system=(
                f"You are the dedicated agent for the {room_name} in an Italian farmhouse renovation. "
                f"Your design brief is: {style_brief}. "
                "Propose a budget allocation and list 4-5 specific furniture/decor items with Italian vendors and prices in EUR. "
                "Format: start with your budget ask, then list items as '• Item — Vendor — €price — one-line reason'. "
                "Be specific and realistic. Max 200 words."
            ),
            user_text=(
                f"Property context: {property_summary}\n"
                f"Total budget for all rooms: €{total_budget}. Suggested per room: €{budget_per_room}.\n"
                f"Propose your budget for {room_name} and list your top items."
            ),
            pdf_b64=pdf_b64,
            max_tokens=350,
        )

        room_proposals[room_key] = {"name": room_name, "proposal": proposal_text}
        yield _msg(f"{room_name} Agent", "room-agent", f"📋 {room_name} proposal:\n{proposal_text}")

    # ── PHASE 4: Budget Manager flags conflicts ───────────────────────────────
    yield _msg("Budget Manager", "budget", f"💰 Reviewing all proposals against total budget of €{total_budget:,}...")

    all_proposals = "\n\n".join(
        [f"=== {v['name']} ===\n{v['proposal']}" for v in room_proposals.values()]
    )

    budget_review = _call(
        system=(
            "You are a strict budget manager for a luxury Italian renovation. "
            "Review all room proposals and identify: which rooms are over budget, "
            "which items should be cut or deferred, and what the total projected spend is. "
            "Be direct and specific. Max 150 words."
        ),
        user_text=f"Total budget: €{total_budget:,}\n\nRoom proposals:\n{all_proposals}\n\nProvide your budget review.",
        max_tokens=250,
    )

    yield _msg("Budget Manager", "budget", f"⚠️ Budget review: {budget_review}")

    # ── PHASE 5: Master Designer gives final ruling ───────────────────────────
    yield _msg("Master Designer", "master", "👑 Deliberating final design decisions...")

    final_ruling = _call(
        system=(
            "You are the Master Designer — the final authority on this Italian farmhouse renovation. "
            "Review the room proposals and budget review. Give your final ruling: "
            "which items are approved, which are cut, and why. "
            "End with a one-sentence vision statement for the finished property. "
            "Max 200 words."
        ),
        user_text=(
            f"Design brief: {style_brief}\n\n"
            f"Room proposals:\n{all_proposals}\n\n"
            f"Budget review: {budget_review}\n\n"
            "Give your final ruling."
        ),
        max_tokens=300,
    )

    yield _msg("Master Designer", "master", f"✅ Final ruling: {final_ruling}")

    # ── PHASE 6: Emit structured results ─────────────────────────────────────
    # Build a simple budget allocation per room
    allocations = []
    per_room = total_budget // len(rooms)
    remainder = total_budget - (per_room * len(rooms))
    for i, (room_key, room_name) in enumerate(zip(rooms, room_names)):
        alloc = per_room + (remainder if i == 0 else 0)
        allocations.append({"room": room_name, "allocated": alloc})

    yield _msg(
        "System",
        "result",
        json.dumps({
            "type": "session_complete",
            "property_summary": property_summary,
            "style_brief": style_brief,
            "budget_allocations": allocations,
            "final_ruling": final_ruling,
            "total_budget": total_budget,
            "design_mode": design_mode,
        }),
    )
