from app.extraction.models import InteractionExtraction
from app.llm.structured import StructuredLLM


class InteractionExtractor:
    def __init__(
        self,
        structured_llm: StructuredLLM
    ):
        self.structured_llm = structured_llm

    async def extract(
        self,
        text: str
    ) -> InteractionExtraction:
        
        prompt = f"""
                    Extract the CRM interaction information from the text.
                    Text: 
                    {text}
                    """

        return await self.structured_llm.generate( prompt= prompt, output_model=InteractionExtraction)