import inspect
from typing import Any

from app.tools.registry import TOOLS


class ToolExecutionError(Exception):
    pass


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> Any:
    tool = TOOLS.get(tool_name)

    if tool is None:
        raise ToolExecutionError(
            f"Unknown tool: {tool_name}"
        )

    input_model = tool["input_model"]
    handler = tool["handler"]

    validated_input = input_model.model_validate(arguments)

    # pyrefly: ignore [unexpected-positional-argument]
    result = handler(validated_input)

    if inspect.isawaitable(result):
        return await result

    return result