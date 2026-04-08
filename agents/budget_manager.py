from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetManager:
    """
    Budget tracking + conflict detection (scaffold).

    For now this provides a deterministic allocation map that other agents can use.
    """

    def allocate(self, *, budget: int, design_mode: str) -> dict[str, int]:
        # Simple baseline splits; adjust later with learning/heuristics per mode.
        # Sum is exactly budget (handles rounding).
        weights = {
            "kitchen": 0.30,
            "living": 0.22,
            "bedroom": 0.18,
            "bathroom": 0.15,
            "lighting": 0.10,
            "contingency": 0.05,
        }

        allocations: dict[str, int] = {}
        remaining = budget
        keys = list(weights.keys())
        for k in keys[:-1]:
            amt = int(round(budget * weights[k]))
            amt = max(0, min(amt, remaining))
            allocations[k] = amt
            remaining -= amt

        allocations[keys[-1]] = max(0, remaining)
        allocations["_meta_design_mode"] = 0  # placeholder to show extensibility without changing schema
        allocations.pop("_meta_design_mode", None)
        return allocations
