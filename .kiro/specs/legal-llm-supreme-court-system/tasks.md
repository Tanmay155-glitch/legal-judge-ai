# Implementation Plan: Legal LLM Supreme Court System

## Overview

This implementation plan breaks down the Legal LLM Supreme Court System into discrete coding tasks following a hybrid Rust+Python architecture. The Rust API (Axum) serves as the orchestration layer and API gateway, while Python services handle ML/NLP operations including Legal-BERT embeddings, LLM integration, and the RAG pipeline.

The implementation follows an incremental approach:
1. Set up project structure and core infrastructure
2. Implement data ingestion and embedding pipeline (Python)
3. Implement semantic search engine (Python)
4. Implement outcome prediction service (Python)
5. Implement opinion generation service with RAG (Python)
6. Implement Rust API gateway for orchestration
7. Wire all services together with integration tests

## Tasks

- [x] 1. Set up project structure and development environment
  - Create directory structure for hybrid Rust+Python architecture
  - Set up Python virtual environment and install dependencies (sentence-transformers, qdrant-client, fastapi, pydantic, hypothesis)
  - Set up Rust workspace with Axum dependencies (axum, tokio, serde, reqwest)
  - Configure docker-compose.yml with Qdrant service
  - Create shared data models and schemas
  - _Requirements: 11.2, 11.3, 11.5_

- [x] 2. Implement core data models and validation (Python)
  - [x] 2.1 Create Pydantic models for CaseLawDocument with all required fields
    - Implement CaseLawDocument with fields: case_name, year, court, opinion_type, facts, issue, reasoning, holding, final_judgment
    - Add field validators for case_name (must contain " v. "), year (2022-2023), opinion_type (allowed values)
    - Add minimum length validators for text sections (facts: 50 chars, reasoning: 100 chars)
    - _Requirements: 1.2, 9.1, 9.2, 9.4_
  
  - [ ]* 2.2 Write property test for CaseLawDocument validation
    - **Property 1: Case law parsing produces valid schema**
    - **Property 2: Year validation enforces range constraints**
    - **Property 3: Field validation enforces minimum length requirements**
    - **Property 4: Validation errors provide field-specific messages**
    - **Validates: Requirements 1.2, 9.1, 9.2, 9.4, 9.5**
  
  - [x] 2.3 Create Pydantic models for VectorDocument, SearchResult, OutcomePrediction, GeneratedOpinion
    - Implement VectorDocument with document_id, case_name, year, section_type, vector, text_content, metadata
    - Implement SearchResult with similarity_score validation (0.0 to 1.0)
    - Implement OutcomePrediction with probability validation (sum to 1.0)
    - Implement GeneratedOpinion with required sections validation
    - _Requirements: 4.4, 5.3, 5.4, 6.3_
  
  - [ ]* 2.4 Write property test for OutcomePrediction probability validation
    - **Property 18: Probability distributions sum to 1.0**
    - **Property 19: All outcomes have probability scores**
    - **Validates: Requirements 5.3, 5.4**

- [x] 3. Implement embedding service (Python)
  - [x] 3.1 Create EmbeddingService class with Legal-BERT initialization
    - Initialize sentence-transformers with "nlpaueb/legal-bert-base-uncased" model
    - Implement encode_text() method for single text encoding
    - Implement encode_batch() method with configurable batch size (default: 32)
    - Implement get_embedding_dimension() returning 768
    - Add GPU acceleration support when available
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ]* 3.2 Write property test for embedding dimensionality consistency
    - **Property 7: Embedding generation produces consistent dimensionality**
    - **Property 8: All document sections receive embeddings**
    - **Validates: Requirements 2.1, 2.3**
  
  - [x]* 3.3 Write unit tests for embedding service edge cases
    - Test empty string handling
    - Test very long text (>512 tokens) truncation
    - Test batch processing with various batch sizes
    - Test error handling when model fails to load
    - _Requirements: 2.4_

