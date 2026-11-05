
from app.planning.evaluation import (
    evaluate_step_result,
    has_observable_data,
)
from app.planning.models import PlanStep, StepResult


def test_empty_search_result_has_no_observable_data():
    assert not has_observable_data({"data": [], "count": 0})


def test_nonempty_search_result_has_observable_data():
    assert has_observable_data({
        "data": [{"name": "Jane Smith"}],
        "count": 1,
    })


def test_empty_list_has_no_observable_data():
    assert not has_observable_data([])


def test_none_has_no_observable_data():
    assert not has_observable_data(None)


def test_evaluate_step_result_reports_empty_result():
    step = PlanStep(
        step_id="step_1",
        objective="Find Acme contacts.",
        tool_name="search_people",
        arguments={"company_name": "Acme Corporation"},
        required_evidence=["Contact records"],
    )

    result = StepResult(
        step_id="step_1",
        tool_name="search_people",
        status="success",
        result={"data": [], "count": 0},
    )

    evaluation = evaluate_step_result(step, result)

    assert evaluation["has_data"] is False
    assert evaluation["step_id"] == "step_1"
    assert evaluation["required_evidence"] == ["Contact records"]
