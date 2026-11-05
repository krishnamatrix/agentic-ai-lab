
from app.planning.models import ExecutionPlan

plan = ExecutionPlan(
    goal=(
        "Prepare an evidence-grounded account brief for "
        "Acme Corporation."
    ),
    steps=[
        {
            "step_id": "company_profile",
            "objective": "Retrieve the company profile.",
            "tool_name": "search_companies",
            "arguments": {
                "name": "Acme Corporation",
            },
            "required_evidence": [
                "company name",
                "industry",
                "revenue",
                "employee count",
                "description",
            ],
        },
        {
            "step_id": "key_contacts",
            "objective": "Retrieve the company's key contacts.",
            "tool_name": "search_people",
            "arguments": {
                "company_name": "Acme Corporation",
            },
            "required_evidence": [
                "contact names",
                "contact roles",
            ],
        },
        {
            "step_id": "recent_interactions",
            "objective": "Retrieve relevant CRM interactions.",
            "tool_name": "search_interactions",
            "arguments": {
                "company_name": "Acme Corporation",
                "limit": 20,
            },
            "required_evidence": [
                "interaction subjects",
                "interaction dates",
                "recorded concerns",
                "commercial interests",
            ],
        },
        {
            "step_id": "supporting_knowledge",
            "objective": (
                "Retrieve supporting evidence about security, "
                "integration, deployment, and data residency."
            ),
            "tool_name": "search_knowledge",
            "arguments": {
                "query": (
                    "Acme Corporation security SSO integration "
                    "deployment data residency"
                ),
                "company_name": "Acme Corporation",
                "limit": 5,
            },
            "required_evidence": [
                "security requirements",
                "integration requirements",
                "deployment requirements",
                "data residency requirements",
            ],
        },
    ],
)

print(plan.model_dump_json(indent=2))
