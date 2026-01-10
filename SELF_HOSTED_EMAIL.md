# Self-Hosted Email - No SendGrid Needed

**Why self-host email instead of using SendGrid?**
- ✅ Full control over email delivery
- ✅ No monthly costs
- ✅ No API rate limits
- ✅ Custom SMTP server
- ✅ Email forwarding/aliases
- ✅ Privacy (no third-party service)

**You're right - you don't NEED SendGrid.** Here's how to self-host.

---

## Option 1: Python SMTP (Simplest)

**For development/testing - sends email via Python's built-in SMTP.**

### Send Email (No External Service)

```python
# send_email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to, subject, body_text, body_html=None, from_addr='noreply@localhost'):
    """
    Send email using Python SMTP

    Args:
        to: Recipient email
        subject: Email subject
        body_text: Plain text body
        body_html: HTML body (optional)
        from_addr: Sender email
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to

    # Attach plain text
    part1 = MIMEText(body_text, 'plain')
    msg.attach(part1)

    # Attach HTML (if provided)
    if body_html:
        part2 = MIMEText(body_html, 'html')
        msg.attach(part2)

    # Send via localhost SMTP (requires Postfix/sendmail installed)
    try:
        s = smtplib.SMTP('localhost', 25)
        s.send_message(msg)
        s.quit()
        print(f"✅ Email sent to {to}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# Test
if __name__ == '__main__':
    send_email(
        to='friend@example.com',
        subject='Welcome to Soulfra!',
        body_text='Thanks for signing up!',
        body_html='<h1>Thanks for signing up!</h1><p>Welcome to Soulfra.</p>'
    )
```

**Usage in Flask app**:
```python
# In app.py, after user signs up:
from send_email import send_email

@app.route('/signup', methods=['POST'])
def signup():
    user_email = request.form['email']
    username = request.form['username']

    # ... create user in database ...

    # Send welcome email
    send_email(
        to=user_email,
        subject=f'Welcome to Soulfra, {username}!',
        body_text=f'Thanks for joining, {username}!',
        body_html=f'<h1>Welcome {username}!</h1><p>Your account is ready.</p>'
    )

    return redirect('/dashboard')
```

---

## Option 2: Postfix (Production Email Server)

**For real email delivery from your own domain.**

### Install Postfix (macOS)

```bash
# Postfix comes pre-installed on macOS
# Check if running
sudo postfix status

# Start Postfix
sudo postfix start

# Configure
sudo nano /etc/postfix/main.cf
```

### Install Postfix (Ubuntu/Linux)

```bash
# Install
sudo apt update
sudo apt install postfix

# During install, choose:
# - "Internet Site"
# - Mail name: "localhost" (or your domain)

# Start Postfix
sudo systemctl start postfix
sudo systemctl enable postfix

# Check status
sudo systemctl status postfix
```

### Basic Postfix Configuration

Edit `/etc/postfix/main.cf`:

```conf
# Hostname (change to your domain or keep localhost for testing)
myhostname = localhost
mydomain = localhost
myorigin = $mydomain

# Only accept mail from this machine (security)
inet_interfaces = loopback-only

# Relay (send) email to external servers
relayhost =

# Accept mail for these domains
mydestination = $myhostname, localhost, localhost.localdomain

# Mailbox size limit (50MB)
mailbox_size_limit = 51200000

# Reject unknown recipients
local_recipient_maps = proxy:unix:passwd.byname $alias_maps
```

**Restart Postfix**:
```bash
sudo postfix reload
```

### Test Email Delivery

```bash
# Send test email via command line
echo "Test email body" | mail -s "Test Subject" your_email@example.com

# Or use Python
python3 send_email.py
```

**Check logs**:
```bash
# macOS
tail -f /var/log/mail.log

# Linux
tail -f /var/log/mail.log
# or
sudo journalctl -u postfix -f
```

---

## Option 3: MailHog (Local Email Testing)

**Catches all sent emails - perfect for testing without actually sending.**

### Install MailHog

```bash
# macOS
brew install mailhog

# Linux
wget https://github.com/mailhog/MailHog/releases/download/v1.0.1/MailHog_linux_amd64
chmod +x MailHog_linux_amd64
sudo mv MailHog_linux_amd64 /usr/local/bin/mailhog
```

### Start MailHog

```bash
mailhog

# Output:
# [HTTP] Binding to address: 0.0.0.0:8025
# [SMTP] Binding to address: 0.0.0.0:1025
```

**MailHog Web UI**: http://localhost:8025

### Configure Python to Use MailHog

```python
# send_email.py (modified for MailHog)
import smtplib
from email.mime.text import MIMEText

def send_email(to, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'noreply@localhost'
    msg['To'] = to

    # Use MailHog SMTP (port 1025 instead of 25)
    s = smtplib.SMTP('localhost', 1025)
    s.send_message(msg)
    s.quit()

    print(f"✅ Email caught by MailHog: http://localhost:8025")
```

**Test flow**:
1. Start MailHog: `mailhog`
2. Run Python script: `python3 send_email.py`
3. Open http://localhost:8025
4. See email in MailHog inbox!

