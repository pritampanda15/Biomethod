"""Tests for methods generators."""

import pytest
from pathlib import Path

from biomethod.core.models import AnalysisResult, ToolInfo, EnvironmentInfo
from biomethod.generators.prose import ProseGenerator
from biomethod.generators.citations import CitationFormatter


@pytest.fixture
def sample_analysis():
    """Create a sample analysis result for testing."""
    tools = [
        ToolInfo(
            name="fastp",
            version="0.23.2",
            category="preprocessing",
            source_file="analysis.py",
            line_number=10,
            parameters={"-w": "8", "--detect_adapter_for_pe": True},
        ),
        ToolInfo(
            name="star",
            version="2.7.10a",
            category="alignment",
            source_file="analysis.py",
            line_number=20,
            parameters={"--runThreadN": "16", "--quantMode": "GeneCounts"},
            citation="""@article{dobin2013star,
              title={{STAR}: ultrafast universal {RNA-seq} aligner},
              author={Dobin, Alexander},
              journal={Bioinformatics},
              year={2013}
            }""",
        ),
        ToolInfo(
            name="featurecounts",
            version="2.0.1",
            category="quantification",
            source_file="analysis.py",
            line_number=30,
            parameters={"-T": "8", "-p": True},
            citation="""@article{liao2014featurecounts,
              title={{featureCounts}: an efficient program},
              author={Liao, Yang},
              journal={Bioinformatics},
              year={2014}
            }""",
        ),
        ToolInfo(
            name="deseq2",
            version="1.38.0",
            category="differential-expression",
            source_file="analysis.R",
            line_number=5,
            parameters={"alpha": "0.05"},
            citation="""@article{love2014moderated,
              title={Moderated estimation of fold change},
              author={Love, Michael I and Huber, Wolfgang and Anders, Simon},
              journal={Genome Biology},
              year={2014}
            }""",
        ),
    ]

    return AnalysisResult(
        tools=tools,
        source_files=["analysis.py", "analysis.R"],
        workflow_type="script",
        environment=EnvironmentInfo(
            python_version="3.11.0",
            packages={"pandas": "2.0.0", "numpy": "1.24.0"},
        ),
    )


class TestProseGenerator:
    """Tests for prose generation."""

    def test_generate_methods(self, sample_analysis):
        """Test basic methods generation."""
        generator = ProseGenerator(style="generic")
        text = generator.generate(sample_analysis)

        assert len(text) > 0
        assert "fastp" in text.lower() or "preprocessing" in text.lower()
        assert "star" in text.lower() or "alignment" in text.lower()
        assert "deseq2" in text.lower() or "differential" in text.lower()

    def test_generate_with_versions(self, sample_analysis):
        """Test that versions are included when requested."""
        generator = ProseGenerator(style="generic")
        text = generator.generate(sample_analysis, include_versions=True)

        # Should include version numbers
        assert "0.23.2" in text or "v0.23.2" in text  # fastp
        assert "2.7.10a" in text or "v2.7.10a" in text  # STAR

    def test_generate_without_versions(self, sample_analysis):
        """Test that versions can be excluded."""
        generator = ProseGenerator(style="nature")
        text = generator.generate(sample_analysis, include_versions=False)

        # Nature style should not include versions in main text
        # (versions go to supplementary)
        # Check that tool names are present
        assert "fastp" in text.lower() or "star" in text.lower()

    def test_generate_from_template(self, sample_analysis):
        """Test template-based generation."""
        generator = ProseGenerator(style="generic")
        text = generator.generate_from_template(sample_analysis)

        assert len(text) > 0
        assert "Methods" in text or "methods" in text

    def test_supplementary_table(self, sample_analysis):
        """Test supplementary table generation."""
        generator = ProseGenerator(style="generic")
        table = generator.generate_supplementary_table(sample_analysis)

        assert len(table) > 0
        assert all("Tool" in row for row in table)
        assert all("Version" in row for row in table)

    def test_different_styles(self, sample_analysis):
        """Test different journal styles produce different output."""
        generic = ProseGenerator(style="generic").generate(sample_analysis)
        nature = ProseGenerator(style="nature").generate(sample_analysis)
        bioinformatics = ProseGenerator(style="bioinformatics").generate(sample_analysis)

        # All should produce output
        assert len(generic) > 0
        assert len(nature) > 0
        assert len(bioinformatics) > 0


