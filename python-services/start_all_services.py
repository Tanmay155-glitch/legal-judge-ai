"""
Start all Python services individually
This script starts each service in a separate process with proper Python path setup
"""

import sys
import os
import subprocess
import time

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=" * 80)
print("Legal LLM Supreme Court System - Starting All Services")
print("=" * 80)
print()

services = [
    ("Embedding Service", 8001, "embedding_service.main:app"),
    ("Ingestion Service", 8002, "ingestion_service.main:app"),
    ("Search Service", 8003, "search_service.main:app"),
    ("Prediction Service", 8004, "prediction_service.main:app"),
    ("Opinion Service", 8005, "opinion_service.main:app"),
]

processes = []

print("Starting services...")
print()

for service_name, port, app_path in services:
    print(f"Starting {service_name} on port {port}...")
    
    # Start each service in a new PowerShell window
    cmd = [
        "powershell",
        "-NoExit",
        "-Command",
        f"cd '{current_dir}'; python -m uvicorn {app_path} --host 0.0.0.0 --port {port}"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=current_dir
        )
        processes.append((service_name, process))
        print(f"  ✓ {service_name} started (PID: {process.pid})")
        time.sleep(1)  # Small delay between starts
    except Exception as e:
        print(f"  ✗ Failed to start {service_name}: {e}")

print()
print("=" * 80)
print(f"All services started! {len(processes)} services running.")
print("=" * 80)
print()
print("Service URLs:")
for service_name, port, _ in services:
    print(f"  • {service_name}: http://localhost:{port}")
print()
print("Health check endpoints:")
for service_name, port, _ in services:
    print(f"  • {service_name}: http://localhost:{port}/health")
print()
print("=" * 80)
print("Press Ctrl+C to stop monitoring (services will continue running)")
print("To stop services, close their individual windows or use Task Manager")
print("=" * 80)

try:
    # Keep script running
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nMonitoring stopped. Services are still running in separate windows.")
