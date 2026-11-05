import re

from datetime import timezone
from datetime import datetime
from app.memory.memoryItem import MemoryItem

class MemoryStore:

    def __init__(self):
        self.user_memories: dict[
            str,
            dict[str, MemoryItem],
        ] = {}

        self.conversation_memories: dict[
            str,
            dict[str, MemoryItem],
        ] = {}
        self.history: dict[str, list[dict[str, MemoryItem]]] = {}

    def get_memories(
        self,
        user_id: str,
        conversation_id: str,
    ) -> list[MemoryItem]:

        user_memories = self.user_memories.get(
            user_id,
            {},
        )

        conversation_memories = self.conversation_memories.get(
            conversation_id,
            {},
        )

        return [
            *user_memories.values(),
            *conversation_memories.values(),
        ]
    
    def get_user_memories(
        self,
        user_id: str,
    ) -> list[MemoryItem]:

        return list(
            self.user_memories.get(user_id, {}).values()
        )

    def get_conversation_memories(
        self,
        conversation_id: str,
    ) -> list[MemoryItem]:

        return list(
            self.conversation_memories.get(conversation_id, {}).values()
        )

    def get_history(
        self,
        conversation_id: str,
    ) -> list[dict[str, object]]:

        return self.history.get(
            conversation_id,
            [],
        )

    def _store_for(
        self,
        memory: MemoryItem,
    ) -> dict[str, MemoryItem]:

        if memory.scope == "user":
            return self.user_memories.setdefault(
                memory.user_id,
                {},
            )

        if memory.conversation_id is None:
            raise ValueError(
                "conversation_id is required for conversation-scoped memory"
            )

        return self.conversation_memories.setdefault(
            memory.conversation_id,
            {},
        )
        
    def upsert(
        self,
        conversation_id: str,
        memory: MemoryItem,
    ) -> tuple[MemoryItem | None, MemoryItem]:

        conversation_memories = self._store_for(memory)

        previous = conversation_memories.get(
            memory.key
        )

        now = datetime.now(timezone.utc)

        if previous is not None:
            memory.created_at = previous.created_at

        memory.updated_at = now
        
        conversation_memories[memory.key] = memory

        self.history.setdefault(
            conversation_id,
            [],
        ).append(
            {
                "operation": "update" if previous else "create",
                "key": memory.key,
                "previous_value": (
                    previous.value
                    if previous is not None
                    else None
                ),
                "new_value": memory.value,
                "timestamp": now,
            }
        )

        return previous, memory

    def delete(
        self,
        user_id: str,
        conversation_id: str,
        key: str,
        scope: str
    ) -> MemoryItem | None:

        if scope == "user":
            store = self.user_memories.get(
                user_id,
                {},
            )
        else:
            store = self.conversation_memories.get(
                conversation_id,
                {},
            )

        previous = store.pop(key, None)

        if previous is not None:
            self.history.setdefault(conversation_id, []).append(
                {
                    "operation": "delete",
                    "key": key,
                    "previous_value": previous.value,
                    "new_value": None,
                    "timestamp": datetime.now(timezone.utc)
                }
            )


    def clear(
        self,
        conversation_id: str,
    ) -> None:
        self.conversation_memories.pop(conversation_id, None)
        self.history.pop(conversation_id, None)

    
    def memory_score(self, memory: MemoryItem, query: str) -> float:
        def tokenize(text: str) -> set[str]:
            return set(re.findall(r"[a-z0-9]+", text.lower()))

        # Small, explicit normalization rules for this experiment.
        def normalize(token: str) -> str:
            if token == "accounts":
                return "account"
            if token == "prioritizing":
                return "prioritize"
            if token == "prioritizes":
                return "prioritize"
            if token == "prioritized":
                return "prioritize"
            return token

        query_terms = {
            normalize(token)
            for token in tokenize(query)
        }

        key_terms = {
            normalize(token)
            for token in tokenize(memory.key)
        }
        type_terms = {
            normalize(token)
            for token in tokenize(memory.type)
        }
        value_terms = {
            normalize(token)
            for token in tokenize(memory.value)
        }

        key_overlap = len(query_terms & key_terms)
        type_overlap = len(query_terms & type_terms)
        value_overlap = len(query_terms & value_terms)

        return (
            3.0 * key_overlap
            + 0.5 * type_overlap
            + value_overlap
        )


    def search(
        self,
        user_id: str,
        conversation_id: str,
        query: str,
        limit: int = 5,
    ) -> list[MemoryItem]:

        memories = self.get_memories(
            user_id=user_id,
            conversation_id=conversation_id,
        )

        ranked = [
            (memory, self.memory_score(memory, query))
            for memory in memories
        ]

        ranked = [
            item
            for item in ranked
            if item[1] > 0
        ]

        ranked.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            memory
            for memory, _score in ranked[:limit]
        ]