import json


DEFAULT_TOOL_RESULT_MAX_CHARS = 12000


def shape_tool_result(
    result: object,
    max_chars: int = DEFAULT_TOOL_RESULT_MAX_CHARS,
) -> str:

    serialized = json.dumps(
        result,
        default=str,
        ensure_ascii=False,
    )

    if len(serialized) <= max_chars:
        return serialized

    return (
        serialized[:max_chars]
        + "\n...[tool result truncated]..."
    )