# Quick Start Guide - Legal LLM Supreme Court System

**For Developers**: Get up and running in 5 minutes

---

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r python-services/requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r python-services/requirements.txt
```

### 2. Start Infrastructure

```bash
# Start Qdrant (vector database)
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant:latest

# Optional: Start Redis (for caching)
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### 3. Verify Setup

```bash
# Check Qdrant
curl http://localhost:6333/health

# Check Python installation
python -c "import sentence_transformers; print('✓ Dependencies OK')"
```

---

## 💻 Using the Services

### Embedding Service

```python
from embedding_service.service import get_embedding_service

# Initialize (loads Legal-BERT model - takes ~30 seconds first time)
service = get_embedding_service()

# Generate embedding
text = "The Court holds that the landlord breached the implied warranty of habitability."
embedding = service.encode_text(text)
print(f"Embedding shape: {embedding.shape}")  # (768,)

# Batch processing
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = service.encode_batch(texts, batch_size=32)
print(f"Batch shape: {embeddings.shape}")  # (3, 768)

# Section encoding
sections = {
    "facts": "The plaintiff entered into a residential lease...",
    "issue": "Whether the landlord breached the warranty...",
    "reasoning": "The Court has consistently held..."
}
section_embeddings = service.encode_sections(sections)
print(f"Sections encoded: {list(section_embeddings.keys())}")
```

### Vector Index Service

```python
from vector_index.service import get_vector_index_service
import numpy as np

# Initialize (connects to Qdrant)
service = get_vector_index_service(qdrant_url="http://localhost:6333")

# Create collection (only needed once)
service.create_collection(
    collection_name="supreme_court_cases",
    vector_size=768,
    distance="Cosine"
)

# Index a document
vectors = {
    "facts": np.random.randn(768),
    "issue": np.random.randn(768),
    "reasoning": np.random.randn(768)
}
metadata = {
    "case_name": "Doe v. Smith",
    "year": 2023,
    "court": "Supreme Court of the United States",
    "final_judgment": "Affirmed"
}

vector_ids = service.index_document(
    doc_id="case-123",
    vectors=vectors,
    metadata=metadata
)
print(f"Indexed {len(vector_ids)} vectors")

# Search for similar cases
query_vector = np.random.randn(768)
results = service.search_similar(
    query_vector=query_vector,
    top_k=5,
    filters={"year": 2023},
    score_threshold=0.6
)

for result in results:
    print(f"Case: {result['payload']['case_name']}")
    print(f"Score: {result['score']:.3f}")
    print(f"Section: {result['payload']['section_type']}")
    print("---")
```

### Data Models

```python
from shared.models import CaseLawDocument
from shared.validators import validate_case_law_document

# Create a case law document
doc = CaseLawDocument(
    case_name="Doe v. Smith",
    year=2023,
    court="Supreme Court of the United States",
    opinion_type="per_curiam",
    facts="The plaintiff entered into a residential lease agreement with the defendant. The premises suffered from severe water leaks and mold growth, rendering the unit uninhabitable.",
    issue="Whether the landlord breached the implied warranty of habitability by failing to repair the water leaks and mold.",
    reasoning="The Court has consistently held that residential leases contain an implied warranty of habitability. The landlord's failure to repair the water leaks and mold constitutes a material breach of this warranty.",
    holding="The landlord breached the implied warranty of habitability.",
    final_judgment="Affirmed"
)

# Validate
result = validate_case_law_document(doc)
if result.is_valid:
    print("✓ Document is valid")
else:
    print("✗ Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

### Ingestion Service

```python
from ingestion_service.service import get_ingestion_service
from vector_index.service import get_vector_index_service
import asyncio

# Initialize services
vector_service = get_vector_index_service()
vector_service.create_collection()  # Create collection if needed

ingestion_service = get_ingestion_service(
    ocr_service_url="http://localhost:8000",
    embedding_service_url="http://localhost:8001",
    vector_index_service=vector_service
)

# Ingest a PDF
async def ingest_example():
    result = await ingestion_service.ingest_pdf(
        pdf_path="path/to/case.pdf",
        filename="doe_v_smith.pdf"
    )
    
    print(f"Status: {result.status}")
    print(f"Case: {result.case_name}")
    print(f"Sections: {result.sections_extracted}")
    print(f"Vectors: {len(result.vector_ids)}")
    print(f"Time: {result.processing_time_seconds:.2f}s")

# Run
asyncio.run(ingest_example())
```

---

## 🧪 Running Tests

```bash
cd python-services

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run only unit tests (skip integration)
pytest tests/ -v -m "not integration"
```

---

## 🐳 Docker Quick Start

```bash
# Start all services with Docker Compose
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## 📝 Common Tasks

### Task 1: Index a New Case

