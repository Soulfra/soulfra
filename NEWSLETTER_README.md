# Newsletter + Daily Quote System for leftonreadbygod.com

## ✅ What's Working

### 1. Email Collection (Newsletter Signup)
- **Database**: Emails saved to `soulfra.db` → `subscribers` table
- **API**: `POST /api/newsletter/subscribe-public`
- **Frontend**: `generated/frontend_7_20260113_163930.html`
- **Test**: Works! (tested with curl, 1 subscriber saved)

### 2. Daily Quote Generator
- **Database**: Quotes saved to `soulfra.db` → `daily_quotes` table
- **API**: `GET /api/quotes/daily?brand_slug=leftonreadbygod`
- **API**: `POST /api/quotes/generate` (generate new quote with Ollama)
- **Frontend**: `generated/daily_quote_20260113.html`
- **Test**: Works! (generated quote: "Ghosting may feel like a divine apparition...")

## 🚀 How To Use

### Start the Server
```bash
python3 newsletter_test_server.py
```

Server runs on `http://localhost:5001`

### View the Pages
1. **Daily Quote Page**: Open `generated/daily_quote_20260113.html` in browser
   - Shows today's quote
   - Button to generate new quote (uses Ollama)
   - View counter
   - Link to newsletter signup

2. **Newsletter Signup**: Open `generated/frontend_7_20260113_163930.html` in browser
   - Collects name + email
   - Saves to database
   - Generates confirmation token (email sending optional)

### Test the APIs

**Get daily quote:**
```bash
curl "http://localhost:5001/api/quotes/daily?brand_slug=leftonreadbygod"
```

**Generate new quote:**
```bash
curl -X POST http://localhost:5001/api/quotes/generate \\
  -H "Content-Type: application/json" \\
  -d '{"brand_slug": "leftonreadbygod"}'
```

**Newsletter signup:**
```bash
curl -X POST http://localhost:5001/api/newsletter/subscribe-public \\
  -H "Content-Type: application/json" \\
  -d '{"email": "test@example.com", "name": "Test", "brand_slug": "leftonreadbygod"}'
```

### Automate Daily Quotes

**Option 1: Cron Job (macOS/Linux)**
```bash
crontab -e
```

Add this line to generate a new quote every day at 9am:
```
0 9 * * * /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/generate_daily_quote.sh
```

**Option 2: Manual**
```bash
./generate_daily_quote.sh
```

## 📊 Database Schema

### subscribers table
```sql
id, email, name, brand_slug, confirm_token, confirmed, subscribed_at, confirmed_at, unsubscribed_at
```

### daily_quotes table
```sql
id, brand_slug, quote_text, generated_at, active, views
```

## 🎯 What You Get

### In-App Distribution (No Email Server Needed!)
- Users visit `daily_quote_20260113.html` to see today's quote
- Quote auto-generated daily via cron
- View counter tracks engagement
- Share button (native share API or clipboard)

### Optional: Email Newsletter
- Database already collecting emails
- Confirmation tokens generated
- Can export emails to CSV: `SELECT email FROM subscribers WHERE confirmed = 1`
- Send manually via Mail.app or add SMTP later

## 🔮 Next Steps

### Option A: Keep it Simple (Recommended)
✅ You're done! Users visit the page daily to see new quotes.

### Option B: Add Email Sending
1. Configure SMTP in `config_secrets.py`
2. Build email template with daily quote
3. Add cron job to send emails
4. Track open rates, clicks, etc.

### Option C: Add Push Notifications
1. Implement web push API
2. Users subscribe in browser
3. Push notification with daily quote
4. No email server needed, still gets to users

### Option D: RSS Feed
1. Generate RSS XML with daily quotes
2. Users subscribe via RSS reader
3. Auto-updates when new quote generated
4. Zero email infrastructure

## 💡 Why This Approach Works

1. **No Email Headaches**: Skip SMTP, Gmail app passwords, deliverability issues
2. **Cheaper**: No email sending costs (SendGrid, Mailchimp, etc.)
3. **Faster**: Users get content instantly (no inbox delays)
4. **Better UX**: Beautiful web page vs plain email
5. **Trackable**: View counts, shares, engagement metrics built-in

## 🛠️ Files Created

- `quote_routes.py` - Quote API endpoints (generate, fetch daily, list all)
- `generated/daily_quote_20260113.html` - Frontend quote viewer
- `generate_daily_quote.sh` - Cron script for automation
- `newsletter_test_server.py` - Updated with quote routes
- `examples/newsletter-signup-template.html` - Fixed template (correct endpoint)

## 🐛 Known Issues

- Email sending prints to console (intentional - no SMTP configured)
- Flask server is dev mode (use Gunicorn for production)

## 📝 Current Status

✅ **Email collection**: Working
✅ **Quote generation**: Working
✅ **Quote display**: Working
✅ **Automation script**: Ready
⏳ **Email sending**: Optional (not configured)

---

**Bottom line**: You have a working "newsletter" system that doesn't need email at all. Users visit your site daily to see new AI-generated quotes about dating/ghosting. Way simpler than traditional email newsletters!
