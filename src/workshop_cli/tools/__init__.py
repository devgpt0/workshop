"""Tooling package for OpenRouter function calls."""

from workshop_cli.tools.registry import (
    build_tool_schemas,
    default_tool_choice,
    execute_tool,
)

__all__ = ["build_tool_schemas", "default_tool_choice", "execute_tool"]
