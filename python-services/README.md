# Python Services

This directory contains all Python-based ML/NLP services for the Legal LLM Supreme Court System.

## Services

- **embedding_service**: Legal-BERT embedding generation
- **ingestion_service**: Case law document ingestion and structuring
- **search_service**: Semantic search engine with Qdrant
- **prediction_service**: Judicial outcome prediction
- **opinion_service**: Opinion generation with RAG pipeline

## Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running Services

Each service can be run independently:

```bash
# Run all services (recommended)
python main.py

# Or run individual services
uvicorn embedding_service.main:app --port 8001
uvicorn ingestion_service.main:app --port 8002
uvicorn search_service.main:app --port 8003
uvicorn prediction_service.main:app --port 8004
uvicorn opinion_service.main:app --port 8005
```
