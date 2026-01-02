#!/usr/bin/env python3
"""
RNA-seq alignment pipeline
Aligns reads to reference genome using STAR
"""

import subprocess
import os
from pathlib import Path

# Configuration
SAMPLES = ["sample_A", "sample_B", "sample_C"]
TRIMMED_DIR = Path("data/trimmed")
ALIGNED_DIR = Path("data/aligned")
GENOME_DIR = Path("/reference/star_index")
THREADS = 16

# Create output directory
ALIGNED_DIR.mkdir(parents=True, exist_ok=True)

def run_star_alignment(sample_id, r1, r2, output_prefix):
    """Run STAR aligner."""
    cmd = [
        "STAR",
        "--runThreadN", str(THREADS),
        "--genomeDir", str(GENOME_DIR),
        "--readFilesIn", str(r1), str(r2),
        "--readFilesCommand", "zcat",
        "--outFileNamePrefix", str(output_prefix),
        "--outSAMtype", "BAM", "SortedByCoordinate",
        "--outSAMattributes", "NH", "HI", "AS", "NM", "MD",
        "--quantMode", "GeneCounts",
        "--twopassMode", "Basic",
        "--outFilterMultimapNmax", "20",
        "--alignSJoverhangMin", "8",
        "--alignSJDBoverhangMin", "1",
        "--outFilterMismatchNmax", "999",
        "--outFilterMismatchNoverReadLmax", "0.04",
        "--alignIntronMin", "20",
        "--alignIntronMax", "1000000",
        "--alignMatesGapMax", "1000000"
    ]

    subprocess.run(cmd, check=True)

def index_bam(bam_file):
    """Index BAM file with samtools."""
    subprocess.run([
        "samtools", "index",
        "-@", "8",
        str(bam_file)
    ], check=True)

def get_alignment_stats(bam_file, output_file):
    """Get alignment statistics with samtools."""
    with open(output_file, 'w') as f:
        subprocess.run([
            "samtools", "flagstat",
            str(bam_file)
        ], stdout=f, check=True)

def main():
    print("Starting alignment pipeline...")

    for sample in SAMPLES:
        print(f"Aligning {sample}...")

        r1 = TRIMMED_DIR / f"{sample}_R1_trimmed.fastq.gz"
        r2 = TRIMMED_DIR / f"{sample}_R2_trimmed.fastq.gz"
        output_prefix = ALIGNED_DIR / f"{sample}_"

        # Run STAR
        run_star_alignment(sample, r1, r2, output_prefix)

        # Index the output BAM
        bam_file = ALIGNED_DIR / f"{sample}_Aligned.sortedByCoord.out.bam"
        index_bam(bam_file)

        # Get stats
        stats_file = ALIGNED_DIR / f"{sample}_flagstat.txt"
        get_alignment_stats(bam_file, stats_file)

    print("Alignment complete!")

if __name__ == "__main__":
    main()
