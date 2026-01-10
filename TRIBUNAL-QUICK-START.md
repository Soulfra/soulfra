# 🚀 Tribunal System - Quick Start Guide

**Get the CringeProof 3-way filter system running with email notifications**

---

## ✅ What You Have

1. ✅ **Blamechain** - Message edit tracking with SHA-256 hashes
2. ✅ **CringeProof Persona Assignment** - Match users to CalRiven/Soulfra/Death ToData
3. ✅ **3-Way Tribunal** - AI debate system with consensus voting
4. ✅ **Email Notifications** - Gmail SMTP with BCC delivery tracking
5. ✅ **Encryption** - Ready for AES-256 message encryption

---

## 🔧 Setup (5 Minutes)

### Step 1: Configure Email (Gmail)

**Get Gmail App Password**:
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and generate password
3. Copy the 16-character password

**Update `.env` file**:
```bash
# Replace these lines in .env:
SMTP_USER=your-actual-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password-here
SMTP_BCC=your-actual-email@gmail.com  # BCC yourself to track delivery
```

### Step 2: Generate Encryption Key

```bash
# Generate 64-character hex key for blamechain encryption
python3 -c "import secrets; print(secrets.token_hex(32))"

# Copy output and paste into .env:
ENCRYPTION_KEY=<paste-64-char-hex-here>
```

### Step 3: Apply Database Migration

```bash
# Add blamechain tables
sqlite3 soulfra.db < migrations/add_blamechain.sql

# Add persona assignment column
sqlite3 soulfra.db "ALTER TABLE users ADD COLUMN ai_persona_id INTEGER REFERENCES users(id)" 2>/dev/null || echo "Column already exists"
```

### Step 4: Integrate with Flask App

**Option A: Quick Test (Standalone)**

Test without integrating into main app:

```bash
# Test email system
python3 -c "
from tribunal_email_notifier import send_tribunal_verdict_email
result = send_tribunal_verdict_email(
    submission_id=1,  # Use existing submission ID
    recipient_emails=['test@example.com']
)
print(result)
"
```

**Option B: Full Integration (Production)**

Add to `app.py`:

```python
# At top of app.py, add:
from blamechain import init_blamechain
from cringeproof_personas import init_cringeproof_personas
from tribunal_blamechain import init_tribunal_blamechain

# After app = Flask(__name__), add:
init_blamechain(app)
init_cringeproof_personas(app)
init_tribunal_blamechain(app)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
```

Then restart Flask:
```bash
python3 app.py
```

---

## 🎮 How to Use

### 1. Play CringeProof Game

```bash
# Visit in browser:
open http://192.168.1.87:5001/cringeproof

# Complete all 7 chapters
# Get assigned to CalRiven, Soulfra, or DeathToData
```

### 2. Check Your Persona

```bash
curl http://192.168.1.87:5001/api/cringeproof/my-persona
```

**Response**:
```json
{
  "assigned": true,
  "persona": {
    "persona_username": "calriven",
    "persona_display": "CalRiven",
    "persona_bio": "AI persona for Calriven brand. Intelligent, efficient"
  }
}
```

### 3. Send a Message (Gets Tracked)

```bash
curl -X POST http://192.168.1.87:5001/api/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "to_user_id": 2,
    "content": "Original message content"
  }'
```

### 4. Edit the Message (Blamechain Records It)

```bash
curl -X POST http://192.168.1.87:5001/api/blamechain/edit \
  -H "Content-Type: application/json" \
  -d '{
    "message_table": "messages",
    "message_id": 1,
    "new_content": "Edited message content",
    "edit_reason": "Fixed typo"
  }'
```

### 5. View Edit History

```bash
curl http://192.168.1.87:5001/api/blamechain/history/messages/1
```

