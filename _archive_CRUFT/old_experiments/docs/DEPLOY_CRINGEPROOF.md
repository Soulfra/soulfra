# Cringeproof Deployment Guide

Complete guide for deploying the cringeproof personality assessment game.

## What is Cringeproof?

Cringeproof is a 7-question personality assessment game that evaluates users across multiple dimensions:

- **Binary Thinking** - Decision making patterns
- **Array Processing** - Information organization
- **Color Perception** - Emotional awareness
- **Hue Recognition** - Attention to detail
- **Yes/No Responses** - Decisiveness
- **Numerical Reasoning** - Analytical thinking
- **Text Expression** - Communication style

**Scoring System:**
- Each question scored 1-5 points
- Maximum score: 35 points
- Percentage-based levels: Master (80%+), Expert (60-79%), Intermediate (40-59%), Beginner (<40%)
- Category breakdown shows strengths and weaknesses
- AI-generated insights and personalized recommendations

## Features

### ✅ Already Working

1. **Anonymous Play** - Users can play without creating an account
2. **Logged-In Play** - Registered users automatically save results
3. **Account Linking** - Anonymous users can claim results after signup
4. **Neural Network Scoring** - 8 trained neural networks evaluate responses
5. **Dynamic Results** - Insights and recommendations generated per user
6. **Beautiful UI** - Gradient designs, animated progress bars, responsive layout

### 🔧 How It Works

#### Anonymous User Flow
```
User visits /cringeproof
  ↓
Answers 7 questions
  ↓
Submits form → POST /cringeproof/submit
  ↓
Saved to database with user_id=NULL
  ↓
Redirected to /cringeproof/results/<id>
  ↓
Sees yellow box: "💾 Save Your Results!"
  ↓
Clicks "Create Account & Save This Result"
  ↓
Redirected to /signup?claim_result=<id>
  ↓
Creates account
  ↓
Database UPDATE: user_id=NULL → user_id=<new_id>
  ↓
Redirected back to results
  ↓
Sees green box: "✅ Results saved to your profile!"
```

#### Logged-In User Flow
```
User visits /cringeproof (already logged in)
  ↓
Answers 7 questions
  ↓
Submits form → POST /cringeproof/submit
  ↓
Saved to database with user_id=<current_user>
  ↓
Redirected to /cringeproof/results/<id>
  ↓
Sees green box: "✅ Results saved to your profile!"
```

## Deployment Steps

### 1. Prerequisites

- Python 3.9+
- SQLite database with migrations run
- Flask app running
- Neural networks trained and loaded

Verify prerequisites:
```bash
python3 --version  # Should be 3.9+
python3 -c "from database import get_db; db = get_db(); print('✅ Database connected')"
python3 -c "from cringeproof import NETWORKS; print(f'✅ {len(NETWORKS)} neural networks loaded')"
```

### 2. Verify Cringeproof Routes

Check that all routes are registered:

```bash
# List all cringeproof routes
grep -n "route.*cringeproof" app.py

# Should see:
# - /cringeproof (GET)
# - /cringeproof/submit (POST)
# - /cringeproof/results/<int:result_id> (GET)
```

Expected output:
```
8972:@app.route('/cringeproof', methods=['GET', 'POST'])
8988:@app.route('/cringeproof/submit', methods=['POST'])
9032:@app.route('/cringeproof/results/<int:result_id>')
```

### 3. Test Locally

Run the automated test suite:

```bash
python3 test_anonymous_claim.py
```

Expected output:
```
================================================================================
TEST: Anonymous Play → Signup → Claim Flow
================================================================================

[STEP 1] Playing cringeproof anonymously...
✅ Loaded cringeproof game page
✅ Game submitted, redirecting to: /cringeproof/results/X

[STEP 2] Verifying result X is anonymous...
✅ Result X is anonymous (user_id=NULL)

[STEP 3] Viewing results page...
✅ Results page shows signup prompt with claim link

[STEP 4] Creating account to claim result...
✅ Signup successful, redirecting to: /cringeproof/results/X

[STEP 5] Verifying result was claimed...
✅ New user created with ID: Y
✅ Result X successfully claimed by user Y

[STEP 6] Verifying results page shows confirmation...
✅ Results page shows confirmation message

================================================================================
✅ ALL TESTS PASSED - Anonymous claim flow works!
================================================================================
```

