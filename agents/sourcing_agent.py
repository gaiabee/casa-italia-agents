from __future__ import annotations

from typing import Any


class SourcingAgent:
    name = "sourcing_agent"

    async def source(self, *, design_mode: str, allocations: dict[str, int]) -> dict[str, Any]:
        """
        Product sourcing agent (scaffold).

        Returns a dict shaped for easy UI rendering:
        - items[room] = list[ {name, category, est_price, notes} ]
        """

        def item(name: str, category: str, est_price: int, notes: str) -> dict[str, Any]:
            return {"name": name, "category": category, "est_price": est_price, "notes": notes}

        kitchen_budget = allocations.get("kitchen", 0)
        living_budget = allocations.get("living", 0)

        return {
            "kitchen": [
                item(
                    "Pull-down kitchen faucet (brushed steel)",
                    "fixture",
                    max(150, int(kitchen_budget * 0.03)) if kitchen_budget else 250,
                    f"Match mode '{design_mode}' with warm metals if needed.",
                ),
                item(
                    "Under-cabinet LED light kit (dimmable)",
                    "lighting",
                    180,
                    "Prioritize high CRI (90+).",
                ),
            ],
            "living": [
                item(
                    "Wool-blend area rug (neutral)",
                    "textile",
                    max(300, int(living_budget * 0.10)) if living_budget else 800,
                    "Anchors seating; size to place front legs on rug.",
                ),
                item(
                    "Floor lamp (dimmable)",
                    "lighting",
                    220,
                    "Warm 2700K bulb target.",
                ),
            ],
            "bedroom": [
                item("Linen bedding set", "textile", 260, "Breathable; add one accent throw."),
            ],
            "bathroom": [
                item("Mirror with slim frame", "fixture", 190, "Consider integrated defogger."),
            ],
        }
