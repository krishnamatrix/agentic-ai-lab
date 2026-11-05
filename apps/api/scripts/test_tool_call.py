import asyncio

from app.llm.ollama import OllamaClient
from app.tools.definitions import SEARCH_COMPANIES_TOOL
from app.tools.registry import TOOLS


async def main():
    client = OllamaClient()

    response = await client.chat(
        messages=[
            {
                "role": "user",
                "content": "Find the company Acme Corp in the CRM.",
            }
        ],
        temperature=0.0,
        tools=[SEARCH_COMPANIES_TOOL],
    )

    print("\n--- LLM RESPONSE ---")
    print(response.model_dump_json(indent=2))

    for tool_call in response.tool_calls:
        tool_name = tool_call.name
        arguments = tool_call.arguments

        print(f"\n--- TOOL REQUEST ---")
        print(f"Tool: {tool_name}")
        print(f"Arguments: {arguments}")

        tool = TOOLS.get(tool_name)

        if tool is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        input_model = tool["input_model"]
        handler = tool["handler"]

        validated_input = input_model.model_validate(arguments)

        # pyrefly: ignore [unexpected-positional-argument]
        result = handler(validated_input)

        print("\n--- TOOL RESULT ---")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())