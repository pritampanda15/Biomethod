---
name: Tool Addition Request
about: Request support for a new bioinformatics tool
title: '[TOOL] Add support for '
labels: tool-database, enhancement
assignees: ''
---

## Tool Information

**Tool Name:**

**Official Website/Repository:**

**Category:** [e.g., alignment, variant calling, quantification, etc.]

**Description:**
Brief description of what the tool does.

## Citation
Please provide the primary citation for this tool:

```bibtex
@article{,
  title={},
  author={},
  journal={},
  year={},
  doi={}
}
```

## Common Parameters
List common command-line parameters and their descriptions:
- `-t`: Number of threads
- `-o`: Output file
- etc.

## Example Usage
Provide an example of how this tool is typically used:

```bash
tool_name -t 8 -o output.bam input.fastq
```

## Additional Context
Any other relevant information about the tool.

---

**Note:** If you're familiar with YAML, feel free to submit this as a pull request by editing `src/biomethod/data/tools_database.yaml` directly. See [CONTRIBUTING.md](../../CONTRIBUTING.md) for the format.
