# 🚀 Render.com Deployment Quick Start

## Files Created for Deployment ✅

Your project is now ready for Render.com deployment! Here are the files that were added:

1. **`Procfile`** - Tells Render how to run your app
2. **`runtime.txt`** - Specifies Python 3.11.9
3. **`requirements.txt`** (updated) - Added gunicorn and PostgreSQL support
4. **`build.sh`** - Build script for database initialization
5. **`render.yaml`** - Render service configuration
6. **`.env.example`** - Template for environment variables
7. **`RENDER_DEPLOY.md`** - Comprehensive deployment guide

## Quick Deploy Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. Create Render Account
- Sign up at https://render.com

### 3. Create PostgreSQL Database
- Dashboard → New + → PostgreSQL
- Name: `globetrotter-db`
- Plan: **Free**

### 4. Create Web Service
- Dashboard → New + → Web Service
- Connect your GitHub repo
- Name: `globetrotter`
- Build Command: `./build.sh`
- Start Command: `gunicorn app:app`
- Plan: **Free**

### 5. Set Environment Variables

In Render dashboard, go to Environment tab and add:

**Required:**
- `SECRET_KEY` - Click "Generate" button
- `FLASK_ENV` - Set to `production`
- `DATABASE_URL` - Link to your PostgreSQL database
- `SENDGRID_API_KEY` - Get from SendGrid dashboard (see SENDGRID_SETUP.md)
- `SENDGRID_FROM_EMAIL` - Your verified SendGrid sender email

**Optional (for Google OAuth):**
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

**📧 Important**: See `SENDGRID_SETUP.md` for complete email setup instructions!

### 6. Deploy!
- Click "Create Web Service"
- Wait 2-5 minutes for build
- Your app will be live at: `https://your-app-name.onrender.com`

## Important Notes for Free Plan

⚠️ **Free Tier Limitations:**
- App sleeps after 15 min of inactivity
- First request after sleep takes ~30 seconds
- Database expires after 90 days
- 1GB database storage limit
- 100GB bandwidth/month

## SendGrid Email Setup

**WHY SENDGRID?** Render.com blocks external SMTP servers (Gmail, Outlook, etc.). SendGrid uses HTTP API which works perfectly on Render.

**Quick Setup:**
1. Sign up at https://sendgrid.com (free tier: 100 emails/day)
2. Create API key with "Mail Send" permissions
3. Verify sender email address
4. Add `SENDGRID_API_KEY` and `SENDGRID_FROM_EMAIL` to Render environment variables

**📖 Full guide**: Read `SENDGRID_SETUP.md` for step-by-step instructions!

## Need Help?

Read the full deployment guide: **`RENDER_DEPLOY.md`**

## Production Changes Made

Your `app.py` now:
- ✅ Uses environment variables for all sensitive data
- ✅ Supports PostgreSQL (production) and SQLite (local dev)
- ✅ Auto-detects production vs development mode
- ✅ Secure session cookies in production
- ✅ Connection pooling for database
- ✅ Proper error handling

## Testing Locally First

Before deploying, test locally:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run app
python app.py
```

## Troubleshooting

**Build fails?**
- Make build.sh executable: `chmod +x build.sh`
- Check Python version in runtime.txt

**Database errors?**
- Ensure DATABASE_URL is linked to your PostgreSQL database
- Check database is in same region as web service

**Email not working?**
- Check SendGrid API key is valid (starts with `SG.`)
- Verify sender email in SendGrid dashboard
- See troubleshooting in SENDGRID_SETUP.md

---

**Ready to deploy?** Follow the steps above or read `RENDER_DEPLOY.md` for detailed instructions!