```python
import asyncio
from embedding_service.service import get_embedding_service
from vector_index.service import get_vector_index_service
from shared.models import CaseLawDocument

async def index_case():
    # 1. Create document
    doc = CaseLawDocument(
        case_name="New Case v. Defendant",
        year=2023,
        facts="..." * 50,
        issue="..." * 20,
        reasoning="..." * 100,
        holding="..." * 20,
        final_judgment="Affirmed"
    )
    
    # 2. Generate embeddings
    embed_service = get_embedding_service()
    sections = {
        "facts": doc.facts,
        "issue": doc.issue,
        "reasoning": doc.reasoning,
        "holding": doc.holding
    }
    embeddings = embed_service.encode_sections(sections)
    
    # 3. Store in vector index
    vector_service = get_vector_index_service()
    import numpy as np
    vectors = {k: np.array(v) for k, v in embeddings.items() if v is not None}
    
    vector_ids = vector_service.index_document(
        doc_id=doc.document_id,
        vectors=vectors,
        metadata={
            "case_name": doc.case_name,
            "year": doc.year,
            "court": doc.court,
            "final_judgment": doc.final_judgment
        }
    )
    
    print(f"✓ Indexed case: {doc.case_name}")
    print(f"  Vector IDs: {vector_ids}")

asyncio.run(index_case())
```

### Task 2: Search for Similar Cases

```python
from embedding_service.service import get_embedding_service
from vector_index.service import get_vector_index_service
import numpy as np

# 1. Create query
query_text = "landlord failed to repair water damage and mold"

# 2. Generate query embedding
embed_service = get_embedding_service()
query_embedding = embed_service.encode_text(query_text)

# 3. Search
vector_service = get_vector_index_service()
results = vector_service.search_similar(
    query_vector=query_embedding,
    top_k=10,
    filters={"section_type": "facts"},  # Search only in facts sections
    score_threshold=0.7
)

# 4. Display results
print(f"Found {len(results)} similar cases:")
for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['payload']['case_name']} ({result['payload']['year']})")
    print(f"   Similarity: {result['score']:.3f}")
    print(f"   Section: {result['payload']['section_type']}")
    print(f"   Judgment: {result['payload']['final_judgment']}")
```

### Task 3: Validate a Document

```python
from shared.models import CaseLawDocument
from shared.validators import validate_case_law_document, get_validation_summary

# Create document (with intentional errors)
doc = CaseLawDocument(
    case_name="Invalid Name",  # Missing "v."
    year=2021,  # Out of range
    facts="Too short",  # Less than 50 chars
    issue="..." * 20,
    reasoning="..." * 100,
    holding="..." * 20,
    final_judgment="Affirmed"
)

# Validate
result = validate_case_law_document(doc)

# Display results
print(get_validation_summary(result))
print("\nErrors:")
for error in result.errors:
    print(f"  ✗ {error}")

print("\nWarnings:")
for warning in result.warnings:
    print(f"  ⚠ {warning}")

print("\nField Validations:")
for field, is_valid in result.field_validations.items():
    status = "✓" if is_valid else "✗"
    print(f"  {status} {field}")
```

---

## 🔧 Troubleshooting

### Issue: "No module named 'sentence_transformers'"
```bash
pip install sentence-transformers
```

### Issue: "Connection refused to Qdrant"
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Start Qdrant if not running
docker run -d -p 6333:6333 qdrant/qdrant:latest
```

### Issue: "CUDA out of memory"
```python
# Force CPU usage
service = get_embedding_service()
service.device = "cpu"
service.model.to("cpu")
```

### Issue: "Model download is slow"
```bash
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('nlpaueb/legal-bert-base-uncased')"
```

---

## 📚 Next Steps

1. **Read SETUP.md** for detailed installation instructions
2. **Review PROJECT_STRUCTURE.md** to understand the architecture
3. **Check PROGRESS_SUMMARY.md** for current implementation status
4. **Explore tests/** directory for more examples

---

## 🎯 Quick Reference

### Service URLs (when running)
- Embedding Service: http://localhost:8001
- Ingestion Service: http://localhost:8002 (pending)
- Search Service: http://localhost:8003 (pending)
- Prediction Service: http://localhost:8004 (pending)
- Opinion Service: http://localhost:8005 (pending)
- Rust API Gateway: http://localhost:8080 (pending)
- Qdrant: http://localhost:6333
- Redis: http://localhost:6379

### Key Files
- Models: `python-services/shared/models.py`
- Validators: `python-services/shared/validators.py`
- Embedding: `python-services/embedding_service/service.py`
- Vector Index: `python-services/vector_index/service.py`
- Ingestion: `python-services/ingestion_service/service.py`
- Tests: `python-services/tests/`

### Environment Variables
```bash
# Qdrant
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export QDRANT_COLLECTION_NAME=supreme_court_cases

# Embedding
export EMBEDDING_MODEL=nlpaueb/legal-bert-base-uncased
export EMBEDDING_BATCH_SIZE=32

# Services
export OCR_SERVICE_URL=http://localhost:8000
export EMBEDDING_SERVICE_URL=http://localhost:8001
```

---

**Happy Coding! 🚀**
