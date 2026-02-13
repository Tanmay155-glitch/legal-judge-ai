# Legal Judge AI (Phase 2)

A production-grade legal AI system that analyzes PDF legal briefs, searches real caselaw, and predicts outcomes/generates opinions.

## 🏗️ Architecture

- **Rust API (`/rust-api`)**: Core orchestration, ML inference (Burn), and business logic.
- **OCR Service (`/ocr-service`)**: Python/FastAPI service for PDF text extraction.
- **Vector DB**: Qdrant (Docker) for searching 10k+ cases.
- **Frontend (`/frontend-v2`)**: React-based UI for uploading briefs and viewing results.

## 🚀 Quick Start

### 1. Start Infrastructure (Vector DB & OCR)
```bash
docker-compose up -d
```
*Alternatively, run Qdrant locally on port 6333.*

### 2. Ingest Data
Load sample cases into the Vector DB:
```bash
pip install -r requirements.txt
python scripts/ingest_vectors.py
```

### 3. Start Rust API
```bash
cd rust-api
cargo run
```
*Server runs on http://localhost:8080*

### 4. Start Frontend
```bash
cd frontend-v2
npm install
npm run dev
```
*UI runs on http://localhost:5173*

## 📂 Project Structure
- `rust-api/`: Axum server + Burn models
- `ocr-service/`: Python PDF processing
- `frontend-v2/`: Web UI
- `scripts/`: Data ingestion & utils
- `docker-compose.yml`: Service orchestration
