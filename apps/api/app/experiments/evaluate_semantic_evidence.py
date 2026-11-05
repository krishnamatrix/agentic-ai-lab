
import asyncio

from app.planning.evaluation import SemanticEvidenceEvaluator
from app.planning.models import PlanStep, StepResult
from app.planning.planner import Planner


CASES = [
    {
        "id": "security_001",
        "description": "A contact raised concerns but ownership is unproven.",
        "requirement": "Identity of the security decision-maker",
        "result": {
            "data": [
                {
                    "name": "Jane Smith",
                    "role": "VP of Engineering",
                    "note": "Jane Smith raised security concerns.",
                }
            ],
            "count": 1,
        },
        "expected": "insufficient",
    },
    {
        "id": "security_002",
        "description": "A record explicitly identifies the decision-maker.",
        "requirement": "Identity of the security decision-maker",
        "result": {
            "data": [
                {
                    "name": "Alex Morgan",
                    "role": "CISO",
                    "note": (
                        "Alex Morgan is the designated decision-maker "
                        "for Acme Corporation's security reviews."
                    ),
                }
            ],
            "count": 1,
        },
        "expected": "supported",
    },
    {
        "id": "security_003",
        "description": "The search returned no matching contacts.",
        "requirement": "Identity of the security decision-maker",
        "result": {
            "data": [],
            "count": 0,
        },
        "expected": "not_found",
    },
    {
        "id": "security_004",
        "description": "The record explicitly denies the proposed claim.",
        "requirement": "John Doe is the security decision-maker",
        "result": {
            "data": [
                {
                    "name": "John Doe",
                    "note": (
                        "John Doe is not the security decision-maker. "
                        "Security decisions are owned by Alex Morgan."
                    ),
                }
            ],
            "count": 1,
        },
        "expected": "contradicted",
    },
    {
        "id": "security_005",
        "description": "CRM records disagree about security ownership.",
        "requirement": "Identity of the security decision-maker",
        "result": {
            "data": [
                {
                    "name": "Jane Smith",
                    "note": "Jane Smith is the security decision-maker.",
                },
                {
                    "name": "Alex Morgan",
                    "note": "Alex Morgan is the security decision-maker.",
                },
            ],
            "count": 2,
        },
        "expected": "conflicting",
    },
]


async def main():
    planner = Planner()
    evaluator = SemanticEvidenceEvaluator(llm=planner.llm)

    correct = 0
    false_supports = 0
    results = []

    for case in CASES:
        step = PlanStep(
            step_id=case["id"],
            objective=case["description"],
            tool_name="search_people",
            arguments={"company_name": "Acme Corporation"},
            required_evidence=[case["requirement"]],
        )

        tool_result = StepResult(
            step_id=case["id"],
            tool_name="search_people",
            status="success",
            result=case["result"],
        )

        try:
            assessment = await evaluator.evaluate(step, tool_result)
            finding = assessment.findings[0]
            actual = finding.status

            passed = actual == case["expected"]
            correct += int(passed)

            if (
                actual == "supported"
                and case["expected"] != "supported"
            ):
                false_supports += 1

            results.append(
                {
                    "id": case["id"],
                    "expected": case["expected"],
                    "actual": actual,
                    "passed": passed,
                }
            )

            print(f"\n[{case['id']}] {case['description']}")
            print(f"Expected: {case['expected']}")
            print(f"Actual:   {actual}")
            print(f"Rationale: {finding.rationale}")
            print(f"Evidence quotes: {finding.evidence_quotes}")
            print(f"Result: {'PASS' if passed else 'FAIL'}")

        except Exception as exc:
            results.append(
                {
                    "id": case["id"],
                    "expected": case["expected"],
                    "actual": "evaluation_error",
                    "passed": False,
                }
            )
            print(f"\n[{case['id']}] EVALUATION ERROR: {exc}")

    total = len(CASES)

    print("\n=== SEMANTIC EVALUATION SUMMARY ===")
    print(f"Cases: {total}")
    print(f"Correct classifications: {correct}/{total}")
    print(f"Accuracy: {correct / total:.1%}")
    print(f"False supported claims: {false_supports}")
    print(f"Evaluation errors: {sum(r['actual'] == 'evaluation_error' for r in results)}")


if __name__ == "__main__":
    asyncio.run(main())
