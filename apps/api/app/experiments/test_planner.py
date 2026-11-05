
import asyncio
import json

from app.planning.planner import Planner


async def main() -> None:
    planner = Planner()

    goal = (
        "Prepare an account brief for Acme Corporation. "
        "Include its company profile, key contacts, recent "
        "interactions, security and integration concerns, "
        "and a recommended next action based on available "
        "CRM evidence."
    )

    plan = await planner.create_plan(goal)

    print("\n=== GENERATED PLAN ===")
    print(plan.model_dump_json(indent=2))

    print("\n=== PLANNING SUMMARY ===")
    print(f"Goal: {plan.goal}")
    print(f"Number of steps: {len(plan.steps)}")

    for step in plan.steps:
        print(
            json.dumps(
                {
                    "step_id": step.step_id,
                    "tool": step.tool_name,
                    "arguments": step.arguments,
                    "objective": step.objective,
                    "required_evidence": step.required_evidence,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
