# Code Quality & Security Fixes - Implementation Tasks

## Task Organization

Tasks are organized by priority (P0-P3) and should be executed in order within each phase.

**Status Legend**:
- `[ ]` Not started
- `[~]` Queued
- `[-]` In progress
- `[x]` Completed

---

## Phase 1: P0 Critical Security Fixes

### Task 1: Complete Incomplete Security Function
- [ ] 1.1 Fix the `sanitize_query_filter()` function in `python-services/shared/security.py`
  - [ ] 1.1.1 Complete the function implementation with all dangerous patterns
  - [ ] 1.1.2 Add comprehensive unit tests for injection patterns
  - [ ] 1.1.3 Test with MongoDB operators, SQL injection, and edge cases
  - [ ] 1.1.4 Verify function returns sanitized strings correctly

### Task 2: Fix Weak JWT Secret Key
- [ ] 2.1 Update JWT secret configuration in `python-services/shared/config.py`
  - [ ] 2.1.1 Add `generate_secure_secret()` function using `secrets` module
  - [ ] 2.1.2 Update `SecuritySettings` to use secure default
  - [ ] 2.1.3 Add validator to check production secret strength
  - [ ] 2.1.4 Update `.env.example` with secret generation instructions
  - [ ] 2.1.5 Add unit tests for production validation
  - [ ] 2.1.6 Test that weak secrets fail in production mode

### Task 3: Add Authentication to Critical Endpoints
- [ ] 3.1 Add authentication to orchestrator API
  - [ ] 3.1.1 Import `verify_token` from `shared.security`
  - [ ] 3.1.2 Add `Depends(verify_token)` to `/api/analyze-brief` endpoint
  - [ ] 3.1.3 Add logging for authenticated requests
  - [ ] 3.1.4 Test endpoint rejects requests without tokens
  - [ ] 3.1.5 Test endpoint accepts valid tokens
- [ ] 3.2 Add authentication to ingestion service
  - [ ] 3.2.1 Add `Depends(require_role("admin"))` to ingestion endpoints
  - [ ] 3.2.2 Test role-based access control
- [ ] 3.3 Add authentication to opinion service
  - [ ] 3.3.1 Add `Depends(verify_token)` to `/generate/opinion` endpoint
  - [ ] 3.3.2 Test authentication works correctly

### Task 4: Fix CORS Wildcard Configuration
- [ ] 4.1 Update orchestrator API CORS configuration
  - [ ] 4.1.1 Remove wildcard CORS middleware from `orchestrator_api.py`
  - [ ] 4.1.2 Import and use `setup_cors()` from `shared.cors_config`
  - [ ] 4.1.3 Test requests from allowed origins succeed
  - [ ] 4.1.4 Test requests from disallowed origins fail
  - [ ] 4.1.5 Test preflight OPTIONS requests work

---

## Phase 2: P1 Critical Code Errors

### Task 5: Improve OCR Error Handling
- [ ] 5.1 Create specific exception classes in `ocr-service/main.py`
  - [ ] 5.1.1 Create `OCRException` base class
  - [ ] 5.1.2 Create `TesseractException` class
  - [ ] 5.1.3 Create `PopplerException` class
  - [ ] 5.1.4 Create `InvalidFileException` class
- [ ] 5.2 Update error handling in OCR endpoint
  - [ ] 5.2.1 Add file type validation with `InvalidFileException`
  - [ ] 5.2.2 Wrap Poppler calls with `PopplerException`
  - [ ] 5.2.3 Wrap Tesseract calls with `TesseractException`
  - [ ] 5.2.4 Return appropriate HTTP status codes and error messages
  - [ ] 5.2.5 Add error logging with context
- [ ] 5.3 Add tests for error handling
  - [ ] 5.3.1 Test with invalid file types
  - [ ] 5.3.2 Test with corrupted PDFs
  - [ ] 5.3.3 Verify error messages are helpful

