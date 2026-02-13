"""
Complete System Startup Script
Starts all services needed for the Legal Judge AI system
"""

import subprocess
import time
import sys
import os

print("=" * 80)
print("Legal Judge AI - Complete System Startup")
print("=" * 80)
print()

services = [
    {
        "name": "OCR Service",
        "port": 8000,
        "command": "python -m uvicorn main:app --host 0.0.0.0 --port 8000",
        "cwd": "ocr-service"
    },
    {
        "name": "Orchestrator API",
        "port": 8080,
        "command": "python orchestrator_api.py",
        "cwd": "python-services"
    },
    {
        "name": "Embedding Service",
        "port": 8001,
        "command": "python -m uvicorn embedding_service.main:app --host 0.0.0.0 --port 8001",
        "cwd": "python-services"
    },
    {
        "name": "Ingestion Service",
        "port": 8002,
        "command": "python -m uvicorn ingestion_service.main:app --host 0.0.0.0 --port 8002",
        "cwd": "python-services"
    },
    {
        "name": "Search Service",
        "port": 8003,
        "command": "python -m uvicorn search_service.main:app --host 0.0.0.0 --port 8003",
        "cwd": "python-services"
    },
    {
        "name": "Prediction Service",
        "port": 8004,
        "command": "python -m uvicorn prediction_service.main:app --host 0.0.0.0 --port 8004",
        "cwd": "python-services"
    },
    {
        "name": "Opinion Service",
        "port": 8005,
        "command": "python -m uvicorn opinion_service.main:app --host 0.0.0.0 --port 8005",
        "cwd": "python-services"
    }
]

processes = []

print("Starting all services...")
print()

for service in services:
    print(f"Starting {service['name']} on port {service['port']}...")
    
    cmd = [
        "powershell",
        "-NoExit",
        "-Command",
        f"cd '{service['cwd']}'; {service['command']}"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=os.path.abspath(service['cwd'])
        )
        processes.append((service['name'], process))
        print(f"  ✓ {service['name']} started (PID: {process.pid})")
        time.sleep(1)
    except Exception as e:
        print(f"  ✗ Failed to start {service['name']}: {e}")

print()
print("=" * 80)
print(f"All services started! {len(processes)} services running.")
print("=" * 80)
print()
print("Service URLs:")
for service in services:
    print(f"  • {service['name']}: http://localhost:{service['port']}")
print()
print("Frontend: http://localhost:5173 (start separately with: cd frontend-v2 && npm run dev)")
print()
print("=" * 80)
print("Press Ctrl+C to stop monitoring (services will continue running)")
print("To stop services, close their individual windows or use Task Manager")
print("=" * 80)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nMonitoring stopped. Services are still running in separate windows.")
