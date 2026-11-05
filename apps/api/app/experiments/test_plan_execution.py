
import asyncio
import json

from app.planning.executor import PlanExecutor


async def main() -> None:
    executor = PlanExecutor()

    goal = (
        "Prepare an account brief for Acme Corporation, including its profile, "
        "key contacts, recent interactions, and security concerns. "
        "Determine whether the available evidence explicitly identifies the "
        "person responsible for security decisions. If that responsibility "
        "is not established, add a new step to investigate the gap before "
        "finishing. Do not assume a person's role from their job title alone."
    )

    # Generate the plan dynamically, then execute it.
    execution = await executor.execute_adaptive(goal)

    print("\n=== EXECUTION RESULTS ===")
    print(execution.model_dump_json(indent=2))

    print("\n=== EXECUTION SUMMARY ===")
    print(f"Status: {execution.status}")
    print(f"Planned steps: {len(execution.plan.steps)}")
    print(f"Executed steps: {len(execution.results)}")
    print(
        "Successful steps:",
        sum(r.status == "success" for r in execution.results),
    )
    print(
        "Failed steps:",
        sum(r.status == "error" for r in execution.results),
    )
    print("\n=== PLAN EVOLUTION ===")
    for result in execution.results:
        print(
            f"{result.step_id}: "
            f"{result.tool_name} -> {result.status}"
        )


if __name__ == "__main__":
    asyncio.run(main())
