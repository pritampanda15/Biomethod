"""Smoke tests - basic sanity checks for the package."""

import pytest


class TestImports:
    """Test that all main modules can be imported."""

    def test_import_biomethod(self):
        """Test basic package import."""
        import biomethod
        assert biomethod.__version__ is not None
        assert biomethod.__version__ == "0.1.0"

    def test_import_core_modules(self):
        """Test core module imports."""
        from biomethod.core import analyzer, models, report
        assert analyzer is not None
        assert models is not None
        assert report is not None

    def test_import_parsers(self):
        """Test parser module imports."""
        from biomethod.parsers import (
            PythonParser,
            RParser,
            JupyterParser,
            NextflowParser,
            SnakemakeParser,
        )
        assert PythonParser is not None
        assert RParser is not None
        assert JupyterParser is not None
        assert NextflowParser is not None
        assert SnakemakeParser is not None

    def test_import_generators(self):
        """Test generator module imports."""
        from biomethod.generators import prose, citations
        assert prose is not None
        assert citations is not None

    def test_import_detectors(self):
        """Test detector module imports."""
        from biomethod.detectors import version, environment
        assert version is not None
        assert environment is not None


class TestModels:
    """Test basic model instantiation."""

    def test_toolinfo_creation(self):
        """Test creating a ToolInfo object."""
        from biomethod.core.models import ToolInfo

        tool = ToolInfo(
            name="bwa",
            version="0.7.17",
            category="alignment",
            source_file="test.py",
            line_number=10,
        )

        assert tool.name == "bwa"
        assert tool.version == "0.7.17"
        assert tool.category == "alignment"
        assert tool.source_file == "test.py"
        assert tool.line_number == 10

    def test_analysisresult_creation(self):
        """Test creating an AnalysisResult object."""
        from biomethod.core.models import AnalysisResult, ToolInfo

        tools = [
            ToolInfo(name="tool1", category="test", source_file="test.py"),
            ToolInfo(name="tool2", category="test", source_file="test.py"),
        ]

        result = AnalysisResult(
            tools=tools,
            source_files=["test.py"],
            workflow_type="script",
        )

        assert len(result.tools) == 2
        assert result.workflow_type == "script"

    def test_environmentinfo_creation(self):
        """Test creating an EnvironmentInfo object."""
        from biomethod.core.models import EnvironmentInfo

        env = EnvironmentInfo(
            python_version="3.10.0",
            packages={"numpy": "1.24.0", "pandas": "2.0.0"},
        )

        assert env.python_version == "3.10.0"
        assert "numpy" in env.packages
        assert env.packages["numpy"] == "1.24.0"


class TestParsers:
    """Test basic parser instantiation and can_parse methods."""

    def test_python_parser_can_parse(self):
        """Test PythonParser can identify Python files."""
        from pathlib import Path
        from biomethod.parsers import PythonParser

        parser = PythonParser()
        assert parser.can_parse(Path("test.py"))
        assert parser.can_parse(Path("script.py"))
        assert not parser.can_parse(Path("test.R"))
        assert not parser.can_parse(Path("test.nf"))

    def test_r_parser_can_parse(self):
        """Test RParser can identify R files."""
        from pathlib import Path
        from biomethod.parsers import RParser

        parser = RParser()
        assert parser.can_parse(Path("test.R"))
        assert parser.can_parse(Path("test.r"))
        assert parser.can_parse(Path("analysis.Rmd"))
        assert not parser.can_parse(Path("test.py"))

    def test_nextflow_parser_can_parse(self):
        """Test NextflowParser can identify Nextflow files."""
        from pathlib import Path
        from biomethod.parsers import NextflowParser

        parser = NextflowParser()
        assert parser.can_parse(Path("pipeline.nf"))
        assert parser.can_parse(Path("main.nf"))
        assert not parser.can_parse(Path("test.py"))


class TestGenerators:
    """Test basic generator instantiation."""

    def test_prose_generator_creation(self):
        """Test ProseGenerator can be instantiated."""
        from biomethod.generators.prose import ProseGenerator

        generator = ProseGenerator(style="generic")
        assert generator is not None
        assert generator.style == "generic"

    def test_citation_formatter_creation(self):
        """Test CitationFormatter can be instantiated."""
        from biomethod.generators.citations import CitationFormatter

        formatter = CitationFormatter(style="bibtex")
        assert formatter is not None


class TestCLI:
    """Test CLI module imports."""

    def test_cli_import(self):
        """Test that CLI module can be imported."""
        from biomethod import cli
        assert cli is not None
        assert hasattr(cli, "main")


class TestDatabaseLoading:
    """Test that tool database can be loaded."""

    def test_load_tools_database(self):
        """Test loading the tools database."""
        import yaml
        from pathlib import Path

        db_path = Path(__file__).parent.parent / "src" / "biomethod" / "data" / "tools_database.yaml"

        if not db_path.exists():
            pytest.skip("Tools database not found")

        with open(db_path) as f:
            database = yaml.safe_load(f)

        assert database is not None
        assert isinstance(database, dict)
        assert len(database) > 0

        # Check that at least some common tools exist
        common_tools = ["bwa", "star", "samtools", "gatk", "deseq2"]
        found_tools = [tool for tool in common_tools if tool in database]
        assert len(found_tools) > 0, "No common tools found in database"

    def test_load_parameter_descriptions(self):
        """Test loading the parameter descriptions."""
        import yaml
        from pathlib import Path

        param_path = Path(__file__).parent.parent / "src" / "biomethod" / "data" / "parameter_descriptions.yaml"

        if not param_path.exists():
            pytest.skip("Parameter descriptions not found")

        with open(param_path) as f:
            params = yaml.safe_load(f)

        assert params is not None
        assert isinstance(params, dict)


class TestAPI:
    """Test main API functions."""

    def test_analyze_function_exists(self):
        """Test that analyze function is exported."""
        from biomethod import analyze
        assert analyze is not None
        assert callable(analyze)

    def test_generate_methods_function_exists(self):
        """Test that generate_methods function is exported."""
        from biomethod import generate_methods
        assert generate_methods is not None
        assert callable(generate_methods)

    def test_reproducibility_check_function_exists(self):
        """Test that reproducibility_check function is exported."""
        from biomethod import reproducibility_check
        assert reproducibility_check is not None
        assert callable(reproducibility_check)
