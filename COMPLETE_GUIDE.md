# Django Domain Intelligence Platform - Complete Guide

**Last Updated:** 2026-02-13

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [API Reference](#api-reference)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## System Overview

This platform scrapes websites, generates AI-powered business intelligence reports, creates PDFs, and provides sales training modules.

### Architecture Flow

```
Client Request → Django API → Celery Task → Firecrawl Scraping →
LLM Analysis → PDF Generation → R2 Upload → Training Generation → Complete
```

### Tech Stack
- **Django 6.0.2** - REST API framework
- **Celery 5.6.2** - Async task processing
- **Redis** - Message broker
- **Firecrawl API** - Web scraping (with BeautifulSoup fallback)
- **OpenAI/Anthropic** - LLM for business intelligence
- **ReportLab** - PDF generation
- **Cloudflare R2** - File storage (S3-compatible)
- **PostgreSQL** - Database

### Status Flow
- `pending` → Task queued, waiting for Celery
- `scraping` → Firecrawl is scraping the website
- `analyzing` → LLM is generating business intelligence
- `completed` → All done, PDF and JSON ready
- `failed` → Error occurred (check error_message field)

---

## Quick Start

### Prerequisites
```bash
# 1. Install Redis (required for Celery)
brew install redis
brew services start redis

# 2. Verify Redis is running
redis-cli ping  # Should return "PONG"

# 3. Install Python dependencies (if not done)
pip3 install -r requirements.txt
```

### Configuration

Edit `.env` file and add your LLM API key:

**Option A: OpenAI (Recommended)**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

**Option B: Anthropic Claude**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Running the System

**Terminal 1: Django Server**
```bash
cd /Users/pavankumarnaikmude/development/scraping
python3 manage.py runserver
```

**Terminal 2: Celery Worker (REQUIRED)**
```bash
cd /Users/pavankumarnaikmude/development/scraping
celery -A config worker -l info
```

**Keep both terminals running!**

---

## Configuration

### Current Setup (Already Configured)

```env
# Database
DB_NAME=domain_intelligence
DB_USER=pavankumarnaikmude
DB_HOST=localhost

# Cloudflare R2 Storage
R2_ENDPOINT=https://knvkdjnvkejdnvkdjnv
R2_BUCKET_NAME=first_app
R2_ACCESS_KEY_ID=svnjdbvdjbsj

# Firecrawl API
FIRECRAWL_API_KEY=vkjdnvkjenvkednvkdnviej
SCRAPING_PROVIDER=firecrawl

# Celery + Redis
CELERY_BROKER_URL=redis://localhost/0000/1
CELERY_RESULT_BACKEND=redis://localhost:0000/0
```

### What You Need to Add

Only the LLM API key is missing. Add ONE of these to `.env`:

```env
# For OpenAI
OPENAI_API_KEY=your-key-here

# OR for Anthropic
ANTHROPIC_API_KEY=your-key-here
```

---

## API Reference

Base URL: `http://localhost:0000/api`

### 1. Create Analysis

**POST** `/analyses/create_analysis/`

Creates a new domain analysis and starts async processing.

**Request:**
```json
{
  "domain_name": "shopify.com"
}
```

**Response (201 Created):**
```json
{
  "message": "Domain analysis initiated successfully",
  "analysis": {
    "id": 1,
    "domain_name": "shopify.com",
    "status": "pending",
    "created_at": "2026-02-13T10:00:00Z"
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/analyses/create_analysis/ \
  -H "Content-Type: application/json" \
  -d '{"domain_name": "shopify.com"}'
```

---

### 2. Check Status

**GET** `/analyses/{id}/status_check/`

Check the current processing status.

**Response:**
```json
{
  "id": 1,
  "domain_name": "shopify.com",
  "status": "analyzing",
  "progress": "Processing business intelligence...",
  "created_at": "2026-02-13T10:00:00Z",
  "updated_at": "2026-02-13T10:01:30Z"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/analyses/1/status_check/
```

---

### 3. Get Analysis Details

**GET** `/analyses/{id}/`

Get complete analysis with all data (once status = "completed").

**Response:**
```json
{
  "id": 1,
  "domain_name": "shopify.com",
  "status": "completed",
  "scraped_data": {
    "main_page": {
      "title": "Shopify - E-commerce Platform",
      "description": "...",
      "content": "Full markdown content...",
      "metadata": {...}
    },
    "additional_pages": [...]
  },
  "business_intelligence": {
    "executive_summary": "...",
    "market_analysis": "...",
    "product_offerings": "...",
    "target_audience": "...",
    "competitive_advantages": "...",
    "sales_strategies": "...",
    "objection_handling": "...",
    "key_metrics": "...",
    "growth_opportunities": "...",
    "risk_assessment": "...",
    "recommendations": "..."
  },
  "pdf_url": "https://...r2.cloudflarestorage.com/.../shopify_com_report.pdf",
  "json_url": "https://...r2.cloudflarestorage.com/.../shopify_com_data.json",
  "training_modules": [
    {
      "id": 1,
      "module_type": "objection_handling",
      "content": "...",
      "created_at": "2026-02-13T10:02:00Z"
    },
    {
      "id": 2,
      "module_type": "product_knowledge",
      "content": "...",
      "created_at": "2026-02-13T10:02:00Z"
    },
    {
      "id": 3,
      "module_type": "pitch_strategy",
      "content": "...",
      "created_at": "2026-02-13T10:02:00Z"
    },
    {
      "id": 4,
      "module_type": "competitor_analysis",
      "content": "...",
      "created_at": "2026-02-13T10:02:00Z"
    }
  ],
  "created_at": "2026-02-13T10:00:00Z",
  "updated_at": "2026-02-13T10:02:00Z",
  "completed_at": "2026-02-13T10:02:00Z"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/analyses/1/
```

---

### 4. Download PDF

**GET** `/analyses/{id}/download_pdf/`

Get the PDF download URL.

**Response:**
```json
{
  "pdf_url": "https://fd3df45349eb5c03b50e521ad52f88e8.r2.cloudflarestorage.com/dev-hymu/domain-intelligence/2026/02/13/shopify_com_report.pdf"
}
```

---

### 5. Download JSON

**GET** `/analyses/{id}/download_json/`

Get the JSON data download URL.

**Response:**
```json
{
  "json_url": "https://fd3df45349eb5c03b50e521ad52f88e8.r2.cloudflarestorage.com/dev-hymu/domain-intelligence/2026/02/13/shopify_com_data.json"
}
```

---

### 6. Get Training Modules

**GET** `/analyses/{id}/training_modules/`

Get all sales training modules for the analysis.

**Response:**
```json
{
  "domain_name": "shopify.com",
  "training_modules": [
    {
      "id": 1,
      "module_type": "objection_handling",
      "title": "Handling Customer Objections",
      "content": "Detailed training content...",
      "created_at": "2026-02-13T10:02:00Z"
    },
    {
      "id": 2,
      "module_type": "product_knowledge",
      "title": "Product Deep Dive",
      "content": "Detailed training content...",
      "created_at": "2026-02-13T10:02:00Z"
    },
    {
      "id": 3,
      "module_type": "pitch_strategy",
      "title": "Sales Pitch Strategy",
      "content": "Detailed training content...",
      "created_at": "2026-02-13T10:02:00Z"
    },
    {
      "id": 4,
      "module_type": "competitor_analysis",
      "title": "Competitive Intelligence",
      "content": "Detailed training content...",
      "created_at": "2026-02-13T10:02:00Z"
    }
  ]
}
```

---

### 7. List All Analyses

**GET** `/analyses/`

Get paginated list of all analyses.

**Response:**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/analyses/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "domain_name": "shopify.com",
      "status": "completed",
      "created_at": "2026-02-13T10:00:00Z"
    },
    ...
  ]
}
```

---

## Testing

### Complete Workflow Test

**Step 1: Add LLM API Key**
```bash
# Edit .env file
nano .env

