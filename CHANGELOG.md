# Changelog

All notable changes to BioMethod will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- PyPI package publication
- Comprehensive test suite
- Documentation site
- Additional journal style templates
- Support for more bioinformatics tools

## [0.1.0] - 2026-01-06

### Added
- Initial release of BioMethod
- Multi-language parsing support:
  - Python scripts
  - R scripts
  - Jupyter notebooks (.ipynb)
  - Nextflow DSL2 workflows
  - Snakemake workflows
- Automatic version detection from environment
- Built-in citation database for 20+ common bioinformatics tools
- Multiple output formats: Markdown, DOCX, HTML, LaTeX
- Journal style templates:
  - Generic
  - Nature Methods
  - Bioinformatics (Oxford)
  - PLOS ONE
- CLI interface with commands:
  - `generate`: Generate methods section
  - `list-tools`: List detected tools
  - `check`: Reproducibility check
  - `info`: Get tool information
- Python API for programmatic use
- Supplementary materials generation (Excel tables)
- BibTeX citation export
- Reproducibility checking following Sandve's 10 rules

### Project Structure
- Core analyzer and report generation
- Modular parser architecture
- Version detection system
- YAML-based tool database
- Jinja2 template system

[Unreleased]: https://github.com/pritam/Biomethod/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/pritam/Biomethod/releases/tag/v0.1.0