### Task 6: Implement Rust API Service Integration
- [ ] 6.1 Add HTTP client dependencies to Rust API
  - [ ] 6.1.1 Add `reqwest` and `tokio` to `Cargo.toml`
  - [ ] 6.1.2 Create HTTP client with connection pooling
  - [ ] 6.1.3 Add service URL configuration from environment
- [ ] 6.2 Implement service call functions
  - [ ] 6.2.1 Implement `call_ocr_service()` function
  - [ ] 6.2.2 Implement `call_search_service()` function
  - [ ] 6.2.3 Implement `call_prediction_service()` function
  - [ ] 6.2.4 Implement `call_opinion_service()` function
  - [ ] 6.2.5 Add error handling for service failures
  - [ ] 6.2.6 Add timeout configuration
- [ ] 6.3 Update endpoint handlers to use real service calls
  - [ ] 6.3.1 Replace mock data in `/analyze` endpoint
  - [ ] 6.3.2 Test integration with running services
  - [ ] 6.3.3 Test error handling for service failures

### Task 7: Add Input Validation to Orchestrator
- [ ] 7.1 Add file validation to orchestrator
  - [ ] 7.1.1 Import `validate_pdf_file` from `shared.security`
  - [ ] 7.1.2 Add validation call in `/api/analyze-brief` endpoint
  - [ ] 7.1.3 Handle validation exceptions appropriately
- [ ] 7.2 Add tests for input validation
  - [ ] 7.2.1 Test with oversized files (>10MB)
  - [ ] 7.2.2 Test with non-PDF files
  - [ ] 7.2.3 Test with corrupted PDFs
  - [ ] 7.2.4 Test with files containing executables
  - [ ] 7.2.5 Verify proper error responses (400, 413)

### Task 8: Fix Year Validation Range
- [ ] 8.1 Update year validation in models
  - [ ] 8.1.1 Change `year` field in `CaseLawDocument` to `ge=1900, le=2100`
  - [ ] 8.1.2 Update `validate_year_range()` in `shared/security.py`
  - [ ] 8.1.3 Update any other year validations in codebase
- [ ] 8.2 Add tests for expanded year range
  - [ ] 8.2.1 Test with historical years (1900-2021)
  - [ ] 8.2.2 Test with current years (2022-2024)
  - [ ] 8.2.3 Test with future years (2025-2100)
  - [ ] 8.2.4 Test boundary values (1900, 2100)
  - [ ] 8.2.5 Test invalid years (<1900, >2100)

### Task 9: Fix Vector Dimension Validation
- [ ] 9.1 Update embedding service initialization
  - [ ] 9.1.1 Change dimension check from warning to exception
  - [ ] 9.1.2 Add clear error message with expected vs actual dimensions
  - [ ] 9.1.3 Test with correct 768-dimensional model
  - [ ] 9.1.4 Test with wrong dimension model (should fail)
- [ ] 9.2 Update vector validation in models
  - [ ] 9.2.1 Ensure `VectorDocument.vector` validator raises exception
  - [ ] 9.2.2 Add clear error message for dimension mismatch
  - [ ] 9.2.3 Test validation with correct and incorrect dimensions

---

## Phase 3: P2 Performance & Quality Improvements

### Task 10: Implement HTTP Connection Pooling
- [ ] 10.1 Create HTTP client manager
  - [ ] 10.1.1 Create `python-services/shared/http_client.py`
  - [ ] 10.1.2 Implement `HTTPClientManager` singleton class
  - [ ] 10.1.3 Configure connection pooling (max 100, keepalive 20)
  - [ ] 10.1.4 Add timeout configuration (30s request, 5s connect)
  - [ ] 10.1.5 Enable HTTP/2
- [ ] 10.2 Update services to use pooled client
  - [ ] 10.2.1 Update orchestrator API to use `get_http_client()`
  - [ ] 10.2.2 Update search service to use pooled client
  - [ ] 10.2.3 Update prediction service to use pooled client
  - [ ] 10.2.4 Update opinion service to use pooled client
  - [ ] 10.2.5 Add shutdown handlers to close clients
