import json
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from app.planning.models import PlanStep, StepResult


def has_observable_data(value: Any) -> bool:
    """Return whether a tool result contains observable data."""

    if value is None:
        return False

    if isinstance(value, (list, tuple)):
        return len(value) > 0

    if isinstance(value, dict):
        # Handle common search-tool response formats.
        for key in ("data", "results", "records", "items"):
            if key in value:
                return has_observable_data(value[key])

        if "count" in value:
            count = value["count"]
            if isinstance(count, (int, float)) and not isinstance(count, bool):
                return count > 0

        return bool(value)

    if isinstance(value, str):
        return bool(value.strip())

    return True


def evaluate_step_result(
    step: PlanStep,
    result: StepResult,
) -> dict[str, Any]:
    """Evaluate whether a step returned records for further inspection."""

    if result.status != "success":
        return {
            "step_id": step.step_id,
            "has_data": False,
            "reason": f"Step execution status is {result.status}.",
            "required_evidence": step.required_evidence,
        }

    has_data = has_observable_data(result.result)

    return {
        "step_id": step.step_id,
        "has_data": has_data,
        "reason": (
            "Tool returned observable data."
            if has_data
            else "Tool returned no observable data."
        ),
        "required_evidence": step.required_evidence,
    }


class EvidenceFinding(BaseModel):
    """Assessment of one required fact against supplied evidence."""

    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=1)
    status: Literal[
        "supported",
        "contradicted",
        "insufficient",
        "not_found",
        "conflicting",
    ]
    rationale: str = Field(min_length=1)
    evidence_quotes: list[str] = Field(default_factory=list)


class SemanticEvidenceAssessment(BaseModel):
    """Structured semantic assessment of a step's evidence."""

    model_config = ConfigDict(extra="forbid")

    findings: list[EvidenceFinding]


class SemanticEvidenceEvaluator:
    """Use an LLM to assess evidence without treating inference as fact."""

    def __init__(self, llm):
        self.llm = llm

    async def evaluate(
        self,
        step: PlanStep,
        result: StepResult,
    ) -> SemanticEvidenceAssessment:
        if result.status != "success":
            return SemanticEvidenceAssessment(
                findings=[
                    EvidenceFinding(
                        requirement=requirement,
                        status="insufficient",
                        rationale=(
                            f"The tool execution status was "
                            f"{result.status}; its output cannot be "
                            "treated as successful evidence."
                        ),
                    )
                    for requirement in step.required_evidence
                ]
            )

        evidence_json = json.dumps(
            result.result,
            ensure_ascii=False,
            default=str,
        )

        prompt = {
            "task": (
                "Assess each required evidence item using only the "
                "provided tool result. Do not use outside knowledge. "
                "Do not infer decision authority from a job title alone."
            ),
            "requirements": step.required_evidence,
            "tool_name": step.tool_name,
            "tool_objective": step.objective,
            "tool_result": result.result,
            "status_definitions": {
                "supported": (
                    "The supplied result directly supports the requirement."
                ),
                "contradicted": (
                    "The supplied result contains evidence against it."
                ),
                "insufficient": (
                    "The result is relevant but does not establish "
                    "the requirement."
                ),
                "not_found": (
                    "The search returned no matching evidence for "
                    "the requirement. This does not prove the fact "
                    "does not exist."
                ),
                "conflicting": (
                    "Two or more supplied records make materially incompatible "
                    "claims about the same requirement, and the conflict cannot "
                    "be resolved from the supplied evidence."
                ),
            },
            "rules": [
                "Return one finding for every requirement.",
                "Use exact quotes copied from the tool result.",
                "Never invent names, facts, or quotes.",
                "Do not infer decision authority from a job title alone.",
                "If records identify different people as the same exclusive "
                "decision-maker, classify the finding as conflicting unless "
                "the evidence resolves the discrepancy.",
                "Do not classify evidence as supported merely because at least "
                "one record supports the claim when another record materially "
                "contradicts it.",
            ],
        }

        response = await self.llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict evidence evaluator. "
                        "Evaluate only the supplied records. "
                        "Return JSON matching the requested schema."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt, ensure_ascii=False),
                },
            ],
            temperature=0.0,
            response_format=SemanticEvidenceAssessment.model_json_schema(),
        )

        assessment = SemanticEvidenceAssessment.model_validate_json(
            response.content
        )

        # Require the evaluator to assess every requirement exactly once.
        expected = step.required_evidence
        actual = [finding.requirement for finding in assessment.findings]

        if len(actual) != len(expected) or sorted(actual) != sorted(expected):
            raise ValueError(
                "Semantic evaluator must return exactly one finding "
                "for each required evidence item."
            )

        # Verify that any quoted evidence actually occurs in the tool result.
        for finding in assessment.findings:
            for quote in finding.evidence_quotes:
                if not quote or quote not in evidence_json:
                    raise ValueError(
                        "Semantic evaluator returned a quote that "
                        "does not occur in the supplied tool result."
                    )

        return assessment


CompletionDecision = Literal[
    "complete",
    "continue",
    "complete_with_limitations",
]


def decide_completion(
    findings: list[EvidenceFinding],
    has_useful_next_step: bool,
) -> CompletionDecision:
    """Apply a deterministic policy to semantic evidence findings."""

    if not findings:
        return "continue"

    statuses = {finding.status for finding in findings}

    if "conflicting" in statuses:
        return (
            "continue"
            if has_useful_next_step
            else "complete_with_limitations"
        )

    if "insufficient" in statuses:
        return (
            "continue"
            if has_useful_next_step
            else "complete_with_limitations"
        )

    if "not_found" in statuses:
        return (
            "continue"
            if has_useful_next_step
            else "complete_with_limitations"
        )

    if "contradicted" in statuses:
        return (
            "continue"
            if has_useful_next_step
            else "complete_with_limitations"
        )

    return "complete"
