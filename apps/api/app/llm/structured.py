import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.ollama import OllamaClient


T = TypeVar("T", bound=BaseModel)

class StructuredOutputError(Exception):
    """Base exception fro structured output failures."""

class StructuredOutputGenerationError(StructuredOutputError):
    """The LLM response could not be parsed or validated """

class StructuredLLM:
    def __init__(
        self,
        llm: OllamaClient,
        max_attempts: int = 2
    ):
        self.llm = llm
        self.max_attempts = max_attempts

    async def generate(
        self,
        prompt: str,
        output_model: type[T],
    ) -> T:
        schema = output_model.model_json_schema()

        for _ in range(self.max_attempts):
            try:
                response = await self.llm.chat(
                    messages=[
                        {"role": "user", "content" : prompt}
                    ],
                    temperature=0.0,
                    response_format=schema
                )
                print("\n--- STRUCTURED REQUEST ---")
                print("Schema:")
                print(schema)

                response = await self.llm.chat(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    temperature=0.0,
                    response_format=schema,
                )

                print("\n--- STRUCTURED RESPONSE ---")
                print("Content:")
                print(repr(response.content))

                print("\nMetadata:")
                print(response.model_dump_json(indent=2))

                return output_model.model_validate_json(response.content)

            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc

            raise StructuredOutputGenerationError(
                "Failed to generate structured output"
            ) from last_error

                
                    
                                        