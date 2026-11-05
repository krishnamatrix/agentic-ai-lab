import asyncio
import json
from pathlib import Path

from app.embeddings.ollama import OllamaEmbeddingClient
from app.repositories.vector import VectorRepository


EVALUATION_FILE = Path(__file__).parent / "rag_retrieval.json"

TOP_K_VALUES = [1, 3, 5]


def precision_at_k(
    expected_ids: set[str],
    retrieved_ids: list[str],
    k: int,
) -> float:
    """
    Of the documents we retrieved in the top K,
    what percentage were actually relevant?
    """
    top_k = retrieved_ids[:k]

    if not top_k:
        return 0.0

    relevant = sum(
        1
        for interaction_id in top_k
        if interaction_id in expected_ids
    )

    return relevant / len(top_k)


def recall_at_k(
    expected_ids: set[str],
    retrieved_ids: list[str],
    k: int,
) -> float:
    """
    Of all the documents we expected to retrieve,
    what percentage did we actually retrieve in the top K?
    """
    if not expected_ids:
        return 1.0

    top_k = set(retrieved_ids[:k])

    relevant_found = len(expected_ids & top_k)

    return relevant_found / len(expected_ids)


def reciprocal_rank(
    expected_ids: set[str],
    retrieved_ids: list[str],
) -> float:
    """
    Reciprocal rank of the first relevant result.

    Rank 1 -> 1.0
    Rank 2 -> 0.5
    Rank 3 -> 0.333
    Rank 5 -> 0.2
    Not found -> 0.0
    """
    for rank, interaction_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if interaction_id in expected_ids:
            return 1.0 / rank

    return 0.0


async def evaluate():
    with EVALUATION_FILE.open() as file:
        test_cases = json.load(file)

    embedding_client = OllamaEmbeddingClient()
    vector_repository = VectorRepository()

    results = []

    for test_case in test_cases:
        query = test_case["query"]
        company_name = test_case.get("company_name")

        expected_ids = set(
            test_case["expected_interaction_ids"]
        )

        # ---------------------------------------------------------
        # 1. Generate query embedding
        # ---------------------------------------------------------

        embedding = await embedding_client.embed(query)

        # ---------------------------------------------------------
        # 2. Retrieve candidates
        #
        # IMPORTANT:
        # No similarity threshold yet.
        # We want to evaluate raw retrieval first.
        # ---------------------------------------------------------

        retrieved = vector_repository.search_interactions(
            embedding=embedding,
            company_name=company_name,
            limit=max(TOP_K_VALUES),
            min_similarity=0.0,
        )

        retrieved_ids = [
            item["interaction_id"]
            for item in retrieved
        ]

        # ---------------------------------------------------------
        # 3. Calculate ranking metrics
        # ---------------------------------------------------------

        rr = reciprocal_rank(
            expected_ids,
            retrieved_ids,
        )

        # ---------------------------------------------------------
        # 4. Build result
        # ---------------------------------------------------------

        test_result = {
            "id": test_case["id"],
            "query": query,
            "company_name": company_name,
            "expected_ids": list(expected_ids),

            "retrieved": [
                {
                    "rank": index + 1,
                    "interaction_id": item["interaction_id"],
                    "company_name": item.get("company_name"),
                    "person_name": item.get("person_name"),
                    "similarity": item["similarity"],
                }
                for index, item in enumerate(retrieved)
            ],

            "reciprocal_rank": rr,
        }

        # ---------------------------------------------------------
        # 5. Calculate Hit / Precision / Recall for each K
        # ---------------------------------------------------------

        for k in TOP_K_VALUES:
            top_k_ids = set(
                retrieved_ids[:k]
            )

            test_result[f"hit_at_{k}"] = bool(
                expected_ids & top_k_ids
            )

            test_result[f"precision_at_{k}"] = (
                precision_at_k(
                    expected_ids,
                    retrieved_ids,
                    k,
                )
            )

            test_result[f"recall_at_{k}"] = (
                recall_at_k(
                    expected_ids,
                    retrieved_ids,
                    k,
                )
            )

        results.append(test_result)

    print_results(results)
    print_summary(results)


def print_results(results: list[dict]):
    """
    Print metrics for each individual query.
    """

    for result in results:
        print()
        print("=" * 80)
        print(result["id"])
        print(result["query"])
        print("=" * 80)

        print()
        print("Expected:")

        for interaction_id in result["expected_ids"]:
            print(f"  {interaction_id}")

        print()
        print("Retrieved:")

        for item in result["retrieved"]:
            print(
                f"  {item['rank']}. "
                f"{item['interaction_id']} | "
                f"{item['similarity']:.4f} | "
                f"{item['company_name']} | "
                f"{item['person_name']}"
            )

        print()
        print(
            f"Hit@1={result['hit_at_1']} "
            f"Hit@3={result['hit_at_3']} "
            f"Hit@5={result['hit_at_5']}"
        )

        print(
            f"Precision@1={result['precision_at_1']:.3f} "
            f"Precision@3={result['precision_at_3']:.3f} "
            f"Precision@5={result['precision_at_5']:.3f}"
        )

        print(
            f"Recall@1={result['recall_at_1']:.3f} "
            f"Recall@3={result['recall_at_3']:.3f} "
            f"Recall@5={result['recall_at_5']:.3f}"
        )

        print(
            f"Reciprocal Rank={result['reciprocal_rank']:.3f}"
        )


def print_summary(results: list[dict]):
    """
    Calculate aggregate metrics across all evaluation queries.
    """

    total = len(results)

    if total == 0:
        print("No evaluation cases found.")
        return

    print()
    print("=" * 80)
    print("RAG RETRIEVAL SUMMARY")
    print("=" * 80)

    # -------------------------------------------------------------
    # Hit@K
    # -------------------------------------------------------------

    for k in TOP_K_VALUES:
        hits = sum(
            1
            for result in results
            if result[f"hit_at_{k}"]
        )

        percentage = hits / total * 100

        print(
            f"Hit@{k}: "
            f"{hits}/{total} "
            f"({percentage:.1f}%)"
        )

    # -------------------------------------------------------------
    # Precision@K and Recall@K
    # -------------------------------------------------------------

    for k in TOP_K_VALUES:
        average_precision = sum(
            result[f"precision_at_{k}"]
            for result in results
        ) / total

        average_recall = sum(
            result[f"recall_at_{k}"]
            for result in results
        ) / total

        print(
            f"Precision@{k}: "
            f"{average_precision:.3f}"
        )

        print(
            f"Recall@{k}: "
            f"{average_recall:.3f}"
        )

    # -------------------------------------------------------------
    # Mean Reciprocal Rank
    # -------------------------------------------------------------

    mrr = sum(
        result["reciprocal_rank"]
        for result in results
    ) / total

    print(
        f"MRR: {mrr:.3f}"
    )


if __name__ == "__main__":
    asyncio.run(evaluate())