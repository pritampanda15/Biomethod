"""Version detection for bioinformatics tools."""

import subprocess
import sys
import re
from pathlib import Path
from typing import Any
import importlib.metadata


class VersionDetector:
    """Detect versions of installed tools and packages."""

    # Mapping of tool names to their version command
    VERSION_COMMANDS = {
        "bwa": ["bwa"],  # BWA prints version on stderr when run without args
        "bowtie2": ["bowtie2", "--version"],
        "hisat2": ["hisat2", "--version"],
        "star": ["STAR", "--version"],
        "salmon": ["salmon", "--version"],
        "kallisto": ["kallisto", "version"],
        "samtools": ["samtools", "--version"],
        "bcftools": ["bcftools", "--version"],
        "bedtools": ["bedtools", "--version"],
        "gatk": ["gatk", "--version"],
        "fastqc": ["fastqc", "--version"],
        "multiqc": ["multiqc", "--version"],
        "trimmomatic": ["trimmomatic", "-version"],
        "fastp": ["fastp", "--version"],
        "cutadapt": ["cutadapt", "--version"],
        "minimap2": ["minimap2", "--version"],
        "featurecounts": ["featureCounts", "-v"],
    }

    # Mapping of Python package names to their import names
    PYTHON_PACKAGE_MAP = {
        "biopython": "Bio",
        "scikit-learn": "sklearn",
        "numpy": "numpy",
        "pandas": "pandas",
        "scipy": "scipy",
        "scanpy": "scanpy",
        "anndata": "anndata",
        "pysam": "pysam",
        "htseq": "HTSeq",
        "pybedtools": "pybedtools",
        "pydeseq2": "pydeseq2",
        "matplotlib": "matplotlib",
        "seaborn": "seaborn",
    }

    def __init__(self):
        """Initialize the version detector."""
        self._cached_versions: dict[str, str] = {}

    def detect_python_package_version(self, package_name: str) -> str | None:
        """Detect the version of an installed Python package.

        Args:
            package_name: Name of the package

        Returns:
            Version string or None if not installed
        """
        if package_name in self._cached_versions:
            return self._cached_versions[package_name]

        # Try importlib.metadata first (preferred method)
        try:
            version = importlib.metadata.version(package_name)
            self._cached_versions[package_name] = version
            return version
        except importlib.metadata.PackageNotFoundError:
            pass

        # Try alternative package names
        alt_name = self.PYTHON_PACKAGE_MAP.get(package_name.lower())
        if alt_name:
            try:
                version = importlib.metadata.version(alt_name)
                self._cached_versions[package_name] = version
                return version
            except importlib.metadata.PackageNotFoundError:
                pass

        # Try importing and checking __version__
        try:
            import_name = self.PYTHON_PACKAGE_MAP.get(package_name.lower(), package_name)
            module = __import__(import_name)
            if hasattr(module, "__version__"):
                version = module.__version__
                self._cached_versions[package_name] = version
                return version
        except ImportError:
            pass

        return None

    def detect_cli_tool_version(self, tool_name: str) -> str | None:
        """Detect the version of a command-line tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Version string or None if not found
        """
        if tool_name in self._cached_versions:
            return self._cached_versions[tool_name]

        cmd = self.VERSION_COMMANDS.get(tool_name.lower())
        if not cmd:
            # Try generic --version
            cmd = [tool_name, "--version"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout + result.stderr
            version = self._extract_version_from_output(output)
            if version:
                self._cached_versions[tool_name] = version
                return version
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            pass

        return None

    def _extract_version_from_output(self, output: str) -> str | None:
        """Extract version string from command output.

        Args:
            output: Command output text

        Returns:
            Version string or None if not found
        """
        # Common version patterns
        patterns = [
            # "Version: X.Y.Z" or "version X.Y.Z"
            r"[Vv]ersion[:\s]+([v]?[\d]+\.[\d]+(?:\.[\d]+)?(?:[-\w.]*)?)",
            # "tool X.Y.Z" at the start of a line
            r"^\w+\s+([\d]+\.[\d]+(?:\.[\d]+)?)",
            # "vX.Y.Z" or "X.Y.Z" standalone
            r"\b([v]?[\d]+\.[\d]+(?:\.[\d]+)?)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.MULTILINE)
            if match:
                return match.group(1)

        return None

    def detect_all_python_packages(self) -> dict[str, str]:
        """Get versions of all installed Python packages.

        Returns:
            Dictionary mapping package names to versions
        """
        packages = {}
        for dist in importlib.metadata.distributions():
            packages[dist.metadata["Name"]] = dist.version
        return packages

    def get_python_version(self) -> str:
        """Get the Python interpreter version.

        Returns:
            Python version string
        """
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def detect_r_version(self) -> str | None:
        """Detect R version if available.

        Returns:
            R version string or None
        """
        try:
            result = subprocess.run(
                ["R", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout
            match = re.search(r"R version ([\d.]+)", output)
            if match:
                return match.group(1)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def detect_r_package_version(self, package_name: str) -> str | None:
        """Detect the version of an installed R package.

        Args:
            package_name: Name of the R package

        Returns:
            Version string or None if not installed
        """
        try:
            result = subprocess.run(
                [
                    "R",
                    "-q",
                    "-e",
                    f'cat(as.character(packageVersion("{package_name}")))',
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                # Extract version from output
                output = result.stdout.strip()
                # Remove R startup messages
                lines = [l for l in output.split("\n") if not l.startswith(">")]
                if lines:
                    version = lines[-1].strip()
                    if re.match(r"[\d.]+", version):
                        return version
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