- [x] 4. Implement vector index service with Qdrant (Python)
  - [x] 4.1 Create VectorIndexService class with Qdrant client
    - Initialize Qdrant client with configurable URL (default: http://localhost:6333)
    - Implement create_collection() with collection schema (vector_size: 768, distance: Cosine)
    - Implement index_document() to store vectors with section-specific metadata
    - Implement search_similar() with top_k and optional metadata filters
    - Implement delete_document() for removing documents
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ]* 4.2 Write property test for vector storage round-trip
    - **Property 10: Vector storage round-trip preserves embeddings**
    - **Property 11: Metadata is preserved with vectors**
    - **Validates: Requirements 3.1, 3.2**
  
  - [ ]* 4.3 Write property test for duplicate prevention
    - **Property 12: Duplicate documents are prevented**
    - **Validates: Requirements 3.5**

- [x] 5. Checkpoint - Ensure embedding and vector storage tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement ingestion service (Python)
  - [x] 6.1 Create IngestionService class with OCR integration
    - Implement ingest_pdf() to call OCR service and extract text
    - Implement parse_case_law() to extract sections using regex patterns and NLP
    - Add section markers detection: "FACTS:", "ISSUE:", "REASONING:", "HOLDING:", "JUDGMENT:"
    - Implement validate_document() using Pydantic validators
    - Implement batch_ingest() for processing multiple PDFs with configurable batch size
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 11.1_
  
  - [x] 6.2 Implement ingestion pipeline orchestration
    - Coordinate: PDF → OCR → Parsing → Validation → Embedding → Vector Storage
    - Add error handling for each pipeline stage
    - Implement logging for validation errors and processing status
    - Add retry logic for transient failures
    - _Requirements: 1.4, 1.6, 9.6, 12.1_
  
  - [ ]* 6.3 Write property test for data persistence round-trip
    - **Property 5: Data persistence round-trip preserves content**
    - **Property 6: Validation errors are logged**
    - **Validates: Requirements 1.6, 9.6**
  
  - [ ]* 6.4 Write unit tests for ingestion edge cases
    - Test PDF with missing sections
    - Test invalid year values
    - Test case name without " v. "
    - Test text sections below minimum length
    - Test OCR service failure handling
    - _Requirements: 1.3, 9.1, 9.2, 9.4, 9.5_

- [x] 7. Implement semantic search engine (Python)
  - [x] 7.1 Create SemanticSearchEngine class
    - Implement search() with query embedding generation and vector search
    - Implement search_by_facts() filtering to facts sections only
    - Implement search_by_reasoning() filtering to reasoning sections only
    - Implement get_similar_cases() for case-to-case similarity
    - Add result ranking by cosine similarity with recency boost for 2023 cases
    - Implement minimum similarity threshold (default: 0.6)
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6_
  
  - [x] 7.2 Implement search result formatting and metadata enrichment
    - Fetch full CaseLawDocument metadata for each result
    - Generate text snippets from matched sections
    - Format results with similarity scores and metadata
    - Add search time tracking
    - _Requirements: 4.4_
  
  - [ ]* 7.3 Write property tests for search functionality
    - **Property 13: Query embeddings use consistent model**
    - **Property 14: Search results are ranked by similarity**
    - **Property 15: Search results include required metadata**
    - **Property 16: Result limit parameter is respected**
    - **Validates: Requirements 4.1, 4.3, 4.4, 4.5**
  
  - [ ]* 7.4 Write unit tests for search edge cases
    - Test empty query handling
    - Test no results above threshold
    - Test section filtering
    - Test year range filtering
    - _Requirements: 4.6_

