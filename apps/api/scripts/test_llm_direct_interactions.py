import asyncio

from app.llm.ollama import OllamaClient

async def main():
    client = OllamaClient()

    messages = [
                    {
                        "role": "system",
                        "content": """
                            You are a CRM assistant.

                            Answer the user's question directly using the information provided.

                            Return plain natural language.
                            Do not return JSON.
                            """,
                    },
                    {
                        "role": "user",
                        "content": """
                            What did Acme Corporation discuss recently?

                            CRM data:

                            - Jane Smith, VP of Engineering
                            Technical Architecture
                            Jane requested details about security, SSO and integration capabilities.

                            - John Doe, CEO
                            Enterprise Platform Discussion
                            Acme is evaluating our enterprise platform.
                            They want a product demonstration and requested pricing information.
                        """,
                    }
                ]

    result = await client.chat(
        messages=messages,
        temperature=0.0
    )

    print(result.content)
    print("\n")
    print("------ USAGE ------")
    print(result.usage)

if __name__ == "__main__":
    asyncio.run(main())