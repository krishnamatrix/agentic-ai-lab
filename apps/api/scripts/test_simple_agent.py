import asyncio

from app.llm.ollama import OllamaClient
from app.agents.simple_agent import SimpleAgent

async def main():
    llm = OllamaClient()

    agent = SimpleAgent(llm)

    conversation_id = "demo-001"

    answer1 = await agent.run(
        "What security concerns has Acme raised?",
        conversation_id,
    )

    print(answer1)
    answer2 = await agent.run(
        "Who raised them?",
        conversation_id,
    )

    print(answer2)

    answer3 = await agent.run(
        "What specifically did Jane want to know about SSO?",
        conversation_id,
    )

    print(answer3)

    answer4 = await agent.run(
        "What about data residency?",
        conversation_id,
    )

    print(answer4)

    answer5 = await agent.run(
        "Which concerns came from the CEO?",
        conversation_id,
    )

    print(answer5)

    answer6 = await agent.run(
        "What integration requirements does Acme have?",
        conversation_id,
    )

    print(answer6)

    answer7 = await agent.run(
        "What are all the technical concerns Acme has raised?",
        conversation_id,
    )

    print(answer7)

    answer8 = await agent.run(
        "Which concerns came from John?",
        conversation_id,
    )

    print(answer8)

    answer9 = await agent.run(
        "Compare Jane's concerns with John's concerns.",
        conversation_id,
    )

    print(answer9)

    answer10 = await agent.run(
        "Give me a concise executive summary of Acme's concerns.",
        conversation_id,
    )

    print(answer10)

    answer11 = await agent.run(
        "Which concerns came from Jane?",
        conversation_id,
    )

    print(answer11)

if __name__ == "__main__":
    asyncio.run(main())