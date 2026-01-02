"""Tests for code parsers."""

import pytest
from pathlib import Path

from biomethod.parsers import (
    PythonParser,
    JupyterParser,
    RParser,
    NextflowParser,
    SnakemakeParser,
)


@pytest.fixture
def fixtures_dir():
    """Return the path to test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def python_parser():
    """Create a Python parser instance."""
    return PythonParser()


@pytest.fixture
def r_parser():
    """Create an R parser instance."""
    return RParser()


@pytest.fixture
def nextflow_parser():
    """Create a Nextflow parser instance."""
    return NextflowParser()


class TestPythonParser:
    """Tests for Python parser."""

    def test_can_parse_python_file(self, python_parser):
        """Test that parser can identify Python files."""
        assert python_parser.can_parse(Path("test.py"))
        assert not python_parser.can_parse(Path("test.R"))
        assert not python_parser.can_parse(Path("test.nf"))

    def test_parse_sample_rnaseq(self, python_parser, fixtures_dir):
        """Test parsing the sample RNA-seq script."""
        sample_file = fixtures_dir / "sample_rnaseq.py"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        tools = python_parser.parse(sample_file)

        # Should find multiple tools
        assert len(tools) > 0

        # Check for specific tools
        tool_names = [t.name for t in tools]
        assert "fastp" in tool_names
        assert "fastqc" in tool_names
        assert "star" in tool_names
        assert "samtools" in tool_names
        assert "featurecounts" in tool_names
        assert "multiqc" in tool_names

    def test_extract_subprocess_params(self, python_parser, fixtures_dir):
        """Test extraction of subprocess parameters."""
        sample_file = fixtures_dir / "sample_rnaseq.py"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        tools = python_parser.parse(sample_file)

        # Find STAR tool and check parameters
        star_tools = [t for t in tools if t.name == "star"]
        assert len(star_tools) > 0

        star_tool = star_tools[0]
        assert "--runThreadN" in star_tool.parameters or "-runThreadN" in str(star_tool.parameters)

    def test_import_detection(self, python_parser):
        """Test detection of Python imports."""
        import ast

        code = """
import pandas as pd
import numpy as np
from Bio import SeqIO
import scanpy as sc
import pysam
"""
        tree = ast.parse(code)
        tools = python_parser._extract_imports(tree, "test.py")

        tool_names = [t.name for t in tools]
        assert "pandas" in tool_names
        assert "numpy" in tool_names
        assert "biopython" in tool_names
        assert "scanpy" in tool_names
        assert "samtools" in tool_names  # pysam maps to samtools


class TestRParser:
    """Tests for R parser."""

    def test_can_parse_r_file(self, r_parser):
        """Test that parser can identify R files."""
        assert r_parser.can_parse(Path("test.R"))
        assert r_parser.can_parse(Path("test.r"))
        assert r_parser.can_parse(Path("test.Rmd"))
        assert not r_parser.can_parse(Path("test.py"))

    def test_parse_sample_analysis(self, r_parser, fixtures_dir):
        """Test parsing the sample R analysis script."""
        sample_file = fixtures_dir / "sample_analysis.R"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        tools = r_parser.parse(sample_file)

        # Should find multiple tools
        assert len(tools) > 0

        # Check for specific tools
        tool_names = [t.name for t in tools]
        assert "deseq2" in tool_names
        assert "edger" in tool_names
        assert "ggplot2" in tool_names
        assert "clusterprofiler" in tool_names

    def test_library_extraction(self, r_parser):
        """Test extraction of library() calls."""
        line = 'library(DESeq2)'
        tools = r_parser._extract_library_calls(line, "test.R", 1)

        assert len(tools) == 1
        assert tools[0].name == "deseq2"

    def test_function_call_detection(self, r_parser):
        """Test detection of known R functions."""
        line = 'dds <- DESeqDataSetFromMatrix(countData = counts, colData = metadata, design = ~ condition)'
        tools = r_parser._extract_function_calls(line, "test.R", 1)

        assert len(tools) > 0
        assert any(t.name == "deseq2" for t in tools)


class TestNextflowParser:
    """Tests for Nextflow parser."""

    def test_can_parse_nf_file(self, nextflow_parser):
        """Test that parser can identify Nextflow files."""
        assert nextflow_parser.can_parse(Path("pipeline.nf"))
        assert not nextflow_parser.can_parse(Path("test.py"))

    def test_parse_sample_pipeline(self, nextflow_parser, fixtures_dir):
        """Test parsing the sample Nextflow pipeline."""
        sample_file = fixtures_dir / "sample_pipeline.nf"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        tools = nextflow_parser.parse(sample_file)

        # Should find multiple tools
        assert len(tools) > 0

        # Check for specific tools from containers
        tool_names = [t.name for t in tools]
        assert "fastqc" in tool_names
        assert "fastp" in tool_names
        assert "star" in tool_names
        assert "featurecounts" in tool_names

    def test_container_version_extraction(self, nextflow_parser):
        """Test extraction of version from container images."""
        tool = nextflow_parser._parse_container_image(
            "quay.io/biocontainers/fastp:0.23.2--h79da9fb_0",
            "test.nf",
            "FASTP"
        )

        assert tool is not None
        assert tool.name == "fastp"
        assert tool.version == "0.23.2"


class TestSnakemakeParser:
    """Tests for Snakemake parser."""

    def test_can_parse_snakefile(self):
        """Test that parser can identify Snakemake files."""
        parser = SnakemakeParser()

        assert parser.can_parse(Path("Snakefile"))
        assert parser.can_parse(Path("workflow.smk"))
        assert not parser.can_parse(Path("test.py"))


class TestParserIntegration:
    """Integration tests for parsers."""

    def test_all_parsers_return_toolinfo(self, fixtures_dir):
        """Test that all parsers return valid ToolInfo objects."""
        parsers = [
            (PythonParser(), "sample_rnaseq.py"),
            (RParser(), "sample_analysis.R"),
            (NextflowParser(), "sample_pipeline.nf"),
        ]

        for parser, filename in parsers:
            sample_file = fixtures_dir / filename
            if not sample_file.exists():
                continue

            tools = parser.parse(sample_file)

            for tool in tools:
                assert tool.name is not None
                assert tool.source_file is not None
                assert isinstance(tool.parameters, dict)
                assert isinstance(tool.category, str)

    def test_tool_enrichment_from_database(self, fixtures_dir):
        """Test that tools are enriched with database info."""
        # Load database
        import yaml
        db_path = Path(__file__).parent.parent / "src" / "biomethod" / "data" / "tools_database.yaml"

        if not db_path.exists():
            pytest.skip("Tools database not found")

        with open(db_path) as f:
            database = yaml.safe_load(f)

        parser = PythonParser(database)
        sample_file = fixtures_dir / "sample_rnaseq.py"

        if not sample_file.exists():
            pytest.skip("Sample file not found")

        tools = parser.parse(sample_file)

        # Some tools should have citations
        tools_with_citations = [t for t in tools if t.citation]
        assert len(tools_with_citations) > 0