**Perfect for friends/family testing** - you can see all emails without actually sending them.

---

## Option 4: Gmail SMTP (Easy But Not Self-Hosted)

**Use Gmail as SMTP relay (easiest, but uses Google).**

### Setup App Password

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to https://myaccount.google.com/apppasswords
4. Create app password for "Mail"
5. Copy 16-character password

### Python Code

```python
# send_email_gmail.py
import smtplib
from email.mime.text import MIMEText

def send_email_via_gmail(to, subject, body, gmail_user, gmail_app_password):
    """Send email via Gmail SMTP"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = gmail_user
    msg['To'] = to

    # Connect to Gmail SMTP
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(gmail_user, gmail_app_password)
    server.send_message(msg)
    server.quit()

    print(f"✅ Email sent via Gmail to {to}")

# Test
send_email_via_gmail(
    to='friend@example.com',
    subject='Welcome!',
    body='Thanks for signing up!',
    gmail_user='your_email@gmail.com',
    gmail_app_password='abcd efgh ijkl mnop'  # 16-char app password
)
```

**Pros**:
- ✅ Easy setup
- ✅ Reliable delivery
- ✅ No server config

**Cons**:
- ❌ Uses Gmail (not self-hosted)
- ❌ 500 emails/day limit
- ❌ Requires Google account

---

## Email Forwarding / Aliases

**Like email aliases mentioned in READTHEDOCS_ARCHITECTURE.md**

### Postfix Virtual Aliases

**Goal**: `user@soulfra.com` → forwards to `real_email@gmail.com`

#### 1. Create Virtual Alias Map

```bash
# Create alias file
sudo nano /etc/postfix/virtual

# Add aliases:
user1@soulfra.com    real_email1@gmail.com
user2@soulfra.com    real_email2@gmail.com
admin@soulfra.com    your_email@gmail.com
```

#### 2. Convert to Database

```bash
# Generate Postfix database
sudo postmap /etc/postfix/virtual
```

#### 3. Configure Postfix

```bash
# Edit main.cf
sudo nano /etc/postfix/main.cf

# Add:
virtual_alias_domains = soulfra.com calriven.com deathtodata.com
virtual_alias_maps = hash:/etc/postfix/virtual
```

#### 4. Reload Postfix

```bash
sudo postfix reload
```

#### 5. Test

```bash
# Send test email to alias
echo "Test" | mail -s "Test" user1@soulfra.com

# Check if forwarded to real_email1@gmail.com
```

### Dynamic Aliases from Database

**Auto-generate aliases when users sign up**

```python
# In app.py
import subprocess

def create_email_alias(username, forward_to_email):
    """
    Create Postfix virtual alias from database

    Args:
        username: User's username
        forward_to_email: Real email to forward to
    """
    alias_email = f"{username}@soulfra.com"

    # Add to database
    db = get_db()
    db.execute('''
        INSERT INTO email_aliases (alias_email, forward_to, user_id)
        VALUES (?, ?, ?)
    ''', (alias_email, forward_to_email, user_id))
    db.commit()

    # Regenerate Postfix virtual map
    subprocess.run([
        'sudo', 'postmap', '/etc/postfix/virtual'
    ])

    subprocess.run([
        'sudo', 'postfix', 'reload'
    ])

    print(f"✅ Created alias: {alias_email} → {forward_to_email}")
    return alias_email

# When user signs up:
@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    real_email = request.form['email']

    # ... create user ...

    # Create email alias
    alias = create_email_alias(username, real_email)

    # Send welcome email TO the alias (tests forwarding)
    send_email(
        to=alias,
        subject='Your custom email is ready!',
        body=f'You can now receive emails at {alias}'
    )
```

---

## Database Schema for Email Aliases

```sql
-- email_aliases table
CREATE TABLE email_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    alias_email TEXT UNIQUE NOT NULL,   -- 'user@soulfra.com'
    forward_to TEXT NOT NULL,            -- 'real@gmail.com'
    brand_slug TEXT,                     -- 'soulfra', 'calriven', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Index for fast lookups
CREATE INDEX idx_alias_email ON email_aliases(alias_email);
CREATE INDEX idx_forward_to ON email_aliases(forward_to);
```

---

## Comparison: SendGrid vs Self-Hosted

| Feature | SendGrid | Self-Hosted (Postfix) |
|---------|----------|----------------------|
| **Setup** | 5 min (API key) | 30 min (install+config) |
| **Cost** | $15/month (40k emails) | $0 (or $5/month VPS) |
| **Deliverability** | Excellent (their reputation) | Good (your reputation) |
| **Rate Limits** | Yes (tier-based) | No limits |
| **Email Aliases** | No | Yes (Postfix virtual) |
| **Privacy** | Logs sent to SendGrid | Full control |
| **Complexity** | Low | Medium |
| **Spam Risk** | Low (trusted IPs) | Medium (new IPs flagged) |

**Verdict**: For localhost/friends testing → **Self-hosted (Postfix + MailHog)**

---

## Recommended Setup for Friends/Family Testing

### Phase 1: MailHog (Right Now)

