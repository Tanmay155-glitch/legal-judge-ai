# Code Quality & Security Fixes - Requirements

## Overview
This spec addresses critical errors, security vulnerabilities, and quality improvements identified in the Legal LLM Supreme Court System codebase review.

## Priority Classification
- **P0 (Critical)**: Security vulnerabilities that must be fixed immediately
- **P1 (High)**: Errors that break functionality or cause data corruption
- **P2 (Medium)**: Performance issues and code quality improvements
- **P3 (Low)**: Nice-to-have improvements and optimizations

---

## 1. Critical Security Fixes (P0)

### 1.1 Complete Incomplete Security Function
**User Story**: As a developer, I need the `sanitize_query_filter()` function to be complete so NoSQL injection protection works.

**Acceptance Criteria**:
- [ ] The function in `python-services/shared/security.py` is complete
- [ ] All dangerous patterns are properly filtered
- [ ] Function returns sanitized string correctly
- [ ] Unit tests verify injection patterns are blocked

### 1.2 Fix Weak JWT Secret Key
**User Story**: As a security admin, I need strong JWT secrets enforced in production to prevent token forgery.

**Acceptance Criteria**:
- [ ] Default secret is a strong random value
- [ ] Production validation fails if default secret is used
- [ ] Environment variable `JWT_SECRET_KEY` is required in production
- [ ] Documentation updated with secret generation instructions

### 1.3 Add Authentication to Critical Endpoints
**User Story**: As a system admin, I need all sensitive endpoints protected by authentication to prevent unauthorized access.

**Acceptance Criteria**:
- [ ] `/api/analyze-brief` requires authentication
- [ ] All ingestion endpoints require authentication
- [ ] Opinion generation requires authentication
- [ ] Health endpoints remain public
- [ ] Proper 401/403 responses for unauthorized access

### 1.4 Fix CORS Wildcard Configuration
**User Story**: As a security engineer, I need CORS properly configured to prevent CSRF attacks.

**Acceptance Criteria**:
- [ ] Orchestrator API uses `cors_config.py` instead of wildcard
- [ ] Production requires explicit allowed origins
- [ ] Development has safe defaults
- [ ] CORS headers are properly set

---

## 2. Critical Code Errors (P1)

### 2.1 Improve OCR Error Handling
**User Story**: As a developer, I need specific error handling in OCR service to debug failures effectively.

**Acceptance Criteria**:
- [ ] Specific exceptions for Tesseract errors
- [ ] Specific exceptions for Poppler errors
- [ ] Specific exceptions for file format errors
- [ ] Proper error messages returned to client
- [ ] Errors logged with context

### 2.2 Implement Rust API Service Integration
**User Story**: As a developer, I need the Rust API to actually call Python services instead of returning mock data.

**Acceptance Criteria**:
- [ ] HTTP client properly configured
- [ ] Calls to OCR service implemented
- [ ] Calls to search service implemented
- [ ] Calls to prediction service implemented
- [ ] Calls to opinion service implemented
- [ ] Error handling for service failures
- [ ] Timeouts configured

### 2.3 Add Input Validation to Orchestrator
**User Story**: As a developer, I need file uploads validated before processing to prevent crashes.

**Acceptance Criteria**:
- [ ] File size validation (max 10MB)
- [ ] File type validation (PDF only)
- [ ] PDF magic number validation
- [ ] Malicious content detection
- [ ] Proper error responses for invalid files

### 2.4 Fix Year Validation Range
**User Story**: As a user, I need to ingest historical and future cases, not just 2022-2023.

**Acceptance Criteria**:
- [ ] Year range changed to 1900-2100
- [ ] Validation tests updated
- [ ] Documentation updated
- [ ] Existing data models remain compatible

### 2.5 Fix Vector Dimension Validation
**User Story**: As a developer, I need vector dimension mismatches to fail fast instead of corrupting the index.

**Acceptance Criteria**:
- [ ] Raise exception for wrong dimensions
- [ ] Clear error message indicating expected vs actual
- [ ] Prevent indexing of invalid vectors
- [ ] Tests verify dimension validation

---

## 3. Performance Improvements (P2)

### 3.1 Implement HTTP Connection Pooling
**User Story**: As a developer, I need connection pooling to reduce latency and improve throughput.

**Acceptance Criteria**:
- [ ] Singleton `httpx.AsyncClient` instances
- [ ] Connection pool configured (max 100 connections)
- [ ] Connection timeout configured (30s)
- [ ] Proper cleanup on shutdown
- [ ] Performance tests show improvement

### 3.2 Add Async File I/O
**User Story**: As a developer, I need async file operations to prevent blocking the event loop.

**Acceptance Criteria**:
- [ ] `aiofiles` added to requirements
- [ ] Audit logger uses async file writes
- [ ] All file operations in async contexts are async
- [ ] Performance tests verify non-blocking behavior

