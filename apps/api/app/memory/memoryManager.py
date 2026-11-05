

from app.memory.memoryOperation import MemoryOperation
from app.memory.memoryStore import MemoryStore
class MemoryManager:
    def __init__(
        self,
        memoryStore: MemoryStore
    ):
        self.store = memoryStore

    def apply(
        self,
        conversation_id: str,
        operation: MemoryOperation
    ) -> None:

        if operation.operation == "delete":
            if operation.key:
                self.store.delete(conversation_id, operation.key)
            else:
                raise ValueError("Key is required for delete operation")
            return

        if operation.memory is None:
            return

        self.store.upsert(conversation_id, operation.memory)
