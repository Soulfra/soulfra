# CringeProof Workflow - Voice Reactions to News Articles

## Complete End-to-End Flow

### Step 1: Scrape Real News Articles

```bash
# Scrape from Google News RSS
python3 news_scraper_cringeproof.py scrape --topics "ai,crypto,tech" --max-per-topic 5

# Or manually add a real article
sqlite3 soulfra.db "INSERT INTO news_articles (title, url, source, published_date, summary, topics, article_hash)
VALUES (
  'OpenAI Announces GPT-5 Release Date',
  'https://techcrunch.com/2024/01/15/openai-gpt5-announcement',
  'TechCrunch',
  '2024-01-15 10:00:00',
  'OpenAI CEO Sam Altman announces GPT-5 will launch in Q2 2024...',
  'ai',
  '$(echo -n "unique-content-hash" | sha256sum | cut -c1-16)'
);"
```

### Step 2: Record Voice Reaction

User records voice memo via localhost:5001/voice-capsule

This creates a row in `simple_voice_recordings` table with:
- `id` (e.g., 7)
- `transcription` (speech-to-text)
- `created_at` (timestamp)

### Step 3: Pair Voice with Article

```bash
# Get article ID from database
sqlite3 soulfra.db "SELECT id, title FROM news_articles ORDER BY scraped_at DESC LIMIT 5"

# Pair voice memo with article
python3 news_scraper_cringeproof.py pair \
  --recording-id 7 \
  --article-id 2 \
  --prediction "GPT-5 will be delayed until 2025, this is just hype" \
  --time-lock-days 90
```

This creates a **time-locked prediction**:
- Hash published immediately (proof of timestamp)
- Full transcript hidden for 90 days
- After 90 days, transcript unlocks and CringeProof score calculated

### Step 4: Create Live Call-In Show (Optional)

```bash
# Create NPR-style show for this article
python3 news_scraper_cringeproof.py create-show 2

# Output:
# ✅ Created CringeProof show #1
#    Article: OpenAI Announces GPT-5 Release Date
#    Call-in URL: http://192.168.1.87:5001/call-in/1
```

Now other users can call into the show and react to the same article.

### Step 5: Publish to Voice Archive

```bash
# Publish all unlocked pairings (time-lock expired)
python3 news_scraper_cringeproof.py publish-unlocked

# This creates markdown files in ~/soulfra-voice-archive/transcripts/
# Format: YYYY-MM-DD-HH-MM-cringeproof-{recording_id}.md
```

### Step 6: Push to GitHub Pages

```bash
cd ~/soulfra-voice-archive
git add .
git commit -m "CringeProof: Voice reactions to GPT-5 announcement"
git push
```

### Step 7: Access via Raw URLs

**GitHub Pages (rendered):**
```
https://soulfra.github.io/voice-archive/transcripts/2026-01-02-21-34-cringeproof-5.md
```

**Raw Content (for embedding):**
```
https://raw.githubusercontent.com/Soulfra/voice-archive/main/transcripts/2026-01-02-21-34-cringeproof-5.md
```

**Use raw URLs for:**
- Voice-only apps (read transcript aloud)
- Faceless content players
- Background audio while scrolling
- UGC reaction widgets
- AI voiceover generation

### Step 8: Calculate CringeProof Score (After Time Passes)

```bash
# After 90+ days, calculate how badly the prediction aged
python3 news_scraper_cringeproof.py score --article-id 2 --min-days 90

# Output:
# 📊 CringeProof Score for Article #2
#    Age: 95 days
#    Cringe Score: 78/100  (prediction was very wrong)
#    Relevance Score: 22/100  (topic is now irrelevant)
#    Voice Reactions: 12
```

---

## Real-World Examples

### Example 1: Crypto Hype Article

```bash
# 1. Add real article
sqlite3 soulfra.db "INSERT INTO news_articles (title, url, source, published_date, summary, topics, article_hash)
VALUES (
  'Bitcoin to Hit $500K by End of Year, Analysts Say',
  'https://www.coindesk.com/markets/2024/01/10/bitcoin-500k-prediction',
  'CoinDesk',
  '2024-01-10 14:30:00',
  'Top crypto analysts predict Bitcoin will reach $500,000 by December 2024...',
  'crypto',
  'a1b2c3d4e5f6g7h8'
);"

# 2. Record skeptical voice memo
# (User records: "This is complete nonsense, BTC will probably crash to $20K")

# 3. Pair with 1-year time lock
python3 news_scraper_cringeproof.py pair \
  --recording-id 8 \
  --article-id 3 \
  --prediction "Bitcoin will crash to $20K, not rise to $500K" \
  --time-lock-days 365

# 4. One year later, see who was right
python3 news_scraper_cringeproof.py score --article-id 3 --min-days 365
```

