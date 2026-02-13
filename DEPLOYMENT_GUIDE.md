# Deployment Guide - Legal LLM Supreme Court System

## Overview

This guide provides comprehensive instructions for deploying the Legal LLM Supreme Court System in various environments.

## Architecture

The system consists of:
- **5 Python Microservices** (Ports 8001-8005)
- **Qdrant Vector Database** (Port 6333)
- **Redis Cache** (Port 6379)
- **OCR Service** (Port 8000)
- **Rust API Gateway** (Port 8080) - Optional

## Prerequisites

### Required
- Docker & Docker Compose
- 8GB+ RAM
- 20GB+ disk space
- Python 3.11+
- CUDA-capable GPU (optional, for faster embeddings)

### Optional
- Rust 1.70+ (for API gateway)
- OpenAI API key (for opinion generation)

## Quick Start (Docker Compose)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd legal-llm-system
```

### 2. Configure Environment Variables

Create `.env` file:

```bash
# Qdrant Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Redis Configuration  
REDIS_HOST=redis
REDIS_PORT=6379
ENABLE_REDIS_CACHE=true

# OCR Service
OCR_SERVICE_URL=http://ocr_service:8000

# LLM Configuration (for opinion generation)
OPENAI_API_KEY=your-api-key-here
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048

# Audit Logging
AUDIT_LOG_DIR=./audit_logs
AUDIT_RETENTION_DAYS=90

# Performance
DEFAULT_TOP_K=10
MIN_SIMILARITY_THRESHOLD=0.6
PREDICTION_TOP_K=20
PREDICTION_CONFIDENCE_THRESHOLD=0.6
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f python_services
```

### 4. Verify Deployment

```bash
# Check Qdrant
curl http://localhost:6333/health

# Check Python services
curl http://localhost:8001/health  # Embedding
curl http://localhost:8002/health  # Ingestion
curl http://localhost:8003/health  # Search
curl http://localhost:8004/health  # Prediction
curl http://localhost:8005/health  # Opinion
```

## Manual Deployment (Without Docker)

### 1. Install Dependencies

```bash
cd python-services
pip install -r requirements.txt
```

### 2. Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant:latest
```

### 3. Start Redis (Optional)

```bash
docker run -p 6379:6379 redis:7-alpine
```

### 4. Start Python Services

```bash
cd python-services
python main.py
```

This starts all 5 services on ports 8001-8005.

## Service Endpoints

### Embedding Service (Port 8001)
- `GET /health` - Health check
- `GET /model/info` - Model information
- `POST /embed/text` - Single text embedding
- `POST /embed/batch` - Batch embedding
- `POST /embed/sections` - Section embedding

### Ingestion Service (Port 8002)
- `GET /health` - Health check
- `GET /stats` - Ingestion statistics
- `POST /ingest/pdf` - Upload PDF
- `POST /ingest/batch` - Batch ingestion
- `DELETE /documents/{id}` - Delete document

### Search Service (Port 8003)
- `GET /health` - Health check
- `GET /stats` - Search statistics
- `POST /search` - Semantic search
- `POST /search/facts` - Facts search
- `POST /search/reasoning` - Reasoning search

### Prediction Service (Port 8004)
- `GET /health` - Health check
- `GET /stats` - Prediction statistics
- `POST /predict/outcome` - Predict outcome
- `POST /predict/batch` - Batch prediction

### Opinion Service (Port 8005)
- `GET /health` - Health check
- `GET /stats` - Generation statistics
- `POST /generate/opinion` - Generate opinion
- `GET /templates/{type}` - Get template

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | localhost | Qdrant host |
| `QDRANT_PORT` | 6333 | Qdrant port |
| `REDIS_HOST` | localhost | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `ENABLE_REDIS_CACHE` | false | Enable Redis caching |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `LLM_MODEL` | gpt-4 | LLM model name |
| `LLM_TEMPERATURE` | 0.3 | Generation temperature |
| `AUDIT_LOG_DIR` | ./audit_logs | Audit log directory |
| `AUDIT_RETENTION_DAYS` | 90 | Log retention period |

### Service URLs

When running in Docker, services communicate via container names:
- `http://qdrant:6333`
- `http://redis:6379`
- `http://ocr_service:8000`
- `http://python_services:8001-8005`

When running locally, use localhost:
- `http://localhost:6333`
- `http://localhost:6379`
- `http://localhost:8000`
- `http://localhost:8001-8005`

## Data Ingestion

### Upload Single PDF

```bash
curl -X POST http://localhost:8002/ingest/pdf \
  -F "file=@case.pdf" \
  -F "case_name=Smith v. Jones"
```

### Batch Ingestion

```bash
curl -X POST http://localhost:8002/ingest/batch \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/pdfs",
    "batch_size": 10
  }'
```

