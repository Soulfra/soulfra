# Email Stack Setup - Run Your Own Email Server

**"How to do our own email services like Microsoft and Google"**

Complete guide to running your own email infrastructure with brand-specific addresses.

---

## 🎯 What You're Building

```
┌────────────────────────────────────────────────────────────────┐
│              COMPLETE EMAIL INFRASTRUCTURE                      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SMTP SERVER (Postfix)                                         │
│    Send & receive mail for @soulfra.com                        │
│                                                                 │
│  IMAP SERVER (Dovecot)                                         │
│    Access mailboxes from email clients                         │
│                                                                 │
│  EMAIL SIGNING (OpenDKIM)                                      │
│    Prevent spam classification                                 │
│                                                                 │
│  DNS RECORDS                                                   │
│    MX, SPF, DKIM, DMARC configuration                          │
│                                                                 │
│  BRAND EMAIL ADDRESSES                                         │
│    noreply@ocean-dreams.soulfra.com                           │
│    hello@brand-name.soulfra.com                               │
│                                                                 │
│  WEB INTEGRATION                                               │
│    Queue emails from Flask app                                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

### What You Need

```
✅ Domain name (soulfra.com)
✅ Server with static IP (VPS like DigitalOcean, $5/month)
✅ Ubuntu 22.04 LTS (or similar Linux)
✅ Root access (sudo)
✅ DNS access (Cloudflare, Namecheap, etc.)
```

### Why Not Gmail/SendGrid?

**Pros of Self-Hosted:**
- ✅ Full control & privacy
- ✅ Brand-specific addresses (noreply@brand.soulfra.com)
- ✅ No monthly API costs
- ✅ Unlimited emails
- ✅ Learn infrastructure

**Cons:**
- ❌ More complex setup
- ❌ Maintain server yourself
- ❌ Risk of being marked as spam (if misconfigured)
- ❌ Need to monitor deliverability

**Hybrid Approach (Best):**
- Self-hosted for receiving + low-volume sending
- AWS SES for bulk newsletters (cheap, reliable)

---

## 🔧 Part 1: Install Email Stack

### Step 1: Update System

```bash
# SSH into your server
ssh root@your-server-ip

# Update packages
sudo apt update && sudo apt upgrade -y

# Set hostname
sudo hostnamectl set-hostname mail.soulfra.com

# Verify
hostname -f  # Should show: mail.soulfra.com
```

### Step 2: Install Postfix (SMTP Server)

```bash
# Install Postfix
sudo apt install postfix -y

# During install, select:
#   1. "Internet Site"
#   2. System mail name: soulfra.com
```

**Configure Postfix (`/etc/postfix/main.cf`):**

```bash
sudo nano /etc/postfix/main.cf
```

```ini
# Basic settings
myhostname = mail.soulfra.com
mydomain = soulfra.com
myorigin = $mydomain

# Network
inet_interfaces = all
inet_protocols = ipv4

# Mail directories
home_mailbox = Maildir/
mailbox_size_limit = 0
recipient_delimiter = +

# Virtual domains (for brands)
virtual_alias_domains = ocean-dreams.soulfra.com, testbrand.soulfra.com
virtual_alias_maps = hash:/etc/postfix/virtual

# TLS/SSL (for secure connections)
smtpd_tls_cert_file = /etc/letsencrypt/live/mail.soulfra.com/fullchain.pem
smtpd_tls_key_file = /etc/letsencrypt/live/mail.soulfra.com/privkey.pem
smtpd_use_tls = yes
smtpd_tls_security_level = may

# Authentication
smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
smtpd_sasl_auth_enable = yes

# Restrictions (anti-spam)
smtpd_recipient_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination
```

### Step 3: Install Dovecot (IMAP Server)

```bash
sudo apt install dovecot-imapd dovecot-lmtpd -y
```

**Configure Dovecot (`/etc/dovecot/dovecot.conf`):**

```bash
sudo nano /etc/dovecot/dovecot.conf
```

```ini
# Listen on all interfaces
listen = *, ::

