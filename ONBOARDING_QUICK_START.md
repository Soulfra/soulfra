# StPetePros Onboarding - THE BRAINDEAD SIMPLE GUIDE

> **TL;DR:** 3 links. That's it.

---

## YOU → Admin Dashboard

```
https://192.168.1.87:5001/admin/stpetepros
```

**What you see:**
- **Stats cards**: Total pros, pending approval, approved, new today
- **Table of professionals**: All signups with color-coded status
  - 🟡 Yellow = Pending (needs your approval)
  - 🟢 Green = Approved (live on site)
  - ⚫ Grey = Rejected
- **Action buttons**: Approve, Reject, View Profile, Download QR
- **Export CSV**: Click button → downloads mailing list

**What you do:**
1. Check "Pending Approval" count
2. Click "Approve" for legit businesses
3. Click "Reject" for spam
4. Click "Export CSV" for Mailchimp/email campaigns
5. Done!

---

## THEM → Signup Link (Send this to businesses)

```
https://192.168.1.87:5001/signup/professional
```

**What they see:**
1. **Create Soulfra Account**
   - Name: "John Smith"
   - Email: "john@plumbing.com"
   - Password: "password123"
   - Click "Create Account"

2. **Fill Out Business Info** (auto-redirects after signup)
   - Business Name: "ABC Plumbing"
   - Category: "Plumbing"
   - Bio: "20 years experience..."
   - Phone: "(727) 555-1234"
   - Address: "123 Main St"
   - ZIP: "33701"
   - Click "Create My Profile"

3. **Done!** They get:
   - Profile page: `/professional/[ID]`
   - QR business card (auto-generated)
   - Listed in directory
   - Inbox for customer messages

**What you do:**
- NOTHING. It's automatic.
- Just approve them in your admin dashboard when you get a chance.

---

## EVERYONE → Public Directory

```
https://192.168.1.87:5001/professionals
```

**What customers see:**
- All **approved** professionals (grouped by category)
- Profiles with ratings, reviews, contact info
- Search by keyword
- Filter by category
- Contact form to message professionals

**What you do:**
- Share this link on social media
- Add to your website
- Print on business cards
- Text to friends looking for services

---

## Sharing the Link (3 Options)

### Option 1: WiFi Only (Easiest)
```
Just send: https://192.168.1.87:5001/signup/professional
```
**Works if they're on your WiFi.** Good for testing with friends at your house.

### Option 2: Ngrok (8hrs/day free)
```bash
ngrok http 5001
```
**Get a URL like:** `https://abc123.ngrok.io/signup/professional`
**Share that URL** - works anywhere in the world, expires after 8 hours.

### Option 3: Cloudflare Tunnel (Free forever)
```bash
cloudflared tunnel --url https://localhost:5001
```
**Get a permanent URL** - works forever, no limits, share with anyone.

---

## Color-Coded Status System

| Color | Status | Meaning | What to Do |
|-------|--------|---------|------------|
| 🟡 **Yellow** | Pending | Just signed up, needs approval | Click "Approve" or "Reject" |
| 🟢 **Green** | Approved | Live on public directory | Nothing - they're good! |
| 🔵 **Blue** | Contacted | You reached out for sales | Follow up with them |
| ⚫ **Grey** | Rejected | Spam or invalid | Nothing - they're hidden |

You set the status by clicking buttons in the admin dashboard.

---

## FAQ (For Retards Like Us)

### Q: "How do I see who signed up?"
A: Go to `https://192.168.1.87:5001/admin/stpetepros`

### Q: "How do I send them the signup link?"
A: Text them: `https://192.168.1.87:5001/signup/professional`

### Q: "Do I need to approve every signup?"
A: YES. Click "Approve" in admin dashboard. This prevents spam.

### Q: "How do I export the email list?"
A: Admin dashboard → "Export CSV" button → opens in Excel/Google Sheets

### Q: "Where are the QR codes?"
A: Each professional gets one automatically. View their profile → QR code shows in sidebar.

### Q: "Can I add professionals manually?"
A: Yes! Go to `/signup/professional` yourself and fill it out for them.

### Q: "What if someone forgets their password?"
A: Not implemented yet. For now, they create a new account or you reset it in the database admin.

### Q: "How do I customize the categories?"
A: Edit `stpetepros_routes.py` line 189-203 (the category dropdown list).

