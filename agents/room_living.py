from __future__ import annotations

from agents.orchestrator import _Msg


class LivingRoomAgent:
    name = "room_living"

    async def run(self, *, design_mode: str) -> _Msg:
        content = (
            "Living room advocate priorities:\n"
            "- Seating geometry that supports conversation (avoid TV-only layouts).\n"
            "- One hero piece (sofa or rug) + supporting textures (linen, wool, leather).\n"
            "- Lighting: floor lamp + table lamp + dimmable overhead."
        )
        return _Msg(agent=self.name, role="assistant", content=content, ts="", meta={"design_mode": design_mode})
