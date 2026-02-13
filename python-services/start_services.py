"""
Simple startup script for all Python services
Runs services without multiprocessing to avoid import issues
"""

import sys
import os

# Add parent directory to path to fix imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting Legal LLM Python Services...")
print("=" * 60)
print("Services will start on the following ports:")
print("  - Embedding Service: http://localhost:8001")
print("  - Ingestion Service: http://localhost:8002")
print("  - Search Service: http://localhost:8003")
print("  - Prediction Service: http://localhost:8004")
print("  - Opinion Service: http://localhost:8005")
print("=" * 60)
print("\nStarting Embedding Service on port 8001...")
print("This may take a few minutes on first run (downloading Legal-BERT model)")
print("\nPress Ctrl+C to stop the service")
print("=" * 60)

# Start embedding service only for now
import uvicorn
uvicorn.run(
    "embedding_service.main:app",
    host="0.0.0.0",
    port=8001,
    reload=False,
    log_level="info"
)
