"""Nextflow DSL2 parser."""

import re
from pathlib import Path
from typing import Any

from biomethod.parsers.base import BaseParser
from biomethod.core.models import ToolInfo


class NextflowParser(BaseParser):
    """Parser for Nextflow DSL2 workflow files."""

    extensions = [".nf"]

    # Mapping of container images to tools
    CONTAINER_TOOL_MAP = {
        "bwa": "bwa",
        "bowtie2": "bowtie2",
        "hisat2": "hisat2",
        "star": "star",
        "salmon": "salmon",
        "kallisto": "kallisto",
        "rsem": "rsem",
        "samtools": "samtools",
        "bcftools": "bcftools",
        "bedtools": "bedtools",
        "gatk": "gatk",
        "picard": "picard",
        "fastqc": "fastqc",
        "multiqc": "multiqc",
        "trimmomatic": "trimmomatic",
        "fastp": "fastp",
        "cutadapt": "cutadapt",
        "featurecounts": "featurecounts",
        "subread": "featurecounts",
        "htseq": "htseq",
        "stringtie": "stringtie",
        "minimap2": "minimap2",
        "freebayes": "freebayes",
        "varscan": "varscan",
        "snpeff": "snpeff",
        "vep": "vep",
        "annovar": "annovar",
    }

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.extensions

    def parse(self, file_path: Path) -> list[ToolInfo]:
        """Parse a Nextflow file and extract tool information."""
        tools: list[ToolInfo] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return tools

        # Extract processes
        process_tools = self._extract_processes(content, str(file_path))
        tools.extend(process_tools)

        # Extract container definitions
        container_tools = self._extract_containers(content, str(file_path))
        tools.extend(container_tools)

        # Extract from nextflow.config if in same directory
        config_path = file_path.parent / "nextflow.config"
        if config_path.exists():
            config_tools = self._parse_config(config_path)
            tools.extend(config_tools)

        # Enrich all tools with database info
        tools = [self._enrich_tool_info(tool) for tool in tools]

        return tools

    def _extract_processes(self, content: str, source_file: str) -> list[ToolInfo]:
        """Extract tools from Nextflow process definitions."""
        tools: list[ToolInfo] = []

        # Match process blocks
        process_pattern = r"process\s+(\w+)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}"
        processes = re.findall(process_pattern, content, re.DOTALL)

        for process_name, process_body in processes:
            # Extract script section
            script_pattern = r"(?:script|shell)\s*:\s*(?:\'\'\'|\"\"\")(.*?)(?:\'\'\'|\"\"\")"
            script_matches = re.findall(script_pattern, process_body, re.DOTALL)

            for script in script_matches:
                # Parse shell commands in the script
                script_tools = self._parse_script_commands(script, source_file, process_name)
                tools.extend(script_tools)

            # Extract container directive
            container_pattern = r"container\s+['\"]([^'\"]+)['\"]"
            container_matches = re.findall(container_pattern, process_body)

            for container in container_matches:
                container_tool = self._parse_container_image(container, source_file, process_name)
                if container_tool:
                    tools.append(container_tool)

            # Extract conda directive
            conda_pattern = r"conda\s+['\"]([^'\"]+)['\"]"
            conda_matches = re.findall(conda_pattern, process_body)

            for conda_spec in conda_matches:
                conda_tools = self._parse_conda_spec(conda_spec, source_file, process_name)
                tools.extend(conda_tools)

        return tools

    def _parse_script_commands(
        self, script: str, source_file: str, process_name: str
    ) -> list[ToolInfo]:
        """Parse shell commands from a Nextflow script section."""
        tools: list[ToolInfo] = []

        # Split into lines and process each command
        for line in script.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Remove variable interpolations for parsing
            clean_line = re.sub(r"\$\{[^}]+\}", "VAR", line)
            clean_line = re.sub(r"\$\w+", "VAR", clean_line)

            # Get the first word as potential command
            parts = clean_line.split()
            if not parts:
                continue

            cmd = parts[0].lower()
            # Handle path prefixes
            if "/" in cmd:
                cmd = cmd.split("/")[-1]

            # Check if it's a known bioinformatics tool
            from biomethod.parsers.python_parser import PythonParser

            tool_name = PythonParser.SHELL_TOOLS.get(cmd)
            if tool_name:
                # Extract parameters
                params = self._extract_params_from_command(line)
                tools.append(
                    ToolInfo(
                        name=tool_name,
                        source_file=source_file,
                        line_number=0,  # Line numbers not tracked in NF
                        parameters=params,
                        category=self._get_tool_category(tool_name),
                        description=f"Used in process: {process_name}",
                    )
                )

        return tools

    def _extract_params_from_command(self, command: str) -> dict[str, Any]:
        """Extract parameters from a shell command."""
        params: dict[str, Any] = {}

        # Find all flags and their values
        # Match -flag value or --flag=value patterns
        flag_pattern = r"(-{1,2}[\w-]+)(?:\s+|=)([^\s-][^\s]*)"
        matches = re.findall(flag_pattern, command)

        for flag, value in matches:
            # Clean up Nextflow variables
            if "${" in value or value.startswith("$"):
                value = "<variable>"
            params[flag] = value

        # Also match boolean flags
        bool_flag_pattern = r"\s(-{1,2}[\w-]+)(?:\s|$)"
        bool_matches = re.findall(bool_flag_pattern, command)
        for flag in bool_matches:
            if flag not in params:
                params[flag] = True

        return params

    def _parse_container_image(
        self, image: str, source_file: str, process_name: str
    ) -> ToolInfo | None:
        """Parse a container image to extract tool info."""
        # Extract tool name from container image
        # Common patterns: biocontainers/tool:version, quay.io/biocontainers/tool:version
        image_lower = image.lower()

        for tool_key, tool_name in self.CONTAINER_TOOL_MAP.items():
            if tool_key in image_lower:
                # Try to extract version
                version = None
                version_match = re.search(r":([v]?[\d.]+)", image)
                if version_match:
                    version = version_match.group(1)

                return ToolInfo(
                    name=tool_name,
                    version=version,
                    source_file=source_file,
                    line_number=0,
                    category=self._get_tool_category(tool_name),
                    description=f"Container: {image} (process: {process_name})",
                )

        return None

    def _parse_conda_spec(
        self, conda_spec: str, source_file: str, process_name: str
    ) -> list[ToolInfo]:
        """Parse a conda specification to extract tool info."""
        tools: list[ToolInfo] = []

        # Handle different formats:
        # - "bioconda::tool=version"
        # - "environment.yml"
        # - "tool=version tool2=version2"

        if conda_spec.endswith(".yml") or conda_spec.endswith(".yaml"):
            # It's an environment file reference
            return tools

        # Parse package specifications
        packages = conda_spec.split()
        for pkg in packages:
            # Remove channel prefix
            if "::" in pkg:
                pkg = pkg.split("::")[-1]

            # Extract name and version
            if "=" in pkg:
                name, version = pkg.split("=", 1)
            else:
                name = pkg
                version = None

            name_lower = name.lower()
            if name_lower in self.CONTAINER_TOOL_MAP:
                tools.append(
                    ToolInfo(
                        name=self.CONTAINER_TOOL_MAP[name_lower],
                        version=version,
                        source_file=source_file,
                        line_number=0,
                        category=self._get_tool_category(self.CONTAINER_TOOL_MAP[name_lower]),
                        description=f"Conda package in process: {process_name}",
                    )
                )

        return tools

    def _extract_containers(self, content: str, source_file: str) -> list[ToolInfo]:
        """Extract container definitions from params or config sections."""
        tools: list[ToolInfo] = []

        # Match params.container patterns
        container_pattern = r"params\.(\w+)_container\s*=\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(container_pattern, content)

        for tool_hint, container in matches:
            container_tool = self._parse_container_image(container, source_file, "params")
            if container_tool:
                tools.append(container_tool)

        return tools

    def _parse_config(self, config_path: Path) -> list[ToolInfo]:
        """Parse nextflow.config for additional tool information."""
        tools: list[ToolInfo] = []

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return tools

        # Extract container definitions from config
        container_pattern = r"container\s*=\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(container_pattern, content)

        for container in matches:
            container_tool = self._parse_container_image(container, str(config_path), "config")
            if container_tool:
                tools.append(container_tool)

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
            "freebayes": "variant-calling",
            "varscan": "variant-calling",
            "picard": "alignment",
            "fastqc": "quality-control",
            "multiqc": "quality-control",
            "trimmomatic": "preprocessing",
            "fastp": "preprocessing",
            "cutadapt": "preprocessing",
            "snpeff": "annotation",
            "vep": "annotation",
            "annovar": "annotation",
        }
        return categories.get(tool_name, "unknown")
