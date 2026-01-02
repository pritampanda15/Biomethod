"""Snakemake workflow parser."""

import re
from pathlib import Path
from typing import Any

from biomethod.parsers.base import BaseParser
from biomethod.core.models import ToolInfo


class SnakemakeParser(BaseParser):
    """Parser for Snakemake workflow files."""

    extensions = [".smk", ".snakefile", ".snake"]

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        return suffix in self.extensions or name in ["snakefile", "snakefile.py"]

    def parse(self, file_path: Path) -> list[ToolInfo]:
        """Parse a Snakemake file and extract tool information."""
        tools: list[ToolInfo] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return tools

        # Extract rules
        rule_tools = self._extract_rules(content, str(file_path))
        tools.extend(rule_tools)

        # Extract conda environments
        conda_tools = self._extract_conda_envs(content, str(file_path), file_path.parent)
        tools.extend(conda_tools)

        # Extract container/singularity definitions
        container_tools = self._extract_containers(content, str(file_path))
        tools.extend(container_tools)

        # Enrich all tools with database info
        tools = [self._enrich_tool_info(tool) for tool in tools]

        return tools

    def _extract_rules(self, content: str, source_file: str) -> list[ToolInfo]:
        """Extract tools from Snakemake rule definitions."""
        tools: list[ToolInfo] = []

        # Match rule blocks - rules can span multiple lines
        # Snakemake syntax: rule name: followed by indented directives
        rule_pattern = r"rule\s+(\w+)\s*:(.*?)(?=\nrule\s|\ncheckpoint\s|\Z)"
        rules = re.findall(rule_pattern, content, re.DOTALL)

        for rule_name, rule_body in rules:
            # Extract shell/run section
            shell_tools = self._parse_shell_directive(rule_body, source_file, rule_name)
            tools.extend(shell_tools)

            # Extract wrapper usage
            wrapper_tools = self._parse_wrapper_directive(rule_body, source_file, rule_name)
            tools.extend(wrapper_tools)

            # Extract params that might indicate tools
            param_tools = self._parse_params_directive(rule_body, source_file, rule_name)
            tools.extend(param_tools)

        return tools

    def _parse_shell_directive(
        self, rule_body: str, source_file: str, rule_name: str
    ) -> list[ToolInfo]:
        """Parse shell directive for tool usage."""
        tools: list[ToolInfo] = []

        # Match shell directive - can use different quote styles
        shell_patterns = [
            r'shell\s*:\s*"""(.*?)"""',
            r"shell\s*:\s*'''(.*?)'''",
            r'shell\s*:\s*"([^"]*)"',
            r"shell\s*:\s*'([^']*)'",
        ]

        for pattern in shell_patterns:
            matches = re.findall(pattern, rule_body, re.DOTALL)
            for shell_content in matches:
                # Parse commands in the shell block
                cmd_tools = self._parse_shell_commands(shell_content, source_file, rule_name)
                tools.extend(cmd_tools)

        return tools

    def _parse_shell_commands(
        self, shell_content: str, source_file: str, rule_name: str
    ) -> list[ToolInfo]:
        """Parse shell commands to extract tool usage."""
        tools: list[ToolInfo] = []

        # Clean up Snakemake placeholders
        clean_content = re.sub(r"\{[^}]+\}", "PLACEHOLDER", shell_content)

        # Split by common command separators
        commands = re.split(r"[;&|\n]", clean_content)

        from biomethod.parsers.python_parser import PythonParser

        for cmd in commands:
            cmd = cmd.strip()
            if not cmd or cmd.startswith("#"):
                continue

            # Handle pipes - get first command in pipe chain
            pipe_parts = cmd.split("|")

            for pipe_cmd in pipe_parts:
                pipe_cmd = pipe_cmd.strip()
                parts = pipe_cmd.split()
                if not parts:
                    continue

                tool_cmd = parts[0].lower()
                # Handle path prefixes
                if "/" in tool_cmd:
                    tool_cmd = tool_cmd.split("/")[-1]

                # Check if it's a known bioinformatics tool
                tool_name = PythonParser.SHELL_TOOLS.get(tool_cmd)
                if tool_name:
                    params = self._extract_params(parts[1:])
                    tools.append(
                        ToolInfo(
                            name=tool_name,
                            source_file=source_file,
                            line_number=0,
                            parameters=params,
                            category=self._get_tool_category(tool_name),
                            description=f"Used in rule: {rule_name}",
                        )
                    )

        return tools

    def _extract_params(self, args: list[str]) -> dict[str, Any]:
        """Extract parameters from command arguments."""
        params: dict[str, Any] = {}
        i = 0

        while i < len(args):
            arg = args[i]
            if arg.startswith("-"):
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    value = args[i + 1]
                    # Clean up placeholders
                    if "PLACEHOLDER" in value:
                        value = "<variable>"
                    params[arg] = value
                    i += 2
                else:
                    params[arg] = True
                    i += 1
            else:
                i += 1

        return params

    def _parse_wrapper_directive(
        self, rule_body: str, source_file: str, rule_name: str
    ) -> list[ToolInfo]:
        """Parse wrapper directive for tool usage."""
        tools: list[ToolInfo] = []

        # Match wrapper directive
        wrapper_pattern = r'wrapper\s*:\s*["\']([^"\']+)["\']'
        matches = re.findall(wrapper_pattern, rule_body)

        for wrapper in matches:
            # Wrappers follow pattern: "version/bio/tool/subcommand"
            # or URL: "https://..."
            tool_info = self._parse_wrapper_path(wrapper, source_file, rule_name)
            if tool_info:
                tools.append(tool_info)

        return tools

    def _parse_wrapper_path(
        self, wrapper_path: str, source_file: str, rule_name: str
    ) -> ToolInfo | None:
        """Parse a wrapper path to extract tool info."""
        # Common wrapper patterns
        # "v1.0/bio/bwa/mem"
        # "v1.0/bio/samtools/sort"

        parts = wrapper_path.split("/")

        # Try to find a known tool in the path
        from biomethod.parsers.python_parser import PythonParser

        for part in parts:
            part_lower = part.lower()
            if part_lower in PythonParser.SHELL_TOOLS:
                tool_name = PythonParser.SHELL_TOOLS[part_lower]

                # Try to extract version from wrapper path
                version = None
                if parts[0].startswith("v"):
                    version = parts[0]

                return ToolInfo(
                    name=tool_name,
                    version=version,
                    source_file=source_file,
                    line_number=0,
                    category=self._get_tool_category(tool_name),
                    description=f"Wrapper: {wrapper_path} (rule: {rule_name})",
                )

        return None

    def _parse_params_directive(
        self, rule_body: str, source_file: str, rule_name: str
    ) -> list[ToolInfo]:
        """Parse params directive for additional tool info."""
        # This could extract specific parameter configurations
        # For now, we focus on the shell/wrapper directives
        return []

    def _extract_conda_envs(
        self, content: str, source_file: str, base_dir: Path
    ) -> list[ToolInfo]:
        """Extract tools from conda environment references."""
        tools: list[ToolInfo] = []

        # Match conda directive in rules
        conda_pattern = r'conda\s*:\s*["\']([^"\']+)["\']'
        matches = re.findall(conda_pattern, content)

        for env_path in matches:
            # Try to read the conda environment file
            if env_path.endswith(".yaml") or env_path.endswith(".yml"):
                full_path = base_dir / env_path
                if full_path.exists():
                    env_tools = self._parse_conda_yaml(full_path, source_file)
                    tools.extend(env_tools)

        return tools

    def _parse_conda_yaml(self, yaml_path: Path, source_file: str) -> list[ToolInfo]:
        """Parse a conda environment YAML file."""
        tools: list[ToolInfo] = []

        try:
            import yaml

            with open(yaml_path, "r", encoding="utf-8") as f:
                env_data = yaml.safe_load(f)
        except Exception:
            return tools

        if not env_data:
            return tools

        dependencies = env_data.get("dependencies", [])
        from biomethod.parsers.nextflow_parser import NextflowParser

        for dep in dependencies:
            if isinstance(dep, str):
                # Parse package specification
                # Format: package=version or package
                if "=" in dep:
                    name, version = dep.split("=", 1)
                else:
                    name = dep
                    version = None

                # Remove channel prefix if present
                if "::" in name:
                    name = name.split("::")[-1]

                name_lower = name.lower()
                if name_lower in NextflowParser.CONTAINER_TOOL_MAP:
                    tool_name = NextflowParser.CONTAINER_TOOL_MAP[name_lower]
                    tools.append(
                        ToolInfo(
                            name=tool_name,
                            version=version,
                            source_file=source_file,
                            line_number=0,
                            category=self._get_tool_category(tool_name),
                            description=f"From conda env: {yaml_path.name}",
                        )
                    )

        return tools

    def _extract_containers(self, content: str, source_file: str) -> list[ToolInfo]:
        """Extract container/singularity definitions."""
        tools: list[ToolInfo] = []

        # Match singularity/container directives
        container_patterns = [
            r'singularity\s*:\s*["\']([^"\']+)["\']',
            r'container\s*:\s*["\']([^"\']+)["\']',
        ]

        from biomethod.parsers.nextflow_parser import NextflowParser
        nf_parser = NextflowParser()

        for pattern in container_patterns:
            matches = re.findall(pattern, content)
            for container in matches:
                tool_info = nf_parser._parse_container_image(container, source_file, "snakemake")
                if tool_info:
                    tools.append(tool_info)

        return tools

    def _get_tool_category(self, tool_name: str) -> str:
        """Get the category for a tool."""
        categories = {
            "bwa": "alignment",
            "bowtie2": "alignment",
            "hisat2": "alignment",
            "star": "alignment",
            "minimap2": "alignment",
            "salmon": "quantification",
            "kallisto": "quantification",
            "rsem": "quantification",
            "featurecounts": "quantification",
            "htseq": "quantification",
            "samtools": "alignment",
            "bcftools": "variant-calling",
            "gatk": "variant-calling",
            "picard": "alignment",
            "fastqc": "quality-control",
            "multiqc": "quality-control",
            "trimmomatic": "preprocessing",
            "fastp": "preprocessing",
            "cutadapt": "preprocessing",
        }
        return categories.get(tool_name, "unknown")
