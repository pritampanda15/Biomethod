# Sample RNA-seq differential expression analysis in R
# For testing BioMethod R parser

# Load required libraries
library(DESeq2)
library(edgeR)
library(ggplot2)
library(pheatmap)
library(EnhancedVolcano)
library(clusterProfiler)
library(org.Hs.eg.db)

# Read count data
counts <- read.csv("counts/gene_counts.csv", row.names = 1)
metadata <- read.csv("metadata.csv")

# Create DESeq2 dataset
dds <- DESeqDataSetFromMatrix(
  countData = counts,
  colData = metadata,
  design = ~ condition
)

# Filter low count genes
keep <- rowSums(counts(dds)) >= 10
dds <- dds[keep, ]

# Run DESeq2
dds <- DESeq(dds)

# Get results
res <- results(dds, alpha = 0.05)

# Shrink log fold changes
res_shrunk <- lfcShrink(dds, coef = "condition_treated_vs_control", type = "apeglm")

# Get normalized counts for visualization
vsd <- vst(dds, blind = FALSE)

# PCA plot
pca_data <- plotPCA(vsd, intgroup = "condition", returnData = TRUE)
ggplot(pca_data, aes(x = PC1, y = PC2, color = condition)) +
  geom_point(size = 3) +
  theme_minimal()
ggsave("figures/pca_plot.pdf", width = 8, height = 6)

# Heatmap of top genes
top_genes <- head(order(res$padj), 50)
mat <- assay(vsd)[top_genes, ]
mat <- t(scale(t(mat)))
pheatmap(mat,
         annotation_col = metadata[, "condition", drop = FALSE],
         show_rownames = FALSE,
         filename = "figures/heatmap.pdf")

# Volcano plot
EnhancedVolcano(res,
                lab = rownames(res),
                x = 'log2FoldChange',
                y = 'pvalue',
                title = 'Differential Expression',
                pCutoff = 0.05,
                FCcutoff = 1)
ggsave("figures/volcano.pdf", width = 10, height = 8)

# Get significant genes
sig_genes <- subset(res, padj < 0.05 & abs(log2FoldChange) > 1)
sig_gene_names <- rownames(sig_genes)

# Convert to Entrez IDs for enrichment
entrez_ids <- mapIds(org.Hs.eg.db,
                     keys = sig_gene_names,
                     column = "ENTREZID",
                     keytype = "SYMBOL",
                     multiVals = "first")

# GO enrichment with clusterProfiler
ego <- enrichGO(gene = entrez_ids,
                OrgDb = org.Hs.eg.db,
                ont = "BP",
                pAdjustMethod = "BH",
                pvalueCutoff = 0.05,
                qvalueCutoff = 0.1)

# KEGG enrichment
ekegg <- enrichKEGG(gene = entrez_ids,
                    organism = 'hsa',
                    pvalueCutoff = 0.05)

# Save results
write.csv(as.data.frame(res), "results/deseq2_results.csv")
write.csv(as.data.frame(ego), "results/go_enrichment.csv")
write.csv(as.data.frame(ekegg), "results/kegg_enrichment.csv")

# Also demonstrate edgeR for comparison
y <- DGEList(counts = counts, group = metadata$condition)
y <- calcNormFactors(y)
design <- model.matrix(~ metadata$condition)
y <- estimateDisp(y, design)
fit <- glmFit(y, design)
lrt <- glmLRT(fit)
topTags(lrt)

print("Analysis complete!")
