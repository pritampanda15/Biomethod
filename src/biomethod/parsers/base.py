"""Base parser class for code analysis."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from biomethod.core.models import ToolInfo


class BaseParser(ABC):
    """Abstract base class for code parsers."""

    # File extensions this parser can handle
    extensions: list[str] = []

    def __init__(self, tools_database: dict[str, Any] | None = None):
        """Initialize parser with optional tools database.

        Args:
            tools_database: Dictionary of known bioinformatics tools
        """
        self.tools_database = tools_database or {}

    @abstractmethod
    def parse(self, file_path: Path) -> list[ToolInfo]:
        """Parse a file and extract tool information.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of ToolInfo objects found in the file
        """
        pass

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.

        Args:
            file_path: Path to check

        Returns:
            True if this parser can handle the file
        """
        pass

    def _normalize_tool_name(self, name: str) -> str:
        """Normalize a tool name for database lookup.

        Args:
            name: Raw tool name

        Returns:
            Normalized tool name
        """
        return name.lower().replace("-", "_").replace(" ", "_")

    def _lookup_tool(self, name: str) -> dict[str, Any] | None:
        """Look up a tool in the database.

        Args:
            name: Tool name to look up

        Returns:
            Tool info from database or None if not found
        """
        normalized = self._normalize_tool_name(name)

        # Direct lookup
        if normalized in self.tools_database:
            return self.tools_database[normalized]

        # Check aliases
        for tool_name, tool_info in self.tools_database.items():
            aliases = tool_info.get("aliases", [])
            normalized_aliases = [self._normalize_tool_name(a) for a in aliases]
            if normalized in normalized_aliases:
                return tool_info

        return None

    def _enrich_tool_info(self, tool: ToolInfo) -> ToolInfo:
        """Enrich tool info with data from the database.

        Args:
            tool: ToolInfo to enrich

        Returns:
            Enriched ToolInfo
        """
        db_info = self._lookup_tool(tool.name)
        if db_info:
            if not tool.citation:
                tool.citation = db_info.get("citation")
            if tool.category == "unknown":
                tool.category = db_info.get("category", "unknown")
            if not tool.description:
                tool.description = db_info.get("description", "")
            if not tool.aliases:
                tool.aliases = db_info.get("aliases", [])
        return tool
