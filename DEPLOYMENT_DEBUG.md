# Railway Deployment Debugging Guide

## Current Status

Your app is failing at the **healthcheck** stage. Migrations run successfully, but gunicorn crashes silently.

## Changes Made to Debug

### 1. **start.sh** - Verbose startup script
- Shows all environment variables (safely)
- Tests Django configuration
- Tests WSGI application loading
- Runs gunicorn with verbose logging

### 2. **test_wsgi.py** - WSGI test script
- Verifies Django can load the WSGI application
- Shows detailed error if loading fails

### 3. **Procfile & railway.toml** - Updated to use start.sh
- Now uses `bash start.sh` instead of inline commands
- Will show detailed logs of what's happening

## Next Steps

### 1. Push Changes to Railway

```bash
git add Procfile railway.toml start.sh test_wsgi.py DEPLOYMENT_DEBUG.md
git commit -m "Add verbose logging for Railway deployment debugging"
git push origin main
```

### 2. Watch the Deployment Logs

After pushing, go to Railway:
1. Click on your web service
2. Go to **"Deployments"** tab
3. Click on the latest deployment
4. Watch the **"Deploy"** tab logs

### 3. Look for These Messages

**✅ If everything works:**
```
==== Railway Deployment Start ====
PORT: 8000
DATABASE_URL exists: YES
...
==== Testing WSGI Application ====
✅ SUCCESS: WSGI application loaded successfully
...
==== Starting Gunicorn on port 8000 ====
[INFO] Listening at: http://0.0.0.0:8000
```

**❌ If it fails, you'll see:**
```
==== Testing WSGI Application ====
❌ FAILED: <error message here>
```

This will tell us exactly what's wrong!

## Common Issues We're Testing For

### 1. Missing SECRET_KEY
**Symptom:** `ImproperlyConfigured: The SECRET_KEY setting must not be empty`
**Fix:** Add `SECRET_KEY` to Railway variables

### 2. Invalid ALLOWED_HOSTS
**Symptom:** `CommandError: System check identified some issues`
**Fix:** Set `ALLOWED_HOSTS=web-scraping-ai-development.up.railway.app` in Railway

### 3. Missing Required API Keys
**Symptom:** App crashes when trying to import modules that need API keys
**Fix:** Add `GROQ_API_KEY` and `FIRECRAWL_API_KEY` to Railway

### 4. WSGI Import Error
**Symptom:** `ModuleNotFoundError: No module named 'config'`
**Fix:** Check Dockerfile WORKDIR and Python path

### 5. Port Binding Issue
**Symptom:** Gunicorn starts but healthcheck fails
**Fix:** Verify `$PORT` environment variable is set by Railway

## Current Railway Variables (Should Have)

```bash
# Database (auto-set by PostgreSQL plugin)
DATABASE_URL=postgresql://postgres:...

# Django
SECRET_KEY=<generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
ALLOWED_HOSTS=web-scraping-ai-development.up.railway.app
CSRF_TRUSTED_ORIGINS=https://web-scraping-ai-development.up.railway.app

# APIs
GROQ_API_KEY=<your key>
FIRECRAWL_API_KEY=<your key>

# Optional (for R2 storage)
R2_ENDPOINT=<your R2 endpoint>
R2_ACCESS_KEY_ID=<your key>
R2_SECRET_ACCESS_KEY=<your secret>
R2_BUCKET_NAME=<your bucket>
```

## After Deployment Succeeds

Once you see `Listening at: http://0.0.0.0:XXXX` in the logs:

1. **Test the health endpoint:**
   ```bash
   curl https://web-scraping-ai-development.up.railway.app/
   ```
   Should return: `{"status": "ok"}`

2. **Test the admin:**
   ```
   https://web-scraping-ai-development.up.railway.app/admin/
   ```

3. **Test the API:**
   ```
   https://web-scraping-ai-development.up.railway.app/api/
   ```

## Troubleshooting Commands

### Check if Django can start locally with Railway-like config:
```bash
export DEBUG=False
export SECRET_KEY=test-key
export ALLOWED_HOSTS=localhost
python manage.py check --deploy
```

### Test WSGI loading:
```bash
python test_wsgi.py
```

### Test gunicorn locally:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --log-level debug
```

## What to Share If Still Failing

If deployment still fails after these changes, share:

1. **Full deploy logs** (from "Starting Container" to the end)
2. **Screenshot of Railway Variables tab** (blur sensitive values)
3. **The specific error message** from the logs

---

**These changes will give us detailed logs showing exactly where the deployment is failing!**
