
from app.planning.evaluation import (
    EvidenceFinding,
    decide_completion,
)


def finding(status):
    return EvidenceFinding(
        requirement="Identity of the security decision-maker",
        status=status,
        rationale="Test fixture.",
        evidence_quotes=[],
    )


def test_supported_evidence_allows_completion():
    assert decide_completion(
        [finding("supported")],
        has_useful_next_step=False,
    ) == "complete"


def test_conflicting_evidence_requires_more_work_if_possible():
    assert decide_completion(
        [finding("conflicting")],
        has_useful_next_step=True,
    ) == "continue"


def test_conflicting_evidence_allows_qualified_answer():
    assert decide_completion(
        [finding("conflicting")],
        has_useful_next_step=False,
    ) == "complete_with_limitations"


def test_insufficient_evidence_requires_more_work_if_possible():
    assert decide_completion(
        [finding("insufficient")],
        has_useful_next_step=True,
    ) == "continue"


def test_empty_findings_do_not_prove_completion():
    assert decide_completion(
        [],
        has_useful_next_step=False,
    ) == "continue"
