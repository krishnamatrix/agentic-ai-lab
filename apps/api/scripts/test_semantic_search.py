import asyncio

from app.embeddings.ollama import OllamaEmbeddingClient
from app.repositories.vector import VectorRepository


async def main():

    print("Wow")

    query = "What security concerns has Globex raised?"

    embedding_client = OllamaEmbeddingClient()
    repository = VectorRepository()

    embedding = await embedding_client.embed(query)

    results = repository.search_interactions(
        embedding=embedding,
        limit=3,
    )

    print("\nQUERY:")
    print(query)

    print("\nRESULTS:")

    for result in results:
        print(
            f"\nSimilarity: {result['similarity']:.4f}"
        )
        print(result["content"])


if __name__ == "__main__":
    asyncio.run(main())