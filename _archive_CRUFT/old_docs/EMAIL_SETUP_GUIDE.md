# Email System Setup Guide - StPetePros

## Quick Start (Test NOW - 30 seconds)

**1. Run test email script with YOUR email:**

```bash
python3 test_email.py YOUR_EMAIL@gmail.com
```

**What happens:**
- Sends test recovery email via macOS sendmail
- Check your inbox in 1-2 minutes
- Email comes from: `StPetePros <noreply@localhost>`

**2. If it worked:**
✅ Email system is ready!
✅ New signups will auto-send recovery codes
✅ QR codes will be attached

**3. If it didn't work:**
📁 Email was saved to `sent_emails/` folder
📧 You can manually copy/paste to send

---

## How It Works

### 3-Tier Email System

The system tries these methods in order:

1. **Resend API** (if `RESEND_API_KEY` set in .env)
   - Free: 3,000 emails/month
   - Professional branding
   - Emails from: `noreply@soulfra.com`

2. **Local sendmail** (macOS default - WORKS NOW)
   - Built into macOS
   - No signup needed
   - Emails from: `noreply@localhost`
   - Perfect for testing

3. **File fallback** (if above fail)
   - Saves to `sent_emails/*.html`
   - Manually copy/paste into email client

---

## Testing the Signup Flow

**Step 1: Start Flask**
```bash
python3 app.py
```

**Step 2: Go to signup page**
```
http://localhost:5001/signup/professional
```

**Step 3: Fill out form**
- Business Name: Test Plumbing Co.
- Category: Plumbing
- Email: YOUR_EMAIL@gmail.com  ← USE YOUR REAL EMAIL
- Phone: (727) 555-1234
- Bio: Test professional for email system

**Step 4: Submit**
```
✅ Professional created
✅ Recovery code generated
✅ QR code created
✅ Email sent to YOUR_EMAIL@gmail.com
```

**Step 5: Check inbox**
- Email subject: "🎉 Welcome to StPetePros - Your Recovery Code"
- Contains recovery code (e.g., `tampa-plumber-trusted-4821`)
- QR code business card attached as PNG

**Step 6: Test verification**
1. Go to: http://localhost:5001/verify-professional
2. Enter recovery code from email
3. See professional details

---

## Upgrade to Resend (Optional - 10 minutes)

**Why Resend?**
- ✅ Free tier: 3,000 emails/month
- ✅ Emails from your domain: `noreply@soulfra.com`
- ✅ Professional branding
- ✅ Email tracking (opens, clicks)
- ✅ API is dead simple

**Setup:**

1. **Sign up at resend.com**
   - Go to: https://resend.com
   - Click "Start Building"
   - Sign up with GitHub (easiest)

2. **Get API key**
   - Dashboard → API Keys
   - Create new key
   - Copy key (starts with `re_`)

3. **Add to .env**
   ```bash
   # Edit .env file
   RESEND_API_KEY=re_YOUR_KEY_HERE
   ```

4. **Install Resend SDK** (optional but recommended)
   ```bash
   pip install resend
   ```

