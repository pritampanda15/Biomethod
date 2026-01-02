"""BioMethod - Automated methods section generator for bioinformatics papers."""

from biomethod.core.analyzer import analyze, Analyzer
from biomethod.core.report import (
    generate_methods,
    reproducibility_check,
    MethodsReport,
    ReproducibilityReport,
)
from biomethod.core.models import ToolInfo, AnalysisResult, EnvironmentInfo

__version__ = "0.1.0"
__all__ = [
    "analyze",
    "Analyzer",
    "generate_methods",
    "reproducibility_check",
    "MethodsReport",
    "ReproducibilityReport",
    "ToolInfo",
    "AnalysisResult",
    "EnvironmentInfo",
]
