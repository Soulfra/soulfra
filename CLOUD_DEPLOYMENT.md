# ☁️ Cloud Deployment - Practice Rooms

## Quick Deploy to Cloud Platforms

This guide covers deploying your practice rooms to cloud platforms so friends/family can access from anywhere with a permanent URL.

**Best for**: Quick setup, no server management, free tiers available

**Platforms covered**:
- Render.com (recommended for beginners)
- Railway.app (fastest deployment)
- Fly.io (global edge)

---

## Option 1: Render.com ⭐ RECOMMENDED

### Why Render?
- 🆓 Free tier
- 🎯 Simple setup
- 🗄️ Free PostgreSQL
- 🌐 Auto HTTPS

### Quick Deploy (10 minutes)

#### 1. Prepare Files

**Create `requirements.txt`**:
```bash
pip freeze > requirements.txt
```

Make sure it includes:
```txt
Flask>=3.0.0
qrcode>=7.4.2
Pillow>=10.0.0
gunicorn>=21.2.0
```

**Create `render.yaml`**:
```yaml
services:
  - type: web
    name: practice-rooms
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 4 -b 0.0.0.0:$PORT app:app --timeout 120
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

#### 2. Push to GitHub

```bash
git init
git add .
git commit -m "Deploy practice rooms"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/practice-rooms.git
git push -u origin main
```

#### 3. Deploy on Render

1. Go to https://render.com
2. Sign up/login with GitHub
3. Click **"New +"** → **"Web Service"**
4. Connect your repo
5. Settings will auto-fill from `render.yaml`
6. Click **"Create Web Service"**

#### 4. Access Your App

After ~5 minutes, your app will be live at:
```
https://practice-rooms.onrender.com
```

Create a room:
```
https://practice-rooms.onrender.com/practice/create
```

### Important Notes

**Free Tier Limitations**:
- App sleeps after 15 min of inactivity
- First request after sleep takes ~30 seconds
- 750 hours/month free

**Keep it awake** (optional):
```bash
# Use a free service like cron-job.org to ping every 10 minutes
curl https://practice-rooms.onrender.com/practice/
```

---

## Option 2: Railway.app

### Why Railway?
- 🚄 Ultra-fast deployments
- 💰 $5 free credit/month
- 🎨 Beautiful dashboard

### Quick Deploy (5 minutes)

#### 1. Install Railway CLI

```bash
npm install -g @railway/cli
# or
brew install railway
```

#### 2. Login & Deploy

```bash
# Login
railway login

# Initialize in your project directory
railway init

# Deploy
railway up

# Get public URL
railway domain

# Open in browser
railway open
```

That's it! Your app is live.

### Add Database (Optional)

```bash
railway add -d postgres
```

### Environment Variables

```bash
railway variables set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
railway variables set FLASK_ENV=production
```

---

## Option 3: Fly.io

### Why Fly?
- 🌍 Global edge network
- ⚡ Fast worldwide
- 🆓 Generous free tier

### Quick Deploy

#### 1. Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
```

#### 2. Login

```bash
fly auth login
```

#### 3. Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
```

#### 4. Launch

```bash
fly launch
```

Follow prompts:
- App name: `practice-rooms` (or your choice)
- Region: Choose closest to you
- PostgreSQL: No (for now)
- Deploy: Yes

#### 5. Access

Your app: `https://practice-rooms.fly.dev`

---

## Environment Variables

Set these in production:

```bash
# Render: In dashboard under "Environment"
# Railway: railway variables set KEY=VALUE
# Fly: fly secrets set KEY=VALUE

# Required
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Optional
MAX_UPLOAD_SIZE=10485760
DEBUG=False
```

Generate secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database Options

### SQLite (Default - Good for Start)

Works out of the box. Good for:
- Testing
- Low traffic
- Single instance

**Limitation**: File-based, not ideal for multiple workers

### Upgrade to PostgreSQL

When you need:
- Multiple workers
- Higher traffic
- Better concurrency

