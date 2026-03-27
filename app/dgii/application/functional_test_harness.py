from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FunctionalScenarioResult:
    scenario_id: str
    passed: bool
    detail: str


class FunctionalTestHarness:
    """Container for functional DGII scenario execution metadata."""

    def run_scenario(self, scenario_id: str, condition: bool, detail: str) -> FunctionalScenarioResult:
        return FunctionalScenarioResult(scenario_id=scenario_id, passed=condition, detail=detail)
