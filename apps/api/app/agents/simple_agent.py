from app.tools import results
from uuid import uuid4
from datetime import datetime, timezone
from app.memory.memoryItem import MemoryItem
from anyio.streams import memory
from app.llm.structured import StructuredLLM
from app.memory.memoryExtraction import MemoryExtraction
from app.memory.memoryStore import MemoryStore
import json
from typing import Any

from app.agents.tool_executor import execute_tool
from app.llm.ollama import OllamaClient

from app.tools.definitions import (
    SEARCH_COMPANIES_TOOL,
    SEARCH_INTERACTIONS_TOOL,
    SEARCH_KNOWLEDGE_TOOL,
    SEARCH_PEOPLE_TOOL,
)


SYSTEM_PROMPT = """
You are a CRM assistant.

Your job is to answer the user's question using the CRM data available
through the provided tools.

Rules:
- Use tools when CRM information is required.
- After receiving tool results, answer the user's original question directly.
- Do not return JSON unless the user explicitly asks for JSON.
- Do not describe your tool calls or internal process.
- Do not describe what you are going to do.
- Do not invent information.
- Base your answer only on the conversation and tool results.
- If the tool results do not contain enough information, say so clearly.

- Use relevant retrieved user preferences to interpret ambiguous requests.
- When a stored preference directly answers the user's question, answer using that preference.
- Distinguish user preferences from objective CRM findings.
- Do not ask for additional criteria when the user’s stored preference is sufficient to answer their question.
- If the user asks for an objective business recommendation, use CRM evidence and explain how it relates to the user's preferences.
""".strip()


