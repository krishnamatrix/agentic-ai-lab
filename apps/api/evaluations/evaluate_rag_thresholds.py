import asyncio
import json
from pathlib import Path

from app.embeddings.ollama import OllamaEmbeddingClient
from app.repositories.vector import VectorRepository


TOP_K = 3
THRESHOLDS = [0.0, 0.4, 0.5, 0.6, 0.7]

EVALUATION_FILE = (
    Path(__file__).resolve().parent / "rag_retrieval.json"
)


def hit_at_k(results: list[dict], expected_ids: set[str], k: int) -> int:
    return int(
        any(
            str(result["interaction_id"]) in expected_ids
            for result in results[:k]
        )
    )


def reciprocal_rank(results: list[dict], expected_ids: set[str]) -> float:
    for rank, result in enumerate(results, start=1):
        if str(result["interaction_id"]) in expected_ids:
            return 1.0 / rank

    return 0.0


def precision_at_k(
    results: list[dict],
    expected_ids: set[str],
    k: int,
) -> float:
    top_results = results[:k]

    if not top_results:
        return 0.0

    relevant = sum(
        str(result["interaction_id"]) in expected_ids
        for result in top_results
    )

    return relevant / len(top_results)


async def evaluate_threshold(
    repository: VectorRepository,
    embedding_client: OllamaEmbeddingClient,
    test_cases: list[dict],
    threshold: float,
) -> dict:
    hit1_values = []
    recall3_values = []
    precision3_values = []
    reciprocal_ranks = []

    for test_case in test_cases:
        query = test_case["query"]
        company_name = test_case["company_name"]
        expected_ids = test_case["expected_interaction_ids"]

        embedding = await embedding_client.embed(query)

        results = repository.search_interactions(
            embedding=embedding,
            company_name=company_name,
            limit=TOP_K,
            min_similarity=threshold,
        )

        hit1 = hit_at_k(results, expected_ids, 1)
        recall3 = hit_at_k(results, expected_ids, 3)
        precision3 = precision_at_k(results, expected_ids, 3)
        rr = reciprocal_rank(results, expected_ids)

        hit1_values.append(hit1)
        recall3_values.append(recall3)
        precision3_values.append(precision3)
        reciprocal_ranks.append(rr)

    count = len(test_cases)

    return {
        "threshold": threshold,
        "hit_at_1": sum(hit1_values) / count,
        "recall_at_3": sum(recall3_values) / count,
        "precision_at_3": sum(precision3_values) / count,
        "mrr": sum(reciprocal_ranks) / count,
    }


async def main() -> None:
    with EVALUATION_FILE.open() as file:
        test_cases = json.load(file)

    embedding_client = OllamaEmbeddingClient()
    repository = VectorRepository()

    print()
    print("RAG Threshold Sweep")
    print("===================")
    print(f"Queries:    {len(test_cases)}")
    print(f"Top-K:      {TOP_K}")
    print(f"Thresholds: {THRESHOLDS}")
    print()

    results = []

    for threshold in THRESHOLDS:
        print(f"Running threshold={threshold:.2f}...")

        result = await evaluate_threshold(
            repository=repository,
            embedding_client=embedding_client,
            test_cases=test_cases,
            threshold=threshold,
        )

        results.append(result)

    print()
    print(
        f"{'Threshold':<12}"
        f"{'Hit@1':<10}"
        f"{'Recall@3':<12}"
        f"{'Precision@3':<14}"
        f"{'MRR':<10}"
    )
    print("-" * 58)

    for result in results:
        print(
            f"{result['threshold']:<12.2f}"
            f"{result['hit_at_1'] * 100:<10.1f}"
            f"{result['recall_at_3'] * 100:<12.1f}"
            f"{result['precision_at_3'] * 100:<14.1f}"
            f"{result['mrr']:<10.3f}"
        )

    print()
    print("Interpretation:")
    print(
        "  Recall@3 tells us whether the correct evidence survived "
        "the threshold."
    )
    print(
        "  Precision@3 tells us how much of the retrieved context "
        "is actually relevant."
    )
    print(
        "  MRR tells us how highly the correct evidence is ranked."
    )
    print()


if __name__ == "__main__":
    asyncio.run(main())