- [x] 8. Implement outcome predictor service (Python)
  - [x] 8.1 Create OutcomePredictor class with similarity-based classification
    - Implement predict_outcome() using semantic search to retrieve similar cases
    - Extract outcomes from top-k similar cases (k=20)
    - Calculate weighted vote based on similarity scores
    - Normalize to probability distribution (Affirmed, Reversed, Remanded)
    - Determine predicted outcome as max probability
    - _Requirements: 5.1, 5.2, 5.6_
  
  - [x] 8.2 Implement prediction explanation and confidence scoring
    - Implement explain_prediction() with supporting cases
    - Implement get_confidence_score() based on max probability
    - Add low confidence flagging when max probability < threshold (default: 0.6)
    - Format response with probabilities, supporting cases, and explanation
    - _Requirements: 5.3, 5.4, 5.5_
  
  - [ ]* 8.3 Write property tests for outcome prediction
    - **Property 17: Predictions return valid outcome labels**
    - **Property 18: Probability distributions sum to 1.0**
    - **Property 19: All outcomes have probability scores**
    - **Property 20: Low confidence predictions are flagged**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.5**

- [x] 9. Checkpoint - Ensure search and prediction services work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement opinion generator with RAG pipeline (Python)
  - [x] 10.1 Create OpinionGenerator class with precedent retrieval
    - Implement generate_opinion() with case context input
    - Implement precedent retrieval using SemanticSearchEngine (top-k=5)
    - Implement rank_by_relevance() for retrieved precedents
    - Add section-specific retrieval (facts, reasoning, holding)
    - _Requirements: 6.1, 6.2_
  
  - [x] 10.2 Implement LLM prompt engineering and generation
    - Create build_opinion_prompt() with case context and precedents
    - Format precedents with case name, year, facts, reasoning, holding
    - Configure LLM parameters (model: gpt-4, temperature: 0.3, max_tokens: 2048)
    - Implement LLM API call with error handling and retries
    - Add support for alternative models (LLaMA-3, Mistral)
    - _Requirements: 6.7, 12.1_
  
  - [x] 10.3 Implement opinion structure formatting and validation
    - Create opinion template with Supreme Court format sections
    - Implement generate_section() for each opinion section
    - Implement format_citations() for Bluebook-style citations
    - Add post-processing: citation validation, structure validation, tone analysis
    - Add disclaimer: "AI-Generated for Research Purposes Only"
    - _Requirements: 6.3, 6.4, 6.5, 6.6, 10.1_
  
  - [ ]* 10.4 Write property tests for opinion generation
    - **Property 21: Opinion generation retrieves precedents**
    - **Property 22: Generated opinions contain required sections**
    - **Property 23: Per Curiam opinions lack individual attribution**
    - **Property 24: Retrieved precedents are cited in reasoning**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.6**
  
  - [ ]* 10.5 Write unit tests for opinion generation edge cases
    - Test with no retrieved precedents
    - Test with LLM API failure
    - Test citation formatting
    - Test disclaimer inclusion
    - _Requirements: 10.1, 12.1_

- [x] 11. Create Python FastAPI service endpoints
  - [x] 11.1 Set up FastAPI application with CORS and middleware
    - Initialize FastAPI app with title, version, description
    - Add CORS middleware for frontend integration
    - Add request logging middleware
    - Add error handling middleware
    - _Requirements: 11.3_
  
  - [x] 11.2 Implement ingestion endpoints
    - POST /ingest/pdf - single PDF upload with multipart/form-data
    - POST /ingest/batch - batch processing with directory path
    - Add request validation and error responses
    - Return IngestionResult with document_id, status, sections_extracted
    - _Requirements: 7.1, 7.5_
  
  - [x] 11.3 Implement search endpoint
    - POST /search - semantic search with query, top_k, filters
    - Add query parameter validation
    - Return SearchResults with results array, total_results, search_time_ms
    - _Requirements: 7.2, 7.5, 7.6_
  
  - [x] 11.4 Implement prediction endpoint
    - POST /predict/outcome - outcome prediction with facts and issue
    - Add input validation for facts and issue
    - Return OutcomePrediction with outcome, probabilities, confidence, supporting_cases
    - Add disclaimer to response
    - _Requirements: 7.3, 7.5, 7.6, 10.2_
  
  - [x] 11.5 Implement opinion generation endpoint
    - POST /generate/opinion - opinion generation with case context
    - Add case context validation
    - Return GeneratedOpinion with full_text, sections, cited_precedents
    - Add disclaimer to response
    - _Requirements: 7.4, 7.5, 7.6, 10.1_
  
  - [x] 11.6 Implement health and stats endpoints
    - GET /health - service health check
    - GET /stats - system statistics (total_cases_indexed, searches_performed, etc.)
    - _Requirements: 8.3_

