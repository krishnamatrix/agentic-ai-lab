
import asyncio
import json

import pytest

from app.planning.evaluation import (
    SemanticEvidenceAssessment,
    SemanticEvidenceEvaluator,
)
from app.planning.models import PlanStep, StepResult


class FakeLLM:
    def __init__(self, content):
        self.content = content

    async def chat(self, **kwargs):
        return type("FakeResponse", (), {"content": self.content})()


def make_step():
    return PlanStep(
        step_id="step_security",
        objective="Determine who owns security decisions.",
        tool_name="search_people",
        arguments={"company_name": "Acme Corporation"},
        required_evidence=[
            "Identity of the security decision-maker"
        ],
    )


def make_result(data):
    return StepResult(
        step_id="step_security",
        tool_name="search_people",
        status="success",
        result=data,
    )


def test_semantic_evaluator_accepts_supported_evidence():
    result_data = {
        "data": [
            {
                "name": "Jane Smith",
                "role": "VP of Engineering",
                "note": "Jane Smith raised security concerns.",
            }
        ],
        "count": 1,
    }

    assessment = SemanticEvidenceAssessment(
        findings=[
            {
                "requirement": "Identity of the security decision-maker",
                "status": "insufficient",
                "rationale": (
                    "Jane raised security concerns, but the record "
                    "does not establish decision-making authority."
                ),
                "evidence_quotes": [
                    "Jane Smith raised security concerns."
                ],
            }
        ]
    )

    evaluator = SemanticEvidenceEvaluator(
        FakeLLM(assessment.model_dump_json())
    )

    actual = asyncio.run(
        evaluator.evaluate(
            make_step(),
            make_result(result_data),
        )
    )

    assert actual.findings[0].status == "insufficient"
    assert actual.findings[0].evidence_quotes == [
        "Jane Smith raised security concerns."
    ]


def test_semantic_evaluator_rejects_invented_quote():
    assessment = SemanticEvidenceAssessment(
        findings=[
            {
                "requirement": "Identity of the security decision-maker",
                "status": "supported",
                "rationale": "The record identifies the decision-maker.",
                "evidence_quotes": ["Jane is the Acme CISO."],
            }
        ]
    )

    evaluator = SemanticEvidenceEvaluator(
        FakeLLM(assessment.model_dump_json())
    )

    with pytest.raises(ValueError, match="quote"):
        asyncio.run(
            evaluator.evaluate(
                make_step(),
                make_result(
                    {
                        "data": [{"name": "Jane Smith"}],
                        "count": 1,
                    }
                ),
            )
        )


def test_semantic_evaluator_rejects_missing_finding():
    assessment = SemanticEvidenceAssessment(findings=[])

    evaluator = SemanticEvidenceEvaluator(
        FakeLLM(assessment.model_dump_json())
    )

    with pytest.raises(ValueError, match="exactly one finding"):
        asyncio.run(
            evaluator.evaluate(
                make_step(),
                make_result(
                    {
                        "data": [{"name": "Jane Smith"}],
                        "count": 1,
                    }
                ),
            )
        )

def test_semantic_evaluator_accepts_conflicting_evidence():
    result_data = {
        "data": [
            {"name": "Jane Smith", "note":
             "Jane Smith is the security decision-maker."},
            {"name": "Alex Morgan", "note":
             "Alex Morgan is the security decision-maker."},
        ],
        "count": 2,
    }

    assessment = SemanticEvidenceAssessment(
        findings=[
            {
                "requirement": "Identity of the security decision-maker",
                "status": "conflicting",
                "rationale": (
                    "Two records identify different people as the "
                    "security decision-maker."
                ),
                "evidence_quotes": [
                    "Jane Smith is the security decision-maker.",
                    "Alex Morgan is the security decision-maker.",
                ],
            }
        ]
    )

    evaluator = SemanticEvidenceEvaluator(
        FakeLLM(assessment.model_dump_json())
    )

    actual = asyncio.run(
        evaluator.evaluate(make_step(), make_result(result_data))
    )

    assert actual.findings[0].status == "conflicting"
    assert len(actual.findings[0].evidence_quotes) == 2