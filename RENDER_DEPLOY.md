# Deploying GlobeTrotter to Render.com (Free Plan)

This guide will help you deploy your GlobeTrotter Flask application to Render.com's free tier.

## Prerequisites

- A GitHub account
- A Render.com account (sign up at https://render.com)
- Your code pushed to a GitHub repository
- Gmail account for email functionality
- Google Cloud Console account for OAuth (optional)

## Step 1: Prepare Your Repository

Make sure all deployment files are committed to your repository:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

Required files (already created):
- ✅ `Procfile` - Tells Render how to start the app
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version
- ✅ `build.sh` - Build script for database setup
- ✅ `render.yaml` - Render configuration
- ✅ `.env.example` - Environment variable template

## Step 2: Create Database on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `globetrotter-db`
   - **Database**: `globetrotter`
   - **User**: `globetrotter`
   - **Region**: Choose closest to you
   - **Plan**: **Free**
4. Click **"Create Database"**
5. Wait for database to provision (~2 minutes)
6. Copy the **Internal Database URL** (you'll need this)

## Step 3: Create Web Service on Render

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure the service:

### Basic Configuration
- **Name**: `globetrotter` (or your preferred name)
- **Region**: Same as your database
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn app:app`

### Plan
- Select **"Free"** plan
  - ⚠️ Note: Free plan sleeps after 15 min of inactivity
  - First request after sleep takes ~30 seconds

## Step 4: Configure Environment Variables

In the Render dashboard, go to **Environment** tab and add these variables:

### Required Variables

```bash
# Flask Configuration
SECRET_KEY=<click "Generate" button for random secure key>
FLASK_ENV=production

# Database (auto-populated by Render)
DATABASE_URL=<will be auto-filled from database>

# Email Configuration (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=<your-gmail-app-password>
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### Optional (for Google OAuth)

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Setting Up Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** (required)
3. Go to **App Passwords**
4. Select app: **Mail**, device: **Other (Custom name)**
5. Enter "GlobeTrotter" and click **Generate**
6. Copy the 16-character password (no spaces)
7. Use this as `MAIL_PASSWORD` in Render

## Step 5: Link Database to Web Service

1. In your web service settings, go to **Environment** tab
2. Under **Environment Variables**, add:
   - **Key**: `DATABASE_URL`
   - **Value**: Click the dropdown and select your database
   - This will auto-populate with the database connection string

## Step 6: Deploy!

1. Click **"Create Web Service"** or **"Manual Deploy"**
2. Watch the build logs
3. Build process will:
   - Install dependencies from `requirements.txt`
   - Run `build.sh` to initialize database
   - Start the app with gunicorn

Expected build time: 2-5 minutes

## Step 7: Set Up Google OAuth (Optional)

If you want Google login to work in production:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (or create new one)
3. Go to **APIs & Services** → **Credentials**
4. Edit your OAuth 2.0 Client ID
5. Add to **Authorized redirect URIs**:
   ```
   https://your-app-name.onrender.com/login/google/authorized
   ```
6. Update environment variables in Render:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

## Step 8: Test Your Deployment

1. Open your Render app URL: `https://your-app-name.onrender.com`
2. Test key features:
   - ✅ Homepage loads
   - ✅ User registration
   - ✅ Email verification (check spam folder)
   - ✅ Login/logout
   - ✅ Create trip
   - ✅ Profile settings

## Troubleshooting

### Build Fails

**Error**: `Permission denied: ./build.sh`
- **Solution**: Make build.sh executable locally first:
  ```bash
  git update-index --chmod=+x build.sh
  git commit -m "Make build.sh executable"
  git push
  ```

### Database Connection Error

**Error**: `could not connect to server`
- **Solution**: 
  1. Check `DATABASE_URL` is set correctly
  2. Ensure database and web service are in same region
  3. Wait 2-3 minutes after database creation

### Email Not Sending

**Error**: `SMTPAuthenticationError`
- **Solution**:
  1. Verify Gmail App Password is correct (no spaces)
  2. Ensure 2FA is enabled on Gmail
  3. Check `MAIL_USERNAME` matches email address
  4. Try regenerating App Password

### App Sleeps (Free Plan)

**Issue**: App takes 30+ seconds to wake up
- **Solution**: This is normal for Render free tier
- **Workaround**: 
  - Upgrade to paid plan ($7/month)
  - Use external monitoring service (like UptimeRobot) to ping every 14 minutes
  - Accept the limitation for free hosting

### Static Files Not Loading

**Issue**: CSS/JS not loading
- **Solution**: Check that `static/` folder is included in your repository
- Verify `STATIC_URL` is configured correctly in `app.py`

## Free Plan Limitations

⚠️ **Important Render Free Tier Limits:**

- **Web Services**: Spins down after 15 min inactivity
- **Database**: 90-day expiration, 1GB storage limit
- **Bandwidth**: 100GB/month
- **Build Minutes**: 500 minutes/month
- **Custom Domain**: Not available on free tier

## Monitoring Your App

### View Logs
1. Go to your service in Render dashboard
2. Click **"Logs"** tab
3. View real-time application logs

### Check Database
1. Go to your database in Render dashboard
2. Click **"Connect"** → **"External Connection"**
3. Use provided connection string with a PostgreSQL client

## Updating Your App

After making changes locally:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

Render will automatically:
1. Detect the push
2. Rebuild the app
3. Deploy new version (~2-5 minutes)

## Environment Variable Management

### Updating Variables
1. Go to service **Environment** tab
2. Edit variable value
3. Click **"Save Changes"**
4. Service will automatically redeploy

### Viewing Current Variables
- Render masks secret values in the UI
- Use logs to verify variables are loaded correctly

## Backup Your Database

⚠️ **Important**: Free databases expire after 90 days

### Manual Backup
```bash
# From Render dashboard, get connection string
pg_dump DATABASE_URL > backup.sql
```

### Automated Backups
- Not available on free tier
- Consider upgrading to Starter plan ($7/month) for daily backups

## Cost Optimization Tips

1. **Use Free Tier Wisely**:
   - Host on Render free tier for development/testing
   - Upgrade before going to production

2. **Minimize Build Time**:
   - Cache dependencies when possible
   - Keep `requirements.txt` minimal

3. **Database Storage**:
   - Free tier: 1GB limit
   - Monitor usage in Render dashboard
   - Clean up old data periodically

## Next Steps

- ✅ Set up custom domain (requires paid plan)
- ✅ Enable HTTPS (automatic on Render)
- ✅ Set up monitoring/alerts
- ✅ Configure scheduled jobs (cron)
- ✅ Implement database backups
- ✅ Add CDN for static assets

## Support & Resources

- **Render Documentation**: https://render.com/docs
- **Flask Documentation**: https://flask.palletsprojects.com
- **PostgreSQL on Render**: https://render.com/docs/databases

## Security Checklist

Before going live:

- [ ] All environment variables set securely
- [ ] `SECRET_KEY` is strong and unique
- [ ] Gmail App Password is used (not account password)
- [ ] Google OAuth redirect URIs are correct
- [ ] Database credentials are not in code
- [ ] `.env` file is in `.gitignore`
- [ ] HTTPS is enabled (automatic on Render)
- [ ] Session cookies are secure in production

---

## Quick Reference Commands

```bash
# Test locally before deploying
python app.py

# Check Python version
python --version

# Test database connection
python init_db.py

# View environment variables locally
cat .env

# Make build.sh executable
chmod +x build.sh
git update-index --chmod=+x build.sh
```

---

**Congratulations!** 🎉 Your GlobeTrotter app is now deployed on Render.com!

Visit your app at: `https://your-app-name.onrender.com`
