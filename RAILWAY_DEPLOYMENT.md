# Railway Deployment Guide

## Prerequisites
- Railway account: https://railway.app
- This Django project pushed to GitHub

---

## Step-by-Step Deployment

### 1. Create PostgreSQL Database

1. Go to your Railway project dashboard
2. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically provision a PostgreSQL database
4. The database will auto-generate these environment variables:
   - `DATABASE_URL` (this is what Django needs!)
   - `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`

### 2. Deploy Your Django App

1. In your Railway project, click **"+ New"** → **"GitHub Repo"**
2. Select your repository
3. Railway will automatically detect it's a Python app and start building

### 3. Configure Environment Variables

Click on your **web service** → **"Variables"** tab, and add these:

| Variable Name | Example Value | Required? |
|---------------|---------------|-----------|
| `DATABASE_URL` | *Auto-set by PostgreSQL plugin* | ✅ Yes |
| `SECRET_KEY` | `b%#j@0$1@xfw6kr!-8$pcv^a6+3v!n4iqxjccf%0ap(gmr4xp5` | ✅ Yes |
| `DEBUG` | `False` | ✅ Yes |
| `ALLOWED_HOSTS` | `your-app.up.railway.app` | ✅ Yes |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app.up.railway.app` | ✅ Yes |
| `GROQ_API_KEY` | Your Groq API key | ✅ Yes (for LLM) |
| `FIRECRAWL_API_KEY` | Your Firecrawl API key | ✅ Yes (for scraping) |
| `R2_ENDPOINT` | `https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com` | Optional |
| `R2_ACCESS_KEY_ID` | Your R2 access key | Optional |
| `R2_SECRET_ACCESS_KEY` | Your R2 secret key | Optional |
| `R2_BUCKET_NAME` | Your R2 bucket name | Optional |

**Important Notes:**
- Replace `your-app.up.railway.app` with your actual Railway domain (found in "Settings" → "Domains")
- Generate `SECRET_KEY` using: `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DATABASE_URL` should be automatically set when you add the PostgreSQL database

### 4. Verify Database Connection

The PostgreSQL database should be automatically linked to your web service. To verify:

1. Click on your **web service**
2. Go to **"Variables"** tab
3. Confirm `DATABASE_URL` is present and looks like:
   ```
   postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway
   ```

If `DATABASE_URL` is missing:
1. Click **"New Variable"** → **"Add Reference"**
2. Select your PostgreSQL service
3. Choose `DATABASE_URL` from the dropdown

### 5. Deploy!

1. Railway will automatically deploy when you push to GitHub
2. Or manually trigger: **"Deployments"** → **"Deploy"**
3. Watch the build logs for any errors

---

## Common Issues & Solutions

### ❌ Error: "connection to localhost refused"

**Cause:** `DATABASE_URL` is not set

**Solution:**
- Verify PostgreSQL database is added to your project
- Check that `DATABASE_URL` appears in your service variables
- Manually add reference if needed (see Step 4 above)

### ❌ Error: "DisallowedHost"

**Cause:** Your Railway domain is not in `ALLOWED_HOSTS`

**Solution:**
```bash
# Set this environment variable:
ALLOWED_HOSTS=your-app.up.railway.app,localhost
```

### ❌ Error: "CSRF verification failed"

**Cause:** Railway domain not in `CSRF_TRUSTED_ORIGINS`

**Solution:**
```bash
# Set this environment variable:
CSRF_TRUSTED_ORIGINS=https://your-app.up.railway.app
```

### ❌ Error: "Healthcheck failed"

**Cause:** Railway can't reach your app

**Solution:**
- This is now fixed with the health check endpoint at `/`
- Verify your app is binding to `0.0.0.0:$PORT` (Procfile does this)
- Check build logs for startup errors

---

## Optional: Add Redis for Celery

If you need background tasks with Celery:

1. Click **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway auto-generates `REDIS_URL`
3. Add these variables to your web service:
   ```
   CELERY_BROKER_URL=$REDIS_URL
   CELERY_RESULT_BACKEND=$REDIS_URL
   ```
4. Deploy a separate Celery worker service (duplicate your repo, change start command to `celery -A config worker -l info`)

---

## Verify Deployment

Once deployed, test these endpoints:

- Health check: `https://your-app.up.railway.app/` → Should return `{"status": "ok"}`
- Admin panel: `https://your-app.up.railway.app/admin/`
- API: `https://your-app.up.railway.app/api/`

---

## Files Created/Modified for Railway

- ✅ `Procfile` - Tells Railway how to start your app
- ✅ `railway.toml` - Build configuration
- ✅ `requirements.txt` - Added gunicorn, dj-database-url, whitenoise
- ✅ `config/settings.py` - Added DATABASE_URL support, whitenoise, CSRF settings
- ✅ `config/urls.py` - Added health check endpoint at `/`

---

## Local Development Still Works!

The code changes are backwards compatible:
- If `DATABASE_URL` exists → uses it (Railway)
- If not → falls back to `DB_HOST`, `DB_USER`, etc. (local `.env`)

Your local Docker setup continues to work unchanged!
