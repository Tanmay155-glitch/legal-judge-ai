# TLS/HTTPS Setup Guide - Legal LLM Supreme Court System

**Date**: February 9, 2026  
**Purpose**: Enable TLS/HTTPS for secure communication

---

## Overview

This guide covers enabling TLS/HTTPS for all services to fix **VULN-015: No Data Encryption in Transit**.

---

## 1. Generate SSL Certificates

### Option A: Self-Signed Certificates (Development/Testing)

```bash
# Create certificates directory
mkdir -p certs

# Generate private key
openssl genrsa -out certs/server.key 2048

# Generate certificate signing request
openssl req -new -key certs/server.key -out certs/server.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in certs/server.csr \
  -signkey certs/server.key -out certs/server.crt

# Set proper permissions
chmod 600 certs/server.key
chmod 644 certs/server.crt
```

### Option B: Let's Encrypt (Production)

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate for your domain
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

---

## 2. Update Environment Configuration

Add to `.env`:

```bash
# TLS/HTTPS Configuration
ENABLE_HTTPS=true
SSL_CERT_PATH=./certs/server.crt
SSL_KEY_PATH=./certs/server.key

# Force HTTPS redirects
FORCE_HTTPS=true
```

---

## 3. Update Python Services for HTTPS

### Update main.py to support HTTPS

```python
import os
import uvicorn

# TLS Configuration
ENABLE_HTTPS = os.getenv("ENABLE_HTTPS", "false").lower() == "true"
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "./certs/server.crt")
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", "./certs/server.key")

if __name__ == "__main__":
    # Configure uvicorn with SSL
    config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": 8001,
        "log_level": "info"
    }
    
    if ENABLE_HTTPS:
        config.update({
            "ssl_keyfile": SSL_KEY_PATH,
            "ssl_certfile": SSL_CERT_PATH,
            "ssl_version": 3,  # TLS 1.2+
            "ssl_cert_reqs": 0,  # No client cert required
        })
        print(f"🔒 Starting service with HTTPS on port {config['port']}")
    else:
        print(f"⚠️  Starting service with HTTP on port {config['port']}")
        print("   WARNING: HTTPS is disabled. Enable for production!")
    
    uvicorn.run(**config)
```

---

## 4. Update Docker Compose

```yaml
services:
  python_services:
    build: ./python-services
    container_name: python-services
    ports:
      - "8001:8001"
      - "8002:8002"
      - "8003:8003"
      - "8004:8004"
      - "8005:8005"
    volumes:
      - ./python-services:/app
      - ./certs:/app/certs:ro  # Mount certificates as read-only
    environment:
      # TLS Configuration
      - ENABLE_HTTPS=${ENABLE_HTTPS:-false}
      - SSL_CERT_PATH=/app/certs/server.crt
      - SSL_KEY_PATH=/app/certs/server.key
      - FORCE_HTTPS=${FORCE_HTTPS:-false}
      # ... other environment variables
```

---

## 5. Add HTTPS Redirect Middleware

Create `python-services/shared/https_redirect.py`:

```python
"""
HTTPS Redirect Middleware
Forces HTTPS connections in production
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware to force HTTPS connections"""
    
    def __init__(self, app, force_https: bool = False):
        super().__init__(app)
        self.force_https = force_https
    
    async def dispatch(self, request: Request, call_next):
        # Skip health checks
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Force HTTPS if enabled
        if self.force_https:
            if request.url.scheme != "https":
                # Redirect to HTTPS
                url = request.url.replace(scheme="https")
                return RedirectResponse(url=str(url), status_code=status.HTTP_301_MOVED_PERMANENTLY)
        
        return await call_next(request)


def setup_https_redirect(app, force_https: bool = None):
    """Setup HTTPS redirect middleware"""
    if force_https is None:
        force_https = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    
    if force_https:
        app.add_middleware(HTTPSRedirectMiddleware, force_https=True)
        print("🔒 HTTPS redirect enabled")
```

---

## 6. Update Service Startup

Add to each service's `main.py`:

```python
from shared.https_redirect import setup_https_redirect

# After creating app
app = FastAPI(...)

# Setup HTTPS redirect
setup_https_redirect(app)

# ... rest of middleware setup
```

---

## 7. Testing HTTPS