- [x] 12. Implement Rust API gateway with Axum
  - [ ] 12.1 Set up Axum application structure
    - Create main.rs with Axum router setup
    - Configure server to listen on port 8080
    - Add CORS layer for frontend integration
    - Add request tracing and logging middleware
    - _Requirements: 11.3_
  
  - [ ] 12.2 Create Rust data models matching Python schemas
    - Define structs for CaseLawDocument, SearchRequest, SearchResult
    - Define structs for OutcomePrediction, OpinionRequest, GeneratedOpinion
    - Add serde serialization/deserialization
    - Add validation using validator crate
    - _Requirements: 7.6_
  
  - [ ] 12.3 Implement service client modules for Python services
    - Create OcrClient for calling OCR service
    - Create IngestionClient for calling ingestion service
    - Create SearchClient for calling search service
    - Create PredictionClient for calling prediction service
    - Create OpinionClient for calling opinion generation service
    - Add retry logic with exponential backoff (max 3 retries)
    - Add circuit breaker pattern for each service
    - _Requirements: 12.1, 12.6_
  
  - [ ] 12.4 Implement API gateway route handlers
    - POST /api/v1/ingest/pdf - proxy to ingestion service
    - POST /api/v1/ingest/batch - proxy to ingestion service
    - POST /api/v1/search - proxy to search service
    - POST /api/v1/predict/outcome - proxy to prediction service
    - POST /api/v1/generate/opinion - proxy to opinion service
    - GET /api/v1/health - aggregate health from all services
    - GET /api/v1/stats - aggregate stats from all services
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [ ] 12.5 Implement request validation and error handling
    - Add input validation for all endpoints
    - Return HTTP 400 for validation errors with detailed messages
    - Return HTTP 500 for internal errors with generic message
    - Return HTTP 429 for rate limit exceeded
    - Return HTTP 503 for service unavailable
    - Log all errors with full stack traces
    - _Requirements: 7.5, 12.2, 12.3, 12.4, 12.5_
  
  - [ ] 12.6 Implement rate limiting
    - Add rate limiting middleware (100 requests per minute per API key)
    - Return HTTP 429 with retry_after_seconds when limit exceeded
    - Add rate limit headers to responses
    - _Requirements: 7.7_

- [x]* 13. Write property tests for API endpoints
  - [x]* 13.1 Write property tests for API validation and error handling
    - **Property 25: Invalid API inputs return HTTP 400**
    - **Property 26: API responses follow consistent format**
    - **Property 27: Rate limiting prevents excessive requests**
    - **Validates: Requirements 7.5, 7.6, 7.7, 12.3**
  
  - [x]* 13.2 Write property tests for service integration
    - **Property 28: PDF uploads use OCR service**
    - **Property 29: Vectors are stored in Qdrant**
    - **Property 30: API endpoints are compatible with frontend**
    - **Validates: Requirements 11.1, 11.2, 11.4**
  
  - [x]* 13.3 Write property tests for error handling and resilience
    - **Property 31: Failed external calls are retried**
    - **Property 32: Exhausted retries return user-friendly errors**
    - **Property 33: Internal errors return HTTP 500 and log stack traces**
    - **Property 34: Vector index unavailability returns descriptive error**
    - **Property 35: Circuit breaker opens after repeated failures**
    - **Validates: Requirements 12.1, 12.2, 12.4, 12.5, 12.6**