# Protocols
protocols = imap lmtp

# Mail location
mail_location = maildir:~/Maildir

# Authentication
auth_mechanisms = plain login

# SSL
ssl = required
ssl_cert = </etc/letsencrypt/live/mail.soulfra.com/fullchain.pem
ssl_key = </etc/letsencrypt/live/mail.soulfra.com/privkey.pem
```

**Enable authentication (`/etc/dovecot/conf.d/10-auth.conf`):**

```bash
sudo nano /etc/dovecot/conf.d/10-auth.conf
```

```ini
disable_plaintext_auth = yes
auth_mechanisms = plain login
```

### Step 4: Install OpenDKIM (Email Signing)

```bash
sudo apt install opendkim opendkim-tools -y
```

**Configure OpenDKIM (`/etc/opendkim.conf`):**

```bash
sudo nano /etc/opendkim.conf
```

```ini
# Logging
Syslog yes
SyslogSuccess yes
LogWhy yes

# Common settings
Canonicalization relaxed/simple
Mode sv
SubDomains no

# Key location
KeyFile /etc/opendkim/keys/mail.private

# Domains
Domain soulfra.com
Selector mail
```

**Generate DKIM keys:**

```bash
# Create keys directory
sudo mkdir -p /etc/opendkim/keys
cd /etc/opendkim/keys

# Generate key pair
sudo opendkim-genkey -s mail -d soulfra.com

# Set permissions
sudo chown opendkim:opendkim mail.private
sudo chmod 600 mail.private

# View public key (add to DNS)
cat mail.txt
```

### Step 5: SSL Certificates (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot -y

# Get certificate
sudo certbot certonly --standalone -d mail.soulfra.com

# Auto-renew
echo "0 0 1 * * certbot renew --quiet" | sudo crontab -
```

---

## 🌐 Part 2: DNS Configuration

### MX Records (Mail Exchange)

**Add to DNS (Cloudflare/Namecheap):**

```
Type: MX
Name: @
Value: mail.soulfra.com
Priority: 10
TTL: Auto
```

**Test:**

```bash
dig MX soulfra.com +short
# Should show: 10 mail.soulfra.com
```

### A Record (Mail Server IP)

```
Type: A
Name: mail
Value: 192.168.1.100  (your server IP)
TTL: Auto
```

### SPF Record (Sender Policy Framework)

**Tells recipients which servers can send mail for your domain:**

```
Type: TXT
Name: @
Value: v=spf1 mx ~all
TTL: Auto
```