- [ ] 10.3 Performance testing
  - [ ] 10.3.1 Benchmark latency before/after
  - [ ] 10.3.2 Test connection reuse
  - [ ] 10.3.3 Verify connection limits work

### Task 11: Add Async File I/O
- [ ] 11.1 Add aiofiles dependency
  - [ ] 11.1.1 Add `aiofiles==23.2.1` to `requirements.txt`
  - [ ] 11.1.2 Install dependency
- [ ] 11.2 Update audit logger to use async I/O
  - [ ] 11.2.1 Import `aiofiles` in `shared/audit_logger.py`
  - [ ] 11.2.2 Replace `open()` with `aiofiles.open()`
  - [ ] 11.2.3 Update all file operations to use `await`
  - [ ] 11.2.4 Test async logging works correctly
- [ ] 11.3 Update other file operations
  - [ ] 11.3.1 Search codebase for synchronous file operations in async contexts
  - [ ] 11.3.2 Replace with async equivalents
  - [ ] 11.3.3 Test performance improvement

### Task 12: Optimize Qdrant Index Configuration
- [ ] 12.1 Update vector index service
  - [ ] 12.1.1 Import `HnswConfigDiff` from `qdrant_client.models`
  - [ ] 12.1.2 Update `create_collection()` with HNSW parameters
  - [ ] 12.1.3 Set `m=16`, `ef_construct=100`
  - [ ] 12.1.4 Configure `full_scan_threshold` and `on_disk` settings
  - [ ] 12.1.5 Add optimizer configuration
- [ ] 12.2 Performance testing
  - [ ] 12.2.1 Benchmark search latency before/after
  - [ ] 12.2.2 Test with various collection sizes
  - [ ] 12.2.3 Measure memory usage
  - [ ] 12.2.4 Verify accuracy maintained

### Task 13: Add Environment Variable Validation
- [ ] 13.1 Create validation function
  - [ ] 13.1.1 Add `validate_environment_variables()` to `shared/config.py`
  - [ ] 13.1.2 Define required variables for all environments
  - [ ] 13.1.3 Define production-specific required variables
  - [ ] 13.1.4 Add type validation (int, float, bool)
  - [ ] 13.1.5 Add URL format validation
  - [ ] 13.1.6 Generate clear error messages
- [ ] 13.2 Add startup validation
  - [ ] 13.2.1 Call validation in startup event handlers
  - [ ] 13.2.2 Test with missing required variables
  - [ ] 13.2.3 Test with invalid types
  - [ ] 13.2.4 Verify clear error messages

### Task 14: Remove Hardcoded URLs
- [ ] 14.1 Add service URL configuration
  - [ ] 14.1.1 Add service URL fields to `ServiceSettings` in `config.py`
  - [ ] 14.1.2 Set default values for development
  - [ ] 14.1.3 Update `.env.example` with all service URLs
- [ ] 14.2 Update orchestrator API
  - [ ] 14.2.1 Replace hardcoded URLs with config values
  - [ ] 14.2.2 Test with different URL configurations
- [ ] 14.3 Update Docker Compose
  - [ ] 14.3.1 Add service URL environment variables
  - [ ] 14.3.2 Use Docker service names for URLs
  - [ ] 14.3.3 Test Docker deployment

### Task 15: Fix Test Skipping Behavior
- [ ] 15.1 Reorganize test structure
  - [ ] 15.1.1 Create `tests/unit/` directory
  - [ ] 15.1.2 Create `tests/integration/` directory
  - [ ] 15.1.3 Move unit tests to `unit/` folder
  - [ ] 15.1.4 Move integration tests to `integration/` folder
  - [ ] 15.1.5 Add `@pytest.mark.integration` to integration tests
- [ ] 15.2 Update CI/CD configuration
  - [ ] 15.2.1 Add separate unit test step
  - [ ] 15.2.2 Add service startup step
  - [ ] 15.2.3 Add integration test step
  - [ ] 15.2.4 Test CI/CD pipeline