**Response**:
```json
{
  "success": true,
  "total_versions": 2,
  "history": [
    {
      "version": 1,
      "content": "Original message content",
      "content_hash": "sha256...",
      "chain_hash": "sha256...",
      "suspicion_level": "NORMAL"
    },
    {
      "version": 2,
      "content": "Edited message content",
      "edit_reason": "Fixed typo",
      "content_hash": "sha256...",
      "previous_hash": "<v1_chain_hash>",
      "chain_hash": "sha256...",
      "suspicion_level": "NORMAL"
    }
  ]
}
```

### 6. Flag for Tribunal

```bash
curl -X POST http://192.168.1.87:5001/api/tribunal/submit-with-edits \
  -H "Content-Type: application/json" \
  -d '{
    "message_table": "messages",
    "message_id": 1,
    "accusation": "User is changing their story"
  }'
```

**What Happens**:
1. System retrieves all edit history
2. CalRiven analyzes from logic perspective
3. Soulfra analyzes for balance/fairness
4. DeathToData defends individual freedom
5. Consensus verdict calculated
6. **EMAIL SENT** to all participants with verdict
7. **BCC sent** to you for delivery tracking

**Email looks like**:

```
Subject: 🏛️ Tribunal Verdict: GUILTY

⚖️ Tribunal Verdict Reached
3-Way AI Debate Complete

Final Verdict: GUILTY

Reasoning: Soulfra and CalRiven agreed: Progressive edits obscure
original intent. Transparency violated.

3-Way AI Analysis:
🤖 CalRiven (Logic): REQUIRES_MORE_DATA (suspicion 65/100)
⚖️ Soulfra (Balance): GUILTY (suspicion 70/100)
🔥 DeathToData (Rebellion): INNOCENT (defends right to revise)

[View Full Tribunal Transcript →]
```

---

## 🔐 Self-Hosting with Encryption

### Enable Message Encryption

Update `blamechain.py` to encrypt before storing:

```python
from cryptography.fernet import Fernet
import os

# Load encryption key from .env
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY').encode()
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_content(content):
    """Encrypt message content before storage"""
    return cipher.encrypt(content.encode()).decode()

def decrypt_content(encrypted_content):
    """Decrypt message when retrieving"""
    return cipher.decrypt(encrypted_content.encode()).decode()

# In edit_message() function, change:
db.execute('''
    INSERT INTO message_history (content, ...)
    VALUES (?, ...)
''', (encrypt_content(new_content), ...))

# When retrieving, decrypt:
decrypted = decrypt_content(row['content'])
```

### Deploy to Your Own Server

**Option 1: Docker (Recommended)**

```bash
# Create Dockerfile
cat > Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5001
CMD ["python3", "app.py"]
EOF

# Build and run
docker build -t soulfra-tribunal .
docker run -p 5001:5001 --env-file .env soulfra-tribunal
```

**Option 2: Systemd Service**

```bash
# Create service file
sudo nano /etc/systemd/system/soulfra.service
```

```ini
[Unit]
Description=Soulfra Tribunal System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/soulfra-simple
Environment="PATH=/usr/bin:/usr/local/bin"
EnvironmentFile=/path/to/soulfra-simple/.env
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable soulfra
sudo systemctl start soulfra
sudo systemctl status soulfra
```

**Option 3: Railway/Heroku**

```bash
# Add Procfile
echo "web: python3 app.py" > Procfile

# Deploy to Railway
railway init
railway up

# Or Heroku
heroku create soulfra-tribunal
git push heroku main
```

---

## 🧪 Testing the Full Flow

### Test Script

