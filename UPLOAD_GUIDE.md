# Upload to GitHub + Deploy to Railway

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `saint-bot` (or any name)
3. Select "Public" or "Private"
4. Click "Create repository"

## Step 2: Upload Files (2 ways)

### Option A: GitHub Web (Easiest)

1. Sa new repo mo, click "uploading an existing file"
2. Drag and drop these files/folders:
   - `bot.py`
   - `requirements.txt`
   - `Procfile`
   - `.gitignore`
   - `cogs/` folder (all .py files inside)
3. Click "Commit changes"

### Option B: Git Command Line

Open terminal sa bot folder mo:

```bash
git init
git add bot.py requirements.txt Procfile .gitignore cogs/
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/saint-bot.git
git push -u origin main
```

## Step 3: Deploy to Railway

1. Go to https://railway.app
2. Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your `saint-bot` repository
6. Click "Deploy"

## Step 4: Add Environment Variable

1. Sa Railway dashboard, click your project
2. Go to "Variables" tab
3. Click "New Variable"
4. Name: `DISCORD_TOKEN`
5. Value: Your bot token (copy from Discord Developer Portal)
6. Click "Add"

## Step 5: Done!

Railway auto-deploys. Wait 1-2 minutes then check bot status:
- Go to "Deployments" tab
- Should show "Healthy" (green)

Your bot is now running 24/7!

---

## Files to Upload (Checklist):

- [ ] bot.py
- [ ] requirements.txt
- [ ] Procfile
- [ ] .gitignore
- [ ] cogs/antilink.py
- [ ] cogs/moderation.py
- [ ] cogs/help.py
- [ ] cogs/utility.py
- [ ] cogs/welcomelogs.py
- [ ] cogs/afk.py
- [ ] cogs/extras.py
- [ ] cogs/admin.py

**DO NOT upload:**
- ❌ .env (has your secret token)
- ❌ data/ folder (will be created fresh)
- ❌ __pycache__/ (junk files)