- [ ] 14. Checkpoint - Ensure API gateway and service integration work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Implement ethical safeguards and compliance features
  - [x] 15.1 Add disclaimers to all AI-generated content
    - Add research-only disclaimer to generated opinions
    - Add not-legal-advice disclaimer to predictions
    - Add AI-generated label to all outputs
    - _Requirements: 10.1, 10.2, 10.4_
  
  - [x] 15.2 Implement audit logging
    - Log all user queries with timestamp and user identifier
    - Log all generated outputs (opinions, predictions)
    - Store audit logs in structured format (JSON)
    - Add audit log retention policy
    - _Requirements: 10.3_
  
  - [x] 15.3 Add terms of use display
    - Create terms of use endpoint
    - Add terms of use to API documentation
    - Require terms acceptance for first-time users
    - _Requirements: 10.5_
  
  - [ ]* 15.4 Write property tests for ethical safeguards
    - **Property 36: Generated opinions include research disclaimer**
    - **Property 37: Predictions include legal advice disclaimer**
    - **Property 38: User queries and outputs are logged for audit**
    - **Property 39: AI-generated content is labeled**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4**

- [x] 16. Implement performance optimizations
  - [x] 16.1 Add caching layer
    - Implement Redis cache for query embeddings (TTL: 1 hour)
    - Implement cache for frequent search queries (TTL: 30 minutes)
    - Implement in-memory LRU cache for case law metadata
    - Add cache hit/miss metrics
    - _Requirements: 8.5_
  
  - [x] 16.2 Optimize batch processing
    - Configure embedding batch size for optimal GPU utilization
    - Implement parallel processing for batch ingestion
    - Add progress tracking for long-running batch operations
    - _Requirements: 2.5, 8.4_
  
  - [x] 16.3 Add performance monitoring
    - Track search response times (target: <1s for 95% of queries)
    - Track embedding generation times
    - Track opinion generation times
    - Add performance metrics endpoint
    - _Requirements: 3.4, 8.1, 8.2_

- [x]* 17. Write integration tests for end-to-end workflows
  - [x]* 17.1 Write end-to-end ingestion test
    - Test: PDF upload → OCR → Parsing → Embedding → Indexing → Search
    - Verify document is searchable after ingestion
    - _Requirements: 1.1, 1.2, 2.1, 3.1, 4.1_
  
  - [x]* 17.2 Write end-to-end search test
    - Test: Query → Embedding → Vector Search → Result Formatting
    - Verify results are ranked by similarity
    - Verify metadata is included
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x]* 17.3 Write end-to-end prediction test
    - Test: Input → Search → Feature Extraction → Prediction
    - Verify probabilities sum to 1.0
    - Verify supporting cases are included
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [x]* 17.4 Write end-to-end opinion generation test
    - Test: Input → Search → RAG → LLM → Formatting
    - Verify all required sections are present
    - Verify precedents are cited
    - Verify disclaimer is included
    - _Requirements: 6.1, 6.2, 6.3, 6.6, 10.1_

- [x] 18. Create deployment configuration
  - [x] 18.1 Update docker-compose.yml with all services
    - Add Qdrant service configuration
    - Add Python FastAPI service configuration
    - Add Rust API gateway configuration
    - Add environment variables for service URLs
    - Add volume mounts for persistent storage
    - _Requirements: 11.2, 11.3_
  
  - [x] 18.2 Create Dockerfiles for each service
    - Create Dockerfile for Python FastAPI service
    - Create Dockerfile for Rust API gateway
    - Optimize image sizes with multi-stage builds
    - Add health check commands
    - _Requirements: 11.3_
  
  - [x] 18.3 Add deployment documentation
    - Document environment variables
    - Document service dependencies
    - Document startup order
    - Add troubleshooting guide
    - _Requirements: 11.3_

- [x] 19. Final checkpoint - Run full test suite and verify all requirements
  - Run all unit tests, property tests, and integration tests
  - Verify all 39 correctness properties pass
  - Verify all API endpoints work correctly
  - Verify performance benchmarks are met
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based and integration tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and error conditions
- The hybrid architecture uses Rust for orchestration/gateway and Python for ML/NLP operations
- All Python services expose FastAPI endpoints that the Rust gateway proxies
- The Rust gateway handles authentication, rate limiting, and service orchestration
- Python services handle embedding generation, vector operations, and LLM integration