```bash
#!/bin/bash

echo "1. Testing CringeProof persona assignment..."
curl -X POST http://localhost:5001/api/cringeproof/assign-persona \
  -H "Content-Type: application/json" \
  -d '{"session_id": 1}'

echo "\n2. Testing blamechain edit tracking..."
curl -X POST http://localhost:5001/api/blamechain/edit \
  -H "Content-Type: application/json" \
  -d '{
    "message_table": "messages",
    "message_id": 1,
    "new_content": "Test edit",
    "edit_reason": "Testing blamechain"
  }'

echo "\n3. Viewing edit history..."
curl http://localhost:5001/api/blamechain/history/messages/1

echo "\n4. Running 3-way tribunal analysis..."
curl http://localhost:5001/api/tribunal/analyze-edits/messages/1

echo "\n5. Submitting to tribunal (triggers email)..."
curl -X POST http://localhost:5001/api/tribunal/submit-with-edits \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": 1,
    "message_table": "messages",
    "accusation": "Test case"
  }'

echo "\n✅ Test complete! Check your email for verdict notification."
```

Save as `test_tribunal.sh` and run:
```bash
chmod +x test_tribunal.sh
./test_tribunal.sh
```

---

## 📧 Email Delivery Tracking

### Check if Emails Sent

```bash
# Check Flask logs for email confirmations
tail -f flask.log | grep "Sent tribunal verdict"
```

### BCC Yourself

Every email sent will BCC to `SMTP_BCC` address in `.env`.

**Check your inbox** for:
- Subject: "🏛️ Tribunal Verdict: [VERDICT]"
- From: "Soulfra Tribunal <noreply@soulfra.com>"
- BCC: (your email - hidden from recipients)

### Troubleshooting Email Issues

**"SMTP authentication failed"**:
- Gmail App Password wrong
- 2-Step Verification not enabled
- Using regular password instead of app password

**"Connection refused"**:
- Port 587 blocked by firewall
- Try port 465 with SSL instead

**"Emails not arriving"**:
- Check spam folder
- Verify `SMTP_FROM_EMAIL` not blacklisted
- Try sending test email first

---

## 🎯 What's Next?

1. **Test Locally**: Run `test_tribunal.sh` to verify everything works
2. **Configure Email**: Add your real Gmail credentials to `.env`
3. **Deploy**: Choose Docker/Railway/Heroku for production
4. **Add Encryption**: Uncomment encryption code in `blamechain.py`
5. **Invite Users**: Share CringeProof game link
6. **Watch Debates**: See 3-way AI arguments in action

---

## 💡 Pro Tips

### Match Group / Dating App Comparison

You said "this reminds me of a dating app" - you're right!

**Dating App** → **CringeProof Tribunal**:
- Personality Quiz → CringeProof 7-chapter game
- Match Algorithm → Persona assignment (CalRiven/Soulfra/DeathToData)
- Swipe Left/Right → Answer 1-5 rating scale
- Chat → Tribunal debate transcript
- Message Receipts → Blamechain edit tracking
- Report User → Flag for tribunal
- Moderation → 3-way AI consensus voting

### Email as "Passthrough"

Your "BCC or some type of passthrough" concept = **Email relay system**:

- User submits to tribunal
- System analyzes (3 AI personas)
- Verdict reached
- **Passthrough**: Email goes to all participants + BCC to you
- You see delivery status via BCC inbox

### Self-Host Until It Takes Off

Your vision: "learn to encrypt and decentralize release and self host until it takes off"

**Phase 1 (Now)**: Self-hosted on `192.168.1.87:5001`
- Local development
- Test with roommates
- Free Ollama + Gmail SMTP

**Phase 2 (Growth)**: Docker container on DigitalOcean/Railway
- $5/month VPS
- Custom domain (play.soulfra.com)
- Still using free tier email

**Phase 3 (Scale)**: Kubernetes + SendGrid
- Auto-scaling
- Dedicated SMTP service
- CDN for static assets

---

## 🔗 Links

- **Play CringeProof**: http://192.168.1.87:5001/cringeproof
- **View Tribunal Cases**: http://192.168.1.87:5001/tribunal
- **Check Edit History**: http://192.168.1.87:5001/blamechain
- **Get Persona**: http://192.168.1.87:5001/api/cringeproof/my-persona

---

**Questions?** Check `ARCHITECTURE-3WAY-FILTER-SYSTEM.md` for full technical details.