### 4. Manual Browser Testing

1. **Anonymous Play**
   ```
   1. Open browser in incognito mode
   2. Visit http://localhost:5001/cringeproof
   3. Answer all 7 questions
   4. Submit form
   5. Verify redirect to results page
   6. Verify yellow "Save Your Results!" box appears
   7. Click "Create Account & Save This Result"
   8. Fill out signup form
   9. Verify redirect back to results
   10. Verify green "Results saved to your profile!" box appears
   ```

2. **Logged-In Play**
   ```
   1. Log in to account
   2. Visit http://localhost:5001/cringeproof
   3. Answer all 7 questions
   4. Submit form
   5. Verify redirect to results page
   6. Verify green "Results saved to your profile!" box appears
   7. No signup prompt should appear
   ```

### 5. Production Deployment

#### Option A: Same Server as Main App

Cringeproof is already integrated into app.py - just deploy normally:

```bash
# On production server
cd /var/www/soulfra-simple
git pull origin main

# Restart gunicorn
sudo systemctl restart soulfra

# Check status
sudo systemctl status soulfra
curl https://yourdomain.com/cringeproof
```

#### Option B: Dedicated Domain/Subdomain

If deploying to separate domain (e.g., cringeproof.yourdomain.com):

1. **Update BASE_URL in config.py**:
   ```python
   BASE_URL = "https://cringeproof.yourdomain.com"
   ```

2. **Configure nginx**:
   ```nginx
   server {
       server_name cringeproof.yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:5001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Get SSL certificate**:
   ```bash
   sudo certbot --nginx -d cringeproof.yourdomain.com
   ```

### 6. Database Migration

If deploying to new database, ensure game_results table exists:

```sql
-- Check if table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='game_results';

-- If missing, run migration
CREATE TABLE IF NOT EXISTS game_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    game_type TEXT NOT NULL,
    result_data TEXT NOT NULL,  -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_game_results_user ON game_results(user_id);
CREATE INDEX IF NOT EXISTS idx_game_results_game_type ON game_results(game_type);
CREATE INDEX IF NOT EXISTS idx_game_results_created ON game_results(created_at);
```

## Configuration

### Environment Variables

Optional environment variables to customize behavior:

```bash
# Base URL for links (default: http://localhost:5001)
export BASE_URL="https://yourdomain.com"

# Database path (default: soulfra.db)
export DATABASE_PATH="/var/www/soulfra-simple/soulfra.db"

# Flask secret key (required for sessions)
export FLASK_SECRET_KEY="your-secret-key-here"
```

### Feature Flags

In config.py:

```python
# Enable/disable anonymous play
ALLOW_ANONYMOUS_PLAY = True

# Enable/disable result claiming
ALLOW_RESULT_CLAIMING = True

# Neural networks to use for scoring
CRINGEPROOF_NETWORKS = ['calriven', 'theauditor', 'deathtodata', 'soulfra_judge']
```

## Monitoring

### Key Metrics to Track

1. **Game Completion Rate**
   ```sql
   SELECT
     COUNT(*) as total_plays,
     COUNT(CASE WHEN user_id IS NOT NULL THEN 1 END) as claimed_results,
     ROUND(100.0 * COUNT(CASE WHEN user_id IS NOT NULL THEN 1 END) / COUNT(*), 2) as claim_rate
   FROM game_results
   WHERE game_type = 'cringeproof';
   ```

2. **Score Distribution**
   ```sql
   SELECT
     CAST(json_extract(result_data, '$.percentage') AS INTEGER) as score_range,
     COUNT(*) as count
   FROM game_results
   WHERE game_type = 'cringeproof'
   GROUP BY score_range
   ORDER BY score_range;
   ```

3. **Recent Activity**
   ```sql
   SELECT
     id,
     user_id,
     created_at,
     json_extract(result_data, '$.level') as level,
     json_extract(result_data, '$.percentage') as score
   FROM game_results
   WHERE game_type = 'cringeproof'
   ORDER BY created_at DESC
   LIMIT 10;
   ```

### Logs to Watch

```bash
# Application logs
tail -f /var/log/soulfra/app.log | grep cringeproof

# Nginx access logs
tail -f /var/log/nginx/access.log | grep cringeproof

