"""Shared utilities and models for Python services"""

from .models import (
    CaseLawDocument,
    VectorDocument,
    SearchResult,
    OutcomePrediction,
    GeneratedOpinion,
    IngestionResult,
    ValidationResult,
    SearchRequest,
    PredictionRequest,
    OpinionRequest,
)

from .validators import (
    validate_case_law_document,
    get_validation_summary,
    validate_batch,
)

__all__ = [
    # Models
    "CaseLawDocument",
    "VectorDocument",
    "SearchResult",
    "OutcomePrediction",
    "GeneratedOpinion",
    "IngestionResult",
    "ValidationResult",
    "SearchRequest",
    "PredictionRequest",
    "OpinionRequest",
    # Validators
    "validate_case_law_document",
    "get_validation_summary",
    "validate_batch",
]
