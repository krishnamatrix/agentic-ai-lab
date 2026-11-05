import asyncio

from app.extraction.naive import NaiveExtractor
from app.llm.ollama import OllamaClient

async def main():
    llm = OllamaClient()

    extractor = NaiveExtractor(llm)

    text = (
        "I spoke to John from Acme Corp yesterday. They are interested in our enterprise plan and want a demo next week"
    )

    result = await extractor.extract(text)

    print(result)

    print(type(result))

if __name__ == "__main__":
    asyncio.run(main())