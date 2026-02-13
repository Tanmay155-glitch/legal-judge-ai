# Project Structure

## Overview

This document describes the directory structure and organization of the Legal LLM Supreme Court System.

## Directory Tree

```
legal-judge-ai/
├── .kiro/                              # Kiro specifications
│   └── specs/
│       └── legal-llm-supreme-court-system/
│           ├── .config.kiro            # Spec configuration
│           ├── requirements.md         # Requirements document
│           ├── design.md              # Design document
│           └── tasks.md               # Implementation tasks
│
├── rust-api/                          # Rust API Gateway (Axum)
│   ├── src/
│   │   ├── main.rs                   # Main entry point
│   │   └── models.rs                 # Rust data models
│   ├── Cargo.toml                    # Rust dependencies
│   ├── Cargo.lock                    # Locked dependencies
│   ├── Dockerfile                    # Docker build config
│   └── .env.example                  # Environment template
│
├── python-services/                   # Python ML/NLP Services
│   ├── shared/                       # Shared utilities
│   │   ├── __init__.py
│   │   └── models.py                 # Pydantic data models
│   │
│   ├── embedding_service/            # Legal-BERT embeddings
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app (Task 3)
│   │   └── service.py                # Embedding logic (Task 3)
│   │
│   ├── ingestion_service/            # Case law ingestion
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app (Task 6)
│   │   └── service.py                # Ingestion logic (Task 6)
│   │
│   ├── search_service/               # Semantic search
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app (Task 7)
│   │   └── service.py                # Search logic (Task 7)
│   │
│   ├── prediction_service/           # Outcome prediction
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app (Task 8)
│   │   └── service.py                # Prediction logic (Task 8)
│   │
│   ├── opinion_service/              # Opinion generation
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app (Task 10)
│   │   └── service.py                # RAG pipeline (Task 10)
│   │
│   ├── tests/                        # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest configuration
│   │   ├── test_models.py            # Model tests (Task 2)
│   │   ├── test_embedding.py         # Embedding tests (Task 3)
│   │   ├── test_ingestion.py         # Ingestion tests (Task 6)
│   │   ├── test_search.py            # Search tests (Task 7)
│   │   ├── test_prediction.py        # Prediction tests (Task 8)
│   │   └── test_opinion.py           # Opinion tests (Task 10)
│   │
│   ├── main.py                       # Multi-service launcher
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Docker build config
│   └── .env.example                  # Environment template
│
├── ocr-service/                      # OCR Service (existing)
│   ├── main.py                       # FastAPI OCR service
│   ├── Dockerfile                    # Docker build config
│   └── __pycache__/
│
├── frontend-v2/                      # React Frontend (existing)
│   ├── src/
│   │   ├── App.jsx                   # Main React component
│   │   ├── main.jsx                  # Entry point
│   │   └── index.css                 # Styles
│   ├── package.json                  # Node dependencies
│   ├── vite.config.js                # Vite configuration
│   └── tailwind.config.js            # Tailwind CSS config
│
├── scripts/                          # Utility scripts
│   └── ingest_vectors.py             # Data ingestion script
│
├── qdrant_storage/                   # Qdrant data (created by Docker)
│
├── docker-compose.yml                # Multi-service orchestration
├── requirements.txt                  # Root Python dependencies
├── README.md                         # Project overview
├── SETUP.md                          # Setup instructions
└── PROJECT_STRUCTURE.md              # This file

```

## Component Descriptions

### Rust API Gateway (`rust-api/`)

**Purpose**: API gateway, orchestration, rate limiting, authentication

**Key Files**:
- `src/main.rs`: Axum server setup, route definitions, middleware
- `src/models.rs`: Rust structs matching Python Pydantic models
- `Cargo.toml`: Dependencies (axum, tokio, serde, reqwest, tower)

**Responsibilities**:
- Route incoming requests to appropriate Python services
- Implement rate limiting and authentication
- Handle retries and circuit breaker patterns
- Aggregate health checks and statistics
- Provide consistent error responses

### Python Services (`python-services/`)