5. **Test it**
   ```bash
   python3 test_email.py YOUR_EMAIL@gmail.com
   ```

   Should see:
   ```
   ✅ Email sent via Resend to YOUR_EMAIL@gmail.com
      Email ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

6. **Check inbox**
   - Email now comes from: `StPetePros <noreply@soulfra.com>`
   - Much more professional!

---

## Current Status (What You Have Now)

✅ **Working:**
- Recovery code generation (BIP-39 style)
- QR code business card creation
- Email sending (3 methods)
- Verification system
- GitHub Actions validation

✅ **Tested:**
- 17 existing professionals have recovery codes
- Database schema updated
- Wordlist created (300+ Tampa Bay words)

⚠️  **Needs Testing:**
- [ ] Send test email to YOUR inbox
- [ ] Verify email arrives
- [ ] Test signup flow end-to-end
- [ ] Confirm QR code attachment works

---

## Production Deployment Checklist

### Before Deploying to soulfra.com:

1. **Setup Resend**
   - [ ] Sign up for Resend
   - [ ] Add API key to production .env
   - [ ] Verify domain (soulfra.com)
   - [ ] Test sending

2. **Update Flask app**
   - [ ] Set `RESEND_API_KEY` in production environment
   - [ ] Update email URLs (remove localhost:5001)
   - [ ] Test on production server

3. **GitHub Actions**
   - [ ] Add email notifications to workflow
   - [ ] Set secrets for SMTP credentials
   - [ ] Test workflow triggers

4. **Email Existing Professionals**
   - [ ] Run backfill script (already done)
   - [ ] Send recovery codes to all 17 professionals
   - [ ] Track who has received codes

---

## Troubleshooting

### Email not sending?

**Check 1: Is sendmail working?**
```bash
echo "Test email" | mail -s "Test Subject" YOUR_EMAIL@gmail.com
```

**Check 2: Is Python smtplib available?**
```bash
python3 -c "import smtplib; print('✅ smtplib works')"
```

**Check 3: Check sent_emails/ folder**
```bash
ls -lah sent_emails/
```

If emails are there, sendmail isn't working. Use Resend instead.

### Resend API errors?

**Error: "resend module not found"**
```bash
pip install resend
```

**Error: "Invalid API key"**
- Check .env file has correct key
- Key should start with `re_`
- No quotes around key in .env

**Error: "Domain not verified"**
- Go to Resend dashboard
- Add and verify your domain
- Or use their test domain for now

### Gmail blocking emails?

If using sendmail to Gmail:
- Check spam folder
- Add `noreply@localhost` to contacts
- Gmail may delay emails from unknown senders

Use Resend to avoid this.

---

## Advanced: GitHub Actions Email Notifications

Want to get notified when someone signs up?

**Add to `.github/workflows/notify-signup.yml`:**

```yaml
name: Email on New Signup

on:
  # Trigger when database changes
  push:
    paths:
      - 'soulfra.db'

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Send Email
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: ${{ secrets.SMTP_SERVER }}
          server_port: ${{ secrets.SMTP_PORT }}
          username: ${{ secrets.SMTP_USERNAME }}
          password: ${{ secrets.SMTP_PASSWORD }}
          subject: New StPetePros Signup!
          to: ${{ secrets.NOTIFY_EMAIL }}
          from: GitHub Actions
          body: |
            Someone just signed up for StPetePros!

            Check the database for details:
            https://github.com/YOUR_USERNAME/YOUR_REPO/commits/main
```

**Setup GitHub Secrets:**
1. Go to: Settings → Secrets → Actions
2. Add:
   - `SMTP_SERVER` = smtp.gmail.com
   - `SMTP_PORT` = 587
   - `SMTP_USERNAME` = your-email@gmail.com
   - `SMTP_PASSWORD` = your-app-password (NOT regular password)
   - `NOTIFY_EMAIL` = your-email@gmail.com

---

## Next Steps

1. **Test email sending** (do this now!)
   ```bash
   python3 test_email.py YOUR_EMAIL@gmail.com
   ```

2. **Test signup flow**
   - Go to: http://localhost:5001/signup/professional
   - Use YOUR email
   - Check inbox for recovery code

3. **Optional: Setup Resend**
   - Sign up at resend.com
   - Add API key to .env
   - Professional emails!

4. **Deploy to production**
   - Push changes to GitHub
   - Set RESEND_API_KEY on server
   - Update URLs in email templates

---

## Support

**Email not working?**
- Check `sent_emails/` folder
- Manually send recovery codes
- File GitHub issue

**Questions?**
- Check .env.example for config options
- Read code in email_sender.py
- Test with test_email.py

**Want to contribute?**
- Add more email templates
- Support for other SMTP providers
- Email queueing system
- Bulk email sender for newsletters
