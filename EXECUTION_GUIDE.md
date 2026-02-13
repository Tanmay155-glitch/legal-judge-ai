# Legal LLM Supreme Court System - Step-by-Step Execution Guide

## Overview

This guide provides a complete step-by-step process to execute the Legal LLM Supreme Court System on your Windows machine. Follow these steps in order for a successful deployment.

---

## Prerequisites Check

Before starting, ensure you have:

- ✅ **Windows OS** (you have this)
- ✅ **Python 3.11+** installed
- ✅ **Docker Desktop** installed and running
- ✅ **8GB+ RAM** available
- ✅ **20GB+ disk space** available
- ⚠️ **OpenAI API Key** (optional, for opinion generation)

---

## Method 1: Quick Start with Docker Compose (Recommended)

### Step 1: Start Docker Desktop

1. Open **Docker Desktop** application
2. Wait until Docker is fully running (green icon in system tray)
3. Verify Docker is running:
   ```cmd
   docker --version
   docker-compose --version
   ```

### Step 2: Start Qdrant Vector Database

Open **Command Prompt** or **PowerShell** in your project directory:

```cmd
docker run -d -p 6333:6333 --name qdrant-vectors qdrant/qdrant:latest
```

Verify Qdrant is running:
```cmd
curl http://localhost:6333/health
```

Expected output: `{"title":"qdrant - vector search engine","version":"..."}`

### Step 3: Start Redis Cache (Optional but Recommended)

```cmd
docker run -d -p 6379:6379 --name redis-cache redis:7-alpine
```

Verify Redis is running:
```cmd
docker ps
```

You should see both `qdrant-vectors` and `redis-cache` containers running.

### Step 4: Install Python Dependencies

Navigate to the python-services directory:

```cmd
cd python-services
```

Install required packages:
```cmd
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (web framework)
- sentence-transformers (Legal-BERT embeddings)
- qdrant-client (vector database)
- pydantic (data validation)
- loguru (logging)
- httpx (HTTP client)
- redis (caching)
- hypothesis (property-based testing)
- pytest (testing framework)

**Note**: First-time installation will download the Legal-BERT model (~400MB). This may take 5-10 minutes.

### Step 5: Configure Environment Variables (Optional)

Create a `.env` file in the `python-services` directory:

```cmd
echo QDRANT_HOST=localhost > .env
echo QDRANT_PORT=6333 >> .env
echo REDIS_HOST=localhost >> .env
echo REDIS_PORT=6379 >> .env
echo ENABLE_REDIS_CACHE=true >> .env
```

For opinion generation with OpenAI (optional):
```cmd
echo OPENAI_API_KEY=your-api-key-here >> .env
echo LLM_MODEL=gpt-4 >> .env
```

### Step 6: Start All Python Services

From the `python-services` directory:

```cmd
python main.py
```

You should see output like:
```
[MAIN] Starting all services...
[MAIN] Starting Embedding Service on port 8001...
[MAIN] Starting Ingestion Service on port 8002...
[MAIN] Starting Search Service on port 8003...
[MAIN] Starting Prediction Service on port 8004...
[MAIN] Starting Opinion Service on port 8005...
[MAIN] All services started successfully!
```

**Keep this terminal window open** - the services are now running.

### Step 7: Verify All Services Are Running

Open a **new Command Prompt** window and test each service:

```cmd
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

Each should return a JSON response with `"status": "healthy"`.

---

## Method 2: Using Docker Compose (Alternative)

### Step 1: Configure Docker Compose

The `docker-compose.yml` file is already configured. Review it if needed:

```cmd
type docker-compose.yml
```

### Step 2: Start All Services with Docker Compose

From the project root directory:

```cmd
docker-compose up -d
```

This will start:
- Qdrant vector database (port 6333)
- Redis cache (port 6379)
- OCR service (port 8000)
- Python services (ports 8001-8005)

### Step 3: Check Service Status

```cmd
docker-compose ps
```

### Step 4: View Logs

```cmd
docker-compose logs -f python_services
```

Press `Ctrl+C` to stop viewing logs (services continue running).

---

## Using the System

### Test 1: Check Embedding Service

Test text embedding generation:

```cmd
curl -X POST http://localhost:8001/embed/text ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"The Supreme Court holds that the defendant violated constitutional rights.\"}"
```

Expected: JSON response with 768-dimensional embedding vector.

### Test 2: Get Model Information

```cmd
curl http://localhost:8001/model/info
```

Expected: Information about the Legal-BERT model.

### Test 3: Upload a Case Law Document (Ingestion)

**Note**: You need a PDF file of a Supreme Court case. For testing, you can create a sample:

```cmd
curl -X POST http://localhost:8002/ingest/pdf ^
  -F "file=@path\to\your\case.pdf" ^
  -F "case_name=Smith v. Jones"
```

Replace `path\to\your\case.pdf` with your actual PDF path.

