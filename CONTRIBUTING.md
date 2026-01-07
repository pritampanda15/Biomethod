# Contributing to BioMethod

Thank you for your interest in contributing to BioMethod! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (OS, Python version, BioMethod version)
- Sample code or files that demonstrate the issue (if applicable)

### Suggesting Enhancements

We welcome feature requests! Please open an issue with:
- A clear description of the feature
- Use cases and motivation
- Potential implementation approach (optional)

### Adding New Tools to the Database

One of the easiest ways to contribute is adding support for new bioinformatics tools:

1. Edit `src/biomethod/data/tools_database.yaml`
2. Add your tool following this format:

```yaml
tool_name:
  aliases: ["alternative_name", "alt_name"]
  category: "alignment"  # alignment, quantification, variant_calling, etc.
  description: "Brief description of what the tool does"
  citation: |
    @article{author2026tool,
      title={Tool Paper Title},
      author={Author, First and Author, Second},
      journal={Journal Name},
      volume={10},
      pages={123-145},
      year={2026},
      doi={10.1234/example}
    }
  common_parameters:
    -t: "Number of threads"
    -o: "Output file"
```

3. Submit a pull request with your addition

### Code Contributions

#### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/pritam/Biomethod.git
cd Biomethod

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

#### Development Workflow

1. **Fork the repository** and clone your fork
2. **Create a new branch** for your feature: `git checkout -b feature-name`
3. **Make your changes** following the code style guidelines
4. **Run tests**: `pytest`
5. **Run linting**: `black . && ruff check .`
6. **Commit your changes** with clear, descriptive commit messages
7. **Push to your fork** and submit a pull request

#### Code Style

- We use **Black** for code formatting (line length: 100)
- We use **Ruff** for linting
- Follow PEP 8 conventions
- Add type hints for function signatures
- Write docstrings for public functions and classes

#### Testing

- Add tests for new features in the `tests/` directory
- Ensure all tests pass before submitting a PR
- Aim for good test coverage of new code

#### Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Write clear PR descriptions explaining what and why
- Reference any related issues
- Ensure all tests pass and code is properly formatted
- Be responsive to feedback during code review

## Parser Development

If you want to add support for a new language or workflow system:

1. Create a new parser in `src/biomethod/parsers/`
2. Inherit from `BaseParser` in `parsers/base.py`
3. Implement the required methods:
   - `parse()`: Extract tool usage from code
   - `extract_tool_calls()`: Identify tool invocations
   - `extract_parameters()`: Parse command-line parameters
4. Add tests in `tests/test_parsers.py`
5. Update documentation

## Questions?

Feel free to open an issue for any questions about contributing.

## Code of Conduct

Be respectful, inclusive, and professional. We aim to maintain a welcoming community for all contributors.

## License

By contributing to BioMethod, you agree that your contributions will be licensed under the MIT License.
