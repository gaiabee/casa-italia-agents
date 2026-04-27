from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import AsyncGenerator

import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ---------------------------------------------------------------------------
# Design style → vendor/material guide
# ---------------------------------------------------------------------------
STYLE_GUIDE = {
    "warm-rustic": {
        "label": "Warm & Rustic",
        "palette": "terracotta, warm white, aged oak, linen",
        "materials": "stone, reclaimed wood, linen, hand-thrown ceramics, wrought iron",
        "vendors": "Busatti (textiles), Deruta (ceramics), Officine Gullo (kitchen), Salvatori (stone), Flos (lighting), Baxter (upholstery)",
        "avoid": "chrome, high-gloss lacquer, synthetic fabrics",
    },
    "contemporary-minimal": {
        "label": "Contemporary Minimal",
        "palette": "warm white, greige, charcoal, natural oak",
        "materials": "marble, brushed steel, linen, leather, lacquered wood",
        "vendors": "Poliform (storage/kitchen), Minotti (sofas), Flos (lighting), Salvatori (stone), Molteni&C (bedroom)",
        "avoid": "ornate carving, heavy drapery, pattern mixing",
    },
    "bold-layered": {
        "label": "Bold & Layered",
        "palette": "deep green, burnt sienna, midnight blue, gold",
        "materials": "velvet, marble, brass, patterned tile, antique mirrors",
        "vendors": "Rubelli (fabrics), Murano glass (lighting), Fornasetti (accessories), Poltrona Frau (seating), Gessi (bathroom)",
        "avoid": "plain white walls, minimal accessories, flat lighting",
    },
    "organic-modern": {
        "label": "Organic Modern",
        "palette": "sage, sand, warm grey, clay",
        "materials": "rattan, travertine, jute, linen, natural plaster, terracotta tile",
        "vendors": "Paola Lenti (outdoor/rugs), Salvatori (stone), Kettal (outdoor), Flos (lighting), Zara Home (textiles)",
        "avoid": "synthetic materials, cold metals, high-gloss surfaces",
    },
}

# ---------------------------------------------------------------------------
# Priority → room label
# ---------------------------------------------------------------------------
PRIORITY_LABELS = {
    "kitchen": "Kitchen & Cooking",
    "entertaining": "Entertaining & Reception",
    "bedroom": "Sleep & Bedroom",
    "outdoor": "Outdoor Living",
    "office": "Home Office",
    "art": "Art & Atmosphere",
}

# Priority → which agent ID speaks for it
PRIORITY_AGENT = {
    "kitchen": ("KA", "Kitchen Agent"),
    "entertaining": ("LR", "Living Room Agent"),
    "bedroom": ("MA", "Bedroom Agent"),
    "outdoor": ("BA", "Outdoor Agent"),
    "office": ("MA", "Study Agent"),
    "art": ("LR", "Art Agent"),
}

# Agent colour map
AGENT_COLORS = {
    "SP": "#6B7280",
    "SA": "#8B5CF6",
    "KA": "#F59E0B",
    "LR": "#10B981",
    "MA": "#EC4899",
    "BA": "#3B82F6",
    "BM": "#EF4444",
    "MD": "#D97706",
    "SYS": "#1F2937",
}


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _msg(agent_id: str, agent_name: str, role: str, content: str) -> dict:
    return {
        "agent": agent_name,
        "agent_id": agent_id,
        "role": role,
        "color": AGENT_COLORS.get(agent_id, "#6B7280"),
        "content": content,
        "ts": _ts(),
    }