**Render**:
1. Dashboard → "New +" → "PostgreSQL"
2. Copy connection string
3. Add to environment: `DATABASE_URL`

**Railway**:
```bash
railway add -d postgres
```

**Fly**:
```bash
fly postgres create
fly postgres attach
```

---

## Custom Domain

### Render

1. Dashboard → Your service → "Settings"
2. "Custom Domain" → Add domain
3. Update DNS:
   ```
   Type: CNAME
   Name: rooms (or subdomain you want)
   Value: practice-rooms.onrender.com
   ```

### Railway

```bash
railway domain add rooms.yourdomain.com
```

Then update DNS as shown in dashboard.

### Fly

```bash
fly certs add rooms.yourdomain.com
```

---

## Testing Your Deployment

### 1. Create a Room

Visit:
```
https://YOUR_APP_URL/practice/create
```

Fill out:
- Topic: "Test Room"
- Participants: 10
- Duration: 1 hour

### 2. Download QR Code

Click "Download QR" button

### 3. Test from Phone

- Open downloaded QR code
- Scan with phone camera (on cellular data, not WiFi)
- Should open room page
- Submit a test message
- Verify it appears in database

### 4. Check Logs

**Render**: Dashboard → "Logs" tab

**Railway**:
```bash
railway logs
```

**Fly**:
```bash
fly logs
```

---

## Troubleshooting

### App Won't Start

**Check logs** for errors:
- Missing dependencies in `requirements.txt`
- Wrong start command
- Port binding issues

**Fix**: Make sure using `gunicorn` with `$PORT` variable:
```bash
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

### QR Codes Not Working

**Problem**: Using `localhost` URL in QR code

**Fix**: Check that `request.host_url` uses production URL, not localhost

### Upload Errors

**Problem**: No writable file system

**Fix**: Use environment variable for uploads:
```python
import os
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
```

### Database Locked

**Problem**: SQLite locked in multi-worker setup

**Solutions**:
1. Reduce workers: `gunicorn -w 1 ...`
2. Upgrade to PostgreSQL (recommended)

---

## Cost Comparison

| Platform | Free Tier | Monthly Cost (Paid) |
|----------|-----------|---------------------|
| **Render** | 750 hrs, sleeps | $7 (always on) |
| **Railway** | $5 credit (~500 hrs) | Pay as you go ($0.01/hr) |
| **Fly.io** | 3 VMs, 256MB each | ~$2 (no sleep) |

**Recommendation**: Start with Render free tier, upgrade when needed.

---

## Production Checklist

Before going live:

- [ ] `requirements.txt` is complete
- [ ] Secret key set via environment
- [ ] `DEBUG=False` in production
- [ ] HTTPS enabled (automatic on all platforms)
- [ ] Database configured (SQLite or PostgreSQL)
- [ ] Error logging enabled
- [ ] Tested room creation
- [ ] Tested QR code download
- [ ] Tested from mobile phone
- [ ] Backups configured

---

## Next Steps

✅ **App is deployed!**

Now:
1. **Test thoroughly**: Create rooms, scan QR codes
2. **Share with friends**: Send them the URL
3. **Monitor usage**: Check logs and metrics
4. **Set up custom domain** (optional)
5. **Upgrade tier** if needed (traffic/always-on)

---

## Quick Reference

### Render
```bash
# View logs
render logs -t

# Deploy updates
git push origin main  # Auto-deploys
```

### Railway
```bash
railway login
railway up           # Deploy
railway logs         # View logs
railway open         # Open in browser
```

### Fly
```bash
fly deploy           # Deploy
fly logs             # View logs
fly open            # Open in browser
fly ssh console     # SSH into instance
```

---

## Support & Docs

- **Render**: https://docs.render.com
- **Railway**: https://docs.railway.app
- **Fly.io**: https://fly.io/docs

---

**Your practice rooms are now accessible from anywhere!** 🌍

Share the URL, scan the QR codes, and watch your friends join! 🎉
