# Testing Guide - Legal LLM Supreme Court System

## Overview

This document describes the comprehensive test suite for the Legal LLM Supreme Court System, including unit tests, property-based tests, and integration tests.

## Test Structure

```
python-services/tests/
├── test_models.py              # Unit tests for data models
├── test_embedding.py           # Unit tests for embedding service
├── test_vector_index.py        # Unit tests for vector index
├── test_api_properties.py      # Property-based tests for APIs
├── test_integration.py         # End-to-end integration tests
└── conftest.py                 # Pytest configuration
```

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Files**:
- `test_models.py` - Pydantic model validation
- `test_embedding.py` - Embedding service functionality
- `test_vector_index.py` - Vector index operations

**Run**:
```bash
pytest tests/test_models.py -v
pytest tests/test_embedding.py -v
pytest tests/test_vector_index.py -v
```

### 2. Property-Based Tests

**Purpose**: Test universal properties that should hold for all inputs

**File**: `test_api_properties.py`

**Properties Tested**:
- **Property 25**: Invalid API inputs return HTTP 400
- **Property 26**: API responses follow consistent format
- **Property 27**: Rate limiting prevents excessive requests
- **Additional**: Parameter validation (top_k, min_similarity, etc.)

**Run**:
```bash
pytest tests/test_api_properties.py -v --hypothesis-show-statistics
```

**Features**:
- Uses Hypothesis library for property-based testing
- Generates random test cases automatically
- Tests edge cases and boundary conditions
- Configurable number of examples (default: 10)

### 3. Integration Tests

**Purpose**: Test complete workflows across multiple services

**File**: `test_integration.py`

**Workflows Tested**:
- **Test 17.1**: PDF upload → OCR → Parsing → Embedding → Indexing → Search
- **Test 17.2**: Query → Embedding → Vector Search → Result Formatting
- **Test 17.3**: Input → Search → Feature Extraction → Prediction
- **Test 17.4**: Input → Search → RAG → LLM → Formatting

**Run**:
```bash
# Start services first
python main.py

# In another terminal, run integration tests
pytest tests/test_integration.py -v -m integration
```

## Running Tests

### Quick Start

Run all tests:
```bash
python run_tests.py
```

### Individual Test Suites

**Unit Tests Only**:
```bash
pytest tests/test_models.py tests/test_embedding.py tests/test_vector_index.py -v
```

**Property Tests Only**:
```bash
pytest tests/test_api_properties.py -v
```

**Integration Tests Only** (requires services running):
```bash
pytest tests/test_integration.py -v -m integration
```

### With Coverage

```bash
pytest --cov=. --cov-report=html tests/
```

### Specific Test

```bash
pytest tests/test_models.py::TestCaseLawDocument::test_valid_case_law -v
```

## Test Requirements

### For Unit Tests
- No external services required
- Uses mocks for external dependencies

### For Property Tests
- Services should be running (will skip if not available)
- Tests are designed to handle service unavailability gracefully

### For Integration Tests
- **Required**: All services must be running
  ```bash
  python main.py
  ```
- **Required**: Qdrant vector database running
  ```bash
  docker run -p 6333:6333 qdrant/qdrant:latest
  ```
- **Optional**: Redis for caching tests
  ```bash
  docker run -p 6379:6379 redis:7-alpine
  ```

## Property-Based Testing Details

### What is Property-Based Testing?

Property-based testing verifies that certain properties hold true for all possible inputs, not just specific examples.

### Example Properties

**Property 25: Invalid inputs return 400**
```python
@given(invalid_query=st.one_of(st.just(""), st.none()))
async def test_property_25_invalid_inputs_return_400(invalid_query):
    # Test that any invalid input returns HTTP 400
    response = await client.post("/search", json={"query": invalid_query})
    assert response.status_code in [400, 422]
```

**Property 26: Consistent response format**
```python
@given(valid_query=st.text(min_size=5, max_size=100))
async def test_property_26_consistent_response_format(valid_query):
    # Test that all responses have consistent structure
    response = await client.post("/search", json={"query": valid_query})
    if response.status_code == 200:
        data = response.json()
        assert "results" in data
        assert "total_results" in data
        assert "search_time_ms" in data
```

### Hypothesis Configuration

