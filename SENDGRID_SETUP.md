# SendGrid Setup Guide for GlobeTrotter

## Why SendGrid?

**Render.com blocks external SMTP servers** (Gmail, Outlook, etc.) on ports 587 and 465. SendGrid uses an HTTP API instead of SMTP, making it compatible with Render's free tier.

## SendGrid Free Tier Benefits

- **100 emails per day** - Perfect for small apps
- **No credit card required** for signup
- **HTTP API** - Works on Render.com
- **Reliable delivery** with tracking and analytics

---

## Step 1: Create SendGrid Account

1. Go to [SendGrid.com](https://sendgrid.com)
2. Click **"Start for Free"**
3. Sign up with your email
4. Complete email verification
5. Choose **"Free"** plan (100 emails/day)

---

## Step 2: Generate API Key

1. Log in to [SendGrid Dashboard](https://app.sendgrid.com)
2. Go to **Settings** → **API Keys** (left sidebar)
3. Click **"Create API Key"** (top right)
4. Configure:
   - **API Key Name**: `GlobeTrotter-Production`
   - **API Key Permissions**: Select **"Mail Send"** (Full Access)
5. Click **"Create & View"**
6. **COPY THE KEY IMMEDIATELY** - It won't be shown again!
   - Format: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
7. Store securely (you'll need this for environment variables)

---

## Step 3: Verify Sender Email

SendGrid requires you to verify the email address you'll send from.

### Option A: Single Sender Verification (Recommended for Free Tier)

1. Go to **Settings** → **Sender Authentication**
2. Click **"Verify a Single Sender"**
3. Fill in form:
   - **From Name**: `GlobeTrotter`
   - **From Email Address**: Your email (e.g., `noreply@yourdomain.com` or your Gmail)
   - **Reply To**: Same email
   - **Company Address**: Your address
4. Click **"Create"**
5. Check your email for verification link
6. Click the verification link

### Option B: Domain Authentication (For Custom Domains)

Only if you have a custom domain:
1. Go to **Settings** → **Sender Authentication**
2. Click **"Authenticate Your Domain"**
3. Follow DNS setup instructions
4. Wait for DNS propagation (can take 24-48 hours)

---

## Step 4: Set Environment Variables

### For Local Development (.env file)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your SendGrid credentials:
   ```env
   SENDGRID_API_KEY=SG.your-actual-api-key-here
   SENDGRID_FROM_EMAIL=your-verified-email@domain.com
   ```

3. **Never commit .env file to git!** (Already in .gitignore)

### For Render.com Deployment

1. Go to your Render.com dashboard
2. Select your **GlobeTrotter** service
3. Click **"Environment"** tab (left sidebar)
4. Click **"Add Environment Variable"**
5. Add both variables:

   **Variable 1:**
   - Key: `SENDGRID_API_KEY`
   - Value: `SG.your-actual-api-key-here`

   **Variable 2:**
   - Key: `SENDGRID_FROM_EMAIL`
   - Value: `your-verified-email@domain.com`

6. Click **"Save Changes"**
7. Render will automatically redeploy your app

---

## Step 5: Test Email Functionality

### Test Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   python app.py
   ```

3. Try signing up with a new account:
   - Go to `http://localhost:5000`
   - Click **"Sign Up"**
   - Enter email and password
   - Check your email for the OTP code

4. Test password reset:
   - Click **"Forgot Password?"**
   - Enter your email
   - Check for password reset email

### Test on Render

1. After deployment, visit your Render URL
2. Try the same signup/password reset flows
3. Check SendGrid dashboard for email statistics:
   - Go to **Activity Feed** in SendGrid dashboard
   - You'll see sent emails and delivery status

---

## Troubleshooting

### "Unauthorized" or 401 Errors

**Cause**: Invalid API key

**Solutions**:
1. Verify API key is correct (starts with `SG.`)
2. Check API key has **"Mail Send"** permissions
3. Regenerate API key if needed
4. Ensure no extra spaces in environment variable

### "Sender email not verified" Errors

**Cause**: Email address not verified in SendGrid

**Solutions**:
1. Go to SendGrid → **Sender Authentication**
2. Verify the email you're using as `SENDGRID_FROM_EMAIL`
3. Check spam folder for verification email
4. Use exact same email in both places

### Emails Not Arriving

**Check SendGrid Activity Feed**:
1. Go to SendGrid dashboard → **Activity Feed**
2. Look for your sent emails
3. Check delivery status:
   - **Delivered**: Email sent successfully (check spam folder)
   - **Bounced**: Invalid recipient email
   - **Dropped**: SendGrid blocked the email (check why)

**Check Spam Folder**:
- SendGrid emails often land in spam initially
- Add sender to contacts to improve delivery

### Rate Limit Errors

**Cause**: Exceeded 100 emails/day on free tier

**Solutions**:
1. Wait until next day (resets at midnight UTC)
2. Upgrade SendGrid plan if needed
3. Optimize app to send fewer emails (e.g., batch notifications)

---

## SendGrid vs Gmail SMTP Comparison

| Feature | Gmail SMTP | SendGrid API |
|---------|------------|--------------|
| **Render Compatible** | ❌ Blocked (ports 587/465) | ✅ Works (HTTP API) |
| **Free Tier** | 500 emails/day | 100 emails/day |
| **Setup Complexity** | App Passwords, 2FA | Simple API key |
| **Deliverability** | Can land in spam | Better delivery rates |
| **Tracking** | None | Full analytics dashboard |
| **Reliability** | Gmail may block | Enterprise-grade |

---

## Security Best Practices

### API Key Security

1. **Never commit API keys to git**
   - Already protected by `.gitignore`
   - Use environment variables only

2. **Rotate keys regularly**
   - Generate new key every 90 days
   - Delete old keys in SendGrid dashboard

3. **Use restrictive permissions**
   - Only grant "Mail Send" permission
   - Avoid "Full Access" unless needed

4. **Monitor usage**
   - Check SendGrid Activity Feed regularly
   - Set up usage alerts in SendGrid

### Email Security

1. **Verify sender email**
   - Prevents spoofing
   - Improves deliverability

2. **Use dedicated sender address**
   - `noreply@yourdomain.com` instead of personal email
   - Separate from your main email

3. **Don't send sensitive data**
   - Never include passwords in emails
   - Use secure reset links with tokens

---

## Migration from Gmail SMTP (Already Done)

The codebase has been updated to use SendGrid:

### Changes Made:
- ✅ Removed Flask-Mail dependency
- ✅ Added SendGrid SDK (`sendgrid>=6.11.0`)
- ✅ Updated `send_otp_email()` function
- ✅ Updated password reset email function
- ✅ Changed configuration from SMTP to API
- ✅ Updated `.env.example`

### What You Need to Do:
1. Sign up for SendGrid (Step 1)
2. Generate API key (Step 2)
3. Verify sender email (Step 3)
4. Set environment variables (Step 4)
5. Test emails (Step 5)

---

## Support Resources

- **SendGrid Documentation**: https://docs.sendgrid.com
- **API Reference**: https://docs.sendgrid.com/api-reference
- **Support**: https://support.sendgrid.com
- **Status Page**: https://status.sendgrid.com

---

## Quick Start Checklist

- [ ] Create SendGrid account (free)
- [ ] Generate API key with "Mail Send" permission
- [ ] Copy API key securely
- [ ] Verify sender email address
- [ ] Add `SENDGRID_API_KEY` to environment variables
- [ ] Add `SENDGRID_FROM_EMAIL` to environment variables
- [ ] Test signup OTP email
- [ ] Test password reset email
- [ ] Check SendGrid Activity Feed
- [ ] Deploy to Render and test in production

---

**Next Steps**: After completing this setup, your app will be ready for deployment on Render.com with working email functionality! 🚀