# Look for errors
tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Issue: Results page redirects to /cringeproof

**Cause**: Form submission failing validation

**Fix**: Check that all 7 questions are answered
```python
# In app.py:8998-9010
responses = {}
for i in range(1, 8):  # 7 questions
    key = f'q{i}'
    value = request.form.get(key)
    if value:
        responses[i] = int(value)

if len(responses) != 7:
    flash('Please answer all 7 questions', 'error')
    return redirect(url_for('cringeproof_game'))
```

**Debug**:
```bash
# Check server logs for error message
grep "Please answer all 7 questions" /var/log/soulfra/app.log
```

### Issue: Signup doesn't claim result

**Cause**: claim_result parameter not being passed or processed

**Fix**: Verify the signup route handles claim_result
```python
# In app.py:4407-4471
claim_result_id = request.args.get('claim_result') or request.form.get('claim_result')
if claim_result_id:
    db.execute('''
        UPDATE game_results
        SET user_id = ?
        WHERE id = ? AND user_id IS NULL
    ''', (user['id'], int(claim_result_id)))
```

**Debug**:
```bash
# Check if parameter is in URL
curl -I "http://localhost:5001/signup?claim_result=123"

# Check database
sqlite3 soulfra.db "SELECT id, user_id FROM game_results WHERE id = 123;"
```

### Issue: Neural networks not loading

**Cause**: Networks not trained or not in database

**Fix**: Run neural network training script
```bash
python3 train_neural_networks.py
```

**Verify**:
```python
from cringeproof import NETWORKS
print(f"Loaded {len(NETWORKS)} networks")
for name in NETWORKS.keys():
    print(f"  - {name}")
```

### Issue: Results page shows wrong UI

**Cause**: Template not passing is_anonymous variable

**Fix**: Verify cringeproof_results route passes all variables
```python
# In app.py:9032-9055
user_id = session.get('user_id')
is_anonymous = (result['user_id'] is None)

return render_template(
    'cringeproof/results.html',
    score_data=score_data,
    insights=insights,
    recommendations=recommendations,
    result_id=result_id,
    user_id=user_id,
    is_anonymous=is_anonymous  # ← Must be present
)
```

**Debug**:
```bash
# Check template rendering
grep "is_anonymous" templates/cringeproof/results.html
```

## Performance Optimization

### Database Indexes

Ensure indexes exist for fast queries:

```sql
-- Check existing indexes
SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='game_results';

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_game_results_user ON game_results(user_id);
CREATE INDEX IF NOT EXISTS idx_game_results_game_type ON game_results(game_type);
CREATE INDEX IF NOT EXISTS idx_game_results_created ON game_results(created_at);
```

### Caching Neural Networks

Neural networks are cached in memory on app startup. To reload:

```bash
# Restart Flask app
sudo systemctl restart soulfra

# Or in development
# Ctrl+C and restart python3 app.py
```

### Static Assets

For production, serve static assets via nginx:

```nginx
location /static/ {
    alias /var/www/soulfra-simple/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Security Checklist

- ✅ CSRF protection enabled (Flask-WTF)
- ✅ SQL injection prevented (parameterized queries)
- ✅ XSS protection (Jinja2 auto-escaping)
- ✅ HTTPS enabled (certbot)
- ✅ Session secret key set (config.py)
- ✅ User input validated (server-side)
- ✅ Anonymous results isolated (user_id=NULL)

## Next Steps

### Optional Enhancements

1. **QR Code Signup** (already built in qr_signup.py)
   - Display QR code on results page
   - User scans to create account
   - Auto-links results

2. **Social Sharing**
   - "Share Results" button
   - Generate shareable image
   - Social media meta tags

3. **Leaderboard**
   - Top scores by level
   - Category rankings
   - Anonymous vs. logged-in

4. **Analytics Dashboard**
   - Play rates
   - Conversion rates
   - Score distributions

## Support

**Documentation**: See README.md and DEPLOYMENT.md
**Code**: app.py (routes), cringeproof.py (game logic), templates/cringeproof/
**Database**: soulfra.db (game_results table)
**Tests**: test_anonymous_claim.py

For issues, check logs and run test suite:
```bash
python3 test_anonymous_claim.py
```

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Status**: Production Ready ✅
