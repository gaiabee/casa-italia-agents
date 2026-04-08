from __future__ import annotations

from agents.orchestrator import _Msg


class SpacePlannerAgent:
    name = "space_planner"

    async def run(self, *, design_mode: str) -> _Msg:
        content = (
            "Space plan draft:\n"
            "- Define primary circulation paths and clearances (36\" walkways target).\n"
            "- Anchor each room with a focal point and a functional zone map.\n"
            f"- Mode-specific constraint: optimize layout for '{design_mode}'."
        )
        return _Msg(agent=self.name, role="assistant", content=content, ts="", meta={"design_mode": design_mode})
