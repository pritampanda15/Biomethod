"""Jupyter notebook parser."""

import json
from pathlib import Path
from typing import Any

from biomethod.parsers.base import BaseParser
from biomethod.parsers.python_parser import PythonParser
from biomethod.core.models import ToolInfo


class JupyterParser(BaseParser):
    """Parser for Jupyter notebooks."""

    extensions = [".ipynb"]

    def __init__(self, tools_database: dict[str, Any] | None = None):
        """Initialize the Jupyter parser."""
        super().__init__(tools_database)
        self._python_parser = PythonParser(tools_database)

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.extensions

    def parse(self, file_path: Path) -> list[ToolInfo]:
        """Parse a Jupyter notebook and extract tool information."""
        tools: list[ToolInfo] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                notebook = json.load(f)
        except (IOError, json.JSONDecodeError):
            return tools

        # Check if it's a valid notebook
        if "cells" not in notebook:
            return tools

        # Extract kernel info for environment detection
        kernel_info = notebook.get("metadata", {}).get("kernelspec", {})
        language = kernel_info.get("language", "python")

        if language.lower() != "python":
            # Currently only supporting Python notebooks
            return tools

        # Process each code cell
        for cell_idx, cell in enumerate(notebook.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue

            source = cell.get("source", [])
            if isinstance(source, list):
                source = "".join(source)

            if not source.strip():
                continue

            # Create a temporary source with cell tracking
            cell_tools = self._parse_cell_code(source, str(file_path), cell_idx)
            tools.extend(cell_tools)

            # Also check cell outputs for tool version info
            output_tools = self._parse_cell_outputs(
                cell.get("outputs", []), str(file_path), cell_idx
            )
            tools.extend(output_tools)

        # Enrich all tools with database info
        tools = [self._enrich_tool_info(tool) for tool in tools]

        return tools

    def _parse_cell_code(
        self, source: str, source_file: str, cell_idx: int
    ) -> list[ToolInfo]:
        """Parse code from a notebook cell."""
        tools: list[ToolInfo] = []

        # Handle magic commands
        clean_lines = []
        for line in source.split("\n"):
            stripped = line.strip()
            # Skip magic commands but track shell commands
            if stripped.startswith("!"):
                # Shell command in notebook
                shell_cmd = stripped[1:].strip()
                shell_tools = self._parse_shell_magic(shell_cmd, source_file, cell_idx)
                tools.extend(shell_tools)
            elif stripped.startswith("%") or stripped.startswith("%%"):
                # Skip IPython magic commands
                continue
            else:
                clean_lines.append(line)

        # Parse the remaining Python code
        clean_source = "\n".join(clean_lines)
        if clean_source.strip():
            # Use the Python parser for the clean code
            import ast
            import tempfile

            try:
                tree = ast.parse(clean_source)
                # Use Python parser's extraction methods
                python_tools = self._python_parser._extract_imports(tree, source_file)
                tools.extend(python_tools)

                shell_tools = self._python_parser._extract_shell_commands(tree, source_file)
                tools.extend(shell_tools)

                func_tools = self._python_parser._extract_function_calls(tree, source_file)
                tools.extend(func_tools)

                # Update line numbers to reflect cell index
                for tool in tools:
                    if tool.source_file == source_file:
                        tool.line_number = cell_idx  # Use cell index for notebooks

            except SyntaxError:
                pass

        return tools

    def _parse_shell_magic(
        self, command: str, source_file: str, cell_idx: int
    ) -> list[ToolInfo]:
        """Parse shell magic command (! prefix in notebooks)."""
        tools: list[ToolInfo] = []

        # Split by pipes and process each command
        commands = command.split("|")
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue

            parts = cmd.split()
            if not parts:
                continue

            tool_cmd = parts[0].lower()
            # Handle path prefixes
            if "/" in tool_cmd:
                tool_cmd = tool_cmd.split("/")[-1]

            # Check if it's a known bioinformatics tool
            tool_name = self._python_parser.SHELL_TOOLS.get(tool_cmd)
            if tool_name:
                params = self._python_parser._parse_command_parameters(parts[1:])
                tools.append(
                    ToolInfo(
                        name=tool_name,
                        source_file=source_file,
                        line_number=cell_idx,
                        parameters=params,
                        category=self._python_parser._get_tool_category(tool_name),
                    )
                )

        return tools

    def _parse_cell_outputs(
        self, outputs: list[dict], source_file: str, cell_idx: int
    ) -> list[ToolInfo]:
        """Parse cell outputs for version information."""
        tools: list[ToolInfo] = []

        for output in outputs:
            output_type = output.get("output_type", "")

            # Check stream output (stdout/stderr)
            if output_type == "stream":
                text = output.get("text", [])
                if isinstance(text, list):
                    text = "".join(text)
                version_info = self._extract_version_from_output(text)
                for tool_name, version in version_info.items():
                    # Check if we already have this tool, and update version
                    # This will be handled at a higher level
                    pass

            # Check execute_result for version strings
            elif output_type == "execute_result":
                data = output.get("data", {})
                text = data.get("text/plain", "")
                if isinstance(text, list):
                    text = "".join(text)
                # Look for version patterns
                pass

        return tools

    def _extract_version_from_output(self, text: str) -> dict[str, str]:
        """Extract version information from output text."""
        import re

        versions: dict[str, str] = {}

        # Common version patterns
        patterns = [
            # "tool version X.Y.Z"
            r"(\w+)\s+version\s+([\d.]+)",
            # "tool/X.Y.Z"
            r"(\w+)/([\d.]+)",
            # "tool-X.Y.Z"
            r"(\w+)-([\d.]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                tool, version = match
                tool_lower = tool.lower()
                if tool_lower in self._python_parser.SHELL_TOOLS:
                    versions[self._python_parser.SHELL_TOOLS[tool_lower]] = version
                elif tool_lower in self._python_parser.IMPORT_TOOL_MAP:
                    versions[self._python_parser.IMPORT_TOOL_MAP[tool_lower]] = version

        return versions
