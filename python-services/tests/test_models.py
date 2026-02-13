"""
Unit tests for Pydantic data models.
Tests validation logic, field constraints, and error messages.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from shared.models import (
    CaseLawDocument,
    VectorDocument,
    SearchResult,
    OutcomePrediction,
    GeneratedOpinion,
    ValidationResult,
)
from shared.validators import validate_case_law_document, get_validation_summary


class TestCaseLawDocument:
    """Tests for CaseLawDocument model"""
    
    def test_valid_case_law_document(self, sample_case_law):
        """Test creating a valid case law document"""
        doc = CaseLawDocument(**sample_case_law)
        assert doc.case_name == "Doe v. Smith"
        assert doc.year == 2023
        assert doc.final_judgment == "Affirmed"
    
    def test_case_name_must_contain_v(self):
        """Test that case_name must contain ' v. ' or ' v '"""
        with pytest.raises(ValidationError) as exc_info:
            CaseLawDocument(
                case_name="Invalid Case Name",
                year=2023,
                facts="A" * 50,
                issue="B" * 20,
                reasoning="C" * 100,
                holding="D" * 20,
                final_judgment="Affirmed"
            )
        assert "case_name" in str(exc_info.value)
        assert "v." in str(exc_info.value) or "v " in str(exc_info.value)
    
    def test_year_must_be_2022_or_2023(self):
        """Test that year must be between 2022 and 2023"""
        # Test year too low
        with pytest.raises(ValidationError) as exc_info:
            CaseLawDocument(
                case_name="Doe v. Smith",
                year=2021,
                facts="A" * 50,
                issue="B" * 20,
                reasoning="C" * 100,
                holding="D" * 20,
                final_judgment="Affirmed"
            )
        assert "year" in str(exc_info.value).lower()
        
        # Test year too high
        with pytest.raises(ValidationError) as exc_info:
            CaseLawDocument(
                case_name="Doe v. Smith",
                year=2024,
                facts="A" * 50,
                issue="B" * 20,
                reasoning="C" * 100,
                holding="D" * 20,
                final_judgment="Affirmed"
            )
        assert "year" in str(exc_info.value).lower()
    
    def test_facts_minimum_length(self):
        """Test that facts must be at least 50 characters"""
        with pytest.raises(ValidationError) as exc_info:
            CaseLawDocument(
                case_name="Doe v. Smith",
                year=2023,
                facts="Too short",  # Less than 50 chars
                issue="B" * 20,
                reasoning="C" * 100,
                holding="D" * 20,
                final_judgment="Affirmed"
            )
        assert "facts" in str(exc_info.value).lower()
    
    def test_issue_minimum_length(self):
        """Test that issue must be at least 20 characters"""
        with pytest.raises(ValidationError) as exc_info:
            CaseLawDocument(
                case_name="Doe v. Smith",
                year=2023,
                facts="A" * 50,
                issue="Short",  # Less than 20 chars
                reasoning="C" * 100,
                holding="D" * 20,
                final_judgment="Affirmed"
            )
        assert "issue" in str(exc_info.value).lower()
    
    def test_reasoning_minimum_length(self):
        """Test that reasoning must be at least 100 characters"""
        with pytest.raises(ValidationError) as exc_info:
            CaseLawDocument(
                case_name="Doe v. Smith",
                year=2023,
                facts="A" * 50,
                issue="B" * 20,
                reasoning="Too short",  # Less than 100 chars
                holding="D" * 20,
                final_judgment="Affirmed"
            )
        assert "reasoning" in str(exc_info.value).lower()
    
    def test_holding_minimum_length(self):
        """Test that holding must be at least 20 characters"""
        with pytest.raises(ValidationError) as exc_info:
            CaseLawDocument(
                case_name="Doe v. Smith",
                year=2023,
                facts="A" * 50,
                issue="B" * 20,
                reasoning="C" * 100,
                holding="Short",  # Less than 20 chars
                final_judgment="Affirmed"
            )
        assert "holding" in str(exc_info.value).lower()
    
    def test_final_judgment_must_be_valid(self):
        """Test that final_judgment must be Affirmed, Reversed, or Remanded"""
        with pytest.raises(ValidationError) as exc_info:
            CaseLawDocument(
                case_name="Doe v. Smith",
                year=2023,
                facts="A" * 50,
                issue="B" * 20,
                reasoning="C" * 100,
                holding="D" * 20,
                final_judgment="Invalid"
            )
        assert "final_judgment" in str(exc_info.value).lower()
    
    def test_opinion_type_must_be_valid(self):
        """Test that opinion_type must be one of allowed values"""
        with pytest.raises(ValidationError) as exc_info:
            CaseLawDocument(
                case_name="Doe v. Smith",
                year=2023,
                opinion_type="invalid_type",
                facts="A" * 50,
                issue="B" * 20,
                reasoning="C" * 100,
                holding="D" * 20,
                final_judgment="Affirmed"
            )
        assert "opinion_type" in str(exc_info.value).lower()
    
    def test_document_id_auto_generated(self, sample_case_law):
        """Test that document_id is automatically generated"""
        doc = CaseLawDocument(**sample_case_law)
        assert doc.document_id is not None
        assert len(doc.document_id) > 0
    
    def test_ingestion_timestamp_auto_generated(self, sample_case_law):
        """Test that ingestion_timestamp is automatically generated"""
        doc = CaseLawDocument(**sample_case_law)
        assert doc.ingestion_timestamp is not None
        assert isinstance(doc.ingestion_timestamp, datetime)


class TestVectorDocument:
    """Tests for VectorDocument model"""
    
    def test_valid_vector_document(self, sample_vector):
        """Test creating a valid vector document"""
        doc = VectorDocument(
            document_id="test-id",
            case_name="Doe v. Smith",
            year=2023,
            section_type="facts",
            vector=sample_vector,
            text_content="Sample text",
            metadata={}
        )
        assert doc.section_type == "facts"
        assert len(doc.vector) == 768
    
    def test_vector_must_be_768_dimensional(self):
        """Test that vector must be exactly 768 dimensions"""
        with pytest.raises(ValidationError) as exc_info:
            VectorDocument(
                document_id="test-id",
                case_name="Doe v. Smith",
                year=2023,
                section_type="facts",
                vector=[0.1] * 100,  # Wrong dimension
                text_content="Sample text",
                metadata={}
            )
        assert "768" in str(exc_info.value)
    
    def test_section_type_must_be_valid(self, sample_vector):
        """Test that section_type must be one of allowed values"""
        with pytest.raises(ValidationError) as exc_info:
            VectorDocument(
                document_id="test-id",
                case_name="Doe v. Smith",
                year=2023,
                section_type="invalid_section",
                vector=sample_vector,
                text_content="Sample text",
                metadata={}
            )
        assert "section_type" in str(exc_info.value).lower()


class TestOutcomePrediction:
    """Tests for OutcomePrediction model"""
    
    def test_valid_outcome_prediction(self):
        """Test creating a valid outcome prediction"""
        pred = OutcomePrediction(
            outcome="Affirmed",
            probabilities={
                "Affirmed": 0.7,
                "Reversed": 0.2,
                "Remanded": 0.1
            },
            confidence=0.7,
            supporting_cases=["Case 1", "Case 2"],
            explanation="Based on similar cases..."
        )
        assert pred.outcome == "Affirmed"
        assert pred.confidence == 0.7
    
    def test_probabilities_must_sum_to_one(self):
        """Test that probabilities must sum to 1.0"""
        with pytest.raises(ValidationError) as exc_info:
            OutcomePrediction(
                outcome="Affirmed",
                probabilities={
                    "Affirmed": 0.5,
                    "Reversed": 0.3,
                    "Remanded": 0.1  # Sum = 0.9, not 1.0
                },
                confidence=0.5,
                supporting_cases=[],
                explanation="Test"
            )
        assert "sum" in str(exc_info.value).lower() or "1.0" in str(exc_info.value)
    
    def test_probabilities_must_include_all_outcomes(self):
        """Test that probabilities must include all three outcomes"""
        with pytest.raises(ValidationError) as exc_info:
            OutcomePrediction(
                outcome="Affirmed",
                probabilities={
                    "Affirmed": 0.7,
                    "Reversed": 0.3
                    # Missing "Remanded"
                },
                confidence=0.7,
                supporting_cases=[],
                explanation="Test"
            )
        assert "Remanded" in str(exc_info.value) or "outcomes" in str(exc_info.value).lower()
    
    def test_confidence_must_match_max_probability(self):
        """Test that confidence should match the maximum probability"""
        with pytest.raises(ValidationError) as exc_info:
            OutcomePrediction(
                outcome="Affirmed",
                probabilities={
                    "Affirmed": 0.7,
                    "Reversed": 0.2,
                    "Remanded": 0.1
                },
                confidence=0.5,  # Doesn't match max probability of 0.7
                supporting_cases=[],
                explanation="Test"
            )
        assert "confidence" in str(exc_info.value).lower()


class TestGeneratedOpinion:
    """Tests for GeneratedOpinion model"""
    
    def test_valid_generated_opinion(self):
        """Test creating a valid generated opinion"""
        opinion = GeneratedOpinion(
            full_text="A" * 500,
            sections={
                "procedural_history": "History...",
                "facts": "Facts...",
                "issue": "Issue...",
                "reasoning": "Reasoning...",
                "holding": "Holding...",
                "judgment": "Judgment..."
            },
            cited_precedents=["Case 1", "Case 2"],
            generation_metadata={"model": "gpt-4"}
        )
        assert len(opinion.full_text) >= 500
        assert "procedural_history" in opinion.sections
    
    def test_full_text_minimum_length(self):
        """Test that full_text must be at least 500 characters"""
        with pytest.raises(ValidationError) as exc_info:
            GeneratedOpinion(
                full_text="Too short",
                sections={
                    "procedural_history": "History...",
                    "facts": "Facts...",
                    "issue": "Issue...",
                    "reasoning": "Reasoning...",
                    "holding": "Holding...",
                    "judgment": "Judgment..."
                },
                cited_precedents=[],
                generation_metadata={}
            )
        assert "full_text" in str(exc_info.value).lower()
    
    def test_sections_must_include_all_required(self):
        """Test that sections must include all required sections"""
        with pytest.raises(ValidationError) as exc_info:
            GeneratedOpinion(
                full_text="A" * 500,
                sections={
                    "facts": "Facts...",
                    "issue": "Issue..."
                    # Missing other required sections
                },
                cited_precedents=[],
                generation_metadata={}
            )
        assert "sections" in str(exc_info.value).lower() or "Missing" in str(exc_info.value)
    
    def test_disclaimer_has_default_value(self):
        """Test that disclaimer has a default value"""
        opinion = GeneratedOpinion(
            full_text="A" * 500,
            sections={
                "procedural_history": "History...",
                "facts": "Facts...",
                "issue": "Issue...",
                "reasoning": "Reasoning...",
                "holding": "Holding...",
                "judgment": "Judgment..."
            },
            cited_precedents=[],
            generation_metadata={}
        )
        assert "AI-generated" in opinion.disclaimer
        assert "research" in opinion.disclaimer.lower()


class TestValidators:
    """Tests for validation utility functions"""
    
    def test_validate_case_law_document_valid(self, sample_case_law):
        """Test validation of a valid document"""
        doc = CaseLawDocument(**sample_case_law)
        result = validate_case_law_document(doc)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_case_law_document_invalid_year(self, sample_case_law):
        """Test validation catches invalid year"""
        sample_case_law['year'] = 2021
        doc = CaseLawDocument(**sample_case_law)
        result = validate_case_law_document(doc)
        assert result.is_valid is False
        assert any('year' in error.lower() for error in result.errors)
        assert result.field_validations['year'] is False
    
    def test_validate_case_law_document_short_facts(self, sample_case_law):
        """Test validation catches short facts"""
        sample_case_law['facts'] = "Too short"
        doc = CaseLawDocument(**sample_case_law)
        result = validate_case_law_document(doc)
        assert result.is_valid is False
        assert any('facts' in error.lower() for error in result.errors)
    
    def test_get_validation_summary_valid(self, sample_case_law):
        """Test validation summary for valid document"""
        doc = CaseLawDocument(**sample_case_law)
        result = validate_case_law_document(doc)
        summary = get_validation_summary(result)
        assert "valid" in summary.lower()
        assert "✓" in summary or "valid" in summary.lower()
    
    def test_get_validation_summary_invalid(self, sample_case_law):
        """Test validation summary for invalid document"""
        sample_case_law['year'] = 2021
        doc = CaseLawDocument(**sample_case_law)
        result = validate_case_law_document(doc)
        summary = get_validation_summary(result)
        assert "invalid" in summary.lower() or "✗" in summary
        assert "error" in summary.lower()
