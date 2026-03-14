# AI SkillSync - Deployment Guide

## Deploy to Render (Free) - Step by Step

### Step 1: Create Render Account
1. Go to https://render.com
2. Click "Sign Up" → Choose "GitHub"
3. Authorize Render to access your GitHub

### Step 2: Create a New Web Service
1. In Render dashboard, click **"New"** → **"Web Service"**
2. Under "Connect a repository", find and select: **`skaushikan764-byte/ai-skillsync`**
3. Click **"Connect"**

### Step 3: Configure These Settings

Fill in these exact values:

| Field | Value |
|-------|-------|
| **Name** | `ai-skillsync` |
| **Environment** | `Python` |
| **Region** | `Oregon (or nearest to you)` |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Free Instance** | ✅ Select the free tier |

### Step 4: Add Environment Variables

In the Render dashboard for your service:

1. Click **"Environment"** tab
2. Click **"Add Environment Variable"**
3. Add these variables:

| Key | Value | Description |
|-----|-------|-------------|
| `DATABASE_URL` | `sqlite:///./skillsync.db` | SQLite database (default) |
| | OR for PostgreSQL: | |
| | `postgresql+psycopg2://user:pass@host/dbname` | Use if you want PostgreSQL |

**Important:** Create a file named `Procfile` (no extension) with:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Note:** No need to set `PYTHON_VERSION` environment variable - Render automatically detects it from `runtime.txt`!

> **Note:** This app works with SQLite (file-based) by default, so you don't need to set up a database server!

### Step 5: Deploy
1. Click **"Create Web Service"** button at the bottom
2. Wait 2-3 minutes for deployment
3. You'll see "Live" status when done ✅
4. Your URL will be: `https://ai-skillsync.onrender.com`

---

## Deploy to Railway

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Click "Login" → Choose "GitHub"
3. Authorize Railway

### Step 2: Deploy
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Search for: `skaushikan764-byte/ai-skillsync`
4. Click **"Deploy"**

### Step 3: Add Environment Variables
1. In your project dashboard, go to **"Variables"** tab
2. Add these:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `sqlite:///./skillsync.db` |
| `PYTHON_VERSION` | `3.11` |

3. Click **"Deploy"** again

### Step 4: Your URL
- Railway will give you a URL like: `https://ai-skillsync.up.railway.app`

---

## Deploy to Heroku

### Step 1: Install Heroku CLI
Download from: https://devcenter.heroku.com/articles/heroku-cli

### Step 2: Login & Create
```bash
heroku login
heroku create ai-skillsync
```

### Step 3: Set Buildpack (Required for Python)
```bash
heroku buildpacks:set heroku/python
```

### Step 4: Add Environment Variables
```bash
heroku config:set DATABASE_URL=sqlite:///./skillsync.db
heroku config:set PYTHON_VERSION=3.11.0.0
```

### Step 5: Deploy
```bash
git push heroku main
```

### Step 6: Open App
```bash
heroku open
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///./skillsync.db` | Database connection string |
| `PYTHON_VERSION` | No | `3.11.0` | Python version to use |

### Database Options:
- **SQLite** (default - no setup needed): `sqlite:///./skillsync.db`
- **PostgreSQL**: `postgresql+psycopg2://username:password@host:port/databasename`
- **MySQL**: `mysql+pymysql://username:password@host:port/databasename`

---

## Local Development

Run locally:
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Visit: http://localhost:8000

---

## Troubleshooting

**Build fails?**
- Make sure `requirements.txt` is in the root
- Check Python version (use Python 3.11+)

**App crashes?**
- Check logs in Render/Railway/Heroku dashboard
- Make sure `main:app` matches your FastAPI instance name
- Verify environment variables are set correctly

**Database issues?**
- For SQLite: ensure the app has write permissions
- For PostgreSQL/MySQL: verify connection string is correct
