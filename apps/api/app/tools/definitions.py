from app.tools.crm import SearchKnowledgeInput
from app.tools.crm import SearchCompaniesInput, SearchPeopleInput, SearchInteractionsInput

SEARCH_COMPANIES_TOOL = {
    "type": "function",
    "function": {
        "name": "search_companies",
        "description": "Search for companies in the CRM by name",
        "parameters": SearchCompaniesInput.model_json_schema()
    }
}

SEARCH_PEOPLE_TOOL = {
    "type": "function",
    "function": {
        "name": "search_people",
        "description": "Search for people associated with a company. "
            "Use this tool when the user asks about a person's "
            "name, role, title, CEO, CTO, executive, or other "
            "contact associated with a company.",
        "parameters": SearchPeopleInput.model_json_schema()
    }
}

SEARCH_INTERACTIONS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_interactions",
        "description": (
            "Search CRM interactions such as meetings and emails. "
            "Use this when the user asks what a company or person "
            "discussed, what they are interested in, recent activity, "
            "follow-ups, or relationship history."
        ),
        "parameters": (
            SearchInteractionsInput.model_json_schema()
        ),
    },
}

SEARCH_KNOWLEDGE_TOOL = {
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": (
            "Search CRM interaction history using semantic search. "
            "Use this for questions about topics, concerns, "
            "discussions, interests, requirements, or relationship "
            "history that may be expressed in different words "
            "from the user's question. "
            "Use structured CRM tools for exact facts such as "
            "company names, people, roles, or IDs."
        ),
        "parameters": SearchKnowledgeInput.model_json_schema(),
    },
}