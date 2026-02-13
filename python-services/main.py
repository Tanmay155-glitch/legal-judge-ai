"""
Main entry point for all Python services.
This script starts all microservices on their respective ports.
"""

import asyncio
import uvicorn
import multiprocessing
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)


def run_embedding_service():
    """Run embedding service on port 8001"""
    logger.info("Starting Embedding Service on port 8001")
    try:
        import uvicorn
        uvicorn.run(
            "embedding_service.main:app",
            host="0.0.0.0",
            port=8001,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Embedding Service failed: {e}")
        import time
        while True:
            time.sleep(60)


def run_ingestion_service():
    """Run ingestion service on port 8002"""
    logger.info("Starting Ingestion Service on port 8002")
    try:
        import uvicorn
        uvicorn.run(
            "ingestion_service.main:app",
            host="0.0.0.0",
            port=8002,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Ingestion Service failed: {e}")
        import time
        while True:
            time.sleep(60)


def run_search_service():
    """Run search service on port 8003"""
    logger.info("Starting Search Service on port 8003")
    try:
        import uvicorn
        uvicorn.run(
            "search_service.main:app",
            host="0.0.0.0",
            port=8003,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Search Service failed: {e}")
        import time
        while True:
            time.sleep(60)


def run_prediction_service():
    """Run prediction service on port 8004"""
    logger.info("Starting Prediction Service on port 8004")
    try:
        import uvicorn
        uvicorn.run(
            "prediction_service.main:app",
            host="0.0.0.0",
            port=8004,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Prediction Service failed: {e}")
        import time
        while True:
            time.sleep(60)


def run_opinion_service():
    """Run opinion service on port 8005"""
    logger.info("Starting Opinion Service on port 8005")
    try:
        import uvicorn
        uvicorn.run(
            "opinion_service.main:app",
            host="0.0.0.0",
            port=8005,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Opinion Service failed: {e}")
        import time
        while True:
            time.sleep(60)


def main():
    """Start all services using multiprocessing"""
    logger.info("Starting Legal LLM Python Services")
    
    services = [
        ("Embedding Service", run_embedding_service),
        ("Ingestion Service", run_ingestion_service),
        ("Search Service", run_search_service),
        ("Prediction Service", run_prediction_service),
        ("Opinion Service", run_opinion_service),
    ]
    
    processes = []
    
    try:
        for service_name, service_func in services:
            process = multiprocessing.Process(target=service_func, name=service_name)
            process.start()
            processes.append(process)
            logger.info(f"Started {service_name} (PID: {process.pid})")
        
        logger.success("All services started successfully")
        logger.info("Press Ctrl+C to stop all services")
        
        # Wait for all processes
        for process in processes:
            process.join()
            
    except KeyboardInterrupt:
        logger.info("Shutting down all services...")
        for process in processes:
            process.terminate()
            process.join()
        logger.success("All services stopped")


if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()