Expected: JSON response with `document_id` and ingestion status.

### Test 4: Perform Semantic Search

After ingesting documents, search for similar cases:

```cmd
curl -X POST http://localhost:8003/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"breach of warranty of habitability\", \"top_k\": 5, \"min_similarity\": 0.6}"
```

Expected: JSON response with search results ranked by similarity.

### Test 5: Predict Case Outcome

```cmd
curl -X POST http://localhost:8004/predict/outcome ^
  -H "Content-Type: application/json" ^
  -d "{\"facts\": \"The landlord failed to repair the heating system despite multiple requests from the tenant during winter months.\", \"issue\": \"Whether the landlord breached the warranty of habitability\"}"
```

Expected: JSON response with predicted outcome (Affirmed/Reversed/Remanded) and probabilities.

### Test 6: Generate Per Curiam Opinion

```cmd
curl -X POST http://localhost:8005/generate/opinion ^
  -H "Content-Type: application/json" ^
  -d "{\"case_context\": {\"facts\": \"The landlord failed to repair the heating system.\", \"issue\": \"Whether the landlord breached the warranty of habitability\", \"case_name\": \"Smith v. Jones\", \"petitioner\": \"Smith\", \"respondent\": \"Jones\"}, \"opinion_type\": \"per_curiam\", \"max_precedents\": 5}"
```

Expected: JSON response with generated opinion in Supreme Court format.

### Test 7: View Service Statistics

Check how many operations each service has performed:

```cmd
curl http://localhost:8002/stats
curl http://localhost:8003/stats
curl http://localhost:8004/stats
curl http://localhost:8005/stats
```

---

## Running Tests

### Step 1: Navigate to Python Services Directory

```cmd
cd python-services
```

### Step 2: Run All Tests

```cmd
python run_tests.py
```

This will run:
- Unit tests (models, embedding, vector index)
- Property-based tests (API validation)
- Integration tests (end-to-end workflows)

### Step 3: Run Specific Test Suites

**Unit tests only**:
```cmd
pytest tests\test_models.py tests\test_embedding.py tests\test_vector_index.py -v
```

**Property tests only**:
```cmd
pytest tests\test_api_properties.py -v
```

**Integration tests only** (requires services running):
```cmd
pytest tests\test_integration.py -v -m integration
```

### Step 4: Run Tests with Coverage

```cmd
pytest --cov=. --cov-report=html tests\
```

View coverage report:
```cmd
start htmlcov\index.html
```

---

## Sample Workflow: Complete Case Analysis

### Workflow: Ingest → Search → Predict → Generate Opinion

#### Step 1: Ingest a Case Law Document

```cmd
curl -X POST http://localhost:8002/ingest/pdf ^
  -F "file=@supreme_court_case_2023.pdf" ^
  -F "case_name=Johnson v. State"
```

Save the `document_id` from the response.

#### Step 2: Search for Similar Cases

```cmd
curl -X POST http://localhost:8003/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"Fourth Amendment search and seizure\", \"top_k\": 10}"
```

Review the similar cases found.

#### Step 3: Predict Outcome for New Case

```cmd
curl -X POST http://localhost:8004/predict/outcome ^
  -H "Content-Type: application/json" ^
  -d "{\"facts\": \"Police conducted a warrantless search of the defendant's vehicle after a traffic stop.\", \"issue\": \"Whether the warrantless search violated the Fourth Amendment\"}"
```

Note the predicted outcome and confidence score.

#### Step 4: Generate Opinion

```cmd
curl -X POST http://localhost:8005/generate/opinion ^
  -H "Content-Type: application/json" ^
  -d "{\"case_context\": {\"facts\": \"Police conducted a warrantless search...\", \"issue\": \"Whether the warrantless search violated the Fourth Amendment\", \"case_name\": \"Johnson v. State\", \"petitioner\": \"Johnson\", \"respondent\": \"State\"}, \"opinion_type\": \"per_curiam\"}"
```

Review the generated Per Curiam opinion.

---

## Monitoring and Troubleshooting

### Check Service Health

Create a batch script to check all services:

```cmd
@echo off
echo Checking Embedding Service...
curl -s http://localhost:8001/health
echo.
echo Checking Ingestion Service...
curl -s http://localhost:8002/health
echo.
echo Checking Search Service...
curl -s http://localhost:8003/health
echo.
echo Checking Prediction Service...
curl -s http://localhost:8004/health
echo.
echo Checking Opinion Service...
curl -s http://localhost:8005/health
```

Save as `check_health.bat` and run it.

### View Logs

If services are running via `python main.py`, logs appear in the terminal.

If using Docker Compose:
```cmd
docker-compose logs -f python_services
```

### Common Issues and Solutions

#### Issue 1: "Connection refused" when accessing services

**Solution**: Ensure services are running:
```cmd
curl http://localhost:8001/health
```

If not running, start them:
```cmd
cd python-services
python main.py
```

