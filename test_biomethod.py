#!/usr/bin/env python3
"""
Test script for BioMethod package.
Demonstrates analyzing the my_analysis folder and generating methods sections.
"""

import sys
sys.path.insert(0, 'src')

# Now we can test components that don't require external dependencies

def test_parsers():
    """Test the parsers on sample files."""
    from pathlib import Path
    from biomethod.parsers import PythonParser, RParser, JupyterParser

    print("=" * 60)
    print("TESTING BIOMETHOD PARSERS")
    print("=" * 60)

    my_analysis = Path("my_analysis")

    # Test Python parser
    print("\n[Python Parser]")
    py_parser = PythonParser()

    for py_file in my_analysis.glob("scripts/*.py"):
        print(f"\nParsing: {py_file.name}")
        tools = py_parser.parse(py_file)
        for tool in tools:
            version = f" (v{tool.version})" if tool.version else ""
            params = f" - params: {tool.parameters}" if tool.parameters else ""
            print(f"  - {tool.name}{version} [{tool.category}]{params}")

    # Test R parser
    print("\n[R Parser]")
    r_parser = RParser()

    for r_file in my_analysis.glob("scripts/*.R"):
        print(f"\nParsing: {r_file.name}")
        tools = r_parser.parse(r_file)
        for tool in tools:
            version = f" (v{tool.version})" if tool.version else ""
            print(f"  - {tool.name}{version} [{tool.category}]")

    # Test Jupyter parser
    print("\n[Jupyter Parser]")
    jupyter_parser = JupyterParser()

    for nb_file in my_analysis.glob("notebooks/*.ipynb"):
        print(f"\nParsing: {nb_file.name}")
        tools = jupyter_parser.parse(nb_file)
        for tool in tools:
            print(f"  - {tool.name} [{tool.category}]")

    print("\n" + "=" * 60)
    return True


def test_environment_parser():
    """Test environment file parsing."""
    from pathlib import Path
    from biomethod.detectors.environment import EnvironmentParser

    print("\n[Environment Parser]")
    print("-" * 40)

    env_parser = EnvironmentParser()
    my_analysis = Path("my_analysis")

    # Parse requirements.txt
    req_file = my_analysis / "requirements.txt"
    if req_file.exists():
        packages = env_parser.parse_requirements_txt(req_file)
        print(f"\nFrom requirements.txt ({len(packages)} packages):")
        for name, version in list(packages.items())[:5]:
            print(f"  - {name}: {version}")
        if len(packages) > 5:
            print(f"  ... and {len(packages) - 5} more")

    # Parse environment.yml
    env_file = my_analysis / "envs" / "environment.yml"
    if env_file.exists():
        packages = env_parser.parse_conda_yaml(env_file)
        print(f"\nFrom environment.yml ({len(packages)} packages):")
        for name, version in list(packages.items())[:5]:
            print(f"  - {name}: {version}")
        if len(packages) > 5:
            print(f"  ... and {len(packages) - 5} more")

    return True


def test_tool_database():
    """Test loading and querying the tool database."""
    from pathlib import Path
    import yaml

    print("\n[Tool Database]")
    print("-" * 40)

    db_path = Path("src/biomethod/data/tools_database.yaml")
    with open(db_path) as f:
        database = yaml.safe_load(f)

    print(f"\nLoaded {len(database)} tools from database")
    print("\nSample tools:")

    for tool_name in ["star", "deseq2", "salmon", "fastqc"]:
        if tool_name in database:
            tool = database[tool_name]
            print(f"\n  {tool_name.upper()}")
            print(f"    Category: {tool.get('category', 'unknown')}")
            print(f"    Aliases: {tool.get('aliases', [])}")
            print(f"    Has citation: {'Yes' if tool.get('citation') else 'No'}")

    return True


def test_prose_generation():
    """Test prose generation with sample data."""
    from biomethod.core.models import AnalysisResult, ToolInfo, EnvironmentInfo
    from biomethod.generators.prose import ProseGenerator

    print("\n[Prose Generator]")
    print("-" * 40)

    # Create sample analysis result
    tools = [
        ToolInfo(name="fastp", version="0.23.2", category="preprocessing",
                 source_file="preprocessing.py", line_number=10),
        ToolInfo(name="fastqc", version="0.11.9", category="quality-control",
                 source_file="preprocessing.py", line_number=20),
        ToolInfo(name="star", version="2.7.10a", category="alignment",
                 source_file="alignment.py", line_number=15),
        ToolInfo(name="featurecounts", version="2.0.3", category="quantification",
                 source_file="quantification.py", line_number=8),
        ToolInfo(name="deseq2", version="1.38.0", category="differential-expression",
                 source_file="de_analysis.R", line_number=5),
        ToolInfo(name="clusterprofiler", version="4.6.0", category="enrichment",
                 source_file="enrichment.R", line_number=3),
    ]

    analysis = AnalysisResult(
        tools=tools,
        source_files=["preprocessing.py", "alignment.py", "de_analysis.R"],
        workflow_type="script",
        environment=EnvironmentInfo(python_version="3.11.0")
    )

    # Generate with different styles
    for style in ["generic", "nature"]:
        print(f"\n--- {style.upper()} STYLE ---\n")
        generator = ProseGenerator(style=style)
        text = generator.generate(analysis, include_versions=True, include_citations=False)
        print(text[:500] + "..." if len(text) > 500 else text)

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BIOMETHOD TEST SUITE")
    print("=" * 60)

    tests = [
        ("Tool Database", test_tool_database),
        ("Parsers", test_parsers),
        ("Environment Parser", test_environment_parser),
        ("Prose Generation", test_prose_generation),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "PASS" if success else "FAIL"))
        except Exception as e:
            print(f"\nError in {name}: {e}")
            results.append((name, "ERROR"))

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for name, status in results:
        print(f"  {name}: {status}")

    print("\n" + "=" * 60)
    print("To use BioMethod on your analysis:")
    print("=" * 60)
    print("""
# Install (in a virtual environment)
pip install -e .

# Then run:
biomethod generate my_analysis/ -o methods.md
biomethod list-tools my_analysis/
biomethod check my_analysis/
""")


if __name__ == "__main__":
    main()
