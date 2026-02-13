FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    python-multipart==0.0.9 \
    pytesseract==0.3.10 \
    pdf2image==1.17.0

# SECURITY: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
COPY main.py .

# SECURITY: Set ownership
RUN chown -R appuser:appuser /app

# SECURITY: Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
