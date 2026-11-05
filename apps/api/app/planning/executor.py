from app.planning.evaluation import decide_completion
from app.experiments import test_plan_execution
from app.planning.evaluation import SemanticEvidenceEvaluator
from typing import Any

from pydantic import ValidationError

from app.agents.tool_executor import execute_tool
from app.planning.models import (
    ExecutionPlan,
    PlanExecution,
    StepResult,
)
from app.planning.planner import Planner
from app.planning.evaluation import evaluate_step_result
from app.tools.registry import TOOLS


class PlanExecutor:
    def __init__(self, planner: Planner | None = None, 
        max_tool_calls: int = 10, max_decisions: int = 12, evidence_evaluator= None):
        self.planner = planner or Planner()
        self.max_tool_calls = max_tool_calls
        self.max_decisions = max_decisions
        if evidence_evaluator is not None:
            self.evidence_evaluator = evidence_evaluator
        elif hasattr(self.planner, "llm"):
            self.evidence_evaluator = SemanticEvidenceEvaluator(
                llm=self.planner.llm
            )
        else:
            # Allows scripted unit tests to run without an LLM client.
            self.evidence_evaluator = None

    async def execute_adaptive(
        self,
        goal: str,
        plan: ExecutionPlan | None = None,
    ) -> PlanExecution:
        if not goal.strip():
            raise ValueError("Goal must not be empty.")

        if plan is None:
            plan = await self.planner.create_plan(goal)

        # Validate even caller-supplied plans.
        self.planner.validate_plan(plan)

        execution = PlanExecution(
            plan=plan,
            status="running",
        )

        tool_calls = 0

        for decision_index in range(self.max_decisions):
            decision = await self.planner.decide_next(
                goal=goal,
                plan=plan,
                execution=execution,
            )

            print(
                f"[PLANNER DECISION] action={decision.action} "
                f"step_id={decision.step_id} "
                f"reasoning={decision.reasoning}"
            )

            if decision.action == "finish":
                completed_step_ids = {
                    result.step_id for result in execution.results
                }
                pending_steps = [
                    step
                    for step in plan.steps
                    if step.step_id not in completed_step_ids
                ]

                if pending_steps:
                    print(
                        "[FINISH REJECTED] "
                        f"{len(pending_steps)} planned step(s) remain pending: "
                        f"{[step.step_id for step in pending_steps]}"
                    )
                    continue

                if self.evidence_evaluator is not None:
                    results_by_step = {
                        result.step_id: result
                        for result in execution.results
                    }

                    evidence_assessments = []

                    for step in plan.steps:
                        result = results_by_step.get(step.step_id)
                        
                        if result is None:
                            continue

                        if not step.required_evidence:
                            print(
                                f"[EVIDENCE CHECK] Step {step.step_id} has no "
                                "required_evidence definition."
                            )
                            execution.status = "partial"
                            return execution

                        assessment = await self.evidence_evaluator.evaluate(
                            step,
                            result
                        )

                        evidence_assessments.append(
                            {
                                "step_id": step.step_id,
                                "findings": [
                                    finding.model_dump(mode="json")
                                    for finding in assessment.findings
                                ],
                            }
                        )

                    execution.evidence_assessments = evidence_assessments

                    findings = [
                        finding
                        for item in evidence_assessments
                        for finding in item["findings"]
                    ]

                    has_useful_next_step = (
                        tool_calls < self.max_tool_calls
                        and decision_index < self.max_decisions - 1
                    )

                    completion = decide_completion(
                        findings,
                        has_useful_next_step=has_useful_next_step,
                    )

                    print(f"[COMPLETION POLICY] decision={completion}")

                    if completion == "continue":
                        print(
                            "[FINISH REJECTED] Evidence remains unresolved. "
                            "Returning control to the planner."
                        )
                        continue

                    if completion == "complete_with_limitations":
                        execution.status = "partial"
                        print(
                            "[COMPLETION LIMITED] Evidence remains unresolved. "
                            "The final answer must disclose the limitations."
                        )
                        return execution

                    execution.status = "completed"
                    return execution

                results_by_step_deterministic = {
                    result.step_id: result
                    for result in execution.results
                }

                evaluations = []

                for step in plan.steps:
                    result = results_by_step_deterministic.get(step.step_id)

                    if result is None:
                        continue

                    evaluations.append(evaluate_step_result(step, result))

                empty_results = [
                    evaluation
                    for evaluation in evaluations
                    if not evaluation["has_data"]
                ]

                if empty_results:
                    print(
                        "[EVIDENCE CHECK] Cannot mark execution completed. "
                        "Some steps returned no observable data."
                    )

                    for evaluation in empty_results:
                        print(
                            f"  Step {evaluation['step_id']}: "
                            f"{evaluation['reason']}"
                        )

                    execution.status = "partial"
                    return execution
                
                # All planned steps executed and returned observable data.
                execution.status = (
                    "partial"
                    if any(
                        result.status == "error"
                        for result in execution.results
                    )
                    else "completed"
                )
                return execution


            if decision.action == "add_step":
                assert decision.next_step is not None

                if tool_calls >= self.max_tool_calls:
                    execution.status = "partial"
                    return execution

                # Validate against the current plan too.
                # The planner's validation alone is not the boundary.
                step = decision.next_step

                if any(
                    existing.step_id == step.step_id
                    for existing in plan.steps
                ):
                    execution.status = "failed"
                    return execution

                self.planner.validate_plan(
                    ExecutionPlan(
                        goal=goal,
                        steps=[step],
                    )
                )

                plan.steps.append(step)
                continue

            # execute_planned_step
            step = next(
                (
                    candidate
                    for candidate in plan.steps
                    if candidate.step_id == decision.step_id
                ),
                None,
            )

            if step is None:
                execution.status = "failed"
                return execution

            if tool_calls >= self.max_tool_calls:
                execution.status = "partial"
                return execution

            tool_calls += 1

            tool = TOOLS.get(step.tool_name)
            if tool is None:
                execution.results.append(
                    StepResult(
                        step_id=step.step_id,
                        tool_name=step.tool_name,
                        status="error",
                        error="Tool is not registered.",
                    )
                )
                continue

            try:
                input_model = tool["input_model"]
                validated_input = input_model.model_validate(
                    step.arguments
                )
                arguments = validated_input.model_dump(
                    mode="python",
                    exclude_unset=True,
                )

                result: Any = await execute_tool(
                    step.tool_name,
                    arguments,
                )

                if hasattr(result, "model_dump"):
                    result = result.model_dump(mode="json")

                execution.results.append(
                    StepResult(
                        step_id=step.step_id,
                        tool_name=step.tool_name,
                        status="success",
                        result=result,
                    )
                )

            except Exception as exc:
                execution.results.append(
                    StepResult(
                        step_id=step.step_id,
                        tool_name=step.tool_name,
                        status="error",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )

            # The next iteration asks the LLM what to do
            # after observing this step's result.

        # Safety limit reached without a finish decision.
        execution.status = "partial"
        return execution

    async def execute(
        self,
        plan: ExecutionPlan,
    ) -> PlanExecution:
        execution = PlanExecution(
            plan=plan,
            status="running",
        )

        for step in plan.steps:
            tool = TOOLS.get(step.tool_name)

            if tool is None:
                execution.results.append(
                    StepResult(
                        step_id=step.step_id,
                        tool_name=step.tool_name,
                        status="error",
                        error="Tool is not registered.",
                    )
                )
                execution.status = "failed"
                return execution

            try:
                input_model = tool["input_model"]
                validated_input = input_model.model_validate(
                    step.arguments
                )
                arguments = validated_input.model_dump(
                    mode="python",
                    exclude_unset=True,
                )

                result: Any = await execute_tool(
                    step.tool_name,
                    arguments,
                )

                if hasattr(result, "model_dump"):
                    result = result.model_dump(mode="json")

                execution.results.append(
                    StepResult(
                        step_id=step.step_id,
                        tool_name=step.tool_name,
                        status="success",
                        result=result,
                    )
                )

            except Exception as exc:
                execution.results.append(
                    StepResult(
                        step_id=step.step_id,
                        tool_name=step.tool_name,
                        status="error",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )

                # Initial policy: fail fast.
                # Later, we'll experiment with recovery and replanning.
                execution.status = "failed"
                return execution

        execution.status = "completed"
        return execution
