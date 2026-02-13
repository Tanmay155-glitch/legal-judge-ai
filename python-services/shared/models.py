"""
Shared Pydantic data models for all Python services.
These models ensure consistent data structures across services.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
import uuid


class CaseLawDocument(BaseModel):
    """Structured representation of a Supreme Court case"""
    
    # Required fields
    case_name: str = Field(..., min_length=5, max_length=500)
    year: int = Field(..., ge=2022, le=2023)
    court: str = Field(default="Supreme Court of the United States")
    opinion_type: str = Field(default="per_curiam")
    
    # Content sections
    facts: str = Field(..., min_length=50)
    issue: str = Field(..., min_length=20)
    reasoning: str = Field(..., min_length=100)
    holding: str = Field(..., min_length=20)
    final_judgment: str = Field(..., pattern="^(Affirmed|Reversed|Remanded)$")
    
    # Optional metadata
    case_number: Optional[str] = None
    petitioner: Optional[str] = None
    respondent: Optional[str] = None
    lower_court: Optional[str] = None
    procedural_history: Optional[str] = None
    
    # System metadata
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    validation_status: str = "pending"
    
    @validator('case_name')
    def validate_case_name(cls, v):
        if ' v. ' not in v and ' v ' not in v:
            raise ValueError('Case name must contain " v. " or " v "')
        return v
    
    @validator('opinion_type')
    def validate_opinion_type(cls, v):
        allowed = ['per_curiam', 'majority', 'concurring', 'dissenting']
        if v not in allowed:
            raise ValueError(f'Opinion type must be one of {allowed}')
        return v


class VectorDocument(BaseModel):
    """Vector representation of case law section"""
    
    document_id: str
    case_name: str
    year: int = Field(..., ge=2022, le=2023)
    section_type: str  # facts, issue, reasoning, holding, judgment
    vector: List[float]  # 768-dimensional embedding
    text_content: str
    metadata: Dict
    
    @validator('section_type')
    def validate_section_type(cls, v):
        allowed = ['facts', 'issue', 'reasoning', 'holding', 'judgment']
        if v not in allowed:
            raise ValueError(f'Section type must be one of {allowed}')
        return v
    
    @validator('vector')
    def validate_vector_dimension(cls, v):
        if len(v) != 768:
            raise ValueError(f'Vector must be 768-dimensional, got {len(v)}')
        return v
    
    class Config:
        json_encoders = {
            'vector': lambda v: v if isinstance(v, list) else v.tolist()
        }


class SearchResult(BaseModel):
    """Result from semantic search"""
    
    case_name: str
    year: int
    court: str
    section_type: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    snippet: str = Field(..., max_length=500)
    full_document: Optional[CaseLawDocument] = None
    metadata: Dict
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 4)
        }


class OutcomePrediction(BaseModel):
    """Predicted judicial outcome"""
    
    outcome: str = Field(..., pattern="^(Affirmed|Reversed|Remanded)$")
    probabilities: Dict[str, float]
    confidence: float = Field(..., ge=0.0, le=1.0)
    supporting_cases: List[str]
    explanation: str
    
    @validator('probabilities')
    def validate_probabilities(cls, v):
        # Check all required outcomes are present
        required_outcomes = {'Affirmed', 'Reversed', 'Remanded'}
        if set(v.keys()) != required_outcomes:
            raise ValueError(f'Probabilities must include all outcomes: {required_outcomes}')
        
        # Check probabilities sum to 1.0
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point error
            raise ValueError(f'Probabilities must sum to 1.0, got {total}')
        
        # Check all probabilities are in valid range
        for outcome, prob in v.items():
            if not (0.0 <= prob <= 1.0):
                raise ValueError(f'Probability for {outcome} must be between 0.0 and 1.0, got {prob}')
        
        return v
    
    @validator('confidence')
    def validate_confidence_matches_max_probability(cls, v, values):
        if 'probabilities' in values:
            max_prob = max(values['probabilities'].values())
            # Confidence should match the maximum probability
            if abs(v - max_prob) > 0.01:
                raise ValueError(f'Confidence ({v}) should match max probability ({max_prob})')
        return v


class GeneratedOpinion(BaseModel):
    """AI-generated judicial opinion"""
    
    full_text: str = Field(..., min_length=500)
    sections: Dict[str, str]
    cited_precedents: List[str]
    generation_metadata: Dict
    disclaimer: str = "This opinion is AI-generated for research and academic purposes only."
    
    @validator('sections')
    def validate_sections(cls, v):
        required = ['procedural_history', 'facts', 'issue', 'reasoning', 'holding', 'judgment']
        missing = [s for s in required if s not in v]
        if missing:
            raise ValueError(f'Missing required sections: {missing}')
        return v


class IngestionResult(BaseModel):
    """Result of document ingestion"""
    
    document_id: str
    case_name: str
    status: str  # success, failed, partial
    sections_extracted: List[str]
    validation_errors: List[str]
    processing_time_seconds: float
    vector_ids: List[str]  # IDs of vectors stored in Qdrant


class ValidationResult(BaseModel):
    """Document validation result"""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_validations: Dict[str, bool]


class SearchRequest(BaseModel):
    """Request for semantic search"""
    
    query: str = Field(..., min_length=1, max_length=1000)  # FIX VULN-007
    top_k: int = Field(default=10, ge=1, le=100)
    section_filter: Optional[str] = None
    year_range: Optional[List[int]] = None
    min_similarity: float = Field(default=0.6, ge=0.0, le=1.0)


class PredictionRequest(BaseModel):
    """Request for outcome prediction"""
    
    facts: str = Field(..., min_length=20, max_length=10000)  # FIX VULN-007
    issue: str = Field(..., min_length=10, max_length=1000)  # FIX VULN-007


class OpinionRequest(BaseModel):
    """Request for opinion generation"""
    
    case_context: Dict
    opinion_type: str = Field(default="per_curiam")
    max_precedents: int = Field(default=5, ge=1, le=10)