### 3.3 Optimize Qdrant Index Configuration
**User Story**: As a developer, I need optimized vector index configuration for fast searches at scale.

**Acceptance Criteria**:
- [ ] HNSW index parameters configured
- [ ] `m` parameter set to 16
- [ ] `ef_construct` set to 100
- [ ] Index optimization documented
- [ ] Performance benchmarks included

---

## 4. Configuration Improvements (P2)

### 4.1 Add Environment Variable Validation
**User Story**: As a DevOps engineer, I need configuration validation at startup to catch errors early.

**Acceptance Criteria**:
- [ ] All required env vars validated at startup
- [ ] Clear error messages for missing vars
- [ ] Type validation for numeric vars
- [ ] URL format validation
- [ ] Validation runs before service starts

### 4.2 Remove Hardcoded URLs
**User Story**: As a DevOps engineer, I need all service URLs configurable via environment variables.

**Acceptance Criteria**:
- [ ] All `localhost` URLs replaced with env vars
- [ ] Default values provided for development
- [ ] Docker compose uses service names
- [ ] Documentation updated with all env vars

---

## 5. Testing Improvements (P2)

### 5.1 Fix Test Skipping Behavior
**User Story**: As a developer, I need tests to fail when services are unavailable in CI/CD.

**Acceptance Criteria**:
- [ ] Tests use mocking for unit tests
- [ ] Integration tests require services running
- [ ] CI/CD starts services before tests
- [ ] Clear error messages when services unavailable

### 5.2 Add Unit Tests
**User Story**: As a developer, I need unit tests for individual functions to enable fast debugging.

**Acceptance Criteria**:
- [ ] Unit tests for security functions
- [ ] Unit tests for validators
- [ ] Unit tests for parsers
- [ ] Unit tests for formatters
- [ ] 80%+ code coverage for core logic

---

## 6. Architecture Improvements (P3)

### 6.1 Add Service Health Checks
**User Story**: As a DevOps engineer, I need comprehensive health checks for monitoring.

**Acceptance Criteria**:
- [ ] Health checks include dependency status
- [ ] Qdrant connection checked
- [ ] Redis connection checked (if enabled)
- [ ] Model loading status checked
- [ ] Response time < 100ms

### 6.2 Implement Structured Logging
**User Story**: As a DevOps engineer, I need structured JSON logs for better observability.

**Acceptance Criteria**:
- [ ] All logs in JSON format
- [ ] Correlation IDs across services
- [ ] Log levels properly used
- [ ] PII redaction maintained
- [ ] Log aggregation compatible (ELK/Splunk)

### 6.3 Add Metrics Endpoints
**User Story**: As a DevOps engineer, I need Prometheus metrics for monitoring.

**Acceptance Criteria**:
- [ ] `/metrics` endpoint on all services
- [ ] Request count metrics
- [ ] Request duration metrics
- [ ] Error rate metrics
- [ ] Custom business metrics (searches, predictions, etc.)

---

## 7. Documentation Improvements (P3)

### 7.1 Add OpenAPI Documentation
**User Story**: As an API consumer, I need comprehensive API documentation with examples.

**Acceptance Criteria**:
- [ ] OpenAPI 3.0 spec generated
- [ ] All endpoints documented
- [ ] Request/response examples included
- [ ] Authentication documented
- [ ] Error codes documented

### 7.2 Create Architecture Diagrams
**User Story**: As a new developer, I need architecture diagrams to understand the system.

**Acceptance Criteria**:
- [ ] System architecture diagram created
- [ ] Data flow diagram created
- [ ] Deployment diagram created
- [ ] Diagrams in documentation

---

## Non-Functional Requirements

### Security
- All fixes must maintain or improve security posture
- No new vulnerabilities introduced
- Security tests must pass

### Performance
- No performance regression
- Response times remain under SLA
- Resource usage optimized

### Compatibility
- Backward compatible with existing data
- API changes are versioned
- Migration path documented

### Testing
- All fixes must have tests
- Test coverage > 80%
- Integration tests pass

---

## Success Criteria

### Phase 1 (P0 - Critical Security)
- [ ] All P0 security vulnerabilities fixed
- [ ] Security scan shows no critical issues
- [ ] Production deployment safe

### Phase 2 (P1 - Critical Errors)
- [ ] All P1 errors fixed
- [ ] System stable and functional
- [ ] No data corruption possible

### Phase 3 (P2 - Performance & Quality)
- [ ] Performance improved by 20%
- [ ] Code quality metrics improved
- [ ] Technical debt reduced

### Phase 4 (P3 - Architecture & Docs)
- [ ] Monitoring and observability complete
- [ ] Documentation comprehensive
- [ ] Developer onboarding improved

---

## Out of Scope
- Complete rewrite of services
- Migration to different tech stack
- New features not related to fixes
- UI/UX improvements