## Usage Examples

### Semantic Search

```bash
curl -X POST http://localhost:8003/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "breach of warranty of habitability",
    "top_k": 10,
    "min_similarity": 0.6
  }'
```

### Outcome Prediction

```bash
curl -X POST http://localhost:8004/predict/outcome \
  -H "Content-Type: application/json" \
  -d '{
    "facts": "The landlord failed to repair the heating system...",
    "issue": "Whether the landlord breached the warranty of habitability"
  }'
```

### Opinion Generation

```bash
curl -X POST http://localhost:8005/generate/opinion \
  -H "Content-Type: application/json" \
  -d '{
    "case_context": {
      "facts": "The landlord failed to repair...",
      "issue": "Whether the landlord breached...",
      "case_name": "Smith v. Jones",
      "petitioner": "Smith",
      "respondent": "Jones"
    },
    "opinion_type": "per_curiam",
    "max_precedents": 5
  }'
```

## Monitoring

### Check Service Health

```bash
# All services
for port in 8001 8002 8003 8004 8005; do
  echo "Port $port:"
  curl -s http://localhost:$port/health | jq
done
```

### View Statistics

```bash
# Ingestion stats
curl http://localhost:8002/stats | jq

# Search stats
curl http://localhost:8003/stats | jq

# Prediction stats
curl http://localhost:8004/stats | jq

# Opinion stats
curl http://localhost:8005/stats | jq
```

### View Logs

```bash
# Docker logs
docker-compose logs -f python_services

# Local logs
tail -f python-services/logs/*.log
```

## Performance Tuning

### Caching

Enable Redis for better performance:

```bash
export ENABLE_REDIS_CACHE=true
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

### GPU Acceleration

For faster embeddings, ensure CUDA is available:

```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# The embedding service will automatically use GPU if available
```

### Batch Processing

Optimize batch sizes:

```bash
# Embedding batch size (default: 32)
export EMBEDDING_BATCH_SIZE=64

# Ingestion batch size (default: 10)
export INGESTION_BATCH_SIZE=20
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs python_services

# Check dependencies
docker-compose ps

# Restart services
docker-compose restart python_services
```

### Qdrant Connection Failed

```bash
# Check Qdrant is running
curl http://localhost:6333/health

# Check network
docker network inspect legal-llm-system_default
```

### Out of Memory

```bash
# Reduce batch sizes
export EMBEDDING_BATCH_SIZE=16
export INGESTION_BATCH_SIZE=5

# Limit cache sizes
export CACHE_MAX_SIZE=500
```

### Slow Performance

```bash
# Enable Redis caching
export ENABLE_REDIS_CACHE=true

# Increase batch sizes (if memory allows)
export EMBEDDING_BATCH_SIZE=64

# Use GPU for embeddings
# Ensure CUDA is available
```

## Security Considerations

### API Keys

- Store API keys in `.env` file (not in code)
- Use environment variables for sensitive data
- Rotate keys regularly

### Network Security

- Use firewall rules to restrict access
- Enable HTTPS in production
- Use authentication for API endpoints

### Data Privacy

- Audit logs contain user queries
- Implement data retention policies
- Comply with privacy regulations

## Backup and Recovery

### Backup Qdrant Data

```bash
# Backup vector database
docker-compose exec qdrant tar -czf /tmp/qdrant-backup.tar.gz /qdrant/storage
docker cp qdrant-vectors:/tmp/qdrant-backup.tar.gz ./backups/
```

### Backup Audit Logs

```bash
# Backup audit logs
tar -czf audit-logs-backup.tar.gz audit_logs/
```

### Restore

```bash
# Restore Qdrant
docker cp ./backups/qdrant-backup.tar.gz qdrant-vectors:/tmp/
docker-compose exec qdrant tar -xzf /tmp/qdrant-backup.tar.gz -C /
docker-compose restart qdrant
```

## Scaling

### Horizontal Scaling

For high-traffic deployments:

1. **Load Balancer**: Use Nginx or HAProxy
2. **Multiple Instances**: Run multiple Python service containers
3. **Shared Cache**: Use Redis cluster
4. **Shared Storage**: Use network-attached storage for Qdrant

### Vertical Scaling

- Increase container memory limits
- Use larger GPU for embeddings
- Increase Qdrant memory allocation

## Production Checklist

- [ ] Configure environment variables
- [ ] Set up HTTPS/TLS
- [ ] Enable authentication
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Configure backup schedule
- [ ] Test disaster recovery
- [ ] Review audit log retention
- [ ] Load test the system
- [ ] Document runbooks

## Support

For issues and questions:
- Check logs: `docker-compose logs`
- Review documentation
- Check GitHub issues
- Contact system administrators

---

**Remember**: This system is for research and academic purposes only. Do not use for actual legal proceedings or advice.
