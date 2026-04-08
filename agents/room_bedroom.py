from __future__ import annotations

from agents.orchestrator import _Msg


class BedroomRoomAgent:
    name = "room_bedroom"

    async def run(self, *, design_mode: str) -> _Msg:
        content = (
            "Bedroom advocate priorities:\n"
            "- Calm palette; reduce visual noise (closed storage, minimal surfaces).\n"
            "- Bed wall as the anchor: headboard + balanced bedside lighting.\n"
            "- Textiles: breathable layers (linen/cotton) with one richer accent."
        )
        return _Msg(agent=self.name, role="assistant", content=content, ts="", meta={"design_mode": design_mode})
