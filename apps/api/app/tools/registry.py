from app.tools.crm import search_knowledge
from app.tools.crm import SearchKnowledgeInput
from app.tools.crm import search_interactions
from app.tools.crm import SearchInteractionsInput
from app.tools.crm import search_people, search_companies, SearchPeopleInput, SearchCompaniesInput

TOOLS = {
    "search_companies": {
        "input_model": SearchCompaniesInput,
        "handler": search_companies,
    },
    "search_people": {
        "input_model": SearchPeopleInput,
        "handler": search_people,
    },
    "search_interactions": {
        "input_model": SearchInteractionsInput,
        "handler" : search_interactions
    },
    "search_knowledge": {
        "input_model": SearchKnowledgeInput,
        "handler": search_knowledge
    }
}