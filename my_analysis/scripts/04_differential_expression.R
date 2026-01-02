#!/usr/bin/env Rscript
# Differential Expression Analysis with DESeq2
# Compares treatment vs control samples

# Load required libraries
library(DESeq2)
library(ggplot2)
library(pheatmap)
library(RColorBrewer)
library(EnhancedVolcano)

# Set random seed for reproducibility
set.seed(42)

# Read data
counts <- read.csv("results/counts/gene_counts.csv", row.names = 1)
metadata <- data.frame(
  sample = c("sample_A", "sample_B", "sample_C"),
  condition = c("control", "treatment", "treatment"),
  row.names = c("sample_A", "sample_B", "sample_C")
)

# Create DESeq2 dataset
dds <- DESeqDataSetFromMatrix(
  countData = as.matrix(counts),
  colData = metadata,
  design = ~ condition
)

# Filter low count genes (at least 10 reads in at least 2 samples)
keep <- rowSums(counts(dds) >= 10) >= 2
dds <- dds[keep, ]
cat("Genes after filtering:", nrow(dds), "\n")

# Run DESeq2
dds <- DESeq(dds)

# Get results
res <- results(dds,
               contrast = c("condition", "treatment", "control"),
               alpha = 0.05)

# Shrink log fold changes for visualization
res_shrunk <- lfcShrink(dds,
                        coef = "condition_treatment_vs_control",
                        type = "apeglm")

# Summary
cat("\nDESeq2 Results Summary:\n")
summary(res)

# Get variance stabilized counts for visualization
vsd <- vst(dds, blind = FALSE)

# PCA Plot
pca_data <- plotPCA(vsd, intgroup = "condition", returnData = TRUE)
percentVar <- round(100 * attr(pca_data, "percentVar"))

pca_plot <- ggplot(pca_data, aes(x = PC1, y = PC2, color = condition)) +
  geom_point(size = 4) +
  xlab(paste0("PC1: ", percentVar[1], "% variance")) +
  ylab(paste0("PC2: ", percentVar[2], "% variance")) +
  theme_minimal() +
  theme(legend.position = "bottom")

ggsave("results/figures/pca_plot.pdf", pca_plot, width = 8, height = 6)

# Heatmap of top 50 variable genes
topVarGenes <- head(order(rowVars(assay(vsd)), decreasing = TRUE), 50)
mat <- assay(vsd)[topVarGenes, ]
mat <- t(scale(t(mat)))

annotation_col <- data.frame(Condition = metadata$condition, row.names = rownames(metadata))

pdf("results/figures/heatmap_top50.pdf", width = 8, height = 10)
pheatmap(mat,
         annotation_col = annotation_col,
         show_rownames = FALSE,
         color = colorRampPalette(rev(brewer.pal(n = 7, name = "RdBu")))(100),
         main = "Top 50 Variable Genes")
dev.off()

# Volcano plot
pdf("results/figures/volcano_plot.pdf", width = 10, height = 8)
EnhancedVolcano(res,
                lab = rownames(res),
                x = 'log2FoldChange',
                y = 'pvalue',
                title = 'Treatment vs Control',
                pCutoff = 0.05,
                FCcutoff = 1,
                pointSize = 2.0,
                labSize = 3.0)
dev.off()

# Save results
res_df <- as.data.frame(res)
res_df$gene_id <- rownames(res_df)
res_df <- res_df[order(res_df$padj), ]

write.csv(res_df, "results/differential_expression/deseq2_results.csv", row.names = FALSE)

# Get significant genes
sig_genes <- subset(res_df, padj < 0.05 & abs(log2FoldChange) > 1)
write.csv(sig_genes, "results/differential_expression/significant_genes.csv", row.names = FALSE)

cat("\nSignificant genes (padj < 0.05, |LFC| > 1):", nrow(sig_genes), "\n")
cat("Results saved to results/differential_expression/\n")
