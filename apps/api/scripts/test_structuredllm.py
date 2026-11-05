import asyncio

from app.extraction.structured import InteractionExtractor
from app.llm.structured import StructuredLLM

async def main():
    structuredllm = StructuredLLM()
    extractor = InteractionExtractor(structuredllm)

    text = (
        "I spoke to John from Acme Corp yesterday. They are interested in our enterprise plan and want a demo next week"
    )

    result = await extractor.extract(text)

    print(result)
    print(type(result))

if __name__ == "main":
    asyncio.run(main())