class SimpleAgent:

    MAX_ITERATIONS = 10

    def __init__(
        self,
        llm: OllamaClient,
        structured_llm: StructuredLLM,
        verbose: bool = True,
    ):
        self.llm = llm
        self.structured_llm = structured_llm
        self.verbose = verbose
        self.memory_store = MemoryStore()
        self.memory_extraction = MemoryExtraction()
        self.last_execution_trace: list[dict[str, Any]] = []
        # Temporary in-memory conversation store.
        #
        # conversation_id -> messages
        self.conversations: dict[
            str,
            list[dict[str, Any]],
        ] = {}
        self.conversation_summaries: dict[str, str] = {}

    async def summarize_conversation(
        self,
        conversation_id: str,
        messages: list[dict[str, Any]],
    ) -> str:
        existing_summary = self.conversation_summaries.get(
            conversation_id,
            "",
        )

        conversation_text = "\n".join(
            f"{message['role'].upper()}: {message.get('content', '')}"
            for message in messages
            if message.get("role") in {"user", "assistant"}
        )

        prompt = f"""
            You are maintaining memory for a CRM assistant.

            Create a concise factual summary of the conversation.

            Preserve information that may be needed to answer future questions,
            including:
            - user-provided facts
            - user preferences
            - decisions
            - names
            - important references
            - terminology introduced by the user
            - important unresolved questions

            Do not invent information.
            Do not include tool calls or tool results.
            Do not include conversational filler.

            Existing summary:
            {existing_summary or "(none)"}

            Conversation to incorporate:
            {conversation_text}

            Return only the updated summary.
            """.strip()

        response = await self.llm.chat(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.0,
        )

        return response.content.strip()
    
    def context_breakdown(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, int]:

        breakdown = {
            "system": 0,
            "user": 0,
            "assistant": 0,
            "tool": 0,
        }

        for message in messages:

            role = message.get("role", "unknown")

            # Count the complete serialized message.
            #
            # This includes:
            # - content
            # - tool_calls
            # - tool_call_id
            # - function arguments
            #
            # These are all part of the context sent to the LLM.
            serialized = json.dumps(
                message,
                default=str,
            )

            chars = len(serialized)

            if role in breakdown:
                breakdown[role] += chars

        return breakdown

    def print_conversation_summary(
        self,
        conversation_id: str,
    ) -> None:
        messages = self.conversations[conversation_id]

        breakdown = self.context_breakdown(messages)
        total_chars = self.context_size(messages)

        print(
            "\n=== CONVERSATION STATE ==="
            f"\nconversation_id={conversation_id}"
            f"\nmessages={len(messages)}"
            f"\nchars={total_chars:,}"
            f"\nsystem={breakdown['system']:,}"
            f"\nuser={breakdown['user']:,}"
            f"\nassistant={breakdown['assistant']:,}"
            f"\ntool={breakdown['tool']:,}"
        )

    async def compact_conversation(
        self,
        conversation_id: str,
        max_recent_turns: int = 2,
    ) -> None:
        messages = self.conversations[conversation_id]

        system_message = messages[0]
        conversation_messages = messages[1:]

        # Only user + final assistant messages should exist here
        # because tool execution context is already pruned.
        max_messages = max_recent_turns * 2

        if len(conversation_messages) <= max_messages:
            return

        old_messages = conversation_messages[:-max_messages]
        recent_messages = conversation_messages[-max_messages:]

        summary = await self.summarize_conversation(
            conversation_id,
            old_messages,
        )

        self.conversation_summaries[conversation_id] = summary

        self.conversations[conversation_id] = [
            system_message,
            *recent_messages,
        ]

    def context_size(
        self,
        messages: list[dict[str, Any]],
    ) -> int:

        return sum(
            len(
                json.dumps(
                    message,
                    default=str,
                )
            )
            for message in messages
        )

    def prune_execution_context(
        self,
        conversation_id: str,
    ) -> None:
        messages = self.conversations[conversation_id]

        retained_messages = []

        for message in messages:
            role = message.get("role")

            # Keep:
            # - system prompt
            # - user messages
            # - final assistant responses
            #
            # Remove:
            # - assistant tool-call messages
            # - raw tool results
            if role == "system":
                retained_messages.append(message)

            elif role == "user":
                retained_messages.append(message)

            elif role == "assistant" and not message.get("tool_calls"):
                retained_messages.append(message)

        self.conversations[conversation_id] = retained_messages

    def reset_conversation(self, conversation_id: str) -> None:
        self.conversations.pop(conversation_id, None)
        self.conversation_summaries.pop(conversation_id, None)
        self.memory_store.clear(conversation_id)

    def get_conversation_history(self, conversation_id: str) -> list[dict[str, Any]]:
        return [
            msg for msg in self.conversations.get(conversation_id, [])
            if msg.get("role") in {"user", "assistant"}
        ]

    def get_history(
        self,
        conversation_id: str,
    ) -> list[dict[str, object]]:

        return self.history.get(
            conversation_id,
            [],
        )
        
    async def extract_memories(
        self,
        user_message: str,
    ) -> MemoryExtraction:

        prompt = f"""
        You extract memory from a CRM assistant conversation.

        Determine whether information should be remembered across
        all future conversations or only within the current conversation.

        Use:

        scope = "user"
        when the information is a stable user preference, fact,
        goal, or constraint that should apply across conversations.

        Examples:
        - "I prefer concise executive summaries."
        - "I prefer Python for AI backend work."
        - "Always explain the tradeoffs in technical recommendations."

        Use:

        scope = "conversation"
        when the information is specific to the current discussion,
        project, task, or temporary decision.

        Examples:
        - "For this discussion, prioritize Acme."
        - "For this analysis, compare Acme and Globex."
        - "Let's call this initiative Project Phoenix."

        Extract only:
        - explicit user preferences
        - explicit decisions
        - explicit goals
        - explicit constraints
        - stable user-provided facts

        Do NOT extract:
        - ordinary questions
        - temporary conversational context unless it is useful
        as conversation-scoped memory
        - assistant opinions
        - CRM facts unless the user explicitly asks you to remember them

        Important:
        - Do not invent information.
        - Use concise stable snake_case keys.
        - If the user explicitly says "remember this" or equivalent,
        prefer scope="user" unless the statement is clearly
        conversation-specific.
        - If the user says they no longer want a preference,
        generate a DELETE operation for the existing key.
        - Do not create a replacement memory when the user explicitly
        removes a preference.

    Rules for memory keys:

    - Use lowercase snake_case.
    - Keys must be short and stable.
    - Keys identify the logical memory, not the current sentence.
    - Do not use dates, timestamps, UUIDs, numbers, or generated suffixes.
    - Do not use spaces, slashes, or punctuation.

    Good keys:

    preferred_account
    executive_summary_constraint
    strategy_name
    response_style
    technical_recommendation_style
    account_goal

    Bad keys:

    Product/Brand Preference
    preferred_account_1
    preferred_account_20261013
    memory_12345

    Operation rules:

    1. Use "create" when a new durable memory is introduced.
    2. Use "update" when the user changes an existing preference,
    decision, goal, or constraint.
    3. Use "delete" when the user explicitly asks to forget something.
    4. For delete, provide the memory key and do not provide memory.
    5. For create/update, provide memory and do not need a top-level key.

    Examples:

    User:
    "I prefer Acme over Globex."

    Return:

    {{
    "operations": [
        {{
        "operation": "create",
        "memory": {{
            "type": "preference",
            "key": "preferred_account",
            "value": "Acme over Globex"
        }}
        }}
    ]
    }}

    User:
    "Actually, I now prefer Globex."

    Return:

    {{
    "operations": [
        {{
        "operation": "update",
        "memory": {{
            "type": "preference",
            "key": "preferred_account",
            "value": "Globex"
        }}
        }}
    ]
    }}

    User:
    "My executive summaries must be under 100 words."

    Return:

    {{
    "operations": [
        {{
        "operation": "create",
        "memory": {{
            "type": "constraint",
            "key": "executive_summary_constraint",
            "value": "under 100 words"
        }}
        }}
    ]
    }}

    User:
    "Forget my preference about which company to prioritize."

    Return:

    {{
    "operations": [
        {{
        "operation": "delete",
        "key": "preferred_account"
        }}
    ]
    }}

    User message:

    {user_message}

    Return only the structured memory operations.
    """.strip()

        return await self.structured_llm.generate(
            prompt=prompt,
            output_model=MemoryExtraction,
        )
            
    def build_messages(
        self,
        user_id: str,
        conversation_id: str,
        top_memories: list[MemoryItem],
    ) -> list[dict[str, Any]]:
        messages = self.conversations.setdefault(
            conversation_id,
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ],
        )

        summary = self.conversation_summaries.get(
            conversation_id
        )

        # memories = self.memory_store.get_memories(
        #     user_id,
        #     conversation_id
        # )

        context_messages = [
            messages[0]
        ]

        if top_memories:
            memory_text = "\n".join(
                f"- [{memory.scope}] "
                f"- [{memory.type}] "
                f"{memory.key}: {memory.value}"
                for memory in top_memories
            )

            context_messages.append(
                {
                    "role": "system",
                    "content": (
                        "Durable user memory represents the user's CURRENT "
                        "authoritative state.\n\n"
                        "Conversation-scoped memory applies only to the "
                        "current conversation.\n\n"
                        "If the conversation history or the conversation summary "
                        "contradicts durable user memory, ALWAYS follow durable "
                        "user memory.\n\n"
                        "Do not infer a current preference from historical "
                        "conversation if that preference is absent from durable "
                        "user memory.\n\n"
                        + memory_text
                    ),
                }
            )

        if summary:
            context_messages.append(
                {
                    "role": "system",
                    "content": (
                        "Conversation summary:\n\n"
                        + summary
                    ),
                }
            )

        context_messages.extend(
            messages[1:]
        )

        return context_messages

    def conversation_turn_stats(
        self,
        conversation_id: str,
    ) -> None:
        messages = self.conversations[conversation_id]

        user_chars = sum(
            len(str(m.get("content", "")))
            for m in messages
            if m.get("role") == "user"
        )

        assistant_chars = sum(
            len(str(m.get("content", "")))
            for m in messages
            if m.get("role") == "assistant"
        )

        print(
            f"[Memory] "
            f"turns={sum(1 for m in messages if m.get('role') == 'user')} | "
            f"messages={len(messages)} | "
            f"user_chars={user_chars:,} | "
            f"assistant_chars={assistant_chars:,} | "
            f"total_chars={self.context_size(messages):,}"
        )
    
    def upsert(
        self,
        conversation_id: str,
        memory: MemoryItem,
    ) -> tuple[MemoryItem | None, MemoryItem]:
        conversation_memories = self.memories.setdefault(
            conversation_id,
            {}
        )

        previous = conversation_memories.get(memory.key)

        conversation_memories[memory.key] = memory

        return previous, memory

    async def run(
        self,
        user_message: str,
        conversation_id: str,
        user_id: str
    ) -> str:

        # ---------------------------------------------------------
        # 1) SEARCH FOR MEMORIES
        # ---------------------------------------------------------
        print("UserId: ", user_id)
        print("ConversationId: ", conversation_id)
        print("MemoryStore user: ", self.memory_store.user_memories)
        print("MemoryStore conversation: ", self.memory_store.conversation_memories)

        self.last_execution_trace = []

        top_memories = self.memory_store.search(
            user_id=user_id,
            conversation_id=conversation_id,
            query=user_message,
            limit=5,
        )

        print("\n=== SEARCH RESULTS ===")
        if not top_memories:
            print("(no memories found)")
        else:
            for i, memory in enumerate(top_memories, 1):
                print(f"[{i}] {memory.scope} | {memory.type} | {memory.key}")
                print(f"    {memory.value}")

        
        # ---------------------------------------------------------
        # 2) Build the messages list for the LLM call
        # ---------------------------------------------------------

        messages = self.conversations.setdefault(
            conversation_id,
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ],
        )

        # Add the current user message to persistent conversation history.
        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        memory_result = await self.extract_memories(
            user_message
        )

        print("\n=== MEMORY OPERATIONS ===")

        if not memory_result.operations:
            print("(none)")

        for operation in memory_result.operations:

            print(
                f"\nOperation: {operation.operation}"
            )

            # ---------------------------------------------------------
            # DELETE
            # ---------------------------------------------------------

            if operation.operation == "delete":

                print(
                    f"Delete key: {operation.key}"
                )

                if operation.key:
                    deleted = self.memory_store.delete(
                        conversation_id,
                        operation.key,
                    )

                    if deleted:
                        print(
                            f"[MEMORY DELETED] "
                            f"{deleted.key} = "
                            f"{deleted.value}"
                        )
                    else:
                        print(
                            f"[MEMORY DELETE] "
                            f"No memory found for "
                            f"key={operation.key}"
                        )

                continue

            # ---------------------------------------------------------
            # CREATE / UPDATE
            # ---------------------------------------------------------

            if operation.memory is None:
                print(
                    "[MEMORY INVALID] "
                    "Create/update operation has no memory."
                )
                continue

            extracted = operation.memory

            print(
                f"Key   : {extracted.key}"
            )
            print(
                f"Type  : {extracted.type}"
            )
            print(
                f"Value : {extracted.value}"
            )

            # ---------------------------------------------------------
            # Convert LLM output into application MemoryItem
            # ---------------------------------------------------------

            memory = MemoryItem(
                id=str(uuid4()),
                type=extracted.type,
                key=extracted.key,
                value=extracted.value,
                scope=extracted.scope,
                user_id=user_id,
                conversation_id=(
                    conversation_id
                    if extracted.scope == "conversation"
                    else None
                ),
                source="user",
                confidence=1.0,
            )

            previous, current = self.memory_store.upsert(
                conversation_id,
                memory,
            )

            if previous is None:

                print(
                    f"[MEMORY CREATED] "
                    f"{current.key} = "
                    f"{current.value}"
                )

            elif previous.value == current.value:

                print(
                    f"[MEMORY UNCHANGED] "
                    f"{current.key} = "
                    f"{current.value}"
                )

            else:

                print(
                    f"[MEMORY UPDATED] "
                    f"{current.key}: "
                    f"'{previous.value}' → "
                    f"'{current.value}'"
                )

        tools = [
            SEARCH_COMPANIES_TOOL,
            SEARCH_PEOPLE_TOOL,
            SEARCH_INTERACTIONS_TOOL,
            SEARCH_KNOWLEDGE_TOOL,
        ]

        iteration = 0

        while iteration < self.MAX_ITERATIONS:
            iteration += 1

            # ---------------------------------------------------------
            # Build the ACTUAL context that will be sent to the LLM.
            #
            # This may contain:
            #   - system prompt
            #   - conversation summary
            #   - recent conversation messages
            #
            # It should NOT contain old raw tool results.
            # ---------------------------------------------------------
            llm_messages = self.build_messages(
                user_id,
                conversation_id,
                top_memories
            )

            print("\n=== LLM REQUEST ===")

            for index, message in enumerate(llm_messages):
                print(
                    f"\n--- MESSAGE {index} "
                    f"[{message.get('role')}] ---"
                )

                if message.get("content"):
                    print(message["content"])

                if message.get("tool_calls"):
                    print("tool_calls:")
                    print(message["tool_calls"])

                if message.get("tool_call_id"):
                    print(
                        f"tool_call_id: "
                        f"{message['tool_call_id']}"
                    )

            breakdown = self.context_breakdown(
                llm_messages
            )

            total_chars = self.context_size(
                llm_messages
            )

            print(
                "\n[Context] "
                f"messages={len(llm_messages)} | "
                f"chars={total_chars:,} | "
                f"system={breakdown['system']:,} | "
                f"user={breakdown['user']:,} | "
                f"assistant={breakdown['assistant']:,} | "
                f"tool={breakdown['tool']:,}"
            )

            summary = self.conversation_summaries.get(
                conversation_id
            )

            print(
                "[Memory] "
                f"summary_chars={len(summary) if summary else 0:,}"
            )

            if summary:
                print(
                    "\n=== CONVERSATION SUMMARY ==="
                )
                print(summary)

            # ---------------------------------------------------------
            # LLM CALL
            # ---------------------------------------------------------
            response = await self.llm.chat(
                messages=llm_messages,
                tools=tools,
                temperature=0.0,
            )

            print("\n=== LLM RESPONSE ===")
            print(
                response.model_dump_json(
                    indent=2
                )
            )

            if self.verbose:
                print(
                    f"[LLM Response] "
                    f"Latency: "
                    f"{response.usage.latency_ms:.2f}ms | "
                    f"Input tokens: "
                    f"{response.usage.input_tokens} | "
                    f"Cached input tokens: "
                    f"{response.usage.cached_input_tokens} | "
                    f"Output tokens: "
                    f"{response.usage.output_tokens} | "
                    f"Total tokens: "
                    f"{response.usage.total_tokens}"
                )

            # ---------------------------------------------------------
            # FINAL ANSWER
            # ---------------------------------------------------------
            if not response.tool_calls:
                if self.verbose:
                    print(
                        "[Agent] No tool calls requested. "
                        "Arrived at final answer."
                    )

                # Persist only the final assistant response.
                messages.append(
                    {
                        "role": "assistant",
                        "content": response.content,
                    }
                )

                print("\n=== EXECUTION TRACE ===")
                print(
                    json.dumps(
                        self.last_execution_trace,
                        indent=2,
                        default=str,
                    )
                )

                # -----------------------------------------------------
                # Remove transient tool execution context.
                # -----------------------------------------------------
                self.prune_execution_context(
                    conversation_id
                )

                # -----------------------------------------------------
                # Compact old conversational history.
                #
                # This may create/update conversation summary
                # and retain only the most recent turns.
                # -----------------------------------------------------
                await self.compact_conversation(
                    conversation_id,
                    max_recent_turns=2,
                )

                # -----------------------------------------------------
                # Show what is actually persisted AFTER compaction.
                # -----------------------------------------------------
                self.print_conversation_summary(
                    conversation_id
                )

                print(
                    "\n=== PERSISTED CONVERSATION ==="
                )

                for index, message in enumerate(
                    self.conversations[conversation_id]
                ):
                    print(
                        f"\n--- MESSAGE {index} "
                        f"[{message.get('role')}] ---"
                    )
                    print(
                        message.get("content", "")
                    )

                return response.content

            # ---------------------------------------------------------
            # TOOL CALLS
            # ---------------------------------------------------------
            if self.verbose:
                if response.content:
                    print(
                        f"[LLM Thought]: "
                        f"{response.content}"
                    )

                for tool_call in response.tool_calls:
                    print(
                        "[LLM Tool Call]: "
                        f"{tool_call.name}"
                        f"({tool_call.arguments})"
                    )

            # ---------------------------------------------------------
            # Persist the assistant tool-call message temporarily.
            #
            # This is required so the subsequent tool result can be
            # associated with the correct tool call.
            # ---------------------------------------------------------
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "function": {
                                "name": tool_call.name,
                                "arguments": tool_call.arguments,
                            },
                        }
                        for tool_call in response.tool_calls
                    ],
                }
            )

            # ---------------------------------------------------------
            # Execute every requested tool.
            # ---------------------------------------------------------
            for tool_call in response.tool_calls:

                if self.verbose:
                    print(
                        "[Tool Execution] "
                        f"Executing "
                        f"'{tool_call.name}'..."
                    )

                trace_entry = {
                    "step": len(self.last_execution_trace) + 1,
                    "tool": tool_call.name,
                    "arguments": tool_call.arguments,
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }

                result = await execute_tool(
                    tool_call.name,
                    tool_call.arguments,
                )


                if self.verbose:
                    print(
                        f"[Tool Result]: {result}"
                    )

                # Keep a concise, JSON-safe result summary.
                if hasattr(result, "model_dump"):
                    result_data = result.model_dump(mode="json")
                else:
                    result_data = result

                result_text = json.dumps(
                    result_data,
                    default=str,
                )

                trace_entry["result_summary"] = result_text[:1000]

                trace_entry["completed_at"] = datetime.now(timezone.utc).isoformat()

                self.last_execution_trace.append(trace_entry)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text
                    }
                )

        raise RuntimeError(
            "Agent exceeded maximum iterations: "
            f"{self.MAX_ITERATIONS}"
        )