### Task 16: Add Unit Tests
- [ ] 16.1 Create security function tests
  - [ ] 16.1.1 Create `tests/unit/test_security.py`
  - [ ] 16.1.2 Add tests for `sanitize_query_filter()`
  - [ ] 16.1.3 Add tests for `sanitize_llm_input()`
  - [ ] 16.1.4 Add tests for `redact_pii()`
  - [ ] 16.1.5 Add tests for `validate_pdf_file()`
- [ ] 16.2 Create validator tests
  - [ ] 16.2.1 Create `tests/unit/test_validators.py`
  - [ ] 16.2.2 Add tests for year validation
  - [ ] 16.2.3 Add tests for vector dimension validation
- [ ] 16.3 Create model tests
  - [ ] 16.3.1 Add tests for `CaseLawDocument` validation
  - [ ] 16.3.2 Add tests for `VectorDocument` validation
  - [ ] 16.3.3 Add tests for `OutcomePrediction` validation
- [ ] 16.4 Measure coverage
  - [ ] 16.4.1 Run tests with coverage report
  - [ ] 16.4.2 Verify 80%+ coverage for core logic
  - [ ] 16.4.3 Add tests for uncovered code

---

## Phase 4: P3 Architecture & Documentation

### Task 17: Add Service Health Checks
- [ ] 17.1 Create health check module
  - [ ] 17.1.1 Create `python-services/shared/health.py`
  - [ ] 17.1.2 Implement `HealthChecker` class
  - [ ] 17.1.3 Add `/health`, `/health/live`, `/health/ready` endpoints
  - [ ] 17.1.4 Implement check registration system
- [ ] 17.2 Add health checks to services
  - [ ] 17.2.1 Add Qdrant connection check
  - [ ] 17.2.2 Add model loading check
  - [ ] 17.2.3 Add Redis connection check (if enabled)
  - [ ] 17.2.4 Test health checks with dependencies up/down
  - [ ] 17.2.5 Verify response times <100ms

### Task 18: Implement Structured Logging
- [ ] 18.1 Create logging configuration module
  - [ ] 18.1.1 Create `python-services/shared/logging_config.py`
  - [ ] 18.1.2 Implement JSON formatter
  - [ ] 18.1.3 Add request ID context variable
  - [ ] 18.1.4 Implement `setup_logging()` function
- [ ] 18.2 Create request ID middleware
  - [ ] 18.2.1 Implement `RequestIDMiddleware`
  - [ ] 18.2.2 Add X-Request-ID header handling
  - [ ] 18.2.3 Test request ID propagation
- [ ] 18.3 Update services to use structured logging
  - [ ] 18.3.1 Replace logger setup in all services
  - [ ] 18.3.2 Add request ID middleware to all services
  - [ ] 18.3.3 Test JSON format in production mode
  - [ ] 18.3.4 Verify PII redaction still works

### Task 19: Add Metrics Endpoints
- [ ] 19.1 Add Prometheus dependencies
  - [ ] 19.1.1 Add `prometheus-client` to requirements
  - [ ] 19.1.2 Add `prometheus-fastapi-instrumentator` to requirements
- [ ] 19.2 Create metrics module
  - [ ] 19.2.1 Create `python-services/shared/metrics.py`
  - [ ] 19.2.2 Define standard metrics (requests, duration, errors)
  - [ ] 19.2.3 Define business metrics (searches, predictions, embeddings)
  - [ ] 19.2.4 Implement `setup_metrics()` function
- [ ] 19.3 Add metrics to services
  - [ ] 19.3.1 Add metrics to search service
  - [ ] 19.3.2 Add metrics to prediction service
  - [ ] 19.3.3 Add metrics to embedding service
  - [ ] 19.3.4 Add metrics to opinion service
  - [ ] 19.3.5 Test `/metrics` endpoint returns Prometheus format

### Task 20: Add OpenAPI Documentation
- [ ] 20.1 Enhance model documentation
  - [ ] 20.1.1 Add descriptions to all Pydantic models
  - [ ] 20.1.2 Add examples to all fields
  - [ ] 20.1.3 Add field constraints documentation
