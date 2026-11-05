import asyncio

from app.embeddings.ollama import OllamaEmbeddingClient


async def main():
    client = OllamaEmbeddingClient()

    vector = await client.embed(
        "What security concerns has Acme raised?"
    )

    print("Dimensions:", len(vector))
    print("First 10:", vector[:10])


asyncio.run(main())