### Q: "Can I integrate Google Business Profile?"
A: YES! See `GOOGLE_BUSINESS_PROFILE_INTEGRATION.md` for step-by-step guide (takes ~8 hours to implement).

### Q: "How do I backup the database?"
A: Copy `soulfra.db` file to external drive. Or use GitHub encrypted backup (see below).

### Q: "How do I see ALL the data in the database?"
A: Go to `https://192.168.1.87:5001/admin/database` (general database admin for ALL tables)

---

## Database Stuff (For Nerds)

### Encrypted Backup to GitHub
```python
from database_encryption import DatabaseEncryption
db_enc = DatabaseEncryption()
db_enc.encrypt_existing_data()  # Encrypts sensitive fields
```

Then push `soulfra.db` to private GitHub repo. Emails/phones are encrypted with AES-256.

### Voice Transcription (Whisper Integration)
Already built! Route: `/voice`
- Records audio in browser
- Auto-transcribes with Whisper
- Saves to database

**To add to professional signup:**
Add "Record Bio" button → calls `/voice` → fills bio field with transcription.

### Manual Database Queries
```bash
sqlite3 soulfra.db "SELECT * FROM professionals;"
```

View all professionals in terminal. Good for quick checks.

---

## What Features Exist That You Don't Know About

You have ALL this shit already built:

| Feature | Route | What It Does |
|---------|-------|--------------|
| **Admin Dashboard** | `/admin/stpetepros` | Manage professionals (NEW!) |
| **Database Admin** | `/admin/database` | View ALL tables, export CSVs |
| **Voice Recorder** | `/voice` | Record audio + Whisper transcription |
| **Sales Dashboard** | `/stpetepros/admin/sales` | Manage scraped prospects |
| **Route Planner** | `/stpetepros/admin/plan-route` | Optimize sales routes |
| **QR Generator** | Built-in | Auto-generates for each professional |
| **Master Auth** | `/signup-soulfra` | Unified login across all domains |
| **Dual Personas** | Auto-generated | Each user gets monikers for routing |
| **Database Encryption** | `database_encryption.py` | AES-256 for sensitive data |
| **Device Fingerprinting** | Auto-tracked | Binds accounts to hardware |

**Problem:** You didn't know these existed because they're buried in 409 .md files and 2,500 routes.

**Solution:** THIS FILE. Bookmark it.

---

## The 3 Links (Again, Because Simplicity)

1. **YOU** → Admin Dashboard: `https://192.168.1.87:5001/admin/stpetepros`
2. **THEM** → Signup Link: `https://192.168.1.87:5001/signup/professional`
3. **EVERYONE** → Public Directory: `https://192.168.1.87:5001/professionals`

That's it. Everything else is automatic.

---

## Next Steps (If You Want to Expand)

1. **Google Business Profile Integration** (8 hours)
   - See `GOOGLE_BUSINESS_PROFILE_INTEGRATION.md`
   - Auto-creates Google Business listings
   - Pulls real Google reviews

2. **Whisper Voice Bios** (2 hours)
   - Add "Record Bio" button to professional signup
   - Auto-transcribes with Whisper
   - Fills bio field automatically

3. **Payment Integration** (4 hours)
   - Add Stripe checkout for premium listings
   - Featured placement
   - Verified badges

4. **Email Campaigns** (1 hour)
   - Export CSV → Mailchimp
   - Send welcome emails to new signups
   - Monthly newsletter to customers

5. **Multi-State Expansion** (Already built!)
   - `domain_config/domains.yaml` has geo-restriction config
   - Just add subdomains: `tampa.stpetepros.com`, `orlando.stpetepros.com`

---

## Support

**Documentation:**
- `SIMPLE_README.md` - What the fuck is this project?
- `LOCAL_NETWORK_SETUP.md` - How friends can join
- `GOOGLE_BUSINESS_PROFILE_INTEGRATION.md` - Google integration guide
- `COLLABORATION_GUIDE.md` - How friends contribute code

**Need help?**
- Check `/admin/docs` for searchable documentation
- Ask Ollama: `/api/docs/ask` (AI searches all docs)
- GitHub Issues: `github.com/soulfra/soulfra-simple/issues`

---

**Last updated:** 2026-01-10
**Version:** 1.0 - Braindead Simple Edition
