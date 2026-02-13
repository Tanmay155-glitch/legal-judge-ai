# Legal LLM Supreme Court System - Setup Guide

This guide will help you set up the development environment for the Legal LLM Supreme Court System.

## Architecture Overview

The system uses a **hybrid Rust+Python architecture**:

- **Rust API Gateway (Axum)**: Port 8080 - Orchestration, rate limiting, authentication
- **Python Services**: Ports 8001-8005 - ML/NLP operations
  - Embedding Service (8001): Legal-BERT vector generation
  - Ingestion Service (8002): Case law document processing
  - Search Service (8003): Semantic search with Qdrant
  - Prediction Service (8004): Judicial outcome prediction
  - Opinion Service (8005): RAG-based opinion generation
- **OCR Service (Python)**: Port 8000 - PDF text extraction
- **Qdrant**: Port 6333 - Vector database
- **Redis**: Port 6379 - Caching layer

## Prerequisites

### Required Software

1. **Docker & Docker Compose** (recommended for easiest setup)
   - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)

2. **For Local Development** (without Docker):
   - Python 3.11+
   - Rust 1.75+
   - Node.js 18+ (for frontend)
   - Tesseract OCR
   - Poppler (for PDF processing)

## Quick Start with Docker

### 1. Clone and Navigate

```bash
cd legal-judge-ai
```

### 2. Configure Environment Variables

```bash
# Copy example environment files
cp python-services/.env.example python-services/.env
cp rust-api/.env.example rust-api/.env

# Edit .env files with your configuration
# IMPORTANT: Add your OpenAI API key to python-services/.env
```

### 3. Start All Services

```bash
docker-compose up -d
```

This will start:
- Qdrant vector database
- Redis cache
- OCR service
- Python ML/NLP services
- Rust API gateway

### 4. Verify Services

```bash
# Check all services are running
docker-compose ps

# Check API gateway health
curl http://localhost:8080/health

# Check individual services
curl http://localhost:8000/health  # OCR
curl http://localhost:8001/health  # Embedding (when implemented)
```

### 5. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f rust_api
docker-compose logs -f python_services
```

## Local Development Setup (Without Docker)

### 1. Set Up Python Services

```bash
cd python-services

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration
```

### 2. Set Up Rust API

```bash
cd rust-api

# Copy and configure environment
cp .env.example .env

# Build the project
cargo build

# Run the API gateway
cargo run
```

### 3. Start Infrastructure Services

```bash
# Start Qdrant (in separate terminal)
docker run -p 6333:6333 qdrant/qdrant:latest

# Start Redis (in separate terminal)
docker run -p 6379:6379 redis:7-alpine
```

### 4. Start OCR Service

```bash
cd ocr-service
uvicorn main:app --port 8000
```

### 5. Start Python Services

```bash
cd python-services
python main.py
```

### 6. Start Rust API Gateway

```bash
cd rust-api
cargo run
```

## Data Ingestion

### Ingest Sample Cases

```bash
# Ensure services are running, then:
python scripts/ingest_vectors.py
```

This will:
1. Load case law documents
2. Generate embeddings using Legal-BERT
3. Store vectors in Qdrant
4. Index metadata

## Testing

### Run Python Tests

```bash
cd python-services
pytest tests/ -v
```

### Run Property-Based Tests

```bash
cd python-services
pytest tests/ -v --hypothesis-profile=ci
```

### Run Rust Tests

```bash
cd rust-api
cargo test
```

## Frontend Setup (Optional)

```bash
cd frontend-v2

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at http://localhost:5173

## API Documentation

Once services are running:

- **Rust API Gateway**: http://localhost:8080
- **API Health**: http://localhost:8080/health
- **API Stats**: http://localhost:8080/stats

## Troubleshooting

### Services Won't Start

1. Check if ports are already in use:
   ```bash
   # Windows
   netstat -ano | findstr :8080
   
   # Linux/Mac
   lsof -i :8080
   ```

2. Check Docker logs:
   ```bash
   docker-compose logs
   ```

### OCR Not Working

Ensure Tesseract and Poppler are installed:

```bash
# Windows (using Chocolatey)
choco install tesseract poppler

# Mac
brew install tesseract poppler

# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils
```

### Python Dependencies Issues

```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v
```

### Rust Build Issues

```bash
# Update Rust
rustup update

# Clean and rebuild
cargo clean
cargo build
```

## Development Workflow

1. **Make changes** to code
2. **Run tests** to verify changes
3. **Restart services** if needed:
   ```bash
   docker-compose restart rust_api
   docker-compose restart python_services
   ```

## Next Steps

1. Review the [Requirements Document](.kiro/specs/legal-llm-supreme-court-system/requirements.md)
2. Review the [Design Document](.kiro/specs/legal-llm-supreme-court-system/design.md)
3. Start implementing tasks from [Tasks Document](.kiro/specs/legal-llm-supreme-court-system/tasks.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs -f`
3. Verify environment configuration in `.env` files
