"""NER-based detector using Microsoft Presidio and spaCy."""

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
except ImportError:  # presidio / spaCy are optional heavy dependencies
    AnalyzerEngine = None  # type: ignore[assignment,misc]
    AnonymizerEngine = None  # type: ignore[assignment,misc]

# TODO: implement NER detection logic using Presidio AnalyzerEngine
