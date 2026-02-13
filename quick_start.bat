@echo off
echo ================================================================================
echo Legal Judge AI - Quick Start
echo ================================================================================
echo.
echo Starting all services...
echo.

REM Start OCR Service
echo Starting OCR Service (Port 8000)...
start "OCR Service" cmd /k "cd ocr-service && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak > nul

REM Start Orchestrator
echo Starting Orchestrator API (Port 8080)...
start "Orchestrator API" cmd /k "cd python-services && python orchestrator_api.py"
timeout /t 2 /nobreak > nul

REM Start Embedding Service
echo Starting Embedding Service (Port 8001)...
start "Embedding Service" cmd /k "cd python-services && python -m uvicorn embedding_service.main:app --host 0.0.0.0 --port 8001"
timeout /t 2 /nobreak > nul

REM Start Ingestion Service
echo Starting Ingestion Service (Port 8002)...
start "Ingestion Service" cmd /k "cd python-services && python -m uvicorn ingestion_service.main:app --host 0.0.0.0 --port 8002"
timeout /t 2 /nobreak > nul

REM Start Search Service
echo Starting Search Service (Port 8003)...
start "Search Service" cmd /k "cd python-services && python -m uvicorn search_service.main:app --host 0.0.0.0 --port 8003"
timeout /t 2 /nobreak > nul

REM Start Prediction Service
echo Starting Prediction Service (Port 8004)...
start "Prediction Service" cmd /k "cd python-services && python -m uvicorn prediction_service.main:app --host 0.0.0.0 --port 8004"
timeout /t 2 /nobreak > nul

REM Start Opinion Service
echo Starting Opinion Service (Port 8005)...
start "Opinion Service" cmd /k "cd python-services && python -m uvicorn opinion_service.main:app --host 0.0.0.0 --port 8005"
timeout /t 2 /nobreak > nul

REM Start Frontend
echo Starting Frontend (Port 5173)...
start "Frontend" cmd /k "cd frontend-v2 && npm run dev"

echo.
echo ================================================================================
echo All services started!
echo ================================================================================
echo.
echo Service URLs:
echo   - Frontend:          http://localhost:5173
echo   - Orchestrator API:  http://localhost:8080
echo   - OCR Service:       http://localhost:8000
echo   - Embedding Service: http://localhost:8001
echo   - Ingestion Service: http://localhost:8002
echo   - Search Service:    http://localhost:8003
echo   - Prediction Service: http://localhost:8004
echo   - Opinion Service:   http://localhost:8005
echo.
echo Wait 30 seconds for all services to initialize, then run:
echo   python test_complete_system.py
echo.
echo Press any key to exit (services will continue running)...
pause > nul
