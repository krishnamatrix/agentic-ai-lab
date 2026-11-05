import json

from app.extraction.models import InteractionExtraction
from app.llm.ollama import OllamaClient


class NaiveExtractor:
    def __init__(self, llm: OllamaClient):
        self.llm = llm

    async def extract(
        self,
        text: str
    ) -> InteractionExtraction:

        schema = InteractionExtraction.model_json_schema()

        prompt = f"""
            Extract the CRM interaction information from the text.\n\n.
            Text:\n
            {text}
        """

        response = await self.llm.chat(
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format = schema
        )

        data = json.loads(response.content)

        return InteractionExtraction.model_validate(data)