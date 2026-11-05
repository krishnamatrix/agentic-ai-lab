from app.tools.results import ToolResult
from pydantic import BaseModel, Field
from app.repositories.crm_repository import CRMRepository
from app.embeddings.ollama import OllamaEmbeddingClient
from app.repositories.vector import VectorRepository


repository = CRMRepository()

class SearchCompaniesInput(BaseModel):
    name: str


def search_companies(
    input: SearchCompaniesInput
) -> list[dict]:
    return repository.search_companies(
        name=input.name,
    )

class SearchPeopleInput(BaseModel):
    company_name: str | None = Field(
        default=None,
        description="Company name associated with the person.",
    )

    role: str | None = Field(
        default=None,
        description=(
            "Person's role or title, such as CEO, CTO, "
            "CFO, VP Engineering, or Director."
        ),
    )

    name: str | None = Field(
        default=None,
        description="Person's name or part of a person's name.",
    )


def search_people(
    input: SearchPeopleInput
) -> list[dict]:
    return repository.search_people(
        company_name=input.company_name,
        role=input.role,
        name=input.name,
    )

class SearchInteractionsInput(BaseModel):
    company_name: str | None = Field(
        default=None,
        description="Company associated with the interaction.",
    )

    person_name: str | None = Field(
        default=None,
        description="Person associated with the interaction.",
    )

    query: str | None = Field(
        default=None,
        description=(
            "Keywords to search within the interaction "
            "subject and content."
        ),
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=50,
    )    

MAX_INTERACTION_RESULTS = 20

def search_interactions(
    input: SearchInteractionsInput,
) -> ToolResult:

    limit = min(input.limit, MAX_INTERACTION_RESULTS)

    rows = repository.search_interactions(
        company_name=input.company_name,
        person_name=input.person_name,
        query_text=input.query,
        limit=limit + 1,
    )

    truncated = len(rows) > limit
    rows = rows[:limit]

    return ToolResult(
        data=rows,
        count=len(rows),
        truncated=truncated,
        limit=limit,
        message=(
            f"Results limited to {limit} records."
            if truncated
            else None
        ),
    )

class SearchKnowledgeInput(BaseModel):
    query: str = Field(
        description=(
            "Natural-language question or concept to search "
            "for in CRM interaction history."
        )
    )

    company_name: str | None = Field(
        default=None,
        description="Optional company to restrict the search to.",
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )


embedding_client = OllamaEmbeddingClient()
vector_repository = VectorRepository()


async def search_knowledge(
    input: SearchKnowledgeInput,
) -> list[dict]:

    embedding = await embedding_client.embed(
        input.query
    )

    return vector_repository.search_interactions(
        embedding=embedding,
        company_name=input.company_name,
        limit=input.limit,
        min_similarity=0.0,
    )
# tools = [
#     {
#         "name": "search_companies",
#         "description": (
#             "Search CRM companies by name."
#         ),
#         "input_schema": SearchCompaniesInput.model_json_schema()
#     },
#     {
#         "name": "search_people",
#         "description": (
#             "Search for people associated with a company. "
#             "Use this tool when the user asks about a person's "
#             "name, role, title, CEO, CTO, executive, or other "
#             "contact associated with a company."
#         ),
#         "input_schema": SearchPeopleInput.model_json_schema()
#     }
# ]

    