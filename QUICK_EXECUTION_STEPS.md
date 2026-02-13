# Quick Execution Steps - Legal LLM Supreme Court System

## 🚀 5-Minute Quick Start

### Step 1: Start Qdrant (Vector Database)
```cmd
docker run -d -p 6333:6333 --name qdrant-vectors qdrant/qdrant:latest
```

### Step 2: Install Python Dependencies
```cmd
cd python-services
pip install -r requirements.txt
```
⏱️ **First time**: 5-10 minutes (downloads Legal-BERT model ~400MB)

### Step 3: Start All Services
```cmd
python main.py
```
✅ **Services running on ports**: 8001, 8002, 8003, 8004, 8005

### Step 4: Verify (Open New Terminal)
```cmd
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

### Step 5: Test Embedding
```cmd
curl -X POST http://localhost:8001/embed/text -H "Content-Type: application/json" -d "{\"text\": \"The Court holds that...\"}"
```

---

## 🎯 What Each Service Does

| Port | Service | Purpose |
|------|---------|---------|
| 8001 | Embedding | Converts text to Legal-BERT vectors (768-dim) |
| 8002 | Ingestion | Uploads & processes PDF case law documents |
| 8003 | Search | Semantic search across case law database |
| 8004 | Prediction | Predicts outcomes (Affirmed/Reversed/Remanded) |
| 8005 | Opinion | Generates Per Curiam opinions with RAG |

---

## 📝 Common Operations

### Upload a Case Law PDF
```cmd
curl -X POST http://localhost:8002/ingest/pdf ^
  -F "file=@case.pdf" ^
  -F "case_name=Smith v. Jones"
```

### Search for Similar Cases
```cmd
curl -X POST http://localhost:8003/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"breach of contract\", \"top_k\": 5}"
```

### Predict Case Outcome
```cmd
curl -X POST http://localhost:8004/predict/outcome ^
  -H "Content-Type: application/json" ^
  -d "{\"facts\": \"Landlord failed to repair...\", \"issue\": \"Breach of warranty\"}"
```

### Generate Opinion
```cmd
curl -X POST http://localhost:8005/generate/opinion ^
  -H "Content-Type: application/json" ^
  -d "{\"case_context\": {\"facts\": \"...\", \"issue\": \"...\", \"case_name\": \"Smith v. Jones\", \"petitioner\": \"Smith\", \"respondent\": \"Jones\"}, \"opinion_type\": \"per_curiam\"}"
```

---

## 🧪 Run Tests
```cmd
cd python-services
python run_tests.py
```

---

## 🛑 Stop Everything
```cmd
# Stop Python services: Press Ctrl+C in terminal

# Stop Qdrant
docker stop qdrant-vectors
```

---

## 🔧 Troubleshooting

### Services won't start?
```cmd
# Check if ports are available
netstat -an | findstr "8001 8002 8003 8004 8005"

# Restart Qdrant
docker restart qdrant-vectors
```

### Qdrant connection failed?
```cmd
# Verify Qdrant is running
curl http://localhost:6333/health

# If not, start it
docker start qdrant-vectors
```

### Out of memory?
Add to `.env` file:
```
EMBEDDING_BATCH_SIZE=16
INGESTION_BATCH_SIZE=5
```

---

## 📚 Full Documentation

- **Complete Guide**: `EXECUTION_GUIDE.md`
- **Deployment**: `DEPLOYMENT_GUIDE.md`
- **Testing**: `python-services/TESTING.md`
- **API Reference**: `TASK_11_VERIFICATION.md`

---

## ⚠️ Important Notes

- **First Run**: Legal-BERT model downloads automatically (~400MB, 5-10 min)
- **Requirements**: 8GB+ RAM, 20GB+ disk space
- **Legal Disclaimer**: Research purposes only, not for actual legal advice
- **Keep Terminal Open**: Services run in foreground when using `python main.py`

---

## ✅ System Ready When You See:

```
[MAIN] Starting all services...
[MAIN] Starting Embedding Service on port 8001...
[MAIN] Starting Ingestion Service on port 8002...
[MAIN] Starting Search Service on port 8003...
[MAIN] Starting Prediction Service on port 8004...
[MAIN] Starting Opinion Service on port 8005...
[MAIN] All services started successfully!
```

**Now you're ready to use the Legal LLM Supreme Court System!** 🎉
