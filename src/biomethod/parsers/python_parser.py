"""Python file parser using AST."""

import ast
from pathlib import Path
from typing import Any

from biomethod.parsers.base import BaseParser
from biomethod.core.models import ToolInfo


class PythonParser(BaseParser):
    """Parser for Python files using AST."""

    extensions = [".py"]

    # Mapping of common import names to bioinformatics tools
    IMPORT_TOOL_MAP = {
        # Sequence alignment
        "pysam": "samtools",
        "Bio.Align": "biopython",
        "Bio": "biopython",
        "biopython": "biopython",
        # RNA-seq
        "HTSeq": "htseq",
        "pybedtools": "bedtools",
        # Statistics/analysis
        "scanpy": "scanpy",
        "anndata": "anndata",
        "scipy": "scipy",
        "numpy": "numpy",
        "pandas": "pandas",
        "sklearn": "scikit-learn",
        "statsmodels": "statsmodels",
        # Visualization
        "matplotlib": "matplotlib",
        "seaborn": "seaborn",
        "plotly": "plotly",
        # Bioinformatics specific
        "pydeseq2": "deseq2",
        "gseapy": "gsea",
        "mygene": "mygene",
        "biomart": "biomart",
        "pyfaidx": "samtools",
    }

    # Common subprocess/shell commands for bioinformatics tools
    SHELL_TOOLS = {
        "bwa": "bwa",
        "bwa-mem2": "bwa-mem2",
        "bowtie2": "bowtie2",
        "bowtie": "bowtie",
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
        "htseq-count": "htseq",
        "stringtie": "stringtie",
        "cufflinks": "cufflinks",
        "tophat": "tophat",
        "minimap2": "minimap2",
        "blastn": "blast",
        "blastp": "blast",
        "blastx": "blast",
        "diamond": "diamond",
        "hmmer": "hmmer",
        "muscle": "muscle",
        "mafft": "mafft",
        "clustalw": "clustalw",
        "vcftools": "vcftools",
        "bgzip": "htslib",
        "tabix": "htslib",
    }

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.extensions

    def parse(self, file_path: Path) -> list[ToolInfo]:
        """Parse a Python file and extract tool information."""
        tools: list[ToolInfo] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except (IOError, UnicodeDecodeError) as e:
            return tools

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return tools

        # Extract imports
        tools.extend(self._extract_imports(tree, str(file_path)))

        # Extract subprocess/shell commands
        tools.extend(self._extract_shell_commands(tree, str(file_path)))

        # Extract function calls that might indicate tool usage
        tools.extend(self._extract_function_calls(tree, str(file_path)))

        # Enrich all tools with database info
        tools = [self._enrich_tool_info(tool) for tool in tools]

        return tools

    def _extract_imports(self, tree: ast.AST, source_file: str) -> list[ToolInfo]:
        """Extract tool info from import statements."""
        tools: list[ToolInfo] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    tool_name = self._map_import_to_tool(alias.name)
                    if tool_name:
                        tools.append(
                            ToolInfo(
                                name=tool_name,
                                source_file=source_file,
                                line_number=node.lineno,
                                category=self._get_tool_category(tool_name),
                            )
                        )

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Check both the module and root module
                    root_module = node.module.split(".")[0]
                    tool_name = self._map_import_to_tool(node.module) or self._map_import_to_tool(
                        root_module
                    )
                    if tool_name:
                        tools.append(
                            ToolInfo(
                                name=tool_name,
                                source_file=source_file,
                                line_number=node.lineno,
                                category=self._get_tool_category(tool_name),
                            )
                        )

        return tools

    def _extract_shell_commands(self, tree: ast.AST, source_file: str) -> list[ToolInfo]:
        """Extract tool info from subprocess/os.system calls."""
        tools: list[ToolInfo] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for subprocess.run, subprocess.call, os.system, etc.
                func_name = self._get_call_name(node)

                if func_name in (
                    "subprocess.run",
                    "subprocess.call",
                    "subprocess.Popen",
                    "subprocess.check_call",
                    "subprocess.check_output",
                    "os.system",
                    "os.popen",
                ):
                    # Try to extract the command
                    command = self._extract_command_string(node)
                    if command:
                        tool_info = self._parse_shell_command(command, source_file, node.lineno)
                        if tool_info:
                            tools.append(tool_info)

        return tools

    def _extract_function_calls(self, tree: ast.AST, source_file: str) -> list[ToolInfo]:
        """Extract tool info from function calls."""
        tools: list[ToolInfo] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)

                # Check for pysam functions
                if func_name and func_name.startswith("pysam."):
                    params = self._extract_call_parameters(node)
                    tools.append(
                        ToolInfo(
                            name="samtools",
                            source_file=source_file,
                            line_number=node.lineno,
                            parameters=params,
                            category="alignment",
                        )
                    )

                # Check for scanpy functions
                elif func_name and func_name.startswith("sc."):
                    params = self._extract_call_parameters(node)
                    tools.append(
                        ToolInfo(
                            name="scanpy",
                            source_file=source_file,
                            line_number=node.lineno,
                            parameters=params,
                            category="single-cell",
                        )
                    )

        return tools

    def _get_call_name(self, node: ast.Call) -> str | None:
        """Get the full name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return None

    def _extract_call_parameters(self, node: ast.Call) -> dict[str, Any]:
        """Extract parameters from a function call."""
        params: dict[str, Any] = {}

        # Positional arguments
        for i, arg in enumerate(node.args):
            value = self._get_literal_value(arg)
            if value is not None:
                params[f"arg_{i}"] = value

        # Keyword arguments
        for kw in node.keywords:
            if kw.arg:
                value = self._get_literal_value(kw.value)
                if value is not None:
                    params[kw.arg] = value

        return params

    def _get_literal_value(self, node: ast.expr) -> Any:
        """Try to extract a literal value from an AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python 3.7 compatibility
            return node.n
        elif isinstance(node, ast.Str):  # Python 3.7 compatibility
            return node.s
        elif isinstance(node, ast.List):
            values = [self._get_literal_value(el) for el in node.elts]
            if all(v is not None for v in values):
                return values
        elif isinstance(node, ast.Dict):
            keys = [self._get_literal_value(k) if k else None for k in node.keys]
            values = [self._get_literal_value(v) for v in node.values]
            if all(k is not None for k in keys) and all(v is not None for v in values):
                return dict(zip(keys, values))
        elif isinstance(node, ast.Name):
            # Return variable name for reference
            return f"${node.id}"
        return None

    def _extract_command_string(self, node: ast.Call) -> str | None:
        """Extract command string from subprocess/os.system call."""
        if not node.args:
            return None

        first_arg = node.args[0]

        # String command
        if isinstance(first_arg, (ast.Str, ast.Constant)):
            if isinstance(first_arg, ast.Str):
                return first_arg.s
            elif isinstance(first_arg.value, str):
                return first_arg.value

        # List command
        elif isinstance(first_arg, ast.List):
            parts = []
            for el in first_arg.elts:
                val = self._get_literal_value(el)
                if val is not None:
                    parts.append(str(val))
            if parts:
                return " ".join(parts)

        # f-string or formatted string
        elif isinstance(first_arg, ast.JoinedStr):
            # Try to extract literal parts
            parts = []
            for val in first_arg.values:
                if isinstance(val, (ast.Str, ast.Constant)):
                    if isinstance(val, ast.Str):
                        parts.append(val.s)
                    elif isinstance(val.value, str):
                        parts.append(val.value)
            if parts:
                return "".join(parts)

        return None

    def _parse_shell_command(
        self, command: str, source_file: str, line_number: int
    ) -> ToolInfo | None:
        """Parse a shell command to extract tool info."""
        # Split command and get first word (the tool)
        parts = command.strip().split()
        if not parts:
            return None

        tool_cmd = parts[0].lower()
        # Handle path prefixes
        if "/" in tool_cmd:
            tool_cmd = tool_cmd.split("/")[-1]

        # Check if it's a known bioinformatics tool
        tool_name = self.SHELL_TOOLS.get(tool_cmd)
        if not tool_name:
            return None

        # Extract parameters (flags and their values)
        params = self._parse_command_parameters(parts[1:])

        return ToolInfo(
            name=tool_name,
            source_file=source_file,
            line_number=line_number,
            parameters=params,
            category=self._get_tool_category(tool_name),
        )

    def _parse_command_parameters(self, args: list[str]) -> dict[str, Any]:
        """Parse command line arguments into a parameter dict."""
        params: dict[str, Any] = {}
        i = 0

        while i < len(args):
            arg = args[i]
            if arg.startswith("-"):
                # It's a flag
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    # Flag with value
                    params[arg] = args[i + 1]
                    i += 2
                else:
                    # Boolean flag
                    params[arg] = True
                    i += 1
            else:
                # Positional argument (likely input/output file)
                if "input" not in params:
                    params["input"] = arg
                else:
                    params["output"] = arg
                i += 1

        return params

    def _map_import_to_tool(self, import_name: str) -> str | None:
        """Map an import name to a bioinformatics tool name."""
        # Check direct mapping
        if import_name in self.IMPORT_TOOL_MAP:
            return self.IMPORT_TOOL_MAP[import_name]

        # Check root module
        root = import_name.split(".")[0]
        if root in self.IMPORT_TOOL_MAP:
            return self.IMPORT_TOOL_MAP[root]

        # Check in tools database
        normalized = self._normalize_tool_name(root)
        if normalized in self.tools_database:
            return normalized

        return None

    def _get_tool_category(self, tool_name: str) -> str:
        """Get the category for a tool."""
        # Check database first
        if tool_name in self.tools_database:
            return self.tools_database[tool_name].get("category", "unknown")

        # Default categories for common tools
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
            "deseq2": "differential-expression",
            "scanpy": "single-cell",
            "biopython": "general",
            "bedtools": "genomics",
        }
        return categories.get(tool_name, "unknown")
