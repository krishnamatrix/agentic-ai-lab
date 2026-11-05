from app.experiments import test_plan_execution
import asyncio
import importlib

from app.planning.executor import PlanExecutor
from app.planning.models import AgentDecision, ExecutionPlan, PlanStep

executor_module = importlib.import_module("app.planning.executor")


class ScriptedPlanner:
    """Deterministic planner for testing executor control flow."""

    def __init__(self, decisions):
        self.decisions = iter(decisions)

    async def create_plan(self, goal):
        raise AssertionError("This test supplies the initial plan.")

    def validate_plan(self, plan):
        # Tool argument validation remains the executor's responsibility.
        return None

    async def decide_next(self, **kwargs):
        decision = next(self.decisions)

        if decision.action == "add_step":
            print(f"[PLAN UPDATE] Added step: {decision.next_step}")

        return decision


def test_adaptive_executor_executes_added_step(monkeypatch):
    goal = "Prepare an account brief for Acme Corporation."

    initial_step = PlanStep(
        step_id="step_1",
        objective="Find Acme contacts.",
        tool_name="search_people",
        arguments={"company_name": "Acme Corporation"},
        required_evidence=["Contact records"],
    )

    added_step = PlanStep(
        step_id="step_2",
        objective="Search for a security leader.",
        tool_name="search_people",
        arguments={
            "company_name": "Acme Corporation",
            "role": "CISO",
        },
        required_evidence=["Security leadership contact, if found"],
    )

    decisions = [
        AgentDecision(
            action="execute_planned_step",
            reasoning="Retrieve existing contacts.",
            step_id="step_1",
        ),
        AgentDecision(
            action="add_step",
            reasoning="Security ownership has not been established.",
            next_step=added_step,
        ),
        AgentDecision(
            action="execute_planned_step",
            reasoning="Execute the additional security contact search.",
            step_id="step_2",
        ),
        AgentDecision(
            action="finish",
            reasoning="The planned searches have completed.",
        ),
    ]

    tool_calls = []

    async def fake_execute_tool(tool_name, arguments):
        print(f"\n[TOOL CALL] {tool_name}")
        print(f"[TOOL INPUT] {arguments}")

        tool_calls.append((tool_name, arguments))
        result = {
            "data": [{"name": "Jane Smith"}],
            "count": 1,
        }

        print(f"[TOOL RESULT] {result}")
        return result

    monkeypatch.setattr(
        executor_module,
        "execute_tool",
        fake_execute_tool,
    )

    planner = ScriptedPlanner(decisions)
    executor = PlanExecutor(planner=planner)

    initial_plan = ExecutionPlan(
        goal=goal,
        steps=[initial_step],
    )

    execution = asyncio.run(
        executor.execute_adaptive(goal, plan=initial_plan)
    )

    print("\n=== FINAL EXECUTION STATE ===")
    print(f"Status: {execution.status}")
    print(f"Plan steps: {len(execution.plan.steps)}")

    for result in execution.results:
        print(
            f"Step: {result.step_id}, "
            f"tool: {result.tool_name}, "
            f"status: {result.status}, "
            f"result: {result.result}, "
            f"error: {result.error}"
        )

    assert execution.status == "completed"
    assert len(execution.plan.steps) == 2
    assert len(execution.results) == 2
    assert all(result.status == "success" for result in execution.results)

    assert [result.step_id for result in execution.results] == [
        "step_1",
        "step_2",
    ]

    assert len(tool_calls) == 2
    assert tool_calls[0][0] == "search_people"
    assert tool_calls[1][1]["role"] == "CISO"

    print("\n=== EXECUTION SUMMARY ===")
    print(f"Status: {execution.status}")
    print(f"Planned steps: {len(execution.plan.steps)}")
    print(f"Executed steps: {len(execution.results)}")
    print(
        f"Successful steps: "
        f"{sum(r.status == 'success' for r in execution.results)}"
    )
    print(
        f"Failed steps: "
        f"{sum(r.status == 'error' for r in execution.results)}"
    )

    print("\n=== PLAN EVOLUTION ===")
    for step in execution.plan.steps:
        print(f"{step.step_id}: {step.tool_name} -> planned")

    print("\n=== EXECUTION RESULTS ===")
    for result in execution.results:
        print(
            f"{result.step_id}: {result.tool_name} -> "
            f"{result.status}; result={result.result}"
        )
