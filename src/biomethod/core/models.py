"""Core data models for BioMethod."""

from dataclasses import dataclass, field
from typing import Any
from pathlib import Path


@dataclass
class ToolInfo:
    """Information about a detected bioinformatics tool."""

    name: str
    version: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    citation: str | None = None
    category: str = "unknown"
    source_file: str = ""
    line_number: int = 0
    aliases: list[str] = field(default_factory=list)
    description: str = ""

    def __hash__(self) -> int:
        return hash((self.name, self.version, self.source_file, self.line_number))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ToolInfo):
            return NotImplemented
        return (
            self.name == other.name
            and self.version == other.version
            and self.source_file == other.source_file
            and self.line_number == other.line_number
        )


@dataclass
class EnvironmentInfo:
    """Information about the analysis environment."""

    python_version: str | None = None
    r_version: str | None = None
    conda_environment: str | None = None
    packages: dict[str, str] = field(default_factory=dict)  # name -> version
    containers: list[str] = field(default_factory=list)
    requirements_files: list[str] = field(default_factory=list)
    environment_files: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Result of analyzing a codebase for bioinformatics tools."""

    tools: list[ToolInfo] = field(default_factory=list)
    input_files: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    workflow_type: str | None = None  # nextflow, snakemake, script
    environment: EnvironmentInfo = field(default_factory=EnvironmentInfo)
    warnings: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)

    def get_tools_by_category(self) -> dict[str, list[ToolInfo]]:
        """Group tools by their category."""
        categories: dict[str, list[ToolInfo]] = {}
        for tool in self.tools:
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool)
        return categories

    def get_unique_tools(self) -> list[ToolInfo]:
        """Get unique tools (by name and version)."""
        seen: set[tuple[str, str | None]] = set()
        unique: list[ToolInfo] = []
        for tool in self.tools:
            key = (tool.name, tool.version)
            if key not in seen:
                seen.add(key)
                unique.append(tool)
        return unique

    def get_citations(self) -> list[str]:
        """Get all unique citations."""
        citations: set[str] = set()
        for tool in self.tools:
            if tool.citation:
                citations.add(tool.citation)
        return sorted(citations)


@dataclass
class ReproducibilityIssue:
    """An issue flagged during reproducibility checking."""

    severity: str  # "warning", "error", "info"
    category: str  # "version", "seed", "path", "parameter"
    message: str
    source_file: str | None = None
    line_number: int | None = None
    suggestion: str | None = None


@dataclass
class ReproducibilityReport:
    """Report on reproducibility of the analysis."""

    issues: list[ReproducibilityIssue] = field(default_factory=list)
    score: float = 0.0  # 0-100 reproducibility score
    checklist: dict[str, bool] = field(default_factory=dict)

    def summary(self) -> str:
        """Generate a summary of the reproducibility report."""
        lines = [
            "=" * 60,
            "REPRODUCIBILITY REPORT",
            "=" * 60,
            f"Score: {self.score:.1f}/100",
            "",
            "Checklist:",
        ]

        for item, passed in self.checklist.items():
            status = "[PASS]" if passed else "[FAIL]"
            lines.append(f"  {status} {item}")

        if self.issues:
            lines.append("")
            lines.append("Issues Found:")
            for issue in self.issues:
                lines.append(f"  [{issue.severity.upper()}] {issue.message}")
                if issue.suggestion:
                    lines.append(f"    -> {issue.suggestion}")

        lines.append("=" * 60)
        return "\n".join(lines)