def _call(system: str, user: str, max_tokens: int = 400) -> str:
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def _call_vision(system: str, user_text: str, pdf_b64: str, max_tokens: int = 500) -> str:
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


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
async def run_session(
    pdf_b64: str,
    design_style: str,
    total_budget: int,
    priorities: list[str],
) -> AsyncGenerator[dict, None]:

    style = STYLE_GUIDE.get(design_style, STYLE_GUIDE["warm-rustic"])
    priority_labels = [PRIORITY_LABELS.get(p, p.title()) for p in priorities]
    priority_str = " > ".join(priority_labels)
    budget_fmt = f"€{total_budget:,}"

    # ── PHASE 1: Space Planner reads the PDF ────────────────────────────────
    yield _msg("SP", "Space Planner", "analyst",
               "📐 Analysing property brochure — reading layout, room sizes, and architectural features...")

    property_summary = _call_vision(
        system=(
            "You are a professional space planner. Analyse the uploaded property brochure and extract: "
            "property name, location, total sqm, key rooms, architectural features (stone walls, vaulted ceilings, "
            "fireplaces, arches, terraces), current condition, and standout design opportunities. "
            "Be specific and concise. Max 150 words."
        ),
        user_text=(
            f"Analyse this property. The client has a total budget of {budget_fmt} "
            f"and their priorities are: {priority_str}. "
            "What are the key spatial opportunities and constraints for a designer?"
        ),
        pdf_b64=pdf_b64,
        max_tokens=350,
    )
    yield _msg("SP", "Space Planner", "analyst", f"🏛️ {property_summary}")

    # ── PHASE 2: Style Agent sets the aesthetic brief ───────────────────────
    yield _msg("SA", "Style Agent", "designer",
               f"🎨 Setting aesthetic direction: {style['label']}...")

    style_brief = _call(
        system=(
            "You are a luxury interior design Style Agent. "
            "Write a concise design brief (3 sentences) covering: colour palette, key materials, "
            "Italian vendors to use, and the emotional atmosphere to create. "
            "Be specific and opinionated."
        ),
        user_text=(
            f"Design style: {style['label']}\n"
            f"Palette: {style['palette']}\n"
            f"Materials: {style['materials']}\n"
            f"Preferred vendors: {style['vendors']}\n"
            f"Avoid: {style['avoid']}\n"
            f"Property: {property_summary[:250]}\n"
            "Write the design brief."
        ),
        max_tokens=250,
    )
    yield _msg("SA", "Style Agent", "designer", f"✨ {style_brief}")

    # ── PHASE 3: Room Agents argue for their budgets ─────────────────────────
    room_proposals: dict[str, dict] = {}
    pct_map = [0.38, 0.32, 0.22]

    for i, priority in enumerate(priorities[:3]):
        agent_id, agent_name = PRIORITY_AGENT.get(priority, ("KA", "Room Agent"))
        room_label = PRIORITY_LABELS.get(priority, priority.title())
        ask_pct = pct_map[i] if i < len(pct_map) else 0.08
        ask_amt = int(total_budget * ask_pct)

        yield _msg(agent_id, agent_name, "room-agent",
                   f"💬 Building case for {room_label} — requesting €{ask_amt:,} ({int(ask_pct*100)}% of budget)...")

        proposal = _call(
            system=(
                f"You are the {agent_name} advocating for the {room_label} in a luxury property renovation. "
                f"Design style: {style['label']}. Vendors to use: {style['vendors']}. "
                "Make a compelling budget case. List 4 specific items with vendor and price in EUR. "
                "Format each item as: • Item name — Vendor — €price — one-line reason. "
                "Start with your total budget ask and why this space deserves it. Max 180 words."
            ),
            user_text=(
                f"Property: {property_summary[:200]}\n"
                f"Total project budget: {budget_fmt}. "
                f"You are priority #{i+1} of {len(priorities[:3])}. "
                f"Make your case for €{ask_amt:,} for {room_label}."
            ),
            max_tokens=350,
        )
        room_proposals[priority] = {
            "name": room_label,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "proposal": proposal,
            "ask": ask_amt,
        }
        yield _msg(agent_id, agent_name, "room-agent", f"📋 {proposal}")

    # ── PHASE 4: Budget Manager flags conflicts ──────────────────────────────
    total_asked = sum(v["ask"] for v in room_proposals.values())
    over_under = total_asked - total_budget
    all_proposals_text = "\n\n".join(
        [f"=== {v['name']} (asking €{v['ask']:,}) ===\n{v['proposal']}" for v in room_proposals.values()]
    )

    yield _msg("BM", "Budget Manager", "budget",
               f"💰 Total requested: €{total_asked:,} vs budget {budget_fmt} — "
               f"{'over by €' + str(abs(over_under):,) if over_under > 0 else 'within budget'}. Reviewing...")

    budget_review = _call(
        system=(
            "You are a strict budget manager for a luxury renovation. "
            "Review the room proposals. Flag which items should be cut or deferred, "
            "which rooms are over-asking, and propose a final allocation. "
            "Be direct and specific. Name specific items to cut. Max 150 words."
        ),
        user_text=(
            f"Total budget: {budget_fmt}\n"
            f"Total requested: €{total_asked:,}\n\n"
            f"{all_proposals_text}\n\n"
            "Provide your budget review and flag conflicts."
        ),
        max_tokens=300,
    )
    yield _msg("BM", "Budget Manager", "budget", f"⚠️ {budget_review}")

    # ── PHASE 5: Master Designer gives final ruling ──────────────────────────
    yield _msg("MD", "Master Designer", "master",
               "👑 Reviewing all proposals and budget constraints — deliberating final ruling...")

    final_ruling = _call(
        system=(
            "You are the Master Designer — the final authority on this renovation. "
            "Review all proposals and the budget review. Give your definitive ruling: "
            "state the approved budget per space, name 2 key approved items per space with vendor and price, "
            "and state 1 item cut per space with reason. "
            "End with a one-sentence vision for the finished property. Max 220 words."
        ),
        user_text=(
            f"Design brief: {style_brief}\n\n"
            f"Client priorities (ranked): {priority_str}\n"
            f"Total budget: {budget_fmt}\n\n"
            f"Room proposals:\n{all_proposals_text}\n\n"
            f"Budget Manager review: {budget_review}\n\n"
            "Give your final ruling."
        ),
        max_tokens=400,
    )
    yield _msg("MD", "Master Designer", "master", f"✅ {final_ruling}")

    # ── PHASE 6: Structured result for frontend ──────────────────────────────
    allocations = []
    for i, priority in enumerate(priorities[:3]):
        pct = pct_map[i] if i < len(pct_map) else 0.08
        allocations.append({
            "room": PRIORITY_LABELS.get(priority, priority.title()),
            "amount": int(total_budget * pct),
            "percentage": int(pct * 100),
        })
    allocated = sum(a["amount"] for a in allocations)
    allocations.append({
        "room": "Reserve / Contingency",
        "amount": total_budget - allocated,
        "percentage": 100 - sum(a["percentage"] for a in allocations),
    })

    yield _msg(
        "SYS", "System", "result",
        json.dumps({
            "type": "session_complete",
            "property_summary": property_summary,
            "style_label": style["label"],
            "style_vendors": style["vendors"],
            "total_budget": total_budget,
            "priority_ranking": priority_labels,
            "budget_allocations": allocations,
            "final_ruling": final_ruling,
        }),
    )
