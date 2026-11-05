
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlanStep(BaseModel):
    """One executable step in an agent plan."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    required_evidence: list[str] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """Structured plan for achieving a user goal."""

    model_config = ConfigDict(extra="forbid")

    goal: str = Field(min_length=1)
    steps: list[PlanStep] = Field(min_length=1, max_length=10)


class StepResult(BaseModel):
    """Outcome of executing one planned step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    tool_name: str
    status: Literal["success", "error", "skipped"]
    result: Any = None
    error: str | None = None


class PlanExecution(BaseModel):
    """Plan plus its execution outcomes."""

    plan: ExecutionPlan
    results: list[StepResult] = Field(default_factory=list)
    status: Literal[
        "pending",
        "running",
        "completed",
        "partial",
        "failed",
    ] = "pending"
    evidence_assessments: list[dict[str, Any]] = Field(
        default_factory=list
    )


class AgentDecision(BaseModel):
    """The agent's next action after observing execution results."""

    model_config = ConfigDict(extra="forbid")

    action: Literal[
        "execute_planned_step",
        "add_step",
        "finish",
    ]

    reasoning: str = Field(min_length=1)
    step_id: str | None = None
    next_step: PlanStep | None = None
    missing_evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_action_fields(self):
        if self.action == "execute_planned_step":
            if not self.step_id:
                raise ValueError(
                    "execute_planned_step requires step_id"
                )
            if self.next_step is not None:
                raise ValueError(
                    "execute_planned_step cannot include next_step"
                )

        elif self.action == "add_step":
            if self.next_step is None:
                raise ValueError("add_step requires next_step")
            if self.step_id is not None:
                raise ValueError(
                    "add_step cannot include step_id"
                )

        elif self.action == "finish":
            if self.step_id is not None or self.next_step is not None:
                raise ValueError(
                    "finish cannot include step_id or next_step"
                )

        return self
