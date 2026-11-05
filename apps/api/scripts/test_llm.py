import asyncio

from app.llm.ollama import OllamaClient


async def main():
    client = OllamaClient()

    result = await client.chat(
        messages=[
            {
                "role": "user",
                "content": ("Reply with exactly: CRM."),
                "temperature": 0.0,
            }
        ]
    )

    print(result.content)
    print("\n")
    print("------ USAGE ------")
    print(result.usage)


if __name__ == "__main__":
    asyncio.run(main())
