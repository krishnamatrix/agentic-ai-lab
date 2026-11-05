
from app.agents import tool_executor
import json
from typing import Any

from pydantic import ValidationError

from app.agents.tool_executor import ToolExecutionError
from app.llm.ollama import OllamaClient
from app.planning.models import ExecutionPlan, AgentDecision, PlanExecution
from app.tools.definitions import (
    SEARCH_COMPANIES_TOOL,
    SEARCH_INTERACTIONS_TOOL,
    SEARCH_KNOWLEDGE_TOOL,
    SEARCH_PEOPLE_TOOL,
)
from app.tools.registry import TOOLS


AVAILABLE_TOOL_DEFINITIONS = [
    SEARCH_COMPANIES_TOOL,
    SEARCH_PEOPLE_TOOL,
    SEARCH_INTERACTIONS_TOOL,
    SEARCH_KNOWLEDGE_TOOL,
]


PLANNER_SYSTEM_PROMPT = """
You are the planning component of a CRM intelligence agent.

Your task is to create a minimal, executable plan for the user's goal.

You will receive:
1. The user's goal.
2. The tools available to the agent.
3. The required structure for the plan.

Rules:
- Decide which tools are necessary from the user's goal.
- Do not include a tool merely because it is available.
- Use only the tools explicitly provided.
- Supply arguments that conform to each tool's schema.
- Each step must have a specific objective.
- State the evidence each step is intended to obtain.
- Prefer the smallest plan that can satisfy the goal.
- Do not invent CRM facts or tool results.
- Do not execute tools or claim that a step has succeeded.
- Do not generate unnecessary steps for information already available.
- Return only the requested structured plan.
"""