```bash
# Terminal 1
mailhog

# Terminal 2
python3 app.py

# All emails caught at http://localhost:8025
# Perfect for testing without sending real emails
```

### Phase 2: Postfix (Production)

```bash
# Install Postfix
sudo apt install postfix  # or brew install postfix

# Configure for your domain
sudo nano /etc/postfix/main.cf

# Start Postfix
sudo postfix start

# Real emails now delivered
```

### Phase 3: Email Aliases (Advanced)

```bash
# Create virtual alias map
sudo nano /etc/postfix/virtual

# Add aliases for each user
user1@soulfra.com    user1@gmail.com
user2@soulfra.com    user2@yahoo.com

# Reload
sudo postmap /etc/postfix/virtual
sudo postfix reload
```

---

## Flask Integration Example

```python
# In app.py
from send_email import send_email

# After user completes cringeproof quiz
@app.route('/cringeproof/complete', methods=['POST'])
def cringeproof_complete():
    user_id = session.get('user_id')
    ai_friend = request.form.get('ai_friend')  # 'soulfra', 'calriven', etc.

    # Get user email
    db = get_db()
    user = db.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()

    # Send completion email
    send_email(
        to=user['email'],
        subject=f'Meet your AI friend: {ai_friend}!',
        body_text=f'''
        Congratulations! Based on your quiz answers, you've been matched with {ai_friend}.

        Your personality profile is ready at:
        http://localhost:5001/profile/{user_id}
        ''',
        body_html=f'''
        <h1>Meet {ai_friend}!</h1>
        <p>Based on your cringeproof quiz, you've been matched with <strong>{ai_friend}</strong>.</p>
        <p><a href="http://localhost:5001/profile/{user_id}">View your profile</a></p>
        '''
    )

    # Unlock keyring features
    from keyring_unlocks import unlock_quiz_completion
    unlock_quiz_completion(user_id, ai_friend)

    return redirect('/dashboard')
```

---

## Testing Checklist

### MailHog Testing

- [ ] Install MailHog
- [ ] Start MailHog (`mailhog`)
- [ ] Configure Python to use port 1025
- [ ] Send test email
- [ ] Check http://localhost:8025 for caught email
- [ ] Test HTML emails
- [ ] Test multiple recipients

### Postfix Testing

- [ ] Install Postfix
- [ ] Configure `/etc/postfix/main.cf`
- [ ] Start Postfix (`sudo postfix start`)
- [ ] Send test email via Python
- [ ] Check logs (`tail -f /var/log/mail.log`)
- [ ] Verify email delivered to Gmail/Yahoo/etc.
- [ ] Test spam score (mail-tester.com)

### Email Alias Testing

- [ ] Create `/etc/postfix/virtual`
- [ ] Add test alias (`test@soulfra.com`)
- [ ] Run `sudo postmap /etc/postfix/virtual`
- [ ] Reload Postfix
- [ ] Send email to alias
- [ ] Verify forwarded to real email
- [ ] Test multiple aliases
- [ ] Test database-driven aliases

---

## Troubleshooting

### Emails Not Sending (Postfix)

**Check Postfix is running**:
```bash
sudo postfix status

# If not running:
sudo postfix start
```

**Check logs**:
```bash
tail -f /var/log/mail.log
```

**Common errors**:
- "Connection refused" → Postfix not running
- "Relay access denied" → Check `mynetworks` in main.cf
- "Unknown user" → Check `/etc/passwd` or virtual aliases

### Emails Going to Spam

**Improve deliverability**:
1. Add SPF record to DNS:
   ```
   TXT @ "v=spf1 mx ~all"
   ```

2. Add DKIM signing (optional but recommended)

3. Test spam score: https://www.mail-tester.com

4. Use reputable SMTP (Gmail relay for testing)

### MailHog Not Catching Emails

**Check MailHog is running**:
```bash
ps aux | grep mailhog

# If not running:
mailhog &
```

**Check SMTP port**:
```python
# Must use port 1025 (not 25)
s = smtplib.SMTP('localhost', 1025)
```

---

## Summary

**You don't need SendGrid** - you have options:

1. **MailHog** (testing) - Catches emails locally, perfect for development
2. **Postfix** (production) - Full SMTP server, self-hosted
3. **Gmail SMTP** (easy) - Uses Gmail as relay, not fully self-hosted
4. **Email aliases** (advanced) - Custom `user@soulfra.com` addresses

**For friends/family testing RIGHT NOW**:
```bash
# Install MailHog
brew install mailhog  # or download for Linux

# Start MailHog
mailhog

# All emails appear at http://localhost:8025
# Zero config, zero cost, works offline
```

**Later, for production**:
- Install Postfix
- Configure domain DNS (SPF, DKIM)
- Set up email aliases
- Deploy on VPS with static IP

**But you can test EVERYTHING without email working** - just use QR codes for passwordless login!

---

**Related Docs**:
- `LOCALHOST_TESTING_GUIDE.md` - Friends/family testing without email
- `qr_auth.py` - Passwordless authentication (no email needed)
- `READTHEDOCS_ARCHITECTURE.md` - Email alias system architecture

**Start testing!** 🚀
