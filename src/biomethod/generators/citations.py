"""Citation formatting and bibliography generation."""

import re
from typing import Any

from biomethod.core.models import AnalysisResult, ToolInfo


class CitationFormatter:
    """Format citations in various styles."""

    def __init__(self, style: str = "bibtex"):
        """Initialize the citation formatter.

        Args:
            style: Citation style (bibtex, apa, mla, vancouver)
        """
        self.style = style

    def format_bibliography(self, analysis: AnalysisResult) -> str:
        """Generate a formatted bibliography from analysis results.

        Args:
            analysis: The analysis result

        Returns:
            Formatted bibliography string
        """
        citations = analysis.get_citations()

        if self.style == "bibtex":
            return self._format_bibtex(citations)
        elif self.style == "apa":
            return self._format_apa(citations)
        elif self.style == "vancouver":
            return self._format_vancouver(citations)
        else:
            return self._format_bibtex(citations)

    def _format_bibtex(self, citations: list[str]) -> str:
        """Format citations as BibTeX.

        Args:
            citations: List of BibTeX citation strings

        Returns:
            Combined BibTeX file content
        """
        # Clean up and deduplicate
        cleaned = []
        seen_keys = set()

        for citation in citations:
            # Extract key
            match = re.search(r"@\w+\{(\w+),", citation)
            if match:
                key = match.group(1)
                if key not in seen_keys:
                    seen_keys.add(key)
                    cleaned.append(citation.strip())

        return "\n\n".join(cleaned)

    def _format_apa(self, citations: list[str]) -> str:
        """Format citations in APA style.

        Args:
            citations: List of BibTeX citation strings

        Returns:
            APA formatted bibliography
        """
        apa_entries = []

        for citation in citations:
            entry = self._bibtex_to_apa(citation)
            if entry:
                apa_entries.append(entry)

        # Sort alphabetically by first author
        apa_entries.sort()

        return "\n\n".join(apa_entries)

    def _bibtex_to_apa(self, bibtex: str) -> str | None:
        """Convert a BibTeX entry to APA format.

        Args:
            bibtex: BibTeX entry

        Returns:
            APA formatted citation or None
        """
        # Parse BibTeX fields
        fields = self._parse_bibtex_fields(bibtex)
        if not fields:
            return None

        authors = fields.get("author", "Unknown")
        year = fields.get("year", "n.d.")
        title = fields.get("title", "Untitled")
        journal = fields.get("journal", "")
        volume = fields.get("volume", "")
        pages = fields.get("pages", "")
        doi = fields.get("doi", "")

        # Format authors for APA
        authors_apa = self._format_authors_apa(authors)

        # Clean title (remove braces)
        title = re.sub(r"[{}]", "", title)

        # Build citation
        parts = [f"{authors_apa} ({year}). {title}."]

        if journal:
            journal = re.sub(r"[{}]", "", journal)
            journal_part = f"*{journal}*"
            if volume:
                journal_part += f", *{volume}*"
            if pages:
                journal_part += f", {pages}"
            journal_part += "."
            parts.append(journal_part)

        if doi:
            parts.append(f"https://doi.org/{doi}")

        return " ".join(parts)

    def _format_authors_apa(self, authors: str) -> str:
        """Format author names for APA style.

        Args:
            authors: Author string from BibTeX

        Returns:
            APA formatted author list
        """
        # Split by " and "
        author_list = authors.split(" and ")

        formatted = []
        for author in author_list[:7]:  # APA shows max 7 authors
            author = author.strip()
            # Handle "Last, First" format
            if "," in author:
                parts = author.split(",", 1)
                last = parts[0].strip()
                first = parts[1].strip() if len(parts) > 1 else ""
                # Get initials
                initials = ". ".join([n[0] for n in first.split() if n]) + "."
                formatted.append(f"{last}, {initials}")
            else:
                # Handle "First Last" format
                parts = author.split()
                if len(parts) >= 2:
                    last = parts[-1]
                    initials = ". ".join([n[0] for n in parts[:-1]]) + "."
                    formatted.append(f"{last}, {initials}")
                else:
                    formatted.append(author)

        if len(author_list) > 7:
            return ", ".join(formatted[:6]) + ", ... " + formatted[-1]
        elif len(formatted) == 1:
            return formatted[0]
        elif len(formatted) == 2:
            return f"{formatted[0]} & {formatted[1]}"
        else:
            return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"

    def _format_vancouver(self, citations: list[str]) -> str:
        """Format citations in Vancouver style.

        Args:
            citations: List of BibTeX citation strings

        Returns:
            Vancouver formatted bibliography
        """
        vancouver_entries = []

        for i, citation in enumerate(citations, 1):
            entry = self._bibtex_to_vancouver(citation, i)
            if entry:
                vancouver_entries.append(entry)

        return "\n\n".join(vancouver_entries)

    def _bibtex_to_vancouver(self, bibtex: str, number: int) -> str | None:
        """Convert a BibTeX entry to Vancouver format.

        Args:
            bibtex: BibTeX entry
            number: Reference number

        Returns:
            Vancouver formatted citation or None
        """
        fields = self._parse_bibtex_fields(bibtex)
        if not fields:
            return None

        authors = fields.get("author", "Unknown")
        title = fields.get("title", "Untitled")
        journal = fields.get("journal", "")
        year = fields.get("year", "")
        volume = fields.get("volume", "")
        pages = fields.get("pages", "")

        # Format authors for Vancouver (et al. after 6)
        authors_van = self._format_authors_vancouver(authors)

        # Clean title
        title = re.sub(r"[{}]", "", title)
        journal = re.sub(r"[{}]", "", journal)

        # Build citation
        parts = [f"{number}. {authors_van}. {title}."]

        if journal:
            parts.append(f"{journal}.")
            if year:
                parts[-1] = parts[-1][:-1] + f" {year}"
                if volume:
                    parts[-1] += f";{volume}"
                    if pages:
                        parts[-1] += f":{pages}"
                parts[-1] += "."

        return " ".join(parts)

    def _format_authors_vancouver(self, authors: str) -> str:
        """Format author names for Vancouver style.

        Args:
            authors: Author string from BibTeX

        Returns:
            Vancouver formatted author list
        """
        author_list = authors.split(" and ")

        formatted = []
        for author in author_list[:6]:
            author = author.strip()
            if "," in author:
                parts = author.split(",", 1)
                last = parts[0].strip()
                first = parts[1].strip() if len(parts) > 1 else ""
                initials = "".join([n[0] for n in first.split() if n])
                formatted.append(f"{last} {initials}")
            else:
                parts = author.split()
                if len(parts) >= 2:
                    last = parts[-1]
                    initials = "".join([n[0] for n in parts[:-1]])
                    formatted.append(f"{last} {initials}")
                else:
                    formatted.append(author)

        if len(author_list) > 6:
            return ", ".join(formatted) + ", et al"
        else:
            return ", ".join(formatted)

    def _parse_bibtex_fields(self, bibtex: str) -> dict[str, str]:
        """Parse fields from a BibTeX entry.

        Args:
            bibtex: BibTeX entry string

        Returns:
            Dictionary of field names to values
        """
        fields = {}

        # Match field = {value} or field = "value"
        pattern = r"(\w+)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|\"([^\"]*)\")"
        matches = re.findall(pattern, bibtex)

        for match in matches:
            field = match[0].lower()
            value = match[1] if match[1] else match[2]
            fields[field] = value.strip()

        return fields

    def get_citation_keys(self, analysis: AnalysisResult) -> list[str]:
        """Get all citation keys from an analysis.

        Args:
            analysis: The analysis result

        Returns:
            List of citation keys
        """
        keys = []
        for citation in analysis.get_citations():
            match = re.search(r"@\w+\{(\w+),", citation)
            if match:
                keys.append(match.group(1))
        return keys

    def format_inline_citation(self, tool: ToolInfo, style: str = "numeric") -> str:
        """Format an inline citation for a tool.

        Args:
            tool: The tool
            style: Citation style (numeric, author-year, superscript)

        Returns:
            Inline citation marker
        """
        if not tool.citation:
            return ""

        # Parse citation
        fields = self._parse_bibtex_fields(tool.citation)
        key = None
        match = re.search(r"@\w+\{(\w+),", tool.citation)
        if match:
            key = match.group(1)

        if style == "numeric":
            return f"[{key}]" if key else ""
        elif style == "author-year":
            authors = fields.get("author", "")
            year = fields.get("year", "")
            first_author = authors.split(" and ")[0].split(",")[0] if authors else ""
            if len(authors.split(" and ")) > 1:
                return f"({first_author} et al., {year})"
            else:
                return f"({first_author}, {year})"
        elif style == "superscript":
            return f"^{key}^" if key else ""

        return f"[{key}]" if key else ""
