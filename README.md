# Domain Intelligence & Sales Training Platform

Django REST API that scrapes websites, generates AI-powered business intelligence reports, creates PDFs, and provides sales training modules.

## Quick Start

```bash
# 1. Add Groq API key to .env (already configured)
# Get free API key at: https://console.groq.com

# 2. Start Redis
brew services start redis

# 3. Start Django (Terminal 1)
python3 manage.py runserver

# 4. Start Celery Worker (Terminal 2 - REQUIRED!)
celery -A config worker -l info

# 5. Test API
curl -X POST http://localhost:8000/api/analyses/create_analysis/ \
  -H "Content-Type: application/json" \
  -d '{"domain_name": "shopify.com"}'
```

## Current Status

**✅ Fully Configured:**
- Django server running (port 8000)
- PostgreSQL database connected
- Redis running (port 6379)
- Firecrawl API configured
- Cloudflare R2 storage configured
- Groq AI configured (free & fast)

**To Start:**
- Start Celery worker: `celery -A config worker -l info`

## Documentation

**📖 [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)** - Complete setup, API reference, troubleshooting

## Key Features

- **Multi-Source Data Collection** - Website + News + LinkedIn + Industry insights
- **Groq AI (Free)** - Llama 3.3 70B powered business intelligence
- **Sales Team Analysis** - AI-powered sales challenges & upskilling recommendations
- **PDF Generation** - Professional formatted reports with enriched data
- **Cloudflare R2 Storage** - S3-compatible file storage with presigned URLs
- **Sales Training** - 4 personalized training modules per analysis
- **Async Processing** - Celery + Redis for background tasks

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyses/create_analysis/` | Create new analysis |
| GET | `/api/analyses/{id}/status_check/` | Check processing status |
| GET | `/api/analyses/{id}/` | Get complete analysis |
| GET | `/api/analyses/{id}/download_pdf/` | Get PDF URL |
| GET | `/api/analyses/{id}/training_modules/` | Get training modules |
| GET | `/api/analyses/` | List all analyses |

## Tech Stack

- Django 6.0.2 + Django REST Framework 3.16.1
- Celery 5.6.2 + Redis (async tasks)
- PostgreSQL (database)
- Firecrawl API (web scraping)
- Groq AI - Llama 3.3 70B (LLM - free & fast)
- ReportLab (PDF generation)
- Cloudflare R2 (S3-compatible storage)

## Troubleshooting

### Analysis Stuck in "pending"
**Problem:** Celery worker not running
```bash
# Start Celery in new terminal
celery -A config worker -l info
```

### No Scraping Data
**Problem:** Task hasn't started
```bash
# Check if Celery is running
ps aux | grep celery
```

### Redis Connection Error
```bash
# Start Redis
brew services start redis
redis-cli ping  # Should return "PONG"
```

## Complete Documentation

See [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) for:
- Full API reference with request/response examples
- Configuration guide
- Testing workflows
- Detailed troubleshooting
- Python test scripts

---

**Your platform is fully configured and ready! Just start the Celery worker and begin analyzing domains.**
