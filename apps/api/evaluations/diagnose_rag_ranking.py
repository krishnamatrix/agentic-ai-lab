import asyncio
import json
from pathlib import Path

from app.embeddings.ollama import OllamaEmbeddingClient
from app.repositories.vector import VectorRepository


TOP_K = 5

EVALUATION_FILE = (
    Path(__file__).resolve().parent / "rag_retrieval.json"
)


def format_score(value: float) -> str:
    return f"{value:.4f}"


async def main() -> None:
    with EVALUATION_FILE.open() as file:
        test_cases = json.load(file)

    embedding_client = OllamaEmbeddingClient()
    repository = VectorRepository()

    print()
    print("RAG Retrieval Ranking Diagnostic")
    print("================================")
    print(f"Queries: {len(test_cases)}")
    print(f"Top-K:   {TOP_K}")
    print()

    for index, test_case in enumerate(test_cases, start=1):
        query = test_case["query"]
        company_name = test_case["company_name"]
        expected_ids = set(test_case["expected_interaction_ids"])

        embedding = await embedding_client.embed(query)

        results = repository.search_interactions(
            embedding=embedding,
            company_name=company_name,
            limit=TOP_K,
            min_similarity=0.0,
        )

        print("=" * 90)
        print(f"{index}. {query}")
        print(f"Company: {company_name}")
        print()

        for rank, result in enumerate(results, start=1):
            interaction_id = str(result["interaction_id"])
            is_expected = interaction_id in expected_ids

            marker = " ← EXPECTED" if is_expected else ""

            print(
                f"{rank}. "
                f"similarity={format_score(result['similarity'])} "
                f"id={interaction_id}{marker}"
            )

            print(
                f"   Type:    {result.get('interaction_type')}"
            )
            print(
                f"   Subject: {result.get('subject')}"
            )
            print(
                f"   Person:  {result.get('person_name')}"
            )

            content = result.get("content") or ""
            print(
                f"   Content: {content}"
            )

            print()

        expected_rank = None

        for rank, result in enumerate(results, start=1):
            if str(result["interaction_id"]) in expected_ids:
                expected_rank = rank
                break

        if expected_rank is None:
            print("RESULT: Expected evidence NOT in top-K")
        elif expected_rank == 1:
            print("RESULT: Correct evidence ranked #1")
        else:
            print(
                f"RESULT: Ranking issue — correct evidence ranked #{expected_rank}"
            )

        print()


if __name__ == "__main__":
    asyncio.run(main())