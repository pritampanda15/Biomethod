"""R script parser."""

import re
from pathlib import Path
from typing import Any

from biomethod.parsers.base import BaseParser
from biomethod.core.models import ToolInfo


class RParser(BaseParser):
    """Parser for R scripts."""

    extensions = [".R", ".r", ".Rmd", ".rmd"]

    # Mapping of R packages to bioinformatics tools
    R_PACKAGE_MAP = {
        # Bioconductor
        "deseq2": "deseq2",
        "deseq": "deseq",
        "edger": "edger",
        "limma": "limma",
        "genomicranges": "genomicranges",
        "genomicalignments": "genomicalignments",
        "rsamtools": "rsamtools",
        "rtracklayer": "rtracklayer",
        "biostrings": "biostrings",
        "bsgenome": "bsgenome",
        "annotationdbi": "annotationdbi",
        "org.hs.eg.db": "org.hs.eg.db",
        "org.mm.eg.db": "org.mm.eg.db",
        "clusterprofile": "clusterprofiler",
        "clusterprofiler": "clusterprofiler",
        "goseq": "goseq",
        "topgo": "topgo",
        "mast": "mast",
        "singlecellexperiment": "singlecellexperiment",
        "scater": "scater",
        "scran": "scran",
        "seurat": "seurat",
        "monocle": "monocle",
        "monocle3": "monocle3",
        "slingshot": "slingshot",
        "complexheatmap": "complexheatmap",
        "enhancedvolcano": "enhancedvolcano",
        # CRAN packages
        "ggplot2": "ggplot2",
        "dplyr": "dplyr",
        "tidyverse": "tidyverse",
        "pheatmap": "pheatmap",
        "ggrepel": "ggrepel",
        "cowplot": "cowplot",
        "patchwork": "patchwork",
        "survival": "survival",
    }

    # R functions that indicate tool usage
    R_FUNCTION_MAP = {
        # DESeq2
        "DESeqDataSetFromMatrix": ("deseq2", "differential-expression"),
        "DESeq": ("deseq2", "differential-expression"),
        "results": ("deseq2", "differential-expression"),
        "lfcShrink": ("deseq2", "differential-expression"),
        # edgeR
        "DGEList": ("edger", "differential-expression"),
        "calcNormFactors": ("edger", "differential-expression"),
        "estimateDisp": ("edger", "differential-expression"),
        "exactTest": ("edger", "differential-expression"),
        "glmFit": ("edger", "differential-expression"),
        "glmLRT": ("edger", "differential-expression"),
        # limma
        "voom": ("limma", "differential-expression"),
        "lmFit": ("limma", "differential-expression"),
        "eBayes": ("limma", "differential-expression"),
        "topTable": ("limma", "differential-expression"),
        # Seurat
        "CreateSeuratObject": ("seurat", "single-cell"),
        "NormalizeData": ("seurat", "single-cell"),
        "FindVariableFeatures": ("seurat", "single-cell"),
        "ScaleData": ("seurat", "single-cell"),
        "RunPCA": ("seurat", "single-cell"),
        "FindNeighbors": ("seurat", "single-cell"),
        "FindClusters": ("seurat", "single-cell"),
        "RunUMAP": ("seurat", "single-cell"),
        "RunTSNE": ("seurat", "single-cell"),
        # clusterProfiler
        "enrichGO": ("clusterprofiler", "enrichment"),
        "enrichKEGG": ("clusterprofiler", "enrichment"),
        "gseGO": ("clusterprofiler", "enrichment"),
        "gseKEGG": ("clusterprofiler", "enrichment"),
    }

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in [e.lower() for e in self.extensions]

    def parse(self, file_path: Path) -> list[ToolInfo]:
        """Parse an R script and extract tool information."""
        tools: list[ToolInfo] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return tools

        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Extract library/require calls
            lib_tools = self._extract_library_calls(line, str(file_path), line_num)
            tools.extend(lib_tools)

            # Extract function calls
            func_tools = self._extract_function_calls(line, str(file_path), line_num)
            tools.extend(func_tools)

            # Extract system/system2 calls
            sys_tools = self._extract_system_calls(line, str(file_path), line_num)
            tools.extend(sys_tools)

        # Handle Rmd chunks if it's an Rmd file
        if file_path.suffix.lower() in [".rmd"]:
            chunk_tools = self._extract_rmd_chunks(content, str(file_path))
            tools.extend(chunk_tools)

        # Enrich all tools with database info
        tools = [self._enrich_tool_info(tool) for tool in tools]

        return tools

    def _extract_library_calls(
        self, line: str, source_file: str, line_number: int
    ) -> list[ToolInfo]:
        """Extract package names from library() or require() calls."""
        tools: list[ToolInfo] = []

        # Patterns for library/require
        patterns = [
            r"library\s*\(\s*['\"]?(\w+)['\"]?\s*\)",
            r"library\s*\(\s*(\w+)\s*\)",
            r"require\s*\(\s*['\"]?(\w+)['\"]?\s*\)",
            r"require\s*\(\s*(\w+)\s*\)",
            # pacman style
            r"p_load\s*\(['\"]?(\w+)['\"]?",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                package_name = match.lower()
                tool_name = self.R_PACKAGE_MAP.get(package_name, package_name)
                tools.append(
                    ToolInfo(
                        name=tool_name,
                        source_file=source_file,
                        line_number=line_number,
                        category=self._get_r_tool_category(tool_name),
                    )
                )

        return tools

    def _extract_function_calls(
        self, line: str, source_file: str, line_number: int
    ) -> list[ToolInfo]:
        """Extract tool info from known R function calls."""
        tools: list[ToolInfo] = []

        for func_name, (tool_name, category) in self.R_FUNCTION_MAP.items():
            # Match function call with optional namespace prefix
            pattern = rf"(?:\w+::)?{re.escape(func_name)}\s*\("
            if re.search(pattern, line):
                # Extract parameters
                params = self._extract_function_params(line, func_name)
                tools.append(
                    ToolInfo(
                        name=tool_name,
                        source_file=source_file,
                        line_number=line_number,
                        parameters=params,
                        category=category,
                    )
                )

        return tools

    def _extract_function_params(self, line: str, func_name: str) -> dict[str, Any]:
        """Extract parameters from an R function call."""
        params: dict[str, Any] = {}

        # Simple regex to extract named parameters
        # This is a simplified version - R parsing is complex
        pattern = rf"{re.escape(func_name)}\s*\(([^)]*)\)"
        match = re.search(pattern, line)

        if match:
            args_str = match.group(1)
            # Split by comma (simplified - doesn't handle nested calls)
            for arg in args_str.split(","):
                arg = arg.strip()
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    params[key] = value

        return params

    def _extract_system_calls(
        self, line: str, source_file: str, line_number: int
    ) -> list[ToolInfo]:
        """Extract tool info from system() or system2() calls."""
        tools: list[ToolInfo] = []

        # Pattern for system calls
        patterns = [
            r"system\s*\(\s*['\"]([^'\"]+)['\"]",
            r"system2\s*\(\s*['\"](\w+)['\"]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                # Parse the command
                parts = match.split()
                if parts:
                    cmd = parts[0].lower()
                    if "/" in cmd:
                        cmd = cmd.split("/")[-1]

                    # Check against known tools
                    from biomethod.parsers.python_parser import PythonParser

                    tool_name = PythonParser.SHELL_TOOLS.get(cmd)
                    if tool_name:
                        params = {}
                        if len(parts) > 1:
                            params = self._parse_shell_params(parts[1:])
                        tools.append(
                            ToolInfo(
                                name=tool_name,
                                source_file=source_file,
                                line_number=line_number,
                                parameters=params,
                                category="shell",
                            )
                        )

        return tools

    def _parse_shell_params(self, args: list[str]) -> dict[str, Any]:
        """Parse shell command parameters."""
        params: dict[str, Any] = {}
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("-"):
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    params[arg] = args[i + 1]
                    i += 2
                else:
                    params[arg] = True
                    i += 1
            else:
                i += 1
        return params

    def _extract_rmd_chunks(self, content: str, source_file: str) -> list[ToolInfo]:
        """Extract tools from R Markdown code chunks."""
        tools: list[ToolInfo] = []

        # Find R code chunks
        chunk_pattern = r"```\{r[^}]*\}(.*?)```"
        chunks = re.findall(chunk_pattern, content, re.DOTALL)

        for chunk in chunks:
            lines = chunk.split("\n")
            for line_num, line in enumerate(lines, 1):
                lib_tools = self._extract_library_calls(line, source_file, line_num)
                tools.extend(lib_tools)

                func_tools = self._extract_function_calls(line, source_file, line_num)
                tools.extend(func_tools)

        return tools

    def _get_r_tool_category(self, tool_name: str) -> str:
        """Get the category for an R tool."""
        categories = {
            "deseq2": "differential-expression",
            "deseq": "differential-expression",
            "edger": "differential-expression",
            "limma": "differential-expression",
            "seurat": "single-cell",
            "monocle": "single-cell",
            "monocle3": "single-cell",
            "scater": "single-cell",
            "scran": "single-cell",
            "slingshot": "single-cell",
            "clusterprofiler": "enrichment",
            "goseq": "enrichment",
            "topgo": "enrichment",
            "genomicranges": "genomics",
            "biostrings": "genomics",
            "ggplot2": "visualization",
            "pheatmap": "visualization",
            "complexheatmap": "visualization",
            "enhancedvolcano": "visualization",
        }
        return categories.get(tool_name, "unknown")
