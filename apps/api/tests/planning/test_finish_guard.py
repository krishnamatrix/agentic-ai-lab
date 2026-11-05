
import asyncio
import importlib

from app.planning.executor import PlanExecutor
from app.planning.models import (
    AgentDecision,
    ExecutionPlan,
    PlanStep,
)
from tests.planning.test_executor_adaptive import ScriptedPlanner


executor_module = importlib.import_module("app.planning.executor")


def test_finish_is_rejected_when_step_is_pending(monkeypatch):
    step = PlanStep(
        step_id="step_1",
        objective="Find Acme contacts.",
        tool_name="search_people",
        arguments={"company_name": "Acme Corporation"},
        required_evidence=["Contact records"],
    )

    planner = ScriptedPlanner([
        AgentDecision(
            action="finish",
            reasoning="Attempt to finish before executing the pending step.",
        ),
        AgentDecision(
            action="execute_planned_step",
            reasoning="Execute the remaining contact lookup.",
            step_id="step_1",
        ),
        AgentDecision(
            action="finish",
            reasoning="The planned step has now executed.",
        ),
    ])

    async def fake_execute_tool(tool_name, arguments):
        return {"data": [], "count": 0}

    monkeypatch.setattr(
        executor_module,
        "execute_tool",
        fake_execute_tool,
    )

    execution = asyncio.run(
        PlanExecutor(planner=planner).execute_adaptive(
            "Prepare an account brief for Acme Corporation.",
            plan=ExecutionPlan(
                goal="Prepare an account brief for Acme Corporation.",
                steps=[step],
            ),
        )
    )

    assert execution.status == "partial"
    assert len(execution.results) == 1
    assert execution.results[0].step_id == "step_1"
