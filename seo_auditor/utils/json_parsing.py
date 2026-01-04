"""JSON parsing utilities for Claude responses."""
import json
import re
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


def extract_json_from_response(
    content: str,
    default: dict[str, Any] | None = None,
    context: str = "",
) -> dict[str, Any]:
    """Extract JSON from Claude response, handling markdown code blocks.

    Args:
        content: Raw response content from Claude
        default: Default value if parsing fails (defaults to empty dict)
        context: Optional context string for logging (e.g., "synthesis", "technical_analysis")

    Returns:
        Parsed JSON dict, or default value on failure
    """
    if default is None:
        default = {}

    if not content or not content.strip():
        logger.warning("Empty response content", context=context)
        return default

    try:
        # Try to extract from markdown code block first
        if "```json" in content:
            # Handle ```json ... ``` blocks
            match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)
        elif "```" in content:
            # Handle generic ``` ... ``` blocks that might contain JSON
            match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                potential_json = match.group(1).strip()
                if potential_json.startswith("{") or potential_json.startswith("["):
                    content = potential_json

        return json.loads(content.strip())

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse JSON from response",
            context=context,
            error=str(e),
            content_preview=content[:200] if content else "",
        )
        return default

    except Exception as e:
        # Catch any other unexpected errors (e.g., regex issues)
        logger.error(
            "Unexpected error parsing response",
            context=context,
            error_type=type(e).__name__,
            error=str(e),
        )
        return default
