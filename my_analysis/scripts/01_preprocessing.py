#!/usr/bin/env python3
"""
RNA-seq preprocessing pipeline
Performs QC and read trimming on raw FASTQ files
"""

import subprocess
import os
from pathlib import Path

# Configuration
SAMPLES = ["sample_A", "sample_B", "sample_C"]
RAW_DIR = Path("data/raw")
TRIMMED_DIR = Path("data/trimmed")
QC_DIR = Path("results/qc")

# Create output directories
TRIMMED_DIR.mkdir(parents=True, exist_ok=True)
QC_DIR.mkdir(parents=True, exist_ok=True)

def run_fastqc(input_files, output_dir):
    """Run FastQC on input files."""
    cmd = [
        "fastqc",
        "-t", "4",
        "-o", str(output_dir),
        "--noextract"
    ] + [str(f) for f in input_files]

    subprocess.run(cmd, check=True)

def run_fastp(sample_id, r1_in, r2_in, r1_out, r2_out):
    """Run fastp for adapter trimming and quality filtering."""
    cmd = [
        "fastp",
        "-i", str(r1_in),
        "-I", str(r2_in),
        "-o", str(r1_out),
        "-O", str(r2_out),
        "-w", "8",
        "-q", "20",
        "-l", "50",
        "--detect_adapter_for_pe",
        "--correction",
        "--json", f"results/qc/{sample_id}_fastp.json",
        "--html", f"results/qc/{sample_id}_fastp.html"
    ]

    subprocess.run(cmd, check=True)

def main():
    print("Starting preprocessing pipeline...")

    # Process each sample
    for sample in SAMPLES:
        print(f"Processing {sample}...")

        r1_raw = RAW_DIR / f"{sample}_R1.fastq.gz"
        r2_raw = RAW_DIR / f"{sample}_R2.fastq.gz"
        r1_trimmed = TRIMMED_DIR / f"{sample}_R1_trimmed.fastq.gz"
        r2_trimmed = TRIMMED_DIR / f"{sample}_R2_trimmed.fastq.gz"

        # Run fastp
        run_fastp(sample, r1_raw, r2_raw, r1_trimmed, r2_trimmed)

    # Run FastQC on trimmed files
    trimmed_files = list(TRIMMED_DIR.glob("*.fastq.gz"))
    run_fastqc(trimmed_files, QC_DIR)

    # Run MultiQC to aggregate reports
    subprocess.run([
        "multiqc",
        "results/qc",
        "-o", "results/multiqc",
        "-n", "preprocessing_report"
    ], check=True)

    print("Preprocessing complete!")

if __name__ == "__main__":
    main()
