# 🔒 Git Cleanup Script - Remove Sensitive Files

## Problem
GitHub detected hardcoded secrets in your repository and blocked the push.

## Files with Secrets (Now Fixed)
- ✅ `app.py` - Removed hardcoded OAuth credentials
- ✅ `app_temp.py` - Removed hardcoded OAuth credentials  
- ⚠️ `client_secret_*.json` - Needs to be removed from git history

## Solution: Clean Git History

Run these commands in PowerShell to remove sensitive files from git:

```powershell
# 1. Remove the client secret file from git tracking
git rm --cached client_secret_657875905172-ece6kufs2fn5cvmttp8vc58vslles45n.apps.googleusercontent.com.json

# 2. Make sure it's ignored
# (Already added to .gitignore)

# 3. Commit the changes
git add .
git commit -m "Remove hardcoded secrets and sensitive files"

# 4. Push to GitHub
git push origin main
```

## If Push Still Fails (Clean Git History)

If GitHub still blocks because secrets are in previous commits:

### Option 1: Force Push (Simple but rewrites history)
```powershell
# Remove all commits and start fresh
git checkout --orphan temp_branch
git add -A
git commit -m "Initial commit - production ready"
git branch -D main
git branch -m main
git push -f origin main
```

### Option 2: Use BFG Repo-Cleaner (Recommended for large repos)
```powershell
# Download BFG from: https://rtyley.github.io/bfg-repo-cleaner/
# Then run:
java -jar bfg.jar --delete-files client_secret_*.json
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force origin main
```

### Option 3: GitHub Web Interface (Easiest)
1. Go to the GitHub URLs provided in the error message
2. Click "Allow" to permit the push (not recommended for real secrets)
3. This is ONLY for test/development - regenerate secrets after!

## After Successful Push

1. **Regenerate OAuth Credentials** (Important!)
   - Go to Google Cloud Console
   - Create NEW OAuth credentials
   - Don't reuse the exposed ones

2. **Set Environment Variables Locally**
   Create `.env` file (already in .gitignore):
   ```
   GOOGLE_CLIENT_ID=your-new-client-id
   GOOGLE_CLIENT_SECRET=your-new-secret
   ```

3. **Set Environment Variables on Render**
   - Dashboard → Your Service → Environment
   - Add GOOGLE_CLIENT_ID
   - Add GOOGLE_CLIENT_SECRET

## Prevention (Already Implemented)

✅ Added to `.gitignore`:
- `client_secret_*.json`
- `.env` files
- `.venv/` directories

✅ Updated code to use environment variables:
- No hardcoded secrets in `app.py`
- No hardcoded secrets in `app_temp.py`

## Quick Start (Recommended)

```powershell
# Clean approach - start fresh
git checkout --orphan clean_branch
git add .
git commit -m "Production-ready deployment setup"
git branch -D main
git branch -m main
git push -f origin main
```

This removes all history and creates a clean repository.

## Verify Before Pushing

```powershell
# Check what will be pushed
git log --oneline

# Check for sensitive files
git ls-files | findstr client_secret

# If empty, you're good!
```

## Need Help?

- GitHub Docs: https://docs.github.com/code-security/secret-scanning
- BFG Tool: https://rtyley.github.io/bfg-repo-cleaner/
- Contact GitHub Support if issues persist
