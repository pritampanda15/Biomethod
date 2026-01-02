"""Main analysis orchestrator for BioMethod."""

from pathlib import Path
from typing import Any

import yaml

from biomethod.core.models import AnalysisResult, ToolInfo, EnvironmentInfo
from biomethod.parsers import (
    PythonParser,
    JupyterParser,
    RParser,
    NextflowParser,
    SnakemakeParser,
)
from biomethod.detectors import VersionDetector, EnvironmentParser


def analyze(
    path: str | Path,
    detect_versions: bool = True,
    recursive: bool = True,
) -> AnalysisResult:
    """Analyze a directory or file for bioinformatics tools.

    Args:
        path: Path to analyze (file or directory)
        detect_versions: Whether to detect installed versions
        recursive: Whether to search directories recursively

    Returns:
        AnalysisResult containing detected tools and metadata
    """
    analyzer = Analyzer(detect_versions=detect_versions)
    return analyzer.analyze(path, recursive=recursive)


class Analyzer:
    """Main analysis orchestrator."""

    def __init__(self, detect_versions: bool = True):
        """Initialize the analyzer.

        Args:
            detect_versions: Whether to detect installed versions
        """
        self.detect_versions = detect_versions
        self._load_tools_database()
        self._setup_parsers()
        self._setup_detectors()

    def _load_tools_database(self) -> None:
        """Load the tools database from YAML."""
        db_path = Path(__file__).parent.parent / "data" / "tools_database.yaml"
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                self.tools_database = yaml.safe_load(f) or {}
        except (IOError, yaml.YAMLError):
            self.tools_database = {}

    def _setup_parsers(self) -> None:
        """Set up file parsers."""
        self.parsers = [
            PythonParser(self.tools_database),
            JupyterParser(self.tools_database),
            RParser(self.tools_database),
            NextflowParser(self.tools_database),
            SnakemakeParser(self.tools_database),
        ]

    def _setup_detectors(self) -> None:
        """Set up version and environment detectors."""
        self.version_detector = VersionDetector()
        self.env_parser = EnvironmentParser()

    def analyze(
        self,
        path: str | Path,
        recursive: bool = True,
    ) -> AnalysisResult:
        """Analyze a path for bioinformatics tools.

        Args:
            path: Path to analyze
            recursive: Whether to search recursively

        Returns:
            AnalysisResult with detected tools
        """
        path = Path(path)
        result = AnalysisResult()

        if path.is_file():
            tools = self._analyze_file(path)
            result.tools.extend(tools)
            result.source_files.append(str(path))
        elif path.is_dir():
            result = self._analyze_directory(path, recursive)
        else:
            result.warnings.append(f"Path does not exist: {path}")

        # Detect workflow type
        result.workflow_type = self._detect_workflow_type(result.source_files)

        # Enrich with versions
        if self.detect_versions:
            self._enrich_with_versions(result)

        # Parse environment
        if path.is_dir():
            result.environment = self.env_parser.parse_directory(path)
        elif path.is_file():
            result.environment = self.env_parser.parse_directory(path.parent)

        # Add Python version
        result.environment.python_version = self.version_detector.get_python_version()

        # Check for reproducibility issues
        self._check_reproducibility_issues(result)

        return result

    def _analyze_file(self, file_path: Path) -> list[ToolInfo]:
        """Analyze a single file.

        Args:
            file_path: Path to file

        Returns:
            List of detected tools
        """
        tools: list[ToolInfo] = []

        for parser in self.parsers:
            if parser.can_parse(file_path):
                try:
                    file_tools = parser.parse(file_path)
                    tools.extend(file_tools)
                except Exception as e:
                    # Log but don't fail on parse errors
                    pass
                break  # Only use first matching parser

        return tools

    def _analyze_directory(
        self,
        directory: Path,
        recursive: bool = True,
    ) -> AnalysisResult:
        """Analyze all files in a directory.

        Args:
            directory: Directory to analyze
            recursive: Whether to search recursively

        Returns:
            AnalysisResult with all detected tools
        """
        result = AnalysisResult()

        # Get all parseable extensions
        extensions = set()
        for parser in self.parsers:
            extensions.update(parser.extensions)

        # Also check for Snakefile without extension
        special_files = ["Snakefile", "snakefile"]

        # Find all matching files
        pattern = "**/*" if recursive else "*"
        files_to_parse: list[Path] = []

        for ext in extensions:
            files_to_parse.extend(directory.glob(f"{pattern}{ext}"))

        # Check for special files
        for special in special_files:
            if recursive:
                files_to_parse.extend(directory.rglob(special))
            else:
                special_path = directory / special
                if special_path.exists():
                    files_to_parse.append(special_path)

        # Parse each file
        for file_path in files_to_parse:
            try:
                tools = self._analyze_file(file_path)
                result.tools.extend(tools)
                if tools:
                    result.source_files.append(str(file_path))
            except Exception as e:
                result.warnings.append(f"Failed to parse {file_path}: {e}")

        return result

    def _detect_workflow_type(self, source_files: list[str]) -> str | None:
        """Detect the type of workflow from source files.

        Args:
            source_files: List of source file paths

        Returns:
            Workflow type or None
        """
        for file_path in source_files:
            path = Path(file_path)
            name_lower = path.name.lower()
            suffix_lower = path.suffix.lower()

            if suffix_lower == ".nf" or name_lower.endswith(".nf"):
                return "nextflow"
            elif suffix_lower in [".smk", ".snakefile"] or name_lower == "snakefile":
                return "snakemake"

        # Check for majority file types
        python_count = sum(1 for f in source_files if f.endswith((".py", ".ipynb")))
        r_count = sum(1 for f in source_files if f.lower().endswith((".r", ".rmd")))

        if python_count > r_count:
            return "python"
        elif r_count > python_count:
            return "r"

        return "script"

    def _enrich_with_versions(self, result: AnalysisResult) -> None:
        """Add version information to detected tools.

        Args:
            result: AnalysisResult to enrich
        """
        for tool in result.tools:
            if tool.version:
                continue  # Already has version

            # Try Python package detection
            version = self.version_detector.detect_python_package_version(tool.name)

            # Try CLI tool detection
            if not version:
                version = self.version_detector.detect_cli_tool_version(tool.name)

            # Check environment packages
            if not version and tool.name in result.environment.packages:
                version = result.environment.packages[tool.name]

            if version:
                tool.version = version

    def _check_reproducibility_issues(self, result: AnalysisResult) -> None:
        """Check for potential reproducibility issues.

        Args:
            result: AnalysisResult to check
        """
        # Check for tools without versions
        for tool in result.tools:
            if not tool.version:
                result.warnings.append(
                    f"Tool '{tool.name}' has no version specified "
                    f"(source: {tool.source_file})"
                )

        # Check for hardcoded paths
        path_patterns = ["/home/", "/Users/", "C:\\", "/tmp/"]
        for tool in result.tools:
            for param, value in tool.parameters.items():
                if isinstance(value, str):
                    for pattern in path_patterns:
                        if pattern in value:
                            result.warnings.append(
                                f"Hardcoded path detected in {tool.name} "
                                f"parameter '{param}': {value}"
                            )
                            break

        # Check for missing random seeds
        seed_params = ["seed", "random_seed", "random_state", "-s", "--seed"]
        for tool in result.tools:
            if tool.category in ["single-cell", "differential-expression"]:
                has_seed = any(
                    param.lower() in [s.lower() for s in seed_params]
                    for param in tool.parameters.keys()
                )
                if not has_seed:
                    result.warnings.append(
                        f"Tool '{tool.name}' may need a random seed for reproducibility"
                    )

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a tool from the database.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool info dict or None
        """
        normalized = tool_name.lower().replace("-", "_").replace(" ", "_")

        if normalized in self.tools_database:
            return self.tools_database[normalized]

        # Check aliases
        for name, info in self.tools_database.items():
            aliases = [a.lower() for a in info.get("aliases", [])]
            if normalized in aliases:
                return info

        return None