- **Max Examples**: 10 (configurable)
- **Timeout**: 30 seconds per test
- **Shrinking**: Enabled (finds minimal failing case)
- **Statistics**: Available with `--hypothesis-show-statistics`

## Integration Test Details

### Test 17.1: End-to-End Ingestion

**Workflow**:
1. Upload PDF file
2. OCR extracts text
3. Parser extracts sections
4. Validator checks schema
5. Embedder generates vectors
6. Vector index stores document
7. Search verifies document is findable

**Assertions**:
- Ingestion returns success status
- Document ID is generated
- Document is searchable after ingestion

### Test 17.2: End-to-End Search

**Workflow**:
1. Submit search query
2. Embedding service vectorizes query
3. Vector index performs similarity search
4. Results are ranked by similarity
5. Metadata is enriched

**Assertions**:
- Results are ranked by similarity (descending)
- All results include required metadata
- Similarity scores are in range [0, 1]
- Response includes timing information

### Test 17.3: End-to-End Prediction

**Workflow**:
1. Submit facts and issue
2. Search finds similar cases
3. Predictor extracts outcomes
4. Weighted voting calculates probabilities
5. Confidence score is computed

**Assertions**:
- Probabilities sum to 1.0
- All three outcomes have probabilities
- Supporting cases are included
- Confidence is in range [0, 1]
- Disclaimer is present

### Test 17.4: End-to-End Opinion Generation

**Workflow**:
1. Submit case context
2. Search retrieves precedents
3. RAG pipeline assembles context
4. LLM generates opinion
5. Formatter structures output
6. Validator checks sections

**Assertions**:
- All required sections present
- Precedents are cited
- Disclaimer is included
- Full text is at least 500 characters
- Generation metadata is included

## Test Data

### Mock Data

Unit tests use mock data defined in test files:
- Mock case law documents
- Mock embeddings (768-dimensional)
- Mock search results

### Test Fixtures

Located in `conftest.py`:
- Database connections
- Service clients
- Test data generators

## Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - 6333:6333
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run unit tests
        run: |
          pytest tests/test_models.py tests/test_embedding.py tests/test_vector_index.py -v
      
      - name: Run property tests
        run: |
          pytest tests/test_api_properties.py -v
      
      - name: Start services
        run: |
          python main.py &
          sleep 10
      
      - name: Run integration tests
        run: |
          pytest tests/test_integration.py -v -m integration
```

## Troubleshooting

### Tests Fail with "Service not running"

**Solution**: Start services before running integration tests
```bash
python main.py
```

### Property Tests Take Too Long

**Solution**: Reduce max_examples
```python
@settings(max_examples=5)  # Default is 10
```

### Integration Tests Timeout

**Solution**: Increase timeout in test
```python
async with httpx.AsyncClient(timeout=60.0) as client:
    # ...
```

### Mock Data Issues

**Solution**: Check that mock data matches current schema
```bash
pytest tests/test_models.py -v
```

## Best Practices

### Writing New Tests

1. **Unit Tests**: Test one component at a time
2. **Property Tests**: Think about universal properties
3. **Integration Tests**: Test realistic workflows
4. **Mocking**: Mock external dependencies in unit tests
5. **Assertions**: Be specific about what you're testing
6. **Documentation**: Add docstrings explaining what's tested

### Test Naming

- `test_<component>_<behavior>` for unit tests
- `test_property_<number>_<description>` for property tests
- `test_e2e_<workflow>` for integration tests

### Test Organization

- Group related tests in classes
- Use fixtures for common setup
- Keep tests independent
- Clean up after tests

## Test Coverage Goals

- **Unit Tests**: 80%+ code coverage
- **Property Tests**: Cover all API endpoints
- **Integration Tests**: Cover all major workflows

## Running Tests in Docker

```bash
# Build test container
docker build -f Dockerfile.test -t legal-llm-tests .

# Run tests
docker run --network host legal-llm-tests
```

## Performance Testing

For load testing and performance benchmarking:

```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8003
```

## Summary

The test suite provides comprehensive coverage:
- ✅ **75+ unit tests** for individual components
- ✅ **10+ property tests** for API validation
- ✅ **8+ integration tests** for end-to-end workflows
- ✅ **Automated test runner** for easy execution
- ✅ **CI/CD ready** for continuous testing

Run `python run_tests.py` to execute the full test suite!
