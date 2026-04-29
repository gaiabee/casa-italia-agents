from __future__ import annotations

import json
import os
import re
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
        "unsplash_query": "rustic farmhouse interior stone walls warm",
    },
    "contemporary-minimal": {
        "label": "Contemporary Minimal",
        "palette": "warm white, greige, charcoal, natural oak",
        "materials": "marble, brushed steel, linen, leather, lacquered wood",
        "vendors": "Poliform (storage/kitchen), Minotti (sofas), Flos (lighting), Salvatori (stone), Molteni&C (bedroom)",
        "avoid": "ornate carving, heavy drapery, pattern mixing",
        "unsplash_query": "contemporary minimal interior white marble",
    },
    "bold-layered": {
        "label": "Bold & Layered",
        "palette": "deep green, burnt sienna, midnight blue, gold",
        "materials": "velvet, marble, brass, patterned tile, antique mirrors",
        "vendors": "Rubelli (fabrics), Murano glass (lighting), Fornasetti (accessories), Poltrona Frau (seating), Gessi (bathroom)",
        "avoid": "plain white walls, minimal accessories, flat lighting",
        "unsplash_query": "art deco maximalist interior velvet brass",
    },
    "organic-modern": {
        "label": "Organic Modern",
        "palette": "sage, sand, warm grey, clay",
        "materials": "rattan, travertine, jute, linen, natural plaster, terracotta tile",
        "vendors": "Paola Lenti (outdoor/rugs), Salvatori (stone), Kettal (outdoor), Flos (lighting), Zara Home (textiles)",
        "avoid": "synthetic materials, cold metals, high-gloss surfaces",
        "unsplash_query": "scandinavian minimalist interior natural light",
    },
}

# ---------------------------------------------------------------------------
# Fixed rooms for this version
# ---------------------------------------------------------------------------
ROOMS = [
    {
        "id": "living",
        "name": "Living Room",
        "agent_id": "LR",
        "agent_name": "Living Room Agent",
        "color": "#10B981",
        "pct": 0.38,
        "unsplash_ids": {
            "warm-rustic": "photo-1600210492493-0946911123ea",
            "contemporary-minimal": "photo-1586023492125-27b2c045efd7",
            "bold-layered": "photo-1618220179428-22790b461013",
            "organic-modern": "photo-1555041469-a586c61ea9bc",
        },
    },
    {
        "id": "kitchen",
        "name": "Kitchen",
        "agent_id": "KA",
        "agent_name": "Kitchen Agent",
        "color": "#F59E0B",
        "pct": 0.32,
        "unsplash_ids": {
            "warm-rustic": "photo-1556909114-f6e7ad7d3136",
            "contemporary-minimal": "photo-1556909172-54557c7e4fb7",
            "bold-layered": "photo-1556909114-f6e7ad7d3136",
            "organic-modern": "photo-1556909172-54557c7e4fb7",
        },
    },
    {
        "id": "bedroom",
        "name": "Master Bedroom",
        "agent_id": "MA",
        "agent_name": "Bedroom Agent",
        "color": "#EC4899",
        "pct": 0.22,
        "unsplash_ids": {
            "warm-rustic": "photo-1631049307264-da0ec9d70304",
            "contemporary-minimal": "photo-1616594039964-ae9021a400a0",
            "bold-layered": "photo-1631049552057-403cdb8f0658",
            "organic-modern": "photo-1616594039964-ae9021a400a0",
        },
    },
]

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

