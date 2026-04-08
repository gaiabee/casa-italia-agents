from __future__ import annotations

from agents.orchestrator import _Msg


class KitchenRoomAgent:
    name = "room_kitchen"

    async def run(self, *, design_mode: str) -> _Msg:
        content = (
            "Kitchen advocate priorities:\n"
            "- Workflow: fridge–sink–cooktop triangle; keep prep surfaces uninterrupted.\n"
            "- Lighting: layered (task under-cabinet + ambient + statement pendant).\n"
            "- Materials: durable counters, easy-clean backsplash, warm hardware."
        )
        return _Msg(agent=self.name, role="assistant", content=content, ts="", meta={"design_mode": design_mode})