**Purpose**: ML/NLP operations, embedding generation, search, prediction, opinion generation

#### Shared Module (`shared/`)
- `models.py`: Pydantic data models used across all services
- Ensures consistent data structures and validation

#### Embedding Service (Port 8001)
- Loads Legal-BERT model
- Generates 768-dimensional embeddings
- Supports batch processing
- GPU acceleration when available

#### Ingestion Service (Port 8002)
- Processes PDF case law documents
- Extracts structured sections (facts, issue, reasoning, etc.)
- Validates documents against schema
- Coordinates embedding generation and vector storage

#### Search Service (Port 8003)
- Performs semantic search using Qdrant
- Ranks results by cosine similarity
- Supports section-specific and filtered searches
- Returns enriched results with metadata

#### Prediction Service (Port 8004)
- Predicts judicial outcomes (Affirmed, Reversed, Remanded)
- Uses similarity-based classification
- Provides probability distributions
- Includes supporting cases and explanations

#### Opinion Service (Port 8005)
- Implements RAG pipeline
- Retrieves relevant precedents
- Generates opinions using LLM (GPT-4/LLaMA-3/Mistral)
- Formats opinions in Supreme Court style
- Adds disclaimers and citations

### OCR Service (`ocr-service/`)

**Purpose**: PDF text extraction using Tesseract

**Existing Service**: Already implemented, used by ingestion service

### Frontend (`frontend-v2/`)

**Purpose**: User interface for uploading briefs and viewing results

**Existing Implementation**: React + Vite + Tailwind CSS

### Infrastructure

#### Qdrant (Port 6333)
- Vector database for storing case law embeddings
- Supports fast similarity search
- Metadata filtering and indexing

#### Redis (Port 6379)
- Caching layer for query embeddings
- Reduces redundant embedding generation
- Improves search performance

## Data Flow

### Ingestion Flow
```
PDF Upload → OCR Service → Ingestion Service → Embedding Service → Qdrant
                                ↓
                          Metadata Storage
```

### Search Flow
```
User Query → Rust API → Search Service → Embedding Service → Qdrant
                                                                ↓
                                                         Search Results
```

### Prediction Flow
```
Facts + Issue → Rust API → Prediction Service → Search Service → Similar Cases
                                                      ↓
                                              Outcome Prediction
```

### Opinion Generation Flow
```
Case Context → Rust API → Opinion Service → Search Service → Precedents
                                                  ↓
                                            LLM (GPT-4) → Formatted Opinion
```

## Development Workflow

1. **Implement Python Service** (e.g., embedding_service)
   - Create `main.py` with FastAPI app
   - Create `service.py` with business logic
   - Write tests in `tests/test_embedding.py`

2. **Update Rust API Gateway**
   - Add client module for new service
   - Add route handler
   - Implement retry and error handling

3. **Test Integration**
   - Run unit tests: `pytest`
   - Run integration tests
   - Test via Rust API gateway

4. **Deploy**
   - Build Docker images: `docker-compose build`
   - Start services: `docker-compose up -d`
   - Verify health: `curl http://localhost:8080/health`

## Configuration

### Environment Variables

**Python Services** (`.env`):
- Service ports (8001-8005)
- Qdrant connection (host, port, collection)
- Embedding model configuration
- LLM API keys (OpenAI)
- Cache settings (Redis)

**Rust API** (`.env`):
- Server port (8080)
- Python service URLs
- Rate limiting configuration
- Circuit breaker settings
- Retry configuration

## Testing Strategy

### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Fast execution (<1s per test)

### Property-Based Tests
- Use Hypothesis for property testing
- Test universal properties across all inputs
- Validate correctness properties from design doc

### Integration Tests
- Test end-to-end workflows
- Use real services (Qdrant, Redis)
- Verify data flow between components

## Next Steps

1. Complete Task 1 (this task) - Project structure ✓
2. Implement Task 2 - Core data models and validation
3. Implement Task 3 - Embedding service
4. Continue with remaining tasks in order

See [tasks.md](.kiro/specs/legal-llm-supreme-court-system/tasks.md) for detailed implementation plan.
