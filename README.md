# BioMethod

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Development Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/pritam/Biomethod)

**Automated methods section generator for bioinformatics papers**

BioMethod scans bioinformatics code (Python scripts, Jupyter notebooks, R scripts, Nextflow/Snakemake workflows) and automatically generates publication-ready methods sections with all software versions, parameters, and citations.

## Features

- **Multi-language parsing**: Python, R, Jupyter notebooks, Nextflow DSL2, Snakemake
- **Automatic version detection**: Detects installed package versions from the environment
- **Comprehensive tool database**: Built-in citations for 20+ common bioinformatics tools
- **Multiple output formats**: Markdown, DOCX, HTML, LaTeX
- **Journal styles**: Generic, Nature Methods, Bioinformatics (Oxford), PLOS ONE
- **Reproducibility checking**: Follows Sandve's 10 rules for reproducible research

## Installation

```bash
pip install biomethod
```

Or install from source:

```bash
git clone https://github.com/pritam/Biomethod.git
cd Biomethod
pip install -e .
```

## Quick Start

### Python API

```python
import biomethod as bm

# Analyze a directory
analysis = bm.analyze("./my_analysis/")

# Generate methods section
methods = bm.generate_methods(
    analysis,
    style="nature",           # Journal style
    output_format="docx",     # Output format
    include_citations=True,
    include_supplementary=True
)

# Save outputs
methods.save("methods_section.docx")
methods.save_citations("references.bib")
methods.save_supplementary("supplementary_table_s1.xlsx")

# Get reproducibility report
report = bm.reproducibility_check(analysis)
print(report.summary())
```

### Command Line

```bash
# Generate methods section
biomethod generate ./analysis_directory/ -o methods.docx

# With options
biomethod generate ./analysis/ \
    --style nature \
    --format docx \
    --citations-output references.bib \
    --supplementary-output supp_tables.xlsx

# List detected tools
biomethod list-tools ./analysis/

# Check reproducibility
biomethod check ./analysis/

# Get info about a tool
biomethod info bwa
```

## Supported Tools

BioMethod includes citations and metadata for common bioinformatics tools including:

### Alignment
- BWA, BWA-MEM2, Bowtie2, HISAT2, STAR, Minimap2

### Quantification
- Salmon, Kallisto, RSEM, featureCounts, HTSeq, StringTie

### Quality Control & Preprocessing
- FastQC, MultiQC, Trimmomatic, fastp, Cutadapt

### Variant Calling
- GATK, bcftools, samtools, Picard

### Differential Expression
- DESeq2, edgeR, limma

### Single-Cell
- Scanpy, Seurat

### And many more...

## Output Examples

### Generic Style
```
Raw sequencing reads were preprocessed using fastp (v0.23.2).
Quality control was performed using FastQC (v0.11.9) and MultiQC (v1.14).
Sequence alignment was performed using STAR (v2.7.10a) [dobin2013star].
Gene expression quantification was performed using featureCounts (v2.0.1) [liao2014featurecounts].
Differential expression analysis was conducted using DESeq2 (v1.38.0) [love2014moderated].
```

### Nature Style
```
**Data preprocessing.** Raw reads were processed using fastp. Quality metrics were assessed using FastQC.

**Alignment.** Reads were mapped to the reference genome using STAR.

**Quantification.** Expression levels were quantified using featureCounts.

**Differential expression.** Differential expression analysis was performed using DESeq2.

**Software versions.** Detailed software versions are provided in Supplementary Table 1.
```

## Project Structure

```
biomethod/
├── src/biomethod/
│   ├── cli.py              # Command-line interface
│   ├── core/
│   │   ├── analyzer.py     # Main analysis orchestrator
│   │   ├── models.py       # Data models (ToolInfo, AnalysisResult)
│   │   └── report.py       # Report generation
│   ├── parsers/
│   │   ├── python_parser.py
│   │   ├── jupyter_parser.py
│   │   ├── r_parser.py
│   │   ├── nextflow_parser.py
│   │   └── snakemake_parser.py
│   ├── detectors/
│   │   ├── version.py      # Version detection
│   │   └── environment.py  # Environment parsing
│   ├── generators/
│   │   ├── prose.py        # Natural language generation
│   │   ├── citations.py    # Citation formatting
│   │   └── templates/      # Jinja2 templates
│   └── data/
│       └── tools_database.yaml
├── tests/
└── pyproject.toml
```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Adding New Tools

To add a new tool to the database, edit `src/biomethod/data/tools_database.yaml`:

```yaml
your_tool:
  aliases: ["alt_name"]
  category: "alignment"
  description: "Description of the tool"
  citation: |
    @article{author2026tool,
      title={Your Tool Paper},
      author={Author, Name},
      journal={Journal},
      year={2026}
    }
  common_parameters:
    -t: "Number of threads"
```

## License

MIT License - see LICENSE file for details.

## Citation

If you use BioMethod in your research, please cite:

```
BioMethod: Automated methods section generator for bioinformatics papers
https://github.com/pritam/Biomethod
```
