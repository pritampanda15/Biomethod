#!/usr/bin/env python3
"""
RNA-seq quantification pipeline
Counts reads per gene using featureCounts
"""

import subprocess
import pandas as pd
from pathlib import Path

# Configuration
SAMPLES = ["sample_A", "sample_B", "sample_C"]
ALIGNED_DIR = Path("data/aligned")
COUNTS_DIR = Path("results/counts")
GTF_FILE = Path("/reference/annotation.gtf")
THREADS = 8

# Create output directory
COUNTS_DIR.mkdir(parents=True, exist_ok=True)

def run_featurecounts(bam_files, output_file, gtf):
    """Run featureCounts for gene-level quantification."""
    cmd = [
        "featureCounts",
        "-T", str(THREADS),
        "-p",  # paired-end
        "-B",  # both ends mapped
        "-C",  # not count chimeric fragments
        "-t", "exon",
        "-g", "gene_id",
        "-a", str(gtf),
        "-o", str(output_file)
    ] + [str(b) for b in bam_files]

    subprocess.run(cmd, check=True)

def clean_counts_table(raw_counts_file, clean_counts_file):
    """Clean up featureCounts output for downstream analysis."""
    # Read the raw counts
    df = pd.read_csv(raw_counts_file, sep='\t', comment='#')

    # Rename columns to sample names
    sample_cols = [c for c in df.columns if c.endswith('.bam')]
    new_names = {c: Path(c).stem.replace('_Aligned.sortedByCoord.out', '')
                 for c in sample_cols}
    df = df.rename(columns=new_names)

    # Keep only gene ID and count columns
    keep_cols = ['Geneid'] + list(new_names.values())
    df = df[keep_cols]

    # Save cleaned counts
    df.to_csv(clean_counts_file, index=False)

    return df

def main():
    print("Starting quantification pipeline...")

    # Get all BAM files
    bam_files = [ALIGNED_DIR / f"{s}_Aligned.sortedByCoord.out.bam"
                 for s in SAMPLES]

    # Run featureCounts
    raw_counts = COUNTS_DIR / "raw_counts.txt"
    run_featurecounts(bam_files, raw_counts, GTF_FILE)

    # Clean up the counts table
    clean_counts = COUNTS_DIR / "gene_counts.csv"
    counts_df = clean_counts_table(raw_counts, clean_counts)

    print(f"Quantified {len(counts_df)} genes across {len(SAMPLES)} samples")
    print("Quantification complete!")

if __name__ == "__main__":
    main()