class Planner:
    def __init__(self, llm: OllamaClient | None = None):
        self.llm = llm or OllamaClient()


    def summarize_result(self, result, max_chars: int = 600) -> str:
        if result.status == "error":
            return f"Tool failed: {result.error}"

        text = json.dumps(result.result, default=str)

        if len(text) > max_chars:
            text = text[:max_chars] + "...[truncated]"

        return text
        
    async def decide_next(
        self,
        goal: str,
        plan: ExecutionPlan,
        execution: PlanExecution,
    ) -> AgentDecision:
        completed_ids = {
            result.step_id for result in execution.results
        }

        pending_steps = [
            step.model_dump(mode="json")
            for step in plan.steps
            if step.step_id not in completed_ids
        ]

        observed_results = [
            result.model_dump(mode="json")
            for result in execution.results
        ]

        context = {
            "goal": goal,
            "pending_steps": [
                step.model_dump(mode="json")
                for step in plan.steps
                if step.step_id not in {
                    result.step_id for result in execution.results
                }
            ],
            "completed_steps": [
                {
                    "step_id": result.step_id,
                    "tool_name": result.tool_name,
                    "status": result.status,
                    "result_summary": self.summarize_result(result),
                }
                for result in execution.results
            ],
            "available_tools": [
                definition["function"]["name"]
                for definition in AVAILABLE_TOOL_DEFINITIONS
            ],
            "evidence_assessments": execution.evidence_assessments,
        }

        decision_prompt = """
            You are the decision component of an adaptive CRM agent.

            Choose exactly one next action based on the user's goal and
            the evidence collected so far.

            Tool argument constraints:
            - Use only arguments defined by the selected tool's input schema.
            - For search_people, valid arguments are company_name, role, and name.
            - Do not use search_query or other unsupported fields.
            - Search existing CRM records; do not assume that a person or role exists.
            - If the available tools cannot establish the required evidence, explain
            the limitation rather than claiming that the question has been resolved.

            Actions:
            1. execute_planned_step
            Select one step_id from pending_steps.

            2. add_step
            Propose one new PlanStep when the existing plan does not
            cover an evidence gap revealed by the results.

            3. finish
            Finish when enough reliable evidence exists to address
            the user's goal. Do not finish merely because all planned
            steps have run if a material evidence gap remains.

            Decision output rules:

            1. execute_planned_step:
            - Set action to "execute_planned_step".
            - Set step_id to the ID of an existing pending step.
            - Do not include next_step.

            2. add_step:
            - Set action to "add_step".
            - Include next_step with a NEW, unique step_id.
            - Do not include the top-level step_id.
            - The new step must use an available tool and valid arguments.
            - Do not invent unsupported tool arguments.

            3. finish:
            - Set action to "finish".
            - Do not include step_id or next_step.

            Use prior evidence assessments when choosing the next action.

            - If required evidence is insufficient or conflicting, consider a
            useful additional search when an available tool can address the gap.
            - Do not repeat an identical search without a reason.
            - If no useful search remains, finish and explicitly acknowledge
            unresolved or conflicting evidence.
            - Never claim a fact is established merely because a tool executed
            successfully.

            Rules:
            - Use only tools listed in available_tools.
            - Never claim a tool succeeded unless observed_results
            contains its result.
            - Do not repeat completed steps.
            - Do not add steps that duplicate evidence already obtained.
            - If a step fails, do not treat its evidence as available.
            - Keep new steps narrowly focused on missing evidence.
            - Do not invent CRM facts.
            - The application will validate and execute your decision.
            - Return only the structured AgentDecision.

            For execute_planned_step, step_id is mandatory.
            It must exactly match the step_id of an existing pending step.

            Correct:
            {
            "action": "execute_planned_step",
            "reasoning": "Execute the pending security concerns search.",
            "step_id": ":4"
            }

            Incorrect:
            {
            "action": "execute_planned_step",
            "reasoning": "Execute step :4 to gather security concerns."
            }

            Mentioning a step ID in reasoning does not replace the step_id field.
            Return every required field in the JSON object.
        """

        response = await self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": decision_prompt,
                },
                {
                    "role": "user",
                    "content": json.dumps(context, default=str),
                },
            ],
            temperature=0.0,
            response_format=AgentDecision.model_json_schema(),
        )

        
        content = response.content

        if not content or not content.strip():
            print("\n=== EMPTY PLANNER RESPONSE ===")
            print(f"Provider: {response.provider}")
            print(f"Model: {response.model}")
            print(f"Content: {content!r}")
            print(f"Tool calls: {response.tool_calls}")
            print(f"Usage: {response.usage.model_dump()}")

            raise RuntimeError(
                "Planner returned empty content. "
                "Inspect the OllamaClient response parsing "
                "and the raw Ollama API response."
            )

        try:
            decision = AgentDecision.model_validate_json(content)
        except Exception as exc:
            print("\n=== INVALID PLANNER JSON ===")
            print(f"Content: {content!r}")
            print(f"Error type: {type(exc).__name__}")
            print(f"Validation error: {exc}")

            raise ValueError(
                "Planner returned non-empty but invalid AgentDecision JSON."
            ) from exc


        if decision.action == "execute_planned_step":
            pending_ids = {
                step["step_id"] for step in pending_steps
            }

            if decision.step_id not in pending_ids:
                raise ValueError(
                    "Planner selected a missing or already completed "
                    f"step: {decision.step_id}"
                )

        elif decision.action == "add_step":
            assert decision.next_step is not None

            existing_ids = {
                step.step_id for step in plan.steps
            }

            if decision.next_step.step_id in existing_ids:
                raise ValueError(
                    "Planner proposed a duplicate step ID: "
                    f"{decision.next_step.step_id}"
                )

            # Reuse the existing tool and argument validation.
            self.validate_plan(
                ExecutionPlan(
                    goal=goal,
                    steps=[decision.next_step],
                )
            )

        return decision

    async def create_plan(self, goal: str) -> ExecutionPlan:
        if not goal.strip():
            raise ValueError("Goal must not be empty.")

        tool_definitions = json.dumps(
            AVAILABLE_TOOL_DEFINITIONS,
            indent=2,
        )

        messages = [
            {
                "role": "system",
                "content": PLANNER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Goal:\n{goal}\n\n"
                    f"Available tool schemas:\n{tool_definitions}"
                ),
            },
        ]

        response = await self.llm.chat(
            messages=messages,
            temperature=0.0,
            response_format=ExecutionPlan.model_json_schema(),
        )

        try:
            plan = ExecutionPlan.model_validate_json(
                response.content
            )
        except ValidationError as exc:
            raise ValueError(
                f"Planner returned an invalid plan: {exc}"
            ) from exc

        self.validate_plan(plan)

        return plan

    @staticmethod
    def validate_plan(plan: ExecutionPlan) -> None:
        advertised_tools = {
            definition["function"]["name"]
            for definition in AVAILABLE_TOOL_DEFINITIONS
        }

        seen_step_ids: set[str] = set()

        for step in plan.steps:
            if step.step_id in seen_step_ids:
                raise ValueError(
                    f"Duplicate plan step ID: {step.step_id}"
                )

            seen_step_ids.add(step.step_id)

            if step.tool_name not in advertised_tools:
                raise ToolExecutionError(
                    f"Tool is not advertised to the planner: "
                    f"{step.tool_name}"
                )

            registered_tool = TOOLS.get(step.tool_name)

            if registered_tool is None:
                raise ToolExecutionError(
                    f"Tool is not registered: {step.tool_name}"
                )

            input_model = registered_tool["input_model"]

            try:
                validated_arguments = input_model.model_validate(
                    step.arguments
                )
            except ValidationError as exc:
                raise ValueError(
                    f"Invalid arguments for step "
                    f"'{step.step_id}' ({step.tool_name}): {exc}"
                ) from exc

            # Normalize the arguments to the registered input model.
            step.arguments = validated_arguments.model_dump(
                mode="json",
                exclude_unset=True,
            )
