"""
Custom validators and validation utilities for case law documents.
"""

from typing import Dict, List, Tuple
from .models import CaseLawDocument, ValidationResult


def validate_case_law_document(doc: CaseLawDocument) -> ValidationResult:
    """
    Comprehensive validation of a CaseLawDocument.
    
    Returns ValidationResult with detailed error and warning messages.
    """
    errors = []
    warnings = []
    field_validations = {}
    
    # Validate case_name
    try:
        if ' v. ' not in doc.case_name and ' v ' not in doc.case_name:
            errors.append("case_name: Must contain ' v. ' or ' v '")
            field_validations['case_name'] = False
        else:
            field_validations['case_name'] = True
    except Exception as e:
        errors.append(f"case_name: {str(e)}")
        field_validations['case_name'] = False
    
    # Validate year
    try:
        if not (2022 <= doc.year <= 2023):
            errors.append(f"year: Must be between 2022 and 2023, got {doc.year}")
            field_validations['year'] = False
        else:
            field_validations['year'] = True
    except Exception as e:
        errors.append(f"year: {str(e)}")
        field_validations['year'] = False
    
    # Validate court
    try:
        if doc.court != "Supreme Court of the United States":
            warnings.append(f"court: Expected 'Supreme Court of the United States', got '{doc.court}'")
        field_validations['court'] = True
    except Exception as e:
        errors.append(f"court: {str(e)}")
        field_validations['court'] = False
    
    # Validate opinion_type
    try:
        allowed_types = ['per_curiam', 'majority', 'concurring', 'dissenting']
        if doc.opinion_type not in allowed_types:
            errors.append(f"opinion_type: Must be one of {allowed_types}, got '{doc.opinion_type}'")
            field_validations['opinion_type'] = False
        else:
            field_validations['opinion_type'] = True
    except Exception as e:
        errors.append(f"opinion_type: {str(e)}")
        field_validations['opinion_type'] = False
    
    # Validate facts (minimum 50 characters)
    try:
        if len(doc.facts) < 50:
            errors.append(f"facts: Must be at least 50 characters, got {len(doc.facts)}")
            field_validations['facts'] = False
        else:
            field_validations['facts'] = True
            if len(doc.facts) < 100:
                warnings.append(f"facts: Very short ({len(doc.facts)} chars), consider adding more detail")
    except Exception as e:
        errors.append(f"facts: {str(e)}")
        field_validations['facts'] = False
    
    # Validate issue (minimum 20 characters)
    try:
        if len(doc.issue) < 20:
            errors.append(f"issue: Must be at least 20 characters, got {len(doc.issue)}")
            field_validations['issue'] = False
        else:
            field_validations['issue'] = True
    except Exception as e:
        errors.append(f"issue: {str(e)}")
        field_validations['issue'] = False
    
    # Validate reasoning (minimum 100 characters)
    try:
        if len(doc.reasoning) < 100:
            errors.append(f"reasoning: Must be at least 100 characters, got {len(doc.reasoning)}")
            field_validations['reasoning'] = False
        else:
            field_validations['reasoning'] = True
            if len(doc.reasoning) < 200:
                warnings.append(f"reasoning: Relatively short ({len(doc.reasoning)} chars), consider adding more analysis")
    except Exception as e:
        errors.append(f"reasoning: {str(e)}")
        field_validations['reasoning'] = False
    
    # Validate holding (minimum 20 characters)
    try:
        if len(doc.holding) < 20:
            errors.append(f"holding: Must be at least 20 characters, got {len(doc.holding)}")
            field_validations['holding'] = False
        else:
            field_validations['holding'] = True
    except Exception as e:
        errors.append(f"holding: {str(e)}")
        field_validations['holding'] = False
    
    # Validate final_judgment
    try:
        allowed_judgments = ['Affirmed', 'Reversed', 'Remanded']
        if doc.final_judgment not in allowed_judgments:
            errors.append(f"final_judgment: Must be one of {allowed_judgments}, got '{doc.final_judgment}'")
            field_validations['final_judgment'] = False
        else:
            field_validations['final_judgment'] = True
    except Exception as e:
        errors.append(f"final_judgment: {str(e)}")
        field_validations['final_judgment'] = False
    
    is_valid = len(errors) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        field_validations=field_validations
    )


def get_validation_summary(result: ValidationResult) -> str:
    """
    Generate a human-readable validation summary.
    """
    if result.is_valid:
        summary = "✓ Document is valid"
        if result.warnings:
            summary += f" ({len(result.warnings)} warnings)"
    else:
        summary = f"✗ Document is invalid ({len(result.errors)} errors"
        if result.warnings:
            summary += f", {len(result.warnings)} warnings"
        summary += ")"
    
    return summary


def validate_batch(documents: List[CaseLawDocument]) -> Tuple[List[CaseLawDocument], List[Tuple[int, ValidationResult]]]:
    """
    Validate a batch of documents.
    
    Returns:
        - List of valid documents
        - List of (index, ValidationResult) for invalid documents
    """
    valid_docs = []
    invalid_docs = []
    
    for idx, doc in enumerate(documents):
        result = validate_case_law_document(doc)
        if result.is_valid:
            valid_docs.append(doc)
        else:
            invalid_docs.append((idx, result))
    
    return valid_docs, invalid_docs