### Test with curl

```bash
# Test HTTPS connection (self-signed cert)
curl -k https://localhost:8001/health

# Test with certificate verification
curl --cacert certs/server.crt https://localhost:8001/health

# Test HTTP redirect (if FORCE_HTTPS=true)
curl -L http://localhost:8001/health
```

### Test with Python

```python
import requests

# Disable SSL verification for self-signed certs (dev only)
response = requests.get('https://localhost:8001/health', verify=False)
print(response.json())

# With certificate verification (production)
response = requests.get(
    'https://localhost:8001/health',
    verify='certs/server.crt'
)
print(response.json())
```

---

## 8. Update API Client Code

All API calls must use HTTPS:

```python
# Before
url = "http://localhost:8003/search"

# After
url = "https://localhost:8003/search"

# With authentication
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=data, headers=headers, verify=True)
```

---

## 9. Nginx Reverse Proxy (Production Recommended)

For production, use Nginx as a reverse proxy with TLS termination:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Proxy to services
    location /api/search {
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # ... other service proxies
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 10. Certificate Renewal (Let's Encrypt)

### Automatic Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Setup automatic renewal (cron)
sudo crontab -e

# Add this line (runs twice daily)
0 0,12 * * * certbot renew --quiet --post-hook "docker-compose restart python_services"
```

---

## 11. Security Best Practices

### TLS Configuration

1. **Use TLS 1.2 or higher** - Disable older versions
2. **Strong cipher suites** - Use modern, secure ciphers
3. **Perfect Forward Secrecy** - Enable PFS ciphers
4. **HSTS** - Enable HTTP Strict Transport Security
5. **Certificate validation** - Always verify certificates in production

### Certificate Management

1. **Secure private keys** - chmod 600, never commit to git
2. **Regular rotation** - Rotate certificates annually
3. **Monitor expiration** - Set up alerts 30 days before expiry
4. **Backup certificates** - Store securely, encrypted
5. **Use strong key sizes** - Minimum 2048-bit RSA or 256-bit ECC

---

## 12. Troubleshooting

### Common Issues

**Issue**: Certificate verification failed
```bash
# Solution: Add certificate to trusted store or use --cacert
curl --cacert certs/server.crt https://localhost:8001/health
```

**Issue**: Connection refused
```bash
# Solution: Check if HTTPS is enabled and port is correct
# Verify with:
netstat -tlnp | grep 8001
```

**Issue**: Mixed content warnings
```bash
# Solution: Ensure all resources (CSS, JS, API calls) use HTTPS
# Update all URLs to use https://
```

---

## 13. Verification Checklist

- [ ] SSL certificates generated
- [ ] Certificates mounted in Docker containers
- [ ] ENABLE_HTTPS=true in .env
- [ ] Services start with HTTPS
- [ ] Health checks work over HTTPS
- [ ] API calls work with HTTPS
- [ ] HTTP redirects to HTTPS (if FORCE_HTTPS=true)
- [ ] Certificate expiration monitoring setup
- [ ] Documentation updated with HTTPS URLs

---

## 14. Production Deployment

### Pre-Deployment

1. Obtain valid SSL certificate from trusted CA
2. Test certificate with SSL Labs (https://www.ssllabs.com/ssltest/)
3. Configure HSTS with appropriate max-age
4. Setup certificate renewal automation
5. Update all documentation with HTTPS URLs

### Post-Deployment

1. Verify all services accessible via HTTPS
2. Test HTTP to HTTPS redirect
3. Check security headers
4. Monitor certificate expiration
5. Test API functionality

---

## 15. Cost Considerations

- **Let's Encrypt**: Free, automated, 90-day certificates
- **Commercial CA**: $50-500/year, longer validity, better support
- **Wildcard certificates**: $100-300/year, covers all subdomains
- **EV certificates**: $200-1000/year, shows organization name in browser

---

## Summary

Enabling TLS/HTTPS:
1. ✅ Fixes VULN-015 (No data encryption in transit)
2. ✅ Protects against man-in-the-middle attacks
3. ✅ Secures API authentication tokens
4. ✅ Required for production deployment
5. ✅ Improves user trust and SEO

**Status**: Ready to implement  
**Estimated Time**: 2-4 hours  
**Priority**: HIGH - Required for production
