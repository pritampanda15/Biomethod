"""Command-line interface for BioMethod."""

import sys
from pathlib import Path

import click

from biomethod import __version__
from biomethod.core.analyzer import analyze
from biomethod.core.report import generate_methods, reproducibility_check


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="biomethod")
@click.pass_context
def main(ctx: click.Context) -> None:
    """BioMethod - Automated methods section generator for bioinformatics papers.

    Scans bioinformatics code and generates publication-ready methods sections
    with software versions, parameters, and citations.

    \b
    Examples:
        biomethod analyze ./my_analysis/
        biomethod generate ./my_analysis/ -o methods.docx
        biomethod list-tools ./my_analysis/
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    default=None,
    help="Output file path (default: stdout)",
)
@click.option(
    "-f", "--format",
    type=click.Choice(["markdown", "docx", "html", "latex"]),
    default="markdown",
    help="Output format",
)
@click.option(
    "-s", "--style",
    type=click.Choice(["generic", "nature", "bioinformatics", "plos"]),
    default="generic",
    help="Journal style",
)
@click.option(
    "--citations/--no-citations",
    default=True,
    help="Include citation markers",
)
@click.option(
    "--supplementary/--no-supplementary",
    default=True,
    help="Generate supplementary tables",
)
@click.option(
    "-c", "--citations-output",
    type=click.Path(),
    default=None,
    help="Output file for citations (BibTeX)",
)
@click.option(
    "--supplementary-output",
    type=click.Path(),
    default=None,
    help="Output file for supplementary table (Excel/CSV)",
)
@click.option(
    "-r", "--recursive/--no-recursive",
    default=True,
    help="Search directories recursively",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Verbose output",
)
def generate(
    path: str,
    output: str | None,
    format: str,
    style: str,
    citations: bool,
    supplementary: bool,
    citations_output: str | None,
    supplementary_output: str | None,
    recursive: bool,
    verbose: bool,
) -> None:
    """Generate a methods section from bioinformatics code.

    PATH can be a file or directory containing analysis scripts.
    """
    if verbose:
        click.echo(f"Analyzing: {path}")

    # Analyze the path
    analysis = analyze(path, detect_versions=True, recursive=recursive)

    if verbose:
        click.echo(f"Found {len(analysis.tools)} tool usages")
        click.echo(f"Unique tools: {len(analysis.get_unique_tools())}")

    # Generate methods
    methods = generate_methods(
        analysis,
        style=style,
        output_format=format,
        include_citations=citations,
        include_supplementary=supplementary,
    )

    # Output methods text
    if output:
        methods.save(output)
        click.echo(f"Methods saved to: {output}")
    else:
        click.echo(methods.text)

    # Output citations
    if citations_output:
        methods.save_citations(citations_output)
        click.echo(f"Citations saved to: {citations_output}")

    # Output supplementary
    if supplementary_output:
        methods.save_supplementary(supplementary_output)
        click.echo(f"Supplementary table saved to: {supplementary_output}")

    # Show warnings
    if analysis.warnings and verbose:
        click.echo("\nWarnings:")
        for warning in analysis.warnings[:10]:  # Show max 10 warnings
            click.echo(f"  - {warning}")
        if len(analysis.warnings) > 10:
            click.echo(f"  ... and {len(analysis.warnings) - 10} more")


@main.command("analyze")
@click.argument("paths", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "-r", "--recursive/--no-recursive",
    default=True,
    help="Search directories recursively",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed information",
)
def analyze_cmd(
    paths: tuple[str, ...],
    recursive: bool,
    verbose: bool,
) -> None:
    """Analyze files for bioinformatics tools.

    PATHS can be files or directories to analyze.
    """
    all_tools = []
    all_warnings = []

    for path in paths:
        result = analyze(path, detect_versions=True, recursive=recursive)
        all_tools.extend(result.tools)
        all_warnings.extend(result.warnings)

        if verbose:
            click.echo(f"\n{path}:")
            click.echo(f"  Files analyzed: {len(result.source_files)}")
            click.echo(f"  Tools found: {len(result.tools)}")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("ANALYSIS SUMMARY")
    click.echo("=" * 50)

    unique_tools = {}
    for tool in all_tools:
        key = tool.name
        if key not in unique_tools or (tool.version and not unique_tools[key].version):
            unique_tools[key] = tool

    click.echo(f"\nTotal tool usages: {len(all_tools)}")
    click.echo(f"Unique tools: {len(unique_tools)}")

    # Group by category
    categories = {}
    for tool in unique_tools.values():
        cat = tool.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)

    click.echo("\nTools by category:")
    for category, tools in sorted(categories.items()):
        click.echo(f"\n  {category}:")
        for tool in tools:
            version_str = f" (v{tool.version})" if tool.version else ""
            click.echo(f"    - {tool.name}{version_str}")


@main.command("list-tools")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-r", "--recursive/--no-recursive",
    default=True,
    help="Search directories recursively",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
def list_tools(
    path: str,
    recursive: bool,
    format: str,
) -> None:
    """List all bioinformatics tools found in the code.

    PATH can be a file or directory.
    """
    result = analyze(path, detect_versions=True, recursive=recursive)
    unique_tools = result.get_unique_tools()

    if format == "json":
        import json
        tools_data = [
            {
                "name": t.name,
                "version": t.version,
                "category": t.category,
                "source_file": t.source_file,
            }
            for t in unique_tools
        ]
        click.echo(json.dumps(tools_data, indent=2))

    elif format == "csv":
        click.echo("name,version,category,source_file")
        for tool in unique_tools:
            click.echo(f"{tool.name},{tool.version or ''},{tool.category},{tool.source_file}")

    else:  # table
        click.echo(f"{'Tool':<20} {'Version':<15} {'Category':<20} {'Source'}")
        click.echo("-" * 80)
        for tool in sorted(unique_tools, key=lambda t: t.name):
            version = tool.version or "unknown"
            source = Path(tool.source_file).name if tool.source_file else ""
            click.echo(f"{tool.name:<20} {version:<15} {tool.category:<20} {source}")


@main.command("check")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-r", "--recursive/--no-recursive",
    default=True,
    help="Search directories recursively",
)
def check_reproducibility(
    path: str,
    recursive: bool,
) -> None:
    """Check reproducibility of the analysis.

    Generates a reproducibility report following Sandve's 10 rules.
    """
    result = analyze(path, detect_versions=True, recursive=recursive)
    report = reproducibility_check(result)

    click.echo(report.summary())

    # Exit with error if score is too low
    if report.score < 50:
        sys.exit(1)


@main.command("info")
@click.argument("tool_name")
def tool_info(tool_name: str) -> None:
    """Get information about a bioinformatics tool.

    TOOL_NAME is the name of the tool to look up.
    """
    from biomethod.core.analyzer import Analyzer

    analyzer = Analyzer(detect_versions=False)
    info = analyzer.get_tool_info(tool_name)

    if info is None:
        click.echo(f"Tool '{tool_name}' not found in database")
        sys.exit(1)

    click.echo(f"\n{tool_name.upper()}")
    click.echo("=" * len(tool_name))

    if info.get("description"):
        click.echo(f"\nDescription: {info['description']}")

    if info.get("category"):
        click.echo(f"Category: {info['category']}")

    if info.get("aliases"):
        click.echo(f"Aliases: {', '.join(info['aliases'])}")

    if info.get("common_parameters"):
        click.echo("\nCommon Parameters:")
        for param, desc in info["common_parameters"].items():
            click.echo(f"  {param}: {desc}")

    if info.get("citation"):
        click.echo("\nCitation:")
        click.echo(info["citation"])


if __name__ == "__main__":
    main()
