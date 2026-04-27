from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import AsyncGenerator

import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ROOM_AGENTS = {
    "kitchen": {
        "name": "Kitchen Agent",
        "role": "La Cucina Specialist",
        "emoji": "☕",
        "system": "You are the Kitchen Agent for Casa Italia, a Tuscan farmhouse renovation. You passionately advocate for the kitchen budget. You speak with Italian flair, referencing authentic Tuscan cooking culture. Be specific about items: appliances, marble countertops, handmade tiles. Keep response to 2-3 sentences.",
        "budget_share": 0.28,
    },
    "living": {
        "name": "Living Room Agent",
        "role": "Il Salotto Specialist",
        "emoji": "🛋️",
        "system": "You are the Living Room Agent for Casa Italia, a Tuscan farmhouse renovation. You advocate for creating a warm, inviting Italian living space. Reference specific items: linen sofas, Murano glass lamps, handwoven rugs, antique side tables. Keep response to 2-3 sentences.",
        "budget_share": 0.35,
    },
    "bedroom": {
        "name": "Bedroom Agent",
        "role": "La Camera Specialist",
        "emoji": "🌙",
        "system": "You are the Bedroom Agent for Casa Italia, a Tuscan farmhouse renovation. You advocate for a serene, luxurious Italian bedroom. Reference specific items: Frette linens, blackout shutters, a reading armchair, artisan bedside lamps. Keep response to 2-3 sentences.",
        "budget_share": 0.25,
    },
    "bathroom": {
        "name": "Bathroom Agent",
        "role": "Il Bagno Specialist",
        "emoji": "🛁",
        "system": "You are the Bathroom Agent for Casa Italia, a Tuscan farmhouse renovation. You advocate for a spa-like Italian bathroom. Reference specific items: travertine tiles, a rainfall shower, Salvatori stone accessories, heated towel rails. Keep response to 2-3 sentences.",
        "budget_share": 0.12,
    },
}

DESIGN_MODE_DESCRIPTIONS = {
    "rustic-italian": "Rustic Italian — favor artisan craftsmanship, terracotta, linen, and regionally sourced materials. Every piece should feel rooted in Tuscan tradition.",
    "functional": "Functional — prioritize practicality, durability, and clean lines. Minimize decorative spending, maximize usability.",
    "entertaining": "Entertaining — prioritize spaces for hosting guests. Invest in the kitchen and living areas. Create memorable shared spaces.",
    "feng-shui": "Feng Shui — prioritize flow, natural light, and balance. Avoid clutter. Invest in quality over quantity.",
}


def ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def call_claude(system: str, user: str, max_tokens: int = 150) -> str:
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": user}],
        system=system,
    )
    return message.content[0].text


async def run_session(
    design_mode: str, total_budget: int, rooms: list[str]
) -> AsyncGenerator[dict, None]:
    mode_desc = DESIGN_MODE_DESCRIPTIONS.get(
        design_mode, DESIGN_MODE_DESCRIPTIONS["rustic-italian"]
    )

    # --- Space Planner ---
    yield {
        "agent": "Space Planner",
        "role": "Tier 1 — Spatial Analyst",
        "content": call_claude(
            "You are the Space Planner for Casa Italia, a 180sqm Tuscan farmhouse. You analyze spatial flow and set constraints for room agents. Be concise — 2 sentences.",
            f"Briefly assess the spatial priorities for this renovation. Design mode: {mode_desc}. Total budget: €{total_budget:,}. Rooms in scope: {', '.join(rooms)}.",
        ),
        "ts": ts(),
    }

    # --- Style Agent ---
    yield {
        "agent": "Style Agent",
        "role": "Tier 1 — Design Director",
        "content": call_claude(
            "You are the Style Agent for Casa Italia. You set the cross-room design language that all room agents must follow. Be specific about palette, materials, and mood. 2 sentences.",
            f"Set the design language for this renovation. Design mode: {mode_desc}.",
        ),
        "ts": ts(),
    }

    # --- Room Agents propose budgets ---
    room_requests: dict[str, int] = {}
    for room_key in rooms:
        if room_key not in ROOM_AGENTS:
            continue
        agent = ROOM_AGENTS[room_key]
        requested = int(total_budget * agent["budget_share"])
        room_requests[room_key] = requested

        content = call_claude(
            agent["system"],
            f"Argue for your budget allocation of €{requested:,} out of the total €{total_budget:,} budget. Design mode: {mode_desc}. Be passionate and specific.",
        )
        yield {
            "agent": agent["name"],
            "role": agent["role"],
            "content": f"{agent['emoji']} Requesting €{requested:,} — {content}",
            "ts": ts(),
        }

    # --- Budget Manager flags conflicts ---
    total_requested = sum(room_requests.values())
    over_by = total_requested - total_budget
    bm_prompt = f"Total requested: €{total_requested:,}. Total budget: €{total_budget:,}. {'Over budget by €' + str(over_by) + '.' if over_by > 0 else 'Within budget.'} Rooms: {', '.join(f'{k}: €{v:,}' for k, v in room_requests.items())}. Flag the conflict and suggest cuts. 2-3 sentences."

    yield {
        "agent": "Budget Manager",
        "role": "Neutral Referee",
        "content": call_claude(
            "You are the Budget Manager for Casa Italia. You track the global budget pool and flag conflicts when room agents overspend. Be direct and analytical. 2-3 sentences.",
            bm_prompt,
        ),
        "ts": ts(),
    }

    # --- Master Designer final ruling ---
    room_summary = ". ".join(
        f"{ROOM_AGENTS[r]['name']} requested €{room_requests[r]:,}"
        for r in rooms
        if r in ROOM_AGENTS
    )
    final_allocations = {
        r: int(total_budget * ROOM_AGENTS[r]["budget_share"] * (total_budget / max(total_requested, 1)))
        for r in rooms
        if r in ROOM_AGENTS
    }

    yield {
        "agent": "Master Designer",
        "role": "Final Arbitrator",
        "content": call_claude(
            "You are the Master Designer for Casa Italia — the final arbitrator. You review all agent proposals and issue binding decisions. Be authoritative and decisive. 3 sentences max.",
            f"Issue your final ruling. {room_summary}. Design mode: {mode_desc}. Total budget: €{total_budget:,}. Allocate fairly and justify your decision.",
            max_tokens=200,
        ),
        "ts": ts(),
    }

    # --- Final result summary ---
    approved_items_by_room = {
        "kitchen": ["Smeg refrigerator", "Bertazzoni range", "Marble backsplash", "Handmade ceramic tiles", "Espresso station"],
        "living": ["Flexform linen sofa", "Flos floor lamp", "Handwoven Sardinian rug", "Antique side tables", "Botanical prints"],
        "bedroom": ["Frette duvet set", "Busatti blackout curtains", "Flos bedside lamps", "Poltrona Frau armchair", "Magniflex mattress topper"],
        "bathroom": ["Travertine floor tiles", "Gessi rainfall shower", "Salvatori stone accessories", "Scirocco towel warmer", "Frette towels"],
    }

    yield {
        "agent": "System",
        "role": "Session Complete",
        "content": "Design session complete. All agents have reached consensus.",
        "ts": ts(),
        "meta": {
            "final_allocations": final_allocations,
            "approved_items": {r: approved_items_by_room.get(r, []) for r in rooms if r in ROOM_AGENTS},
            "total_approved": sum(final_allocations.values()),
        },
    }
