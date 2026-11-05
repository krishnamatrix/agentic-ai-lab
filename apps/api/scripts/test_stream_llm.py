import asyncio
import time

from app.llm.ollama import OllamaClient


async def main():
    client = OllamaClient()

    start = time.perf_counter()

    first_token_time = None
    token_count = 0
    full_response = ""

    async for chunk in client.chat_stream(
        messages=[
            {
                "role": "user",
                "content": "Explain what a CRM is in detail.",
            }
        ],
        temperature=0.0,
    ):
        if first_token_time is None:
            first_token_time = time.perf_counter()

        token_count += 1
        full_response += chunk
        print(
            chunk,
            end="",
            flush=True,
        )

    end = time.perf_counter()

    print("\n")

    total_ms = (end - start) * 1000

    ttft_ms = None
    if first_token_time:
        ttft_ms = (first_token_time - start) * 1000

    print("------ STREAMING METRICS ------")
    if ttft_ms is not None:
        print(f"time_to_first_chunk_ms={ttft_ms:.2f}")
    print(f"total_latency_ms={total_ms:.2f}")
    print(f"chunks_received={token_count}")


if __name__ == "__main__":
    asyncio.run(main())