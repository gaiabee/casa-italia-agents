from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from dotenv import load_dotenv

from agents.budget_manager import BudgetManager
from agents.build_brief import BuildBriefAgent
from agents.room_bathroom import BathroomRoomAgent
from agents.room_bedroom import BedroomRoomAgent
from agents.room_kitchen import KitchenRoomAgent
from agents.room_living import LivingRoomAgent
from agents.space_planner import SpacePlannerAgent
from agents.sourcing_agent import SourcingAgent
from agents.style_agent import StyleAgent

load_dotenv()


@dataclass(frozen=True)
class AgentMessage:
    agent: str
    role: str
    content: str
    ts: str
    meta: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "role": self.role,
            "content": self.content,
            "ts": self.ts,
            "meta": self.meta,
        }


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Orchestrator:
    """
    Master Designer agent (Claude 3.5 Sonnet via Anthropic SDK).

    This scaffold keeps the Anthropic call optional so the system runs even
    without API keys during early development / demos.
    """

    def __init__(self, *, enable_llm: Optional[bool] = None) -> None:
        self.enable_llm = enable_llm if enable_llm is not None else bool(os.getenv("ANTHROPIC_API_KEY"))

        self.space_planner = SpacePlannerAgent()
        self.style_agent = StyleAgent()

        self.kitchen = KitchenRoomAgent()
        self.living = LivingRoomAgent()
        self.bedroom = BedroomRoomAgent()
        self.bathroom = BathroomRoomAgent()

        self.budget_manager = BudgetManager()
        self.sourcing_agent = SourcingAgent()
        self.build_brief = BuildBriefAgent()

    async def run(self, *, design_mode: str, budget: int) -> dict[str, Any]:
        agent_messages: list[AgentMessage] = []

        agent_messages.append(
            AgentMessage(
                agent="orchestrator",
                role="system",
                content="Casa Italia orchestration started.",
                ts=_iso_now(),
                meta={"design_mode": design_mode, "budget": budget, "llm_enabled": self.enable_llm},
            )
        )

        # 1) High-level intent: optionally ask Claude for an overall direction.
        if self.enable_llm:
            llm_summary = await self._anthropic_master_summary(design_mode=design_mode, budget=budget)
            agent_messages.append(
                AgentMessage(
                    agent="orchestrator",
                    role="assistant",
                    content=llm_summary,
                    ts=_iso_now(),
                    meta={"model": "claude-3-5-sonnet-latest"},
                )
            )
        else:
            agent_messages.append(
                AgentMessage(
                    agent="orchestrator",
                    role="assistant",
                    content=(
                        f"Working in offline mode. Using deterministic heuristics for design_mode='{design_mode}'."
                    ),
                    ts=_iso_now(),
                    meta={"reason": "missing ANTHROPIC_API_KEY or enable_llm=False"},
                )
            )

        # 2) Specialist agents.
        agent_messages.extend(
            [
                (await self.style_agent.run(design_mode=design_mode))._replace_ts(_iso_now()),
                (await self.space_planner.run(design_mode=design_mode))._replace_ts(_iso_now()),
                (await self.kitchen.run(design_mode=design_mode))._replace_ts(_iso_now()),
                (await self.living.run(design_mode=design_mode))._replace_ts(_iso_now()),
                (await self.bedroom.run(design_mode=design_mode))._replace_ts(_iso_now()),
                (await self.bathroom.run(design_mode=design_mode))._replace_ts(_iso_now()),
            ]
        )

        allocations = self.budget_manager.allocate(budget=budget, design_mode=design_mode)
        agent_messages.append(
            AgentMessage(
                agent="budget_manager",
                role="assistant",
                content="Proposed allocations by room/category.",
                ts=_iso_now(),
                meta={"allocations": allocations},
            )
        )

        sourcing = await self.sourcing_agent.source(
            design_mode=design_mode,
            allocations=allocations,
        )
        agent_messages.append(
            AgentMessage(
                agent="sourcing_agent",
                role="assistant",
                content="Draft product list and sourcing plan.",
                ts=_iso_now(),
                meta={"items": sourcing},
            )
        )

        brief = await self.build_brief.run(
            design_mode=design_mode,
            allocations=allocations,
            items=sourcing,
        )
        agent_messages.append(
            AgentMessage(
                agent="build_brief",
                role="assistant",
                content=brief,
                ts=_iso_now(),
                meta={},
            )
        )

        return {
            "agent_messages": [m.as_dict() for m in agent_messages],
            "allocations": allocations,
            "items": sourcing,
        }

    async def _anthropic_master_summary(self, *, design_mode: str, budget: int) -> str:
        """
        Minimal Anthropic SDK usage. If the SDK/API changes, this is the only
        method that should need updates.
        """

        try:
            from anthropic import AsyncAnthropic  # type: ignore
        except Exception:
            return (
                "Anthropic SDK not available at runtime; continuing in offline mode "
                f"for design_mode='{design_mode}'."
            )

        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        prompt = (
            "You are the Master Designer for Casa Italia, an interior design multi-agent system. "
            "Provide a concise north-star design direction for the given mode and budget. "
            "Output 5 bullets: (1) concept, (2) palette/materials, (3) lighting, (4) key hero pieces, "
            "(5) what to avoid. Keep it under 140 words.\n\n"
            f"design_mode: {design_mode}\n"
            f"budget: {budget}\n"
        )

        resp = await client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=300,
            temperature=0.4,
            messages=[{"role": "user", "content": prompt}],
        )

        # Anthropic returns content as a list of blocks; keep it simple.
        parts: list[str] = []
        for block in getattr(resp, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts).strip() or "Master summary unavailable."


# Small helper so leaf agents can be tiny and still produce AgentMessage.
class _Msg(AgentMessage):
    def _replace_ts(self, ts: str) -> "AgentMessage":
        return AgentMessage(agent=self.agent, role=self.role, content=self.content, ts=ts, meta=self.meta)