#### Issue 2: "Qdrant connection failed"

**Solution**: Start Qdrant:
```cmd
docker run -d -p 6333:6333 --name qdrant-vectors qdrant/qdrant:latest
```

Verify:
```cmd
curl http://localhost:6333/health
```

#### Issue 3: "Model not found" or embedding errors

**Solution**: The Legal-BERT model needs to download on first run. Wait 5-10 minutes for download to complete.

Check model status:
```cmd
curl http://localhost:8001/model/info
```

#### Issue 4: Out of memory errors

**Solution**: Reduce batch sizes in `.env`:
```cmd
echo EMBEDDING_BATCH_SIZE=16 >> .env
echo INGESTION_BATCH_SIZE=5 >> .env
```

Restart services.

#### Issue 5: Slow performance

**Solution**: Enable Redis caching:
```cmd
docker run -d -p 6379:6379 --name redis-cache redis:7-alpine
echo ENABLE_REDIS_CACHE=true >> .env
```

Restart services.

---

## Stopping the System

### Stop Python Services

In the terminal running `python main.py`, press `Ctrl+C`.

### Stop Docker Containers

```cmd
docker stop qdrant-vectors redis-cache
```

### Stop All Services (Docker Compose)

```cmd
docker-compose down
```

To also remove volumes:
```cmd
docker-compose down -v
```

---

## Data Management

### Backup Vector Database

```cmd
docker exec qdrant-vectors tar -czf /tmp/qdrant-backup.tar.gz /qdrant/storage
docker cp qdrant-vectors:/tmp/qdrant-backup.tar.gz .\backups\
```

### Restore Vector Database

```cmd
docker cp .\backups\qdrant-backup.tar.gz qdrant-vectors:/tmp/
docker exec qdrant-vectors tar -xzf /tmp/qdrant-backup.tar.gz -C /
docker restart qdrant-vectors
```

### View Audit Logs

Audit logs are stored in `python-services/audit_logs/`:

```cmd
dir python-services\audit_logs
type python-services\audit_logs\audit_log_2024-02-09.json
```

---

## Performance Optimization

### Enable GPU Acceleration (if available)

Check if CUDA is available:
```cmd
python -c "import torch; print(torch.cuda.is_available())"
```

If `True`, the embedding service will automatically use GPU for faster processing.

### Optimize Batch Sizes

For systems with more RAM:
```cmd
echo EMBEDDING_BATCH_SIZE=64 >> .env
echo INGESTION_BATCH_SIZE=20 >> .env
```

### Enable All Caching

```cmd
echo ENABLE_REDIS_CACHE=true >> .env
echo CACHE_MAX_SIZE=1000 >> .env
```

---

## Production Deployment

For production deployment, see:
- `DEPLOYMENT_GUIDE.md` - Comprehensive deployment guide
- `docker-compose.yml` - Container orchestration
- `python-services/Dockerfile` - Service containerization

---

## Quick Reference Commands

### Start System
```cmd
# Start Qdrant
docker run -d -p 6333:6333 --name qdrant-vectors qdrant/qdrant:latest

# Start Redis (optional)
docker run -d -p 6379:6379 --name redis-cache redis:7-alpine

# Start Python services
cd python-services
python main.py
```

### Test System
```cmd
# Health checks
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health

# Run tests
cd python-services
python run_tests.py
```

### Stop System
```cmd
# Stop Python services: Ctrl+C in terminal

# Stop Docker containers
docker stop qdrant-vectors redis-cache
```

---

## Next Steps

1. ✅ **System is running** - All services are operational
2. 📄 **Ingest case law documents** - Upload Supreme Court PDFs
3. 🔍 **Perform searches** - Find similar cases
4. 🎯 **Predict outcomes** - Get case predictions
5. 📝 **Generate opinions** - Create Per Curiam opinions
6. 📊 **Monitor performance** - Check stats and logs

---

## Support and Documentation

- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Testing Guide**: `python-services/TESTING.md`
- **API Verification**: `TASK_11_VERIFICATION.md`
- **Quick Start**: `QUICK_START.md`

---

## Important Notes

⚠️ **Legal Disclaimer**: This system is for research and academic purposes only. Do not use for actual legal proceedings or advice.

⚠️ **Data Privacy**: Audit logs contain user queries. Implement proper data retention policies.

⚠️ **API Keys**: Store OpenAI API keys securely in `.env` file, never in code.

⚠️ **Resource Requirements**: Ensure adequate RAM (8GB+) and disk space (20GB+) for optimal performance.

---

## Summary

You now have a complete step-by-step guide to:
1. ✅ Install prerequisites
2. ✅ Start all services
3. ✅ Test the system
4. ✅ Use all features (ingest, search, predict, generate)
5. ✅ Monitor and troubleshoot
6. ✅ Optimize performance

**Ready to start?** Follow Method 1 (Quick Start) for the fastest setup!
