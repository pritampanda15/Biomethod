"""Natural language prose generation for methods sections."""

from pathlib import Path
from typing import Any
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape

from biomethod.core.models import AnalysisResult, ToolInfo


class ProseGenerator:
    """Generate natural language methods sections from analysis results."""

    # Category order for methods sections
    CATEGORY_ORDER = [
        "preprocessing",
        "quality-control",
        "alignment",
        "quantification",
        "variant-calling",
        "differential-expression",
        "enrichment",
        "single-cell",
        "genomics",
        "annotation",
        "visualization",
        "general",
        "unknown",
    ]

    # Category descriptions for prose
    CATEGORY_DESCRIPTIONS = {
        "preprocessing": "Raw sequencing reads were preprocessed",
        "quality-control": "Quality control was performed",
        "alignment": "Reads were aligned to the reference genome",
        "quantification": "Gene expression was quantified",
        "variant-calling": "Variant calling was performed",
        "differential-expression": "Differential expression analysis was conducted",
        "enrichment": "Functional enrichment analysis was performed",
        "single-cell": "Single-cell analysis was performed",
        "genomics": "Genomic analysis was conducted",
        "annotation": "Variant annotation was performed",
        "visualization": "Data visualization was performed",
        "general": "Additional analyses were performed",
        "unknown": "Additional tools were used",
    }

    def __init__(self, style: str = "generic"):
        """Initialize the prose generator.

        Args:
            style: Journal style (generic, nature, bioinformatics, plos)
        """
        self.style = style
        self._setup_templates()

    def _setup_templates(self) -> None:
        """Set up Jinja2 template environment."""
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["format_version"] = self._format_version
        self.env.filters["format_params"] = self._format_params
        self.env.filters["tool_list"] = self._format_tool_list

    def generate(
        self,
        analysis: AnalysisResult,
        include_versions: bool = True,
        include_citations: bool = True,
    ) -> str:
        """Generate a methods section from analysis results.

        Args:
            analysis: The analysis result to generate from
            include_versions: Whether to include version information
            include_citations: Whether to include citation markers

        Returns:
            Generated methods text
        """
        # Group tools by category
        categories = analysis.get_tools_by_category()

        # Generate prose for each category
        sections = []
        for category in self.CATEGORY_ORDER:
            if category in categories:
                tools = categories[category]
                section = self._generate_category_section(
                    category, tools, include_versions, include_citations
                )
                if section:
                    sections.append(section)

        # Combine sections
        methods_text = " ".join(sections)

        # Apply style-specific formatting
        methods_text = self._apply_style(methods_text)

        return methods_text

    def generate_from_template(
        self,
        analysis: AnalysisResult,
        include_versions: bool = True,
        include_citations: bool = True,
    ) -> str:
        """Generate methods using a Jinja2 template.

        Args:
            analysis: The analysis result
            include_versions: Whether to include versions
            include_citations: Whether to include citations

        Returns:
            Generated methods text
        """
        try:
            template = self.env.get_template(f"{self.style}.j2")
        except Exception:
            template = self.env.get_template("generic.j2")

        # Prepare template context
        context = {
            "analysis": analysis,
            "tools_by_category": analysis.get_tools_by_category(),
            "unique_tools": analysis.get_unique_tools(),
            "include_versions": include_versions,
            "include_citations": include_citations,
            "category_order": self.CATEGORY_ORDER,
            "category_descriptions": self.CATEGORY_DESCRIPTIONS,
        }

        return template.render(**context)

    def _generate_category_section(
        self,
        category: str,
        tools: list[ToolInfo],
        include_versions: bool,
        include_citations: bool,
    ) -> str:
        """Generate prose for a single category.

        Args:
            category: The tool category
            tools: List of tools in this category
            include_versions: Whether to include versions
            include_citations: Whether to include citations

        Returns:
            Prose section for the category
        """
        if not tools:
            return ""

        # Get unique tools
        unique_tools = {}
        for tool in tools:
            key = tool.name
            if key not in unique_tools or (tool.version and not unique_tools[key].version):
                unique_tools[key] = tool

        # Generate tool mentions
        tool_mentions = []
        for tool in unique_tools.values():
            mention = self._format_tool_mention(tool, include_versions, include_citations)
            tool_mentions.append(mention)

        # Combine into prose
        intro = self.CATEGORY_DESCRIPTIONS.get(category, "Analysis was performed")

        if len(tool_mentions) == 1:
            return f"{intro} using {tool_mentions[0]}."
        elif len(tool_mentions) == 2:
            return f"{intro} using {tool_mentions[0]} and {tool_mentions[1]}."
        else:
            tools_str = ", ".join(tool_mentions[:-1]) + f", and {tool_mentions[-1]}"
            return f"{intro} using {tools_str}."

    def _format_tool_mention(
        self,
        tool: ToolInfo,
        include_version: bool,
        include_citation: bool,
    ) -> str:
        """Format a tool mention for prose.

        Args:
            tool: The tool to format
            include_version: Whether to include version
            include_citation: Whether to include citation

        Returns:
            Formatted tool mention
        """
        # Tool name
        name = tool.name

        # Add version
        if include_version and tool.version:
            name = f"{name} (v{tool.version})"

        # Add citation marker
        if include_citation and tool.citation:
            # Extract citation key from BibTeX
            cite_key = self._extract_cite_key(tool.citation)
            if cite_key:
                name = f"{name} [{cite_key}]"

        return name

    def _extract_cite_key(self, citation: str) -> str | None:
        """Extract citation key from BibTeX entry.

        Args:
            citation: BibTeX citation string

        Returns:
            Citation key or None
        """
        match = re.search(r"@\w+\{(\w+),", citation)
        if match:
            return match.group(1)
        return None

    def _format_version(self, version: str | None) -> str:
        """Format a version string.

        Args:
            version: Version string

        Returns:
            Formatted version
        """
        if not version:
            return ""
        if version.startswith("v"):
            return version
        return f"v{version}"

    def _format_params(self, params: dict[str, Any]) -> str:
        """Format parameters for prose.

        Args:
            params: Parameter dictionary

        Returns:
            Formatted parameters string
        """
        if not params:
            return ""

        param_strs = []
        for key, value in params.items():
            if isinstance(value, bool):
                if value:
                    param_strs.append(key)
            else:
                param_strs.append(f"{key}={value}")

        return ", ".join(param_strs)

    def _format_tool_list(self, tools: list[ToolInfo]) -> str:
        """Format a list of tools for prose.

        Args:
            tools: List of tools

        Returns:
            Formatted tool list
        """
        names = [t.name for t in tools]
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} and {names[1]}"
        else:
            return ", ".join(names[:-1]) + f", and {names[-1]}"

    def _apply_style(self, text: str) -> str:
        """Apply journal-specific styling.

        Args:
            text: Raw methods text

        Returns:
            Styled text
        """
        if self.style == "nature":
            # Nature style: concise, no tool versions in main text
            text = re.sub(r"\s*\(v[\d.]+\)", "", text)
        elif self.style == "bioinformatics":
            # Bioinformatics: keep versions, add doi links
            pass
        elif self.style == "plos":
            # PLOS: verbose, include all details
            pass

        return text

    def generate_supplementary_table(
        self, analysis: AnalysisResult
    ) -> list[dict[str, Any]]:
        """Generate data for a supplementary tools table.

        Args:
            analysis: The analysis result

        Returns:
            List of dictionaries for table rows
        """
        rows = []
        for tool in analysis.get_unique_tools():
            row = {
                "Tool": tool.name,
                "Version": tool.version or "Not specified",
                "Category": tool.category,
                "Parameters": self._format_params(tool.parameters),
                "Source": tool.source_file,
                "Citation": self._extract_cite_key(tool.citation) if tool.citation else "",
            }
            rows.append(row)

        return rows