**Explanation:**
- `v=spf1` - SPF version 1
- `mx` - Allow MX servers to send mail
- `~all` - Soft fail for others (mark as suspicious, don't reject)

### DKIM Record (DomainKeys Identified Mail)

**Add public key from `/etc/opendkim/keys/mail.txt`:**

```
Type: TXT
Name: mail._domainkey
Value: v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC...
TTL: Auto
```

### DMARC Record (Domain-based Message Authentication)

**Tells recipients what to do with failed SPF/DKIM:**

```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc@soulfra.com
TTL: Auto
```

**Explanation:**
- `p=quarantine` - Put failed emails in spam
- `rua=mailto:...` - Send aggregate reports here

### Reverse DNS (PTR Record)

**Must be set via your hosting provider (DigitalOcean, AWS, etc.):**

```
IP: 192.168.1.100
PTR: mail.soulfra.com
```

**Verify:**

```bash
dig -x 192.168.1.100 +short
# Should show: mail.soulfra.com
```

---

## 📬 Part 3: Virtual Email Addresses (Brands)

### Setup Virtual Aliases

**Create `/etc/postfix/virtual`:**

```bash
sudo nano /etc/postfix/virtual
```

```
# Generic soulfra.com addresses
noreply@soulfra.com         postmaster
hello@soulfra.com           admin
support@soulfra.com         admin

# Ocean Dreams brand
noreply@ocean-dreams.soulfra.com    oceanteam
hello@ocean-dreams.soulfra.com      oceanteam
support@ocean-dreams.soulfra.com    oceanteam

# TestBrand
noreply@testbrand.soulfra.com       testteam
hello@testbrand.soulfra.com         testteam
```

**Compile the alias map:**

```bash
sudo postmap /etc/postfix/virtual
sudo systemctl reload postfix
```

### Create User Mailboxes

```bash
# Create system users (one per brand or shared)
sudo adduser --system --no-create-home --shell /bin/false --group oceanteam
sudo adduser --system --no-create-home --shell /bin/false --group testteam
sudo adduser --system --no-create-home --shell /bin/false --group postmaster
sudo adduser --system --no-create-home --shell /bin/false --group admin

# Create mail directories
sudo mkdir -p /var/mail/vhosts/soulfra.com/oceanteam
sudo mkdir -p /var/mail/vhosts/soulfra.com/testteam
sudo chown -R mail:mail /var/mail/vhosts
```

### Automated Brand Email Creation

**Python script to auto-create brand emails:**

```python
#!/usr/bin/env python3
"""
Auto-create email addresses for new brands

When brand is created in database, automatically:
1. Add virtual aliases
2. Create mailbox directory
3. Reload Postfix
"""

import subprocess
from database import get_db

def setup_brand_email(brand_slug, brand_name):
    """
    Setup email addresses for brand

    Creates:
      - noreply@{brand-slug}.soulfra.com
      - hello@{brand-slug}.soulfra.com
      - support@{brand-slug}.soulfra.com

    All route to: {brand-slug}team
    """

    # Create system user (mailbox)
    mailbox_user = f"{brand_slug}team"

    subprocess.run([
        'sudo', 'adduser',
        '--system',
        '--no-create-home',
        '--shell', '/bin/false',
        '--group', mailbox_user
    ])

    # Create mail directory
    subprocess.run([
        'sudo', 'mkdir', '-p',
        f'/var/mail/vhosts/soulfra.com/{mailbox_user}'
    ])

    subprocess.run([
        'sudo', 'chown', '-R', 'mail:mail',
        '/var/mail/vhosts'
    ])

    # Add virtual aliases
    aliases = [
        f"noreply@{brand_slug}.soulfra.com    {mailbox_user}",
        f"hello@{brand_slug}.soulfra.com      {mailbox_user}",
        f"support@{brand_slug}.soulfra.com    {mailbox_user}"
    ]

    with open('/etc/postfix/virtual', 'a') as f:
        f.write(f"\n# {brand_name}\n")
        for alias in aliases:
            f.write(f"{alias}\n")

    # Recompile virtual map
    subprocess.run(['sudo', 'postmap', '/etc/postfix/virtual'])

    # Reload Postfix
    subprocess.run(['sudo', 'systemctl', 'reload', 'postfix'])

    print(f"✅ Created email addresses for {brand_name}")
    print(f"   noreply@{brand_slug}.soulfra.com")
    print(f"   hello@{brand_slug}.soulfra.com")
    print(f"   support@{brand_slug}.soulfra.com")


# Usage
if __name__ == '__main__':
    setup_brand_email('ocean-dreams', 'Ocean Dreams')
```

---

## 📤 Part 4: Sending Email from Flask App

### Method 1: Direct SMTP (Simple)

```python
import smtplib
from email.mime.text import MIMEText

def send_email_via_postfix(to, subject, body, from_addr='noreply@soulfra.com'):
    """Send email via local Postfix server"""

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to

    # Connect to local Postfix
    server = smtplib.SMTP('localhost', 25)

    try:
        server.sendmail(from_addr, [to], msg.as_string())
        print(f"✅ Sent email to {to}")
    except Exception as e:
        print(f"❌ Failed to send: {e}")
    finally:
        server.quit()
```

### Method 2: Email Queue (Better)

**Use existing `email_server.py` but connect to local Postfix:**

```python
from email_server import queue_email, send_queued_emails

# Queue email
queue_email(
    from_addr='noreply@ocean-dreams.soulfra.com',
    to_addrs=['user@example.com'],
    subject='Welcome to Ocean Dreams',
    body='Thanks for subscribing!'
)

# Send queued emails via Postfix
send_queued_emails(
    dry_run=False,
    smtp_config={
        'host': 'localhost',
        'port': 25,
        'username': None,  # No auth needed for localhost
        'password': None
    }
)
```

### Method 3: Background Worker (Best)

**Cron job to send queued emails:**

```bash
# Add to crontab
crontab -e

# Send queued emails every 5 minutes
*/5 * * * * cd /path/to/soulfra && python3 -c "from email_server import send_queued_emails; send_queued_emails(smtp_config={'host': 'localhost', 'port': 25})"
```

---

## 📥 Part 5: Receiving Email

### Configure Mail Delivery

**Update `/etc/postfix/main.cf`:**

```ini
# Use Dovecot for local delivery
mailbox_transport = lmtp:unix:private/dovecot-lmtp
```

**Dovecot LMTP (`/etc/dovecot/conf.d/10-master.conf`):**

```ini
service lmtp {
  unix_listener /var/spool/postfix/private/dovecot-lmtp {
    mode = 0600
    user = postfix
    group = postfix
  }
}
```

**Restart services:**

```bash
sudo systemctl restart postfix
sudo systemctl restart dovecot
```

### Access Email via IMAP

**From Python:**

```python
import imaplib
import email

def check_brand_email(mailbox='oceanteam', password='your_password'):
    """Check emails for brand mailbox"""

    # Connect to Dovecot IMAP
    mail = imaplib.IMAP4_SSL('mail.soulfra.com', 993)

    # Login
    mail.login(mailbox, password)

    # Select inbox
    mail.select('INBOX')

    # Search for unread emails
    status, messages = mail.search(None, 'UNSEEN')

    email_ids = messages[0].split()

    for email_id in email_ids:
        # Fetch email
        status, msg_data = mail.fetch(email_id, '(RFC822)')

        # Parse email
        msg = email.message_from_bytes(msg_data[0][1])

        print(f"From: {msg['From']}")
        print(f"Subject: {msg['Subject']}")
        print(f"Body: {msg.get_payload()}")
        print("---")

    mail.logout()
```

**Or use email client (Thunderbird, Apple Mail, etc.):**

```
Incoming Mail (IMAP):
  Server: mail.soulfra.com
  Port: 993
  Security: SSL/TLS
  Username: oceanteam
  Password: (set during user creation)

Outgoing Mail (SMTP):
  Server: mail.soulfra.com
  Port: 587
  Security: STARTTLS
  Authentication: Same as incoming
```

---

## 🧪 Part 6: Testing

### Test 1: Send Test Email

```bash
# From server
echo "Test email body" | mail -s "Test Subject" user@example.com
```

### Test 2: Check DNS Records

```bash
# MX
dig MX soulfra.com +short

# SPF
dig TXT soulfra.com +short

# DKIM
dig TXT mail._domainkey.soulfra.com +short

# Reverse DNS
dig -x YOUR_SERVER_IP +short
```

### Test 3: Deliverability Test

**Send test to:**
- Gmail (check if arrives in inbox or spam)
- mail-tester.com (get deliverability score)

```bash
echo "Test email from Postfix" | mail -s "Test" test-xxxx@mail-tester.com
# Visit mail-tester.com, check score (should be 8+/10)
```

### Test 4: Brand Email

```bash
# Send from brand address
echo "Hello from Ocean Dreams!" | mail -s "Test" -r "noreply@ocean-dreams.soulfra.com" user@example.com
```

---

## 🔒 Part 7: Security & Maintenance

### Firewall

```bash
# Allow SMTP, IMAP, HTTPS
sudo ufw allow 25/tcp    # SMTP
sudo ufw allow 587/tcp   # SMTP submission
sudo ufw allow 993/tcp   # IMAPS
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Fail2Ban (Anti-Brute Force)

```bash
sudo apt install fail2ban -y

# Configure Postfix/Dovecot jails
sudo nano /etc/fail2ban/jail.local
```

```ini
[postfix]
enabled = true

[dovecot]
enabled = true
```

```bash
sudo systemctl restart fail2ban
```

### Monitoring

```bash
# Check mail logs
sudo tail -f /var/log/mail.log

# Check queue
mailq

# Postfix status
sudo postfix status

# Dovecot status
sudo dovecot status
```

### Backups

```bash
# Backup mailboxes
sudo tar -czf mailboxes-backup-$(date +%Y%m%d).tar.gz /var/mail/vhosts

# Backup config
sudo tar -czf postfix-config-$(date +%Y%m%d).tar.gz /etc/postfix /etc/dovecot
```

---

## 📊 Part 8: Scaling & Hybrid Approach

### When to Use Self-Hosted

```
✅ Receiving mail (always)
✅ Transactional emails (password resets, confirmations)
✅ Low-volume newsletters (<1000/day)
✅ Brand-specific addresses
```

### When to Use AWS SES

```
✅ Bulk newsletters (10,000+)
✅ High deliverability critical
✅ Don't want to manage infrastructure
✅ Need detailed analytics
```

### Hybrid Setup

**Self-hosted Postfix for receiving:**
```
All incoming mail → Postfix → Dovecot → Your mailboxes
```

**AWS SES for bulk sending:**
```python
import boto3

ses = boto3.client('ses', region_name='us-east-1')

# Send via AWS SES instead of Postfix
ses.send_email(
    Source='noreply@ocean-dreams.soulfra.com',
    Destination={'ToAddresses': ['user@example.com']},
    Message={
        'Subject': {'Data': 'Newsletter'},
        'Body': {'Text': {'Data': 'Content...'}}
    }
)
```

**Cost comparison:**
```
Self-hosted: $5-10/month (fixed)
AWS SES: $0.10 per 1,000 emails (variable)

Break-even: ~5,000 emails/month
```

---

## 📋 Summary Checklist

### Setup

```
☐ Install Postfix, Dovecot, OpenDKIM
☐ Configure main.cf, dovecot.conf
☐ Generate DKIM keys
☐ Get SSL certificates (Let's Encrypt)
☐ Set DNS records (MX, SPF, DKIM, DMARC, PTR)
☐ Create virtual aliases for brands
☐ Test email sending/receiving
☐ Check deliverability score (mail-tester.com)
☐ Setup firewall & Fail2Ban
☐ Configure backups
```

### For Each New Brand

```
☐ Add to virtual_alias_domains in main.cf
☐ Create virtual aliases in /etc/postfix/virtual
☐ Run postmap /etc/postfix/virtual
☐ Reload Postfix
☐ Test brand email address
```

---

## 🚀 Quick Start Script

```bash
#!/bin/bash
# Email stack setup script

echo "🚀 Setting up email server for soulfra.com..."

# Install packages
sudo apt update
sudo apt install -y postfix dovecot-imapd dovecot-lmtpd opendkim opendkim-tools certbot

# Get SSL certificate
sudo certbot certonly --standalone -d mail.soulfra.com

# Generate DKIM keys
sudo mkdir -p /etc/opendkim/keys
cd /etc/opendkim/keys
sudo opendkim-genkey -s mail -d soulfra.com
sudo chown opendkim:opendkim mail.private

echo "✅ Email stack installed!"
echo ""
echo "Next steps:"
echo "1. Configure /etc/postfix/main.cf"
echo "2. Configure /etc/dovecot/dovecot.conf"
echo "3. Add DNS records (see /etc/opendkim/keys/mail.txt for DKIM)"
echo "4. Run: sudo systemctl restart postfix dovecot"
```

---

**You now have email infrastructure like Microsoft/Google - but for your brands!** 📧

**Addresses created:**
```
noreply@soulfra.com
hello@ocean-dreams.soulfra.com
support@testbrand.soulfra.com
... (auto-generated for each brand)
```
