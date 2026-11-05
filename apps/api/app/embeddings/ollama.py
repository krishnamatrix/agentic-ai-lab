import httpx


OLLAMA_URL = "http://localhost:11434"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"


class OllamaEmbeddingClient:

    def __init__(
        self,
        base_url: str = OLLAMA_URL,
        model: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def embed(self, text: str) -> list[float]:
        payload = {
            "model": self.model,
            "input": text,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json=payload,
                timeout=120.0,
            )

        response.raise_for_status()

        data = response.json()

        return data["embeddings"][0]