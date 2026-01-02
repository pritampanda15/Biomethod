"""Sample RNA-seq analysis script for testing BioMethod."""

import subprocess
import pandas as pd
import numpy as np

# Preprocessing with fastp
subprocess.run([
    "fastp",
    "-i", "sample_R1.fastq.gz",
    "-I", "sample_R2.fastq.gz",
    "-o", "sample_R1_trimmed.fastq.gz",
    "-O", "sample_R2_trimmed.fastq.gz",
    "-w", "8",
    "--detect_adapter_for_pe"
])

# Quality control with FastQC
subprocess.run(["fastqc", "sample_R1_trimmed.fastq.gz", "-o", "qc/"])

# Alignment with STAR
subprocess.run([
    "STAR",
    "--runThreadN", "16",
    "--genomeDir", "/ref/star_index",
    "--readFilesIn", "sample_R1_trimmed.fastq.gz", "sample_R2_trimmed.fastq.gz",
    "--readFilesCommand", "zcat",
    "--outFileNamePrefix", "aligned/sample_",
    "--outSAMtype", "BAM", "SortedByCoordinate",
    "--quantMode", "GeneCounts"
])

# Alternatively: alignment with HISAT2
# subprocess.run([
#     "hisat2",
#     "-x", "/ref/hisat2_index/genome",
#     "-1", "sample_R1_trimmed.fastq.gz",
#     "-2", "sample_R2_trimmed.fastq.gz",
#     "-p", "16",
#     "--dta",
#     "-S", "aligned/sample.sam"
# ])

# Index and sort with samtools
subprocess.run(["samtools", "sort", "-@", "8", "-o", "aligned/sample_sorted.bam", "aligned/sample.bam"])
subprocess.run(["samtools", "index", "aligned/sample_sorted.bam"])

# Quantification with featureCounts
subprocess.run([
    "featureCounts",
    "-T", "8",
    "-p",
    "-a", "/ref/annotation.gtf",
    "-o", "counts/sample_counts.txt",
    "aligned/sample_sorted.bam"
])

# Aggregate QC with MultiQC
subprocess.run(["multiqc", ".", "-o", "multiqc_report/"])

# Load counts for downstream analysis
counts = pd.read_csv("counts/sample_counts.txt", sep="\t", comment="#")

# Simple normalization
total_counts = counts.iloc[:, 6:].sum(axis=0)
normalized = counts.iloc[:, 6:].div(total_counts) * 1e6  # CPM

print(f"Analyzed {len(counts)} genes")
print(f"Total counts per sample: {total_counts.values}")