- [ ] 20.2 Enhance endpoint documentation
  - [ ] 20.2.1 Add summaries to all endpoints
  - [ ] 20.2.2 Add detailed descriptions
  - [ ] 20.2.3 Add response examples
  - [ ] 20.2.4 Document authentication requirements
  - [ ] 20.2.5 Document error codes
- [ ] 20.3 Test documentation
  - [ ] 20.3.1 Verify `/docs` renders correctly
  - [ ] 20.3.2 Test all examples are valid
  - [ ] 20.3.3 Verify completeness

### Task 21: Create Architecture Diagrams
- [ ] 21.1 Create architecture documentation
  - [ ] 21.1.1 Create `ARCHITECTURE.md` file
  - [ ] 21.1.2 Add system architecture diagram (Mermaid)
  - [ ] 21.1.3 Add data flow diagram
  - [ ] 21.1.4 Add deployment diagram
  - [ ] 21.1.5 Add component descriptions
- [ ] 21.2 Update README
  - [ ] 21.2.1 Link to architecture documentation
  - [ ] 21.2.2 Add quick start guide
  - [ ] 21.2.3 Add troubleshooting section

---

## Testing & Validation Tasks

### Task 22: Security Testing
- [ ] 22.1 Run security scan
  - [ ] 22.1.1 Run `python-services/security_scan.py`
  - [ ] 22.1.2 Verify no critical vulnerabilities
  - [ ] 22.1.3 Fix any issues found
- [ ] 22.2 Manual security testing
  - [ ] 22.2.1 Test injection attack prevention
  - [ ] 22.2.2 Test authentication bypass attempts
  - [ ] 22.2.3 Test file upload attacks
  - [ ] 22.2.4 Test CORS configuration

### Task 23: Performance Testing
- [ ] 23.1 Benchmark performance improvements
  - [ ] 23.1.1 Measure baseline performance
  - [ ] 23.1.2 Measure post-optimization performance
  - [ ] 23.1.3 Verify 20% improvement target met
- [ ] 23.2 Load testing
  - [ ] 23.2.1 Test with concurrent requests
  - [ ] 23.2.2 Test connection pooling under load
  - [ ] 23.2.3 Verify no performance regression

### Task 24: Integration Testing
- [ ] 24.1 End-to-end testing
  - [ ] 24.1.1 Test complete analysis pipeline
  - [ ] 24.1.2 Test with authentication
  - [ ] 24.1.3 Test error handling
  - [ ] 24.1.4 Test with various file types
- [ ] 24.2 Service integration testing
  - [ ] 24.2.1 Test all service-to-service calls
  - [ ] 24.2.2 Test error propagation
  - [ ] 24.2.3 Test timeout handling

---

## Deployment Tasks

### Task 25: Update Deployment Configuration
- [ ] 25.1 Update environment files
  - [ ] 25.1.1 Update `.env.example` with all new variables
  - [ ] 25.1.2 Update `.env.security.example`
  - [ ] 25.1.3 Document all configuration options
- [ ] 25.2 Update Docker configuration
  - [ ] 25.2.1 Update `docker-compose.yml` with new env vars
  - [ ] 25.2.2 Test Docker deployment
  - [ ] 25.2.3 Verify all services start correctly
- [ ] 25.3 Update documentation
  - [ ] 25.3.1 Update `DEPLOYMENT_GUIDE.md`
  - [ ] 25.3.2 Update `QUICK_START.md`
  - [ ] 25.3.3 Update `SECURITY_QUICKSTART.md`

---

## Success Criteria

All tasks must be completed and verified before marking the spec as complete:

- [ ] All P0 security vulnerabilities fixed
- [ ] All P1 critical errors fixed
- [ ] Performance improved by 20%
- [ ] Test coverage >80%
- [ ] All services have health checks
- [ ] All services have metrics
- [ ] Documentation complete
- [ ] Security scan passes
- [ ] Integration tests pass
- [ ] Production deployment successful
