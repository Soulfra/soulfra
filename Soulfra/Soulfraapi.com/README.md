# Soulfraapi.com - Account Creation & Session API

**Purpose:** Backend API for QR-based account creation and session management

## What This Does

Flask API that:
1. Creates user accounts from QR scan
2. Generates session tokens
3. Validates sessions for soulfra.ai
4. Stores user data in SQLite

## Flow

```
User scans QR on soulfra.com
    ↓
GET /qr-signup?ref=landing
    ↓
Create account + session token
    ↓
Redirect to soulfra.ai/?session=TOKEN
```

## API Endpoints

### `GET /qr-signup`
Creates account from QR scan, returns redirect to soulfra.ai

**Query params:**
- `ref` (optional): Referral source (landing, qr, etc.)

**Response:**
```
HTTP 302 Redirect
Location: http://localhost:5003/?session=ABC123XYZ
```

**Example:**
```bash
curl -L http://localhost:5002/qr-signup?ref=landing
```

### `POST /validate-session`
Validates session token

**Body:**
```json
{
  "token": "SESSION_TOKEN_HERE"
}
```

**Response:**
```json
{
  "valid": true,
  "user_id": 123,
  "username": "CoolSoul456",
  "email": null,
  "created_at": "2025-12-31T10:30:00"
}
```

**Example:**
```bash
curl -X POST http://localhost:5002/validate-session \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN"}'
```

### `GET /account/<user_id>`
Get account info by user ID

**Response:**
```json
{
  "id": 123,
  "username": "CoolSoul456",
  "email": null,
  "created_at": "2025-12-31T10:30:00",
  "ref_source": "landing",
  "is_active": true
}
```

### `GET /stats`
Get API statistics

**Response:**
```json
{
  "total_users": 50,
  "active_sessions": 12,
  "ref_sources": {
    "landing": 30,
    "qr": 15,
    "direct": 5
  }
}
```

### `GET /health`
Health check

**Response:**
```json
{
  "status": "healthy",
  "service": "soulfraapi.com",
  "timestamp": "2025-12-31T10:30:00"
}
```

## Installation

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/soulfra/Soulfraapi.com
pip3 install -r requirements.txt
```

## Running Locally

```bash
python3 app.py
```

Runs on: http://localhost:5002

## Database

SQLite database: `soulfraapi.db`

**Tables:**

### `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ref_source TEXT,
    is_active BOOLEAN DEFAULT 1
);
```

### `sessions`
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    device_fingerprint TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Environment Variables

```bash
# Port (default: 5002)
export PORT=5002

# Where to redirect after signup (default: http://localhost:5003)
export SOULFRA_AI_URL=http://localhost:5003

# Session expiry in hours (default: 24)
export SESSION_EXPIRY_HOURS=24
```

## Testing Flow

1. Start API:
   ```bash
   python3 app.py
   ```

2. Simulate QR scan:
   ```bash
   curl -L http://localhost:5002/qr-signup?ref=test
   ```

3. Should redirect to soulfra.ai with session token

4. Check stats:
   ```bash
   curl http://localhost:5002/stats
   ```

## Deployment

### Option 1: Run on Laptop

```bash
# Expose to local network
python3 app.py
# API available at http://192.168.x.x:5002
```

### Option 2: Deploy to DigitalOcean

```bash
# Create droplet ($5/month)
# SSH in
git clone <your-repo>
cd soulfra/Soulfraapi.com
pip3 install -r requirements.txt

# Run with production settings
export SOULFRA_AI_URL=https://soulfra.ai
export PORT=5002
python3 app.py

# Set up nginx reverse proxy (optional)
# Point DNS: soulfraapi.com → droplet IP
```

### Option 3: Heroku (Free Tier)

```bash
# Add Procfile
echo "web: python3 app.py" > Procfile

# Deploy
heroku create soulfraapi
git push heroku main
```

## Security Notes

- Sessions expire after 24 hours (configurable)
- Tokens are cryptographically secure (32 bytes urlsafe)
- CORS enabled for soulfra.ai to call API
- Database is SQLite (consider PostgreSQL for production)

## Integration with Other Domains

**soulfra.com → soulfraapi.com:**
- QR code points to `/qr-signup` endpoint

**soulfraapi.com → soulfra.ai:**
- Redirects with session token after account creation

**soulfra.ai → soulfraapi.com:**
- Calls `/validate-session` to verify tokens
