Record:

native Ollama tool calling worked with gemma4:e4b
tool schema/description matters
tool contract mismatch caused repeated/wrong calls
tool result must be fed back to the LLM
unique tool-call IDs are required
agent loop requires explicit termination
tool execution belongs to the application, not the model
final successful trace: search_people → John Doe → final answer