class TestCitationFormatter:
    """Tests for citation formatting."""

    @pytest.fixture
    def sample_bibtex(self):
        """Sample BibTeX citation."""
        return """@article{dobin2013star,
          title={{STAR}: ultrafast universal {RNA-seq} aligner},
          author={Dobin, Alexander and Davis, Carrie A and Schlesinger, Felix},
          journal={Bioinformatics},
          volume={29},
          number={1},
          pages={15--21},
          year={2013},
          doi={10.1093/bioinformatics/bts635}
        }"""

    def test_bibtex_format(self, sample_analysis):
        """Test BibTeX output format."""
        formatter = CitationFormatter(style="bibtex")
        bibliography = formatter.format_bibliography(sample_analysis)

        assert "@article" in bibliography
        assert "dobin2013star" in bibliography or "star" in bibliography.lower()

    def test_apa_format(self, sample_analysis):
        """Test APA output format."""
        formatter = CitationFormatter(style="apa")
        bibliography = formatter.format_bibliography(sample_analysis)

        # APA should have author names and years
        assert len(bibliography) > 0
        # Should contain year in parentheses
        assert "2013" in bibliography or "2014" in bibliography

    def test_get_citation_keys(self, sample_analysis):
        """Test extraction of citation keys."""
        formatter = CitationFormatter()
        keys = formatter.get_citation_keys(sample_analysis)

        assert len(keys) > 0
        assert all(isinstance(k, str) for k in keys)

    def test_inline_citation(self):
        """Test inline citation formatting."""
        formatter = CitationFormatter()

        tool = ToolInfo(
            name="star",
            citation="""@article{dobin2013star,
              author={Dobin, Alexander},
              year={2013}
            }""",
        )

        numeric = formatter.format_inline_citation(tool, style="numeric")
        assert "[dobin2013star]" in numeric

        author_year = formatter.format_inline_citation(tool, style="author-year")
        assert "Dobin" in author_year
        assert "2013" in author_year


class TestAnalysisResult:
    """Tests for AnalysisResult methods."""

    def test_get_tools_by_category(self, sample_analysis):
        """Test grouping tools by category."""
        categories = sample_analysis.get_tools_by_category()

        assert "preprocessing" in categories
        assert "alignment" in categories
        assert "quantification" in categories
        assert "differential-expression" in categories

        assert len(categories["alignment"]) == 1
        assert categories["alignment"][0].name == "star"

    def test_get_unique_tools(self, sample_analysis):
        """Test getting unique tools."""
        unique = sample_analysis.get_unique_tools()

        assert len(unique) == 4
        names = [t.name for t in unique]
        assert len(names) == len(set(names))  # All unique

    def test_get_citations(self, sample_analysis):
        """Test getting citations."""
        citations = sample_analysis.get_citations()

        # Should have citations for star, featurecounts, deseq2
        assert len(citations) >= 3
        assert all("@article" in c for c in citations)


class TestIntegration:
    """Integration tests for generators."""

    def test_full_generation_pipeline(self, sample_analysis):
        """Test the full generation pipeline."""
        from biomethod.core.report import generate_methods

        methods = generate_methods(
            sample_analysis,
            style="generic",
            output_format="markdown",
            include_citations=True,
            include_supplementary=True,
        )

        # Check methods text
        assert len(methods.text) > 0

        # Check citations
        assert len(methods.citations) > 0

        # Check supplementary
        assert len(methods.supplementary) > 0

    def test_reproducibility_check(self, sample_analysis):
        """Test reproducibility checking."""
        from biomethod.core.report import reproducibility_check

        report = reproducibility_check(sample_analysis)

        assert report.score >= 0
        assert report.score <= 100
        assert len(report.checklist) > 0

        # Summary should be formatted
        summary = report.summary()
        assert "REPRODUCIBILITY REPORT" in summary
        assert "Score:" in summary
