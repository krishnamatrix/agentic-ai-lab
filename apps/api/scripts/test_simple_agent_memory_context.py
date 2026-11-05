from app.llm.structured import StructuredLLM
import asyncio

from app.llm.ollama import OllamaClient
from app.agents.simple_agent import SimpleAgent

QUESTIONS = [
    "1. Remember that I prefer Acme over Globex.",
    "2. My executive summaries should be under 100 words.",
    "3. My strategy is called Project Phoenix.",
    "5. Which company should we prioritize?",
    "6. What is my executive summary constraint?",
    "7. What is the name of my strategy?",
]


async def main():
    llm = OllamaClient()
    structured_llm = StructuredLLM(llm)
    agent = SimpleAgent(llm, structured_llm)

    conversation_id = "demo-001"

    for i, question in enumerate(QUESTIONS, start=1):
        print(f"\n{'=' * 80}")
        print(f"QUESTION {i}: {question}")
        print(f"{'=' * 80}\n")

        answer = await agent.run(
            question,
            conversation_id,
        )

        print(f"\n--- ANSWER {i} ---")
        print(answer)


if __name__ == "__main__":
    asyncio.run(main())