# Furniture image map: style → room → list of Unsplash photo IDs for items
FURNITURE_IMAGES = {
    "warm-rustic": {
        "living": [
            "photo-1555041469-a586c61ea9bc",  # sofa
            "photo-1567538096630-e0c55bd6374c",  # armchair
            "photo-1524758631624-e2822e304c36",  # coffee table
            "photo-1513519245088-0e12902e35ca",  # rug
        ],
        "kitchen": [
            "photo-1556909114-f6e7ad7d3136",  # kitchen
            "photo-1556909172-54557c7e4fb7",  # kitchen 2
            "photo-1565538810643-b5bdb714032a",  # ceramics
            "photo-1584568694244-14fbdf83bd30",  # lighting
        ],
        "bedroom": [
            "photo-1631049307264-da0ec9d70304",  # bed
            "photo-1555529669-e69e7aa0ba9a",  # nightstand
            "photo-1616594039964-ae9021a400a0",  # bedroom
            "photo-1513519245088-0e12902e35ca",  # rug
        ],
    },
    "contemporary-minimal": {
        "living": [
            "photo-1586023492125-27b2c045efd7",
            "photo-1567538096630-e0c55bd6374c",
            "photo-1524758631624-e2822e304c36",
            "photo-1555041469-a586c61ea9bc",
        ],
        "kitchen": [
            "photo-1556909172-54557c7e4fb7",
            "photo-1556909114-f6e7ad7d3136",
            "photo-1584568694244-14fbdf83bd30",
            "photo-1565538810643-b5bdb714032a",
        ],
        "bedroom": [
            "photo-1616594039964-ae9021a400a0",
            "photo-1631049307264-da0ec9d70304",
            "photo-1555529669-e69e7aa0ba9a",
            "photo-1513519245088-0e12902e35ca",
        ],
    },
    "bold-layered": {
        "living": [
            "photo-1618220179428-22790b461013",
            "photo-1567538096630-e0c55bd6374c",
            "photo-1555041469-a586c61ea9bc",
            "photo-1524758631624-e2822e304c36",
        ],
        "kitchen": [
            "photo-1556909114-f6e7ad7d3136",
            "photo-1584568694244-14fbdf83bd30",
            "photo-1556909172-54557c7e4fb7",
            "photo-1565538810643-b5bdb714032a",
        ],
        "bedroom": [
            "photo-1631049552057-403cdb8f0658",
            "photo-1631049307264-da0ec9d70304",
            "photo-1555529669-e69e7aa0ba9a",
            "photo-1616594039964-ae9021a400a0",
        ],
    },
    "organic-modern": {
        "living": [
            "photo-1555041469-a586c61ea9bc",
            "photo-1586023492125-27b2c045efd7",
            "photo-1524758631624-e2822e304c36",
            "photo-1513519245088-0e12902e35ca",
        ],
        "kitchen": [
            "photo-1556909172-54557c7e4fb7",
            "photo-1556909114-f6e7ad7d3136",
            "photo-1565538810643-b5bdb714032a",
            "photo-1584568694244-14fbdf83bd30",
        ],
        "bedroom": [
            "photo-1616594039964-ae9021a400a0",
            "photo-1631049307264-da0ec9d70304",
            "photo-1555529669-e69e7aa0ba9a",
            "photo-1513519245088-0e12902e35ca",
        ],
    },
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


def _parse_furniture_json(text: str) -> list[dict]:
    """Extract JSON array from LLM output, tolerating markdown fences."""
    # Try to find a JSON array in the text
    match = re.search(r'\[[\s\S]*\]', text)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return []


def _unsplash_url(photo_id: str, width: int = 400) -> str:
    return f"https://images.unsplash.com/{photo_id}?w={width}&q=80&auto=format&fit=crop"


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
    budget_fmt = f"€{total_budget:,}"

    # ── PHASE 1: Space Planner reads the PDF ────────────────────────────────
    yield _msg("SP", "Space Planner", "analyst",
               "Analysing property brochure — reading layout, room sizes, and architectural features...")

    property_summary = _call_vision(
        system=(
            "You are a professional space planner. Analyse the uploaded property brochure and extract: "
            "property name, location, total sqm, key rooms with approximate sizes, architectural features "
            "(stone walls, vaulted ceilings, fireplaces, arches, terraces, original floors), "
            "current condition, and the three most compelling design opportunities. "
            "Be specific and concise. Max 160 words."
        ),
        user_text=(
            f"Analyse this property. The client has a total budget of {budget_fmt}. "
            "What are the key spatial opportunities and constraints for a luxury interior designer?"
        ),
        pdf_b64=pdf_b64,
        max_tokens=400,
    )
    yield _msg("SP", "Space Planner", "analyst", property_summary)

    # ── PHASE 2: Style Agent sets the aesthetic brief ───────────────────────
    yield _msg("SA", "Style Agent", "designer",
               f"Setting aesthetic direction: {style['label']}. Drafting the design brief...")

    style_brief = _call(
        system=(
            "You are a luxury interior design Style Agent. "
            "Write a concise design brief (3 sentences) covering: colour palette, key materials, "
            "Italian vendors to use, and the emotional atmosphere to create. "
            "Be specific, opinionated, and reference the property's architectural features."
        ),
        user_text=(
            f"Design style: {style['label']}\n"
            f"Palette: {style['palette']}\n"
            f"Materials: {style['materials']}\n"
            f"Preferred vendors: {style['vendors']}\n"
            f"Avoid: {style['avoid']}\n"
            f"Property: {property_summary[:300]}\n"
            "Write the design brief."
        ),
        max_tokens=280,
    )
    yield _msg("SA", "Style Agent", "designer", style_brief)

    # ── PHASE 3: Room Agents each make their case ────────────────────────────
    room_proposals: dict[str, dict] = {}

    for room in ROOMS:
        ask_amt = int(total_budget * room["pct"])
        yield _msg(room["agent_id"], room["agent_name"], "room-agent",
                   f"Building case for {room['name']} — requesting €{ask_amt:,} ({int(room['pct']*100)}% of budget)...")

        proposal_text = _call(
            system=(
                f"You are the {room['agent_name']} advocating for the {room['name']} "
                "in a luxury Italian property renovation. "
                f"Design style: {style['label']}. Vendors to use: {style['vendors']}. "
                "Make a passionate budget case. Name 4 specific items you want to purchase "
                "with vendor and price. Start with your total ask and why this room deserves it. "
                "Be direct and specific. Max 160 words."
            ),
            user_text=(
                f"Property: {property_summary[:220]}\n"
                f"Total project budget: {budget_fmt}. "
                f"Make your case for €{ask_amt:,} for the {room['name']}."
            ),
            max_tokens=320,
        )
        room_proposals[room["id"]] = {
            "room": room,
            "proposal": proposal_text,
            "ask": ask_amt,
        }
        yield _msg(room["agent_id"], room["agent_name"], "room-agent", proposal_text)

    # ── PHASE 4: Budget Manager flags conflicts ──────────────────────────────
    total_asked = sum(v["ask"] for v in room_proposals.values())
    over_by = total_asked - total_budget
    all_proposals_text = "\n\n".join(
        [f"=== {v['room']['name']} (asking €{v['ask']:,}) ===\n{v['proposal']}"
         for v in room_proposals.values()]
    )

    yield _msg("BM", "Budget Manager", "budget",
               f"Total requested: €{total_asked:,} against budget of {budget_fmt} — "
               f"{'OVER by €' + f'{abs(over_by):,}' if over_by > 0 else 'within budget'}. "
               "Reviewing all proposals now...")

    budget_review = _call(
        system=(
            "You are a strict budget manager for a luxury renovation. "
            "Review the room proposals critically. "
            "Name specific items that must be cut or deferred, explain why, "
            "and propose a revised allocation that fits within the total budget. "
            "Be blunt. Push back on over-spending. Max 180 words."
        ),
        user_text=(
            f"Total budget: {budget_fmt}\n"
            f"Total requested: €{total_asked:,} (over by €{max(0, over_by):,})\n\n"
            f"{all_proposals_text}\n\n"
            "Provide your critical review. Name items to cut."
        ),
        max_tokens=350,
    )
    yield _msg("BM", "Budget Manager", "budget", budget_review)

    # ── PHASE 5: Room Agents push back on Budget Manager ────────────────────
    # Pick the highest-priority room agent to push back
    top_room = ROOMS[0]
    pushback = _call(
        system=(
            f"You are the {top_room['agent_name']}. The Budget Manager has just cut your budget. "
            "Push back firmly. Defend your most important items. "
            "Explain why cutting them would compromise the entire design vision. "
            "Be specific and passionate. Max 120 words."
        ),
        user_text=(
            f"Budget Manager review: {budget_review}\n\n"
            f"Your original proposal for {top_room['name']}: {room_proposals[top_room['id']]['proposal'][:300]}\n\n"
            "Defend your position."
        ),
        max_tokens=250,
    )
    yield _msg(top_room["agent_id"], top_room["agent_name"], "room-agent", pushback)

    # ── PHASE 6: Master Designer gives final ruling ──────────────────────────
    yield _msg("MD", "Master Designer", "master",
               "I have heard all arguments. Deliberating the final ruling...")

    final_ruling = _call(
        system=(
            "You are the Master Designer — the final authority on this renovation. "
            "You have heard the room agents argue and the budget manager push back. "
            "Give your definitive ruling: state the approved budget per room, "
            "name 2 approved items per room with vendor and price, "
            "and state 1 item cut per room with a clear reason. "
            "End with a single sentence vision for the finished property. Max 250 words."
        ),
        user_text=(
            f"Design brief: {style_brief}\n\n"
            f"Total budget: {budget_fmt}\n\n"
            f"Room proposals:\n{all_proposals_text}\n\n"
            f"Budget Manager review: {budget_review}\n\n"
            f"Living Room Agent pushback: {pushback}\n\n"
            "Give your final ruling."
        ),
        max_tokens=450,
    )
    yield _msg("MD", "Master Designer", "master", final_ruling)

    # ── PHASE 7: Generate furniture list per room ────────────────────────────
    furniture_by_room: dict[str, list[dict]] = {}
    img_map = FURNITURE_IMAGES.get(design_style, FURNITURE_IMAGES["warm-rustic"])

    for room in ROOMS:
        room_budget = int(total_budget * room["pct"])
        raw = _call(
            system=(
                f"You are a luxury interior designer specifying furniture for a {style['label']} "
                f"renovation of an Italian property. "
                "Return ONLY a valid JSON array with exactly 4 objects. "
                "Each object must have these keys: "
                '"name" (product name), "vendor" (Italian or international luxury brand), '
                '"price" (integer in EUR, realistic for luxury), "category" (e.g. Seating, Lighting, Storage, Textiles). '
                "No markdown, no explanation, just the JSON array."
            ),
            user_text=(
                f"Room: {room['name']}\n"
                f"Room budget: €{room_budget:,}\n"
                f"Style: {style['label']}\n"
                f"Palette: {style['palette']}\n"
                f"Preferred vendors: {style['vendors']}\n"
                f"Property context: {property_summary[:200]}\n\n"
                "Return 4 furniture items as a JSON array."
            ),
            max_tokens=400,
        )
        items = _parse_furniture_json(raw)
        # Assign Unsplash images
        img_ids = img_map.get(room["id"], img_map.get("living", []))
        for i, item in enumerate(items[:4]):
            item["image"] = _unsplash_url(img_ids[i]) if i < len(img_ids) else ""
        furniture_by_room[room["id"]] = items[:4]

    # ── PHASE 8: Emit structured result ─────────────────────────────────────
    allocations = []
    for room in ROOMS:
        allocations.append({
            "room": room["name"],
            "amount": int(total_budget * room["pct"]),
            "percentage": int(room["pct"] * 100),
        })
    allocated = sum(a["amount"] for a in allocations)
    allocations.append({
        "room": "Reserve / Contingency",
        "amount": total_budget - allocated,
        "percentage": 100 - sum(a["percentage"] for a in allocations),
    })

    # Room mood images (style-matched Unsplash)
    room_images = {
        room["id"]: _unsplash_url(
            room["unsplash_ids"].get(design_style, room["unsplash_ids"]["warm-rustic"]),
            width=800,
        )
        for room in ROOMS
    }

    yield _msg(
        "SYS", "System", "result",
        json.dumps({
            "type": "session_complete",
            "property_summary": property_summary,
            "style_label": style["label"],
            "style_vendors": style["vendors"],
            "total_budget": total_budget,
            "budget_allocations": allocations,
            "final_ruling": final_ruling,
            "furniture_by_room": furniture_by_room,
            "room_images": room_images,
            "rooms": [{"id": r["id"], "name": r["name"]} for r in ROOMS],
        }),
    )
