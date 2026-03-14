# Push to GitHub

Run these commands in your terminal:

```bash
# 1. Navigate to your project folder
cd c:/Users/kaush/Downloads/files

# 2. Initialize git (if not already initialized)
git init

# 3. Add all files
git add .

# 4. Commit
git commit -m "Initial commit: AI SkillSync API"

# 5. Create GitHub repository
gh repo create ai-skillsync --public --source=. --description "AI-powered Learning & Career Intelligence System"

# 6. Push to GitHub
git push -u origin main
```

**Note:** If `gh` (GitHub CLI) is not installed, use:
```bash
# Alternative without GitHub CLI:
git remote add origin https://github.com/skaushikan764-byte/ai-skillsync.git
git branch -M main
git push -u origin main
```

**For first-time GitHub authentication:**
- Create repo manually at: https://github.com/new
- Then run step 6 above
