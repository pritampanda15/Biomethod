#!/usr/bin/env Rscript
# Functional Enrichment Analysis
# GO and KEGG pathway analysis of differentially expressed genes

# Load required libraries
library(clusterProfiler)
library(org.Hs.eg.db)
library(enrichplot)
library(ggplot2)
library(DOSE)

# Set seed for reproducibility
set.seed(42)

# Read significant genes from DESeq2 analysis
sig_genes <- read.csv("results/differential_expression/significant_genes.csv")

# Separate up and down regulated genes
upregulated <- sig_genes[sig_genes$log2FoldChange > 0, "gene_id"]
downregulated <- sig_genes[sig_genes$log2FoldChange < 0, "gene_id"]
all_sig <- sig_genes$gene_id

cat("Upregulated genes:", length(upregulated), "\n")
cat("Downregulated genes:", length(downregulated), "\n")

# Convert gene symbols to Entrez IDs
convert_to_entrez <- function(genes) {
  entrez <- mapIds(org.Hs.eg.db,
                   keys = genes,
                   column = "ENTREZID",
                   keytype = "SYMBOL",
                   multiVals = "first")
  entrez[!is.na(entrez)]
}

entrez_all <- convert_to_entrez(all_sig)
entrez_up <- convert_to_entrez(upregulated)
entrez_down <- convert_to_entrez(downregulated)

# GO Enrichment Analysis (Biological Process)
ego_bp <- enrichGO(gene = entrez_all,
                   OrgDb = org.Hs.eg.db,
                   ont = "BP",
                   pAdjustMethod = "BH",
                   pvalueCutoff = 0.05,
                   qvalueCutoff = 0.1,
                   readable = TRUE)

# GO Enrichment (Molecular Function)
ego_mf <- enrichGO(gene = entrez_all,
                   OrgDb = org.Hs.eg.db,
                   ont = "MF",
                   pAdjustMethod = "BH",
                   pvalueCutoff = 0.05,
                   qvalueCutoff = 0.1,
                   readable = TRUE)

# KEGG Pathway Enrichment
ekegg <- enrichKEGG(gene = entrez_all,
                    organism = 'hsa',
                    pvalueCutoff = 0.05,
                    qvalueCutoff = 0.1)

# Create output directory
dir.create("results/enrichment", showWarnings = FALSE, recursive = TRUE)

# Save results
write.csv(as.data.frame(ego_bp), "results/enrichment/go_biological_process.csv", row.names = FALSE)
write.csv(as.data.frame(ego_mf), "results/enrichment/go_molecular_function.csv", row.names = FALSE)
write.csv(as.data.frame(ekegg), "results/enrichment/kegg_pathways.csv", row.names = FALSE)

# Visualizations
# GO Dotplot
pdf("results/figures/go_bp_dotplot.pdf", width = 10, height = 8)
dotplot(ego_bp, showCategory = 20, title = "GO Biological Process Enrichment")
dev.off()

# KEGG Barplot
pdf("results/figures/kegg_barplot.pdf", width = 10, height = 8)
barplot(ekegg, showCategory = 15, title = "KEGG Pathway Enrichment")
dev.off()

# Gene-Concept Network
pdf("results/figures/go_cnetplot.pdf", width = 12, height = 10)
cnetplot(ego_bp, showCategory = 5, categorySize = "pvalue")
dev.off()

cat("\nEnrichment analysis complete!\n")
cat("Results saved to results/enrichment/\n")