# Add your OpenAI or Anthropic API key
```

**Step 2: Start Celery Worker**
```bash
# Open new terminal
cd /Users/pavankumarnaikmude/development/scraping
celery -A config worker -l info

# Keep this running!
```

**Step 3: Create Analysis**
```bash
curl -X POST http://localhost:8000/api/analyses/create_analysis/ \
  -H "Content-Type: application/json" \
  -d '{"domain_name": "shopify.com"}'
```

Save the `id` from response (e.g., 1)

**Step 4: Monitor Progress**
```bash
# Check every 5 seconds
watch -n 5 'curl -s http://localhost:8000/api/analyses/1/status_check/ | jq'

# Or manually
curl http://localhost:8000/api/analyses/1/status_check/
```

Expected status progression:
- `pending` (1-2 seconds)
- `scraping` (10-30 seconds)
- `analyzing` (30-60 seconds)
- `completed` (done!)

**Step 5: Get Results**
```bash
# Full analysis
curl http://localhost:8000/api/analyses/1/ | jq

# PDF URL
curl http://localhost:8000/api/analyses/1/download_pdf/ | jq

# Training modules
curl http://localhost:8000/api/analyses/1/training_modules/ | jq
```

---

### Python Test Script

Save as `test_api.py`:

```python
import requests
import time

API_BASE = "http://localhost:8000/api"

print("Creating analysis for shopify.com...")
response = requests.post(
    f"{API_BASE}/analyses/create_analysis/",
    json={"domain_name": "shopify.com"}
)

if response.status_code != 201:
    print(f"Error: {response.text}")
    exit(1)

analysis_id = response.json()["analysis"]["id"]
print(f"✓ Created analysis {analysis_id}")

