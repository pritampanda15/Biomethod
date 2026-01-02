"""Helper utility functions for BioMethod."""

from pathlib import Path


def normalize_tool_name(name: str) -> str:
    """Normalize a tool name for consistent comparison.

    Args:
        name: Tool name to normalize

    Returns:
        Normalized tool name (lowercase, underscores)
    """
    return name.lower().replace("-", "_").replace(" ", "_")


def format_version(version: str | None, prefix: str = "v") -> str:
    """Format a version string with optional prefix.

    Args:
        version: Version string
        prefix: Prefix to add (default: "v")

    Returns:
        Formatted version string
    """
    if not version:
        return ""
    if version.startswith(prefix):
        return version
    return f"{prefix}{version}"


def is_bioinformatics_file(path: Path) -> bool:
    """Check if a file is likely a bioinformatics analysis file.

    Args:
        path: Path to check

    Returns:
        True if the file is likely a bioinformatics file
    """
    bioinf_extensions = {
        ".py", ".ipynb", ".r", ".R", ".rmd", ".Rmd",
        ".nf", ".smk", ".snakefile", ".wdl",
    }

    bioinf_names = {
        "snakefile", "nextflow.config", "params.yaml",
        "environment.yml", "environment.yaml",
    }

    if path.suffix in bioinf_extensions:
        return True

    if path.name.lower() in bioinf_names:
        return True

    return False


def extract_file_paths(text: str) -> list[str]:
    """Extract potential file paths from text.

    Args:
        text: Text to search

    Returns:
        List of potential file paths
    """
    import re

    patterns = [
        # Unix paths
        r'["\']?(/[\w./\-_]+\.\w+)["\']?',
        # Windows paths
        r'["\']?([A-Za-z]:\\[\w\\./\-_]+\.\w+)["\']?',
        # Relative paths
        r'["\']?(\.{1,2}/[\w./\-_]+\.\w+)["\']?',
    ]

    paths = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        paths.extend(matches)

    return list(set(paths))


def categorize_path(path: str) -> str | None:
    """Categorize a file path by type.

    Args:
        path: File path

    Returns:
        Category (input, output, reference, annotation) or None
    """
    path_lower = path.lower()

    # Input file patterns
    input_patterns = [".fastq", ".fq", ".bam", ".sam", ".vcf", ".bed"]
    if any(pattern in path_lower for pattern in input_patterns):
        if "output" in path_lower or "result" in path_lower:
            return "output"
        return "input"

    # Reference patterns
    ref_patterns = [".fa", ".fasta", ".fna", "genome", "reference"]
    if any(pattern in path_lower for pattern in ref_patterns):
        return "reference"

    # Annotation patterns
    annot_patterns = [".gtf", ".gff", ".gff3", "annotation"]
    if any(pattern in path_lower for pattern in annot_patterns):
        return "annotation"

    # Output patterns
    output_patterns = ["output", "result", ".csv", ".tsv", ".xlsx"]
    if any(pattern in path_lower for pattern in output_patterns):
        return "output"

    return None