### Example 2: AI Regulation Article

```bash
# 1. Add article
sqlite3 soulfra.db "INSERT INTO news_articles (title, url, source, published_date, summary, topics, article_hash)
VALUES (
  'EU Passes Strict AI Regulation Law',
  'https://www.theverge.com/2024/03/15/eu-ai-act-passes',
  'The Verge',
  '2024-03-15 09:00:00',
  'European Union approves comprehensive AI regulation framework...',
  'tech regulation',
  'eu-ai-reg-2024'
);"

# 2. Record voice reaction
# (User records: "This will kill European AI startups, talent will flee to US")

# 3. Pair with 6-month time lock
python3 news_scraper_cringeproof.py pair \
  --recording-id 9 \
  --article-id 4 \
  --prediction "EU AI talent exodus to US within 6 months" \
  --time-lock-days 180

# 4. After 6 months, calculate cringe score
python3 news_scraper_cringeproof.py score --article-id 4 --min-days 180
```

---

## UGC Army Strategy

### How to Build Reaction Ecosystem:

1. **Host publishes article** → Creates live call-in show
2. **Listeners record voice reactions** → Submit via /call-in endpoint
3. **Host approves reactions** → Pairs with sponsors/ads
4. **Reactions publish to archive** → GitHub Pages + raw URLs
5. **Community builds on top** → Voice apps, faceless content, AI voiceovers
6. **CringeProof scores reveal winners** → Gamification of predictions

### Raw URL Use Cases:

```bash
# Fetch raw markdown for voice app
curl https://raw.githubusercontent.com/Soulfra/voice-archive/main/transcripts/2026-01-02-21-34-cringeproof-5.md

# Parse transcript for AI voiceover
grep "## Voice Reaction" -A 10 file.md | ollama run llama3.2-vision

# Embed in faceless video generator
python3 generate_faceless_video.py --transcript-url https://raw.githubusercontent.com/...

# Feed to TTS for background audio
curl https://raw.githubusercontent.com/... | grep -A 100 "## Voice Reaction" | say
```

---

## Database Schema Reference

### news_articles
```sql
CREATE TABLE news_articles (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,  -- Real article URL (e.g., TechCrunch, CoinDesk)
    source TEXT,
    published_date TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    summary TEXT,
    topics TEXT,
    article_hash TEXT,
    cringe_score REAL DEFAULT 0.0,
    relevance_score REAL DEFAULT 0.0
);
```

### voice_article_pairings
```sql
CREATE TABLE voice_article_pairings (
    id INTEGER PRIMARY KEY,
    recording_id INTEGER REFERENCES simple_voice_recordings(id),
    article_id INTEGER REFERENCES news_articles(id),
    paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_prediction TEXT,
    time_lock_until TIMESTAMP,
    published_to_archive BOOLEAN DEFAULT 0,
    live_show_id INTEGER,
    cringe_factor REAL DEFAULT 0.0
);
```

---

## Next Steps

1. **Hook up real RSS scraper** with rate-limit handling
2. **Add voice fingerprinting** (Ollama analysis of prosody/cadence)
3. **Auto-calculate CringeProof scores** using AI after time-lock expires
4. **Build UGC reaction widget** for embedding on websites
5. **Add screenshot/image support** for visual articles
6. **Create leaderboard** of best/worst predictions
7. **Monetize via sponsors** (pair ads with reactions like NPR)

---

## Quick Reference Commands

```bash
# Scrape news
python3 news_scraper_cringeproof.py scrape --topics "ai,crypto,tech"

# Pair voice with article
python3 news_scraper_cringeproof.py pair --recording-id X --article-id Y --prediction "..." --time-lock-days N

# Create live show
python3 news_scraper_cringeproof.py create-show ARTICLE_ID

# Publish unlocked pairings
python3 news_scraper_cringeproof.py publish-unlocked

# Calculate cringe score
python3 news_scraper_cringeproof.py score --article-id X --min-days N

# Push to GitHub
cd ~/soulfra-voice-archive && git add . && git commit -m "New reactions" && git push
```
