# Email System Setup

**Get Soulfra newsletters working with SMTP**

---

## Quick Setup (Gmail SMTP)

### 1. Get Gmail App Password

```
1. Go to Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate app password for "Mail"
4. Copy the 16-character password
```

### 2. Create config_secrets.py

```python
# config_secrets.py (git-ignored)
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'your-email@gmail.com'
SMTP_PASSWORD = 'your-app-password'  # 16-char from step 1
FROM_EMAIL = 'noreply@soulfra.com'
FROM_NAME = 'Soulfra Newsletter'
```

### 3. Update send_newsletter.py

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config_secrets import *
import sqlite3

def send_newsletter(brand_slug, post_id):
    """Send newsletter to brand subscribers"""

    # Get post details
    conn = sqlite3.connect('soulfra.db')
    cursor = conn.cursor()

    cursor.execute("SELECT title, content FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()

    # Get subscribers
    cursor.execute("SELECT email FROM subscribers WHERE confirmed = 1 AND unsubscribed_at IS NULL")
    subscribers = cursor.fetchall()

    # Create email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"New post: {post[0]}"
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"

    # HTML email
    html = f"""
    <html>
      <body>
        <h1>{post[0]}</h1>
        <p>{post[1][:200]}...</p>
        <p><a href="http://soulfra.com/post/{post_id}">Read full post →</a></p>
      </body>
    </html>
    """

    msg.attach(MIMEText(html, 'html'))

    # Send to each subscriber
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)

    for sub in subscribers:
        msg['To'] = sub[0]
        server.send_message(msg)
        print(f"✓ Sent to {sub[0]}")

    server.quit()
    conn.close()

# Usage
send_newsletter('deathtodata', 25)
```

---

## Alternative: SendGrid

Easier for high volume:

```bash
pip install sendgrid
```

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_with_sendgrid(to_email, subject, html_content):
    message = Mail(
        from_email='noreply@soulfra.com',
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )

    sg = SendGridAPIClient('YOUR_SENDGRID_API_KEY')
    response = sg.send(message)
    return response.status_code == 202
```

---

## Auto-Send on Post Creation

Add to app.py:

```python
@app.route('/api/posts/create', methods=['POST'])
def create_post():
    # ... create post logic ...

    post_id = cursor.lastrowid

    # Auto-send newsletter
    if request.json.get('send_newsletter'):
        send_newsletter(brand_slug, post_id)

    return jsonify({'success': True, 'post_id': post_id})
```

---

## Weekly Digest

```python
# weekly_digest.py
import schedule
import time

def send_weekly_digest():
    """Send weekly digest of all new posts"""
    # Get posts from last 7 days
    # Group by brand
    # Send one email per brand
    pass

# Run every Monday at 9am
schedule.every().monday.at("09:00").do(send_weekly_digest)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

---

## Email Templates

Create `templates/emails/`:

**newsletter.html:**
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: sans-serif; max-width: 600px; margin: 0 auto; }
    h1 { color: #667eea; }
    .cta { background: #667eea; color: white; padding: 12px 24px; text-decoration: none; }
  </style>
</head>
<body>
  <h1>{{ brand_name }} Newsletter</h1>
  <p>{{ post_title }}</p>
  <p>{{ post_excerpt }}</p>
  <a href="{{ post_url }}" class="cta">Read Full Post →</a>
  <hr>
  <p><small><a href="{{ unsubscribe_url }}">Unsubscribe</a></small></p>
</body>
</html>
```

---

## Test

```bash
python3 send_newsletter.py --test
# Sends test email to YOUR_EMAIL
```

That's it! Emails working.
