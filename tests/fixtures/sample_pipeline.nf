#!/usr/bin/env nextflow

/*
 * Sample RNA-seq pipeline for testing BioMethod
 * DSL2 syntax
 */

nextflow.enable.dsl = 2

// Parameters
params.reads = "data/*_{R1,R2}.fastq.gz"
params.genome = "ref/genome.fa"
params.gtf = "ref/annotation.gtf"
params.outdir = "results"

// Process: Quality control with FastQC
process FASTQC {
    container 'biocontainers/fastqc:v0.11.9'

    input:
    tuple val(sample_id), path(reads)

    output:
    path("*.html"), emit: html
    path("*.zip"), emit: zip

    script:
    """
    fastqc -t ${task.cpus} ${reads}
    """
}

// Process: Trimming with fastp
process FASTP {
    container 'quay.io/biocontainers/fastp:0.23.2--h79da9fb_0'

    input:
    tuple val(sample_id), path(reads)

    output:
    tuple val(sample_id), path("*.trimmed.fastq.gz"), emit: reads
    path("*.json"), emit: json

    script:
    """
    fastp \\
        -i ${reads[0]} \\
        -I ${reads[1]} \\
        -o ${sample_id}_R1.trimmed.fastq.gz \\
        -O ${sample_id}_R2.trimmed.fastq.gz \\
        -w ${task.cpus} \\
        --detect_adapter_for_pe \\
        --json ${sample_id}_fastp.json
    """
}

// Process: Alignment with STAR
process STAR_ALIGN {
    container 'quay.io/biocontainers/star:2.7.10a--h9ee0642_0'

    input:
    tuple val(sample_id), path(reads)
    path(genome_dir)

    output:
    tuple val(sample_id), path("*.bam"), emit: bam
    path("*Log.final.out"), emit: log

    script:
    """
    STAR \\
        --runThreadN ${task.cpus} \\
        --genomeDir ${genome_dir} \\
        --readFilesIn ${reads[0]} ${reads[1]} \\
        --readFilesCommand zcat \\
        --outFileNamePrefix ${sample_id}_ \\
        --outSAMtype BAM SortedByCoordinate \\
        --quantMode GeneCounts
    """
}

// Process: Quantification with featureCounts
process FEATURECOUNTS {
    container 'quay.io/biocontainers/subread:2.0.1--hed695b0_0'

    input:
    path(bams)
    path(gtf)

    output:
    path("counts.txt"), emit: counts
    path("counts.txt.summary"), emit: summary

    script:
    """
    featureCounts \\
        -T ${task.cpus} \\
        -p \\
        -a ${gtf} \\
        -o counts.txt \\
        ${bams}
    """
}

// Process: MultiQC report
process MULTIQC {
    container 'quay.io/biocontainers/multiqc:1.14--pyhdfd78af_0'

    input:
    path("*")

    output:
    path("multiqc_report.html")
    path("multiqc_data")

    script:
    """
    multiqc .
    """
}

// Workflow
workflow {
    // Read input
    Channel
        .fromFilePairs(params.reads)
        .set { read_pairs_ch }

    // QC
    FASTQC(read_pairs_ch)

    // Trim
    FASTP(read_pairs_ch)

    // Align
    STAR_ALIGN(FASTP.out.reads, params.genome)

    // Quantify
    bams = STAR_ALIGN.out.bam.map { it[1] }.collect()
    FEATURECOUNTS(bams, params.gtf)

    // Report
    MULTIQC(
        FASTQC.out.zip
            .mix(FASTP.out.json)
            .mix(STAR_ALIGN.out.log)
            .mix(FEATURECOUNTS.out.summary)
            .collect()
    )
}
