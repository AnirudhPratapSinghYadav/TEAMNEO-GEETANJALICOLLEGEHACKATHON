"""Hybrid detector — combines regex and NER results for higher accuracy."""

from . import ner_detector
from . import regex_detector

# TODO: implement result merging / deduplication logic using regex_detector and ner_detector
