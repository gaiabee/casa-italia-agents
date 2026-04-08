from __future__ import annotations

from agents.orchestrator import _Msg


class StyleAgent:
    name = "style_agent"

    async def run(self, *, design_mode: str) -> _Msg:
        content = (
            "Style direction draft:\n"
            "- Italian warmth with disciplined lines (stone/wood + crisp silhouettes).\n"
            "- Palette: warm neutrals, espresso/umber accents, brushed metal.\n"
            f"- Mode tweak: '{design_mode}' influences contrast and statement pieces."
        )
        return _Msg(agent=self.name, role="assistant", content=content, ts="", meta={"design_mode": design_mode})
