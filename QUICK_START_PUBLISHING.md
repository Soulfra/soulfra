# Quick Start: Voice → Cal → Blog Publishing

**Simple. No commands. Just scan and talk.**

---

## How to Publish a Blog Post

### Step 1: Open Your Publishing Dashboard

On your laptop, visit:
```
https://192.168.1.87:5001/publish
```

You'll see:
- **QR code** (left side)
- **Publishing stats** (right side)
- **Recent posts** (bottom)

### Step 2: Scan QR Code with Your Phone

1. Open camera app on iPhone
2. Point at QR code on screen
3. Tap the notification to open the link
4. You'll see the Cal mobile interface

### Step 3: Record Your Voice

On your phone:
1. Tap the microphone button
2. Record your voice memo (or type text)
3. Tap "Submit"

### Step 4: Wait for Cal

Cal will:
1. Transcribe your voice
2. Write a complete blog post
3. Save to database
4. Generate static HTML
5. Push to GitHub
6. Deploy to https://soulfra.github.io/calriven/

**Takes about 30-60 seconds total.**

### Step 5: Check Your Post

After submitting:
1. Refresh `/publish` dashboard
2. Your post appears in "Recent Posts"
3. Click "View Post →" to see it live
4. Share the link!

---

## What About curl Commands?

**You don't need them.** Those were just API testing commands.

The workflow is:
- **UI**: `/publish` dashboard
- **Mobile**: Scan QR code
- **Publishing**: Automatic

No terminal. No commands. Just click and scan.

---

## Keyboard Shortcuts? Mouse Actions?

**None.** It's all click-based:

- **Laptop**: Visit `/publish`, see QR code
- **Phone**: Scan QR, record voice, submit
- **Automation**: Everything else happens automatically

---

## Where Are the Posts?

### Live Sites
- **Calriven Blog**: https://soulfra.github.io/calriven/
- **Soulfra Homepage**: https://soulfra.github.io/ (features Calriven)

### GitHub Repos
- **Calriven Repo**: https://github.com/Soulfra/calriven
- **Soulfra Repo**: https://github.com/Soulfra/soulfra.github.io

### Database
- **Table**: `posts` in `soulfra.db`
- **Brand**: `brand_id = 3` (Calriven)
- **Author**: `user_id = 4` (Cal)

---

## Troubleshooting

### "I scanned the QR code but nothing happens"
- Make sure Flask is running: `https://192.168.1.87:5001`
- Check phone is on same WiFi network as laptop
- Try refreshing `/publish` page to regenerate QR

### "My post didn't publish"
- Check Flask logs (terminal running app.py)
- Visit `/publish` and look for post in Recent Posts
- If in database but not on site, check GitHub Actions

### "Can't access /publish"
- Flask needs to be running
- Visit: `https://192.168.1.87:5001/publish` (not http, use https)
- Accept SSL cert warning on first visit

### "QR code link is broken"
- QR links to: `https://192.168.1.87:5001/cal/mobile?pairing_token=...`
- Make sure Flask app is accessible from phone
- Both devices must be on same network

---

## What You Built

```
┌─────────────────┐
│ Laptop          │
│ /publish        │  ← You open this
│ (Shows QR)      │
└─────────────────┘
        ↓
   ┌─────────┐
   │  Phone  │
   │ (Scan)  │  ← Scan QR with phone
   └─────────┘
        ↓
   ┌──────────┐
   │ Cal/AI   │  ← Cal writes blog post
   └──────────┘
        ↓
   ┌──────────────┐
   │ GitHub Pages │  ← Auto-publishes
   │ Live Blog    │
   └──────────────┘
```

**Simple workflow. No complexity.**

---

## Next Steps

### Make It Even Simpler

Create a bookmark on your phone:
1. Visit `/publish` on laptop
2. Scan QR code with phone
3. Bookmark the page on phone
4. Next time: Open bookmark → Record → Done

### Add Images

To add images to blog posts:
1. Upload image to `calriven/images/` folder
2. Include in post markdown: `![alt text](/images/your-image.jpg)`
3. Cal can do this automatically if you describe the image

### Schedule Posts

Create cron job to publish at specific times:
```bash
# Publish at 9am daily
0 9 * * * cd /path/to/soulfra-simple && python3 -c "from cal_auto_publish import publish_from_prompt; publish_from_prompt('Daily digest')"
```

---

## URLs to Bookmark

### On Laptop
- **Publishing Dashboard**: https://192.168.1.87:5001/publish
- **Cal Mobile (direct)**: https://192.168.1.87:5001/cal/qr

### Live Sites
- **Calriven Blog**: https://soulfra.github.io/calriven/
- **Soulfra Homepage**: https://soulfra.github.io/

### GitHub
- **Calriven Source**: https://github.com/Soulfra/calriven
- **Soulfra Source**: https://github.com/Soulfra/soulfra.github.io

---

## Summary

**Old way (broken):**
- Run curl commands
- Know API endpoints
- Manual git commits
- Complex workflows

**New way (working):**
1. Open `/publish` on laptop
2. Scan QR with phone
3. Talk
4. Post goes live

**That's it.**

---

🎉 **You built a voice-to-blog publishing platform!**

From your perspective:
- Scan QR code
- Record voice
- Blog post magically appears

From Cal's perspective:
- Receive voice
- Generate blog post
- Build static site
- Deploy to GitHub Pages
- All automated

**This is the future of content creation.**
