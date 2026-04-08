from __future__ import annotations

from agents.orchestrator import _Msg


class BathroomRoomAgent:
    name = "room_bathroom"

    async def run(self, *, design_mode: str) -> _Msg:
        content = (
            "Bathroom advocate priorities:\n"
            "- Durable, slip-aware flooring; prioritize easy maintenance.\n"
            "- Mirror + vanity lighting that flatters (avoid harsh overhead-only).\n"
            "- Storage: recessed/medicine cabinet strategy to keep counters clear."
        )
        return _Msg(agent=self.name, role="assistant", content=content, ts="", meta={"design_mode": design_mode})