print("\nMonitoring progress...")
while True:
    response = requests.get(
        f"{API_BASE}/analyses/{analysis_id}/status_check/"
    )
    data = response.json()

    status = data['status']
    print(f"  Status: {status}")

    if status == "completed":
        print("\n✓ Analysis completed!")

        # Get results
        response = requests.get(f"{API_BASE}/analyses/{analysis_id}/")
        result = response.json()

        print(f"\nResults:")
        print(f"  PDF: {result.get('pdf_url', 'Not available')}")
        print(f"  JSON: {result.get('json_url', 'Not available')}")
        print(f"  Training Modules: {len(result.get('training_modules', []))}")
        break

    elif status == "failed":
        print(f"\n✗ Analysis failed: {data.get('error_message', 'Unknown error')}")
        break

    time.sleep(5)
```

Run it:
```bash
python3 test_api.py
```

---

## Troubleshooting

### Issue: Analysis Stuck in "pending" Status

**Cause:** Celery worker not running

**Fix:**
```bash
# Check if Celery is running
ps aux | grep celery

# Start Celery worker in new terminal
celery -A config worker -l info
```

---

### Issue: "Connection refused" to Redis

**Fix:**
```bash
# Check if Redis is running
redis-cli ping  # Should return "PONG"

# If not running, start it
brew services start redis

# Restart Django server after starting Redis
kill $(lsof -ti:8000)
python3 manage.py runserver
```

---

### Issue: Analysis Fails with "LLM API Error"

**Cause:** LLM API key not configured or invalid

**Fix:**
```bash
# Edit .env file
nano .env

# Add valid API key:
OPENAI_API_KEY=sk-proj-your-valid-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-valid-key-here

# Restart Celery worker
# Press Ctrl+C in Celery terminal
celery -A config worker -l info
```

---

### Issue: "No scraping data" (scraped_data is null)

**Cause:** Task hasn't started or Celery not running

**Check:**
```bash
# 1. Is Celery running?
ps aux | grep celery

# 2. Check Celery logs for errors
# Look at the Celery terminal output

# 3. Check analysis status
curl http://localhost:8000/api/analyses/4/status_check/
```

**Fix:**
- If status is still "pending" → Start Celery worker
- If status is "failed" → Check error_message field
- If Firecrawl fails → System will fallback to BeautifulSoup

---

### Issue: Celery Worker Crashes

**Fix:**
```bash
# Run in debug mode to see errors
celery -A config worker -l debug

# Check for:
# - Missing dependencies
# - Database connection issues
# - Invalid API keys
```

---

### Issue: Database Errors

**Fix:**
```bash
# Check database exists
psql -l | grep domain_intelligence

# If not exists, create it
createdb domain_intelligence

# Re-run migrations
python3 manage.py migrate
```

---

## Performance Notes

- **Firecrawl Scraping:** 10-30 seconds per domain
- **LLM Analysis:** 30-60 seconds (depends on content size)
- **PDF Generation:** 5 seconds
- **R2 Upload:** 2 seconds
- **Total Time:** 1-2 minutes per analysis

---

## System Checklist

- [x] Django server running
- [x] PostgreSQL database connected
- [x] Redis installed and running
- [x] Firecrawl API configured
- [x] Cloudflare R2 configured
- [ ] **LLM API key added** ← YOU NEED THIS
- [ ] **Celery worker running** ← YOU NEED THIS

---

## Current System Status

**What's Working:**
- ✅ Django server (port 8000)
- ✅ PostgreSQL database
- ✅ Redis (port 6379)
- ✅ Firecrawl API
- ✅ Cloudflare R2 storage
- ✅ API endpoints

**What's Missing:**
- ⚠️ LLM API key (add to .env)
- ⚠️ Celery worker (must be running)

**Once you start Celery worker, your pending analysis (ID: 4) will automatically start processing!**

---

## Quick Commands Reference

```bash
# Start Redis
brew services start redis

# Start Django
python3 manage.py runserver

# Start Celery (NEW TERMINAL - REQUIRED!)
celery -A config worker -l info

# Test API
curl http://localhost:8000/api/analyses/

# Create analysis
curl -X POST http://localhost:8000/api/analyses/create_analysis/ \
  -H "Content-Type: application/json" \
  -d '{"domain_name": "shopify.com"}'

# Check status
curl http://localhost:8000/api/analyses/4/status_check/

# Get results
curl http://localhost:8000/api/analyses/4/
```

---

## Your Next Steps

1. **Add LLM API Key** - Edit `.env` and add your OpenAI or Anthropic key
2. **Start Celery Worker** - Open new terminal and run: `celery -A config worker -l info`
3. **Your pending analysis (ID: 4) will automatically start processing!**
4. **Monitor progress** - `curl http://localhost:8000/api/analyses/4/status_check/`

**Your platform is ready! Just start the Celery worker!** 🚀
