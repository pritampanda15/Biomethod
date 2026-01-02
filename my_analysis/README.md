# RNA-seq Analysis Pipeline

This directory contains a complete RNA-seq differential expression analysis pipeline.

## Pipeline Steps

1. **Preprocessing** (`scripts/01_preprocessing.py`)
   - Quality control with FastQC
   - Adapter trimming with fastp
   - Aggregate QC with MultiQC

2. **Alignment** (`scripts/02_alignment.py`)
   - Align reads to reference genome with STAR
   - Index BAM files with samtools

3. **Quantification** (`scripts/03_quantification.py`)
   - Count reads per gene with featureCounts

4. **Differential Expression** (`scripts/04_differential_expression.R`)
   - DESeq2 analysis
   - Visualization (PCA, heatmaps, volcano plots)

5. **Enrichment Analysis** (`scripts/05_enrichment_analysis.R`)
   - GO enrichment with clusterProfiler
   - KEGG pathway analysis

## Exploratory Analysis

See `notebooks/exploratory_analysis.ipynb` for interactive data exploration.

## Environment Setup

```bash
# Using conda
conda env create -f envs/environment.yml
conda activate rnaseq_analysis

# Or using pip
pip install -r requirements.txt
```

## Running the Pipeline

```bash
# Run each step sequentially
python scripts/01_preprocessing.py
python scripts/02_alignment.py
python scripts/03_quantification.py
Rscript scripts/04_differential_expression.R
Rscript scripts/05_enrichment_analysis.R
```
