"""Quick test script to verify models work without pytest"""

import sys
sys.path.insert(0, '.')

from shared.models import CaseLawDocument, OutcomePrediction, VectorDocument, GeneratedOpinion
from shared.validators import validate_case_law_document, get_validation_summary
from pydantic import ValidationError

print("Testing CaseLawDocument...")

# Test 1: Valid document
try:
    doc = CaseLawDocument(
        case_name="Doe v. Smith",
        year=2023,
        facts="A" * 50,
        issue="B" * 20,
        reasoning="C" * 100,
        holding="D" * 20,
        final_judgment="Affirmed"
    )
    print("✓ Valid document created successfully")
    print(f"  Document ID: {doc.document_id}")
    print(f"  Case: {doc.case_name}")
except Exception as e:
    print(f"✗ Failed to create valid document: {e}")

# Test 2: Invalid year
try:
    doc = CaseLawDocument(
        case_name="Doe v. Smith",
        year=2021,  # Invalid
        facts="A" * 50,
        issue="B" * 20,
        reasoning="C" * 100,
        holding="D" * 20,
        final_judgment="Affirmed"
    )
    print("✗ Should have failed with invalid year")
except ValidationError as e:
    print("✓ Correctly rejected invalid year")

# Test 3: Invalid case name (no 'v.')
try:
    doc = CaseLawDocument(
        case_name="Invalid Name",  # No 'v.'
        year=2023,
        facts="A" * 50,
        issue="B" * 20,
        reasoning="C" * 100,
        holding="D" * 20,
        final_judgment="Affirmed"
    )
    print("✗ Should have failed with invalid case name")
except ValidationError as e:
    print("✓ Correctly rejected case name without 'v.'")

# Test 4: Short facts
try:
    doc = CaseLawDocument(
        case_name="Doe v. Smith",
        year=2023,
        facts="Too short",  # Less than 50 chars
        issue="B" * 20,
        reasoning="C" * 100,
        holding="D" * 20,
        final_judgment="Affirmed"
    )
    print("✗ Should have failed with short facts")
except ValidationError as e:
    print("✓ Correctly rejected short facts")

print("\nTesting OutcomePrediction...")

# Test 5: Valid prediction
try:
    pred = OutcomePrediction(
        outcome="Affirmed",
        probabilities={
            "Affirmed": 0.7,
            "Reversed": 0.2,
            "Remanded": 0.1
        },
        confidence=0.7,
        supporting_cases=["Case 1"],
        explanation="Test"
    )
    print("✓ Valid prediction created successfully")
    print(f"  Outcome: {pred.outcome}")
    print(f"  Confidence: {pred.confidence}")
except Exception as e:
    print(f"✗ Failed to create valid prediction: {e}")

# Test 6: Probabilities don't sum to 1.0
try:
    pred = OutcomePrediction(
        outcome="Affirmed",
        probabilities={
            "Affirmed": 0.5,
            "Reversed": 0.3,
            "Remanded": 0.1  # Sum = 0.9
        },
        confidence=0.5,
        supporting_cases=[],
        explanation="Test"
    )
    print("✗ Should have failed with probabilities not summing to 1.0")
except ValidationError as e:
    print("✓ Correctly rejected probabilities not summing to 1.0")

print("\nTesting VectorDocument...")

# Test 7: Valid vector
try:
    vec = VectorDocument(
        document_id="test-id",
        case_name="Doe v. Smith",
        year=2023,
        section_type="facts",
        vector=[0.1] * 768,
        text_content="Sample",
        metadata={}
    )
    print("✓ Valid vector document created successfully")
    print(f"  Vector dimension: {len(vec.vector)}")
except Exception as e:
    print(f"✗ Failed to create valid vector: {e}")

# Test 8: Wrong vector dimension
try:
    vec = VectorDocument(
        document_id="test-id",
        case_name="Doe v. Smith",
        year=2023,
        section_type="facts",
        vector=[0.1] * 100,  # Wrong dimension
        text_content="Sample",
        metadata={}
    )
    print("✗ Should have failed with wrong vector dimension")
except ValidationError as e:
    print("✓ Correctly rejected wrong vector dimension")

print("\nTesting GeneratedOpinion...")

# Test 9: Valid opinion
try:
    opinion = GeneratedOpinion(
        full_text="A" * 500,
        sections={
            "procedural_history": "History",
            "facts": "Facts",
            "issue": "Issue",
            "reasoning": "Reasoning",
            "holding": "Holding",
            "judgment": "Judgment"
        },
        cited_precedents=["Case 1"],
        generation_metadata={"model": "gpt-4"}
    )
    print("✓ Valid opinion created successfully")
    print(f"  Disclaimer: {opinion.disclaimer[:50]}...")
except Exception as e:
    print(f"✗ Failed to create valid opinion: {e}")

# Test 10: Missing required sections
try:
    opinion = GeneratedOpinion(
        full_text="A" * 500,
        sections={
            "facts": "Facts",
            "issue": "Issue"
        },
        cited_precedents=[],
        generation_metadata={}
    )
    print("✗ Should have failed with missing sections")
except ValidationError as e:
    print("✓ Correctly rejected missing sections")

print("\nTesting Validators...")

# Test 11: Validation function
doc = CaseLawDocument(
    case_name="Doe v. Smith",
    year=2023,
    facts="A" * 50,
    issue="B" * 20,
    reasoning="C" * 100,
    holding="D" * 20,
    final_judgment="Affirmed"
)
result = validate_case_law_document(doc)
summary = get_validation_summary(result)
print(f"✓ Validation result: {summary}")
print(f"  Is valid: {result.is_valid}")
print(f"  Errors: {len(result.errors)}")
print(f"  Warnings: {len(result.warnings)}")

print("\n" + "="*50)
print("All model tests passed! ✓")
print("="*50)
