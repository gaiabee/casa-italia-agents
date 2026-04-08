from __future__ import annotations

from typing import Any


class BuildBriefAgent:
    name = "build_brief"

    async def run(self, *, design_mode: str, allocations: dict[str, Any], items: dict[str, Any]) -> str:
        # Contractor-facing text output (kept simple for scaffolding).
        lines: list[str] = []
        lines.append("Casa Italia — Build Brief (Scaffold)")
        lines.append(f"Design mode: {design_mode}")
        lines.append("")
        lines.append("Scope overview:")
        lines.append("- Validate field measurements (door swings, window heights, outlet positions).")
        lines.append("- Confirm paint schedule + finish schedule before ordering.")
        lines.append("")
        lines.append("Budget allocations (high level):")
        for k, v in allocations.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
        lines.append("Procurement notes:")
        lines.append("- Order long-lead items first (sofa, kitchen hardware, lighting).")
        lines.append("- Confirm return policies and delivery access (stairs/elevator).")
        lines.append("")
        lines.append("Draft items (scaffold):")
        for section, section_items in (items or {}).items():
            lines.append(f"- {section}: {len(section_items) if isinstance(section_items, list) else 'n/a'} items")
        return "\n".join(lines).strip()
