# Soulfra Simple + Cal-Riven AI Integration

## Overview

This integration bridges **Soulfra Simple** (newsletter platform) with **Cal-Riven** (multi-LLM AI system) to create an AI-powered workflow:

1. You write markdown posts in Soulfra Simple admin panel
2. Cal-Riven AI reads your posts and generates 3-brand perspective analysis:
   - 🔐 **Soulfra**: Security & encryption focus
   - 🕵️ **DeathToData**: Privacy & anti-surveillance focus
   - 💻 **CalRiven**: Technical architecture & data focus
3. AI commentary is automatically posted back to Soulfra Simple
4. You receive an email with the multi-perspective analysis
5. You review, approve, and publish the final newsletter

## Architecture

```
┌──────────────────┐         ┌─────────────────────┐         ┌────────────────┐
│ Soulfra Simple   │         │  Cal-Riven Bridge   │         │  Cal-Riven AI  │
│   (Flask App)    │────────▶│  (Python Script)    │────────▶│   (Ollama)     │
│                  │         │                     │         │                │
│  - Write posts   │         │  - Monitor new posts│         │  - Soulfra     │
│  - Admin panel   │         │  - Send to AI       │         │  - DeathToData │
│  - Database      │         │  - Create AI posts  │         │  - CalRiven    │
│                  │◀────────│  - Email you        │◀────────│                │
└──────────────────┘         └─────────────────────┘         └────────────────┘
     soulfra.db              cal_riven_bridge.py          generate_article_debate.py
```

## Setup

### 1. Migrate Database

Add new columns to existing Soulfra Simple database:

```bash
cd soulfra-simple
python migrate_db.py
```

This adds:
- `ai_processed` - Flag to prevent re-processing posts
- `source_post_id` - Links AI commentary to original posts

### 2. Configure Email (Optional)

If you want email alerts, set up SMTP:

```bash
export SMTP_EMAIL="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

See `emails.py` for Gmail setup instructions.

### 3. Ensure Cal-Riven Dependencies

The bridge requires Cal-Riven's `generate_article_debate.py`:

```bash
# Check it exists
ls ../python/generate_article_debate.py

# If missing, you need the full roommate-chat project
```

### 4. Ensure Ollama is Running

Cal-Riven uses Ollama for AI generation:

```bash
# Start Ollama (if not running)
ollama serve

# Pull required model (llama3.2:3b)
ollama pull llama3.2:3b
```

## Usage

### One-Time Processing

Process all unprocessed posts once:

```bash
python cal_riven_bridge.py
```

### Watch Mode (Recommended)

Continuously monitor for new posts every 30 seconds:

```bash
python cal_riven_bridge.py --watch
```

Keep this running in a terminal while you work!

### Process Specific Post

Manually trigger AI analysis for a specific post:

```bash
# By post ID
python cal_riven_bridge.py --process-id 1

# By slug
python cal_riven_bridge.py --process-id my-post-slug
```

## Workflow Example

### Step 1: Write a Post

Via admin panel (http://localhost:5001/admin):

```markdown
# My Thoughts on Web3 Privacy

Web3 claims to be decentralized, but most users still rely on centralized
infrastructure like Infura, Alchemy, and hosted wallets...

[Your full post content]
```

### Step 2: AI Analysis (Automatic)

If cal_riven_bridge.py is running in watch mode, it will:

1. Detect your new post
2. Send content to Cal-Riven AI
3. Generate 3 brand perspectives:
   - Soulfra analyzes from security/encryption angle
   - DeathToData analyzes from privacy/surveillance angle
   - CalRiven analyzes from technical/data angle
4. Create new post: "🤖 AI Analysis: My Thoughts on Web3 Privacy"
5. Email you the AI commentary

### Step 3: Review AI Commentary

Check your email or visit http://localhost:5001 to see the AI-generated post.

Example AI output:

```markdown
## 🔐 Soulfra's Perspective (Security Focus)

Web3's reliance on centralized infrastructure creates single points
of failure. Users should self-host nodes and use hardware wallets to
maintain true sovereignty over their keys and data.

Confidence: 85%

## 🕵️ DeathToData's Perspective (Privacy Advocacy)

The surveillance capitalism of Web2 is being replicated in Web3
through analytics, tracking, and KYC requirements. True privacy requires
zero-knowledge proofs and anonymous transactions.

Confidence: 78%

## 💻 CalRiven's Perspective (Technical Architecture)

The cost-benefit analysis favors centralized infrastructure for most
users. Self-hosting requires technical expertise and ongoing maintenance.
The market will determine the optimal centralization/decentralization balance.

Confidence: 82%
```

### Step 4: Publish Your Newsletter

Use the AI perspectives to:
- Validate your ideas
- Add multi-domain context
- Create richer newsletters
- Engage subscribers with AI-augmented content

## Database Schema

### Posts Table (Updated)

```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    emailed BOOLEAN DEFAULT 0,
    emailed_at TIMESTAMP,
    ai_processed BOOLEAN DEFAULT 0,        -- NEW: Prevents re-processing
    source_post_id INTEGER,                 -- NEW: Links AI posts to originals
    FOREIGN KEY (source_post_id) REFERENCES posts(id)
);
```

### Querying AI Posts

```python
# Get all human-written posts (not AI-generated)
SELECT * FROM posts WHERE source_post_id IS NULL;

# Get AI commentary for specific post
SELECT * FROM posts WHERE source_post_id = <post_id>;

# Get unprocessed posts
SELECT * FROM posts WHERE ai_processed = 0 AND source_post_id IS NULL;
```

## Open Source Strategy

This integration is designed to be:

1. **Easy to reproduce**: Single command setup with docker-compose
2. **Customizable**: Add your own AI personas/domains
3. **Local-first**: Runs on Ollama (no API costs)
4. **Open source**: MIT licensed, GitHub repo

### Future Docker Compose Setup

```yaml
# Coming soon!
version: '3.8'
services:
  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

  soulfra:
    build: ./soulfra-simple
    ports:
      - "5001:5001"
    environment:
      - SMTP_EMAIL=${SMTP_EMAIL}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      - ollama

  cal-riven-bridge:
    build: ./soulfra-simple
    command: python cal_riven_bridge.py --watch
    depends_on:
      - ollama
      - soulfra
```

## Troubleshooting

### "Could not import generate_article_debate"

Make sure you're running from the `soulfra-simple` directory and that the parent `roommate-chat/python/` directory exists:

```bash
pwd  # Should show: /path/to/roommate-chat/soulfra-simple
ls ../python/generate_article_debate.py  # Should exist
```

### "Ollama connection refused"

Start Ollama service:

```bash
ollama serve
```

### AI Analysis Taking Too Long

Cal-Riven uses 3 separate Ollama calls (one per brand persona). Each can take 10-30 seconds depending on your hardware. Total time: 30-90 seconds per post.

### Email Not Sending

1. Check SMTP credentials are set:
   ```bash
   echo $SMTP_EMAIL
   echo $SMTP_PASSWORD
   ```

2. Test email manually:
   ```bash
   python emails.py send-latest
   ```

3. Use dry-run mode to test without sending:
   ```bash
   python emails.py send-latest --dry-run
   ```

### Bridge Not Detecting New Posts

1. Check ai_processed flag:
   ```bash
   python database.py  # Opens sqlite shell
   SELECT id, title, ai_processed FROM posts;
   ```

2. Manually reset flag:
   ```python
   import database as db
   db.mark_post_ai_processed(post_id)  # Reverses: sets to 0
   ```

## Next Steps

1. ✅ Database migration complete
2. ✅ Bridge script created
3. ⏳ Admin panel "Request AI Analysis" button (coming soon)
4. ⏳ Enhanced email template for AI commentary (coming soon)
5. ⏳ Docker compose for one-command setup (coming soon)

## Contributing

This integration is designed to be **open source and reproducible**.

Ideas for contributions:
- Add custom AI personas beyond Soulfra/DeathToData/CalRiven
- Build web UI for managing AI analysis queue
- Create RSS feed of AI commentary posts
- Add support for other LLMs (GPT-4, Claude, etc.)
- Implement multi-language analysis

## License

MIT - Same as Soulfra Simple

---

**Questions?** Open an issue or check the main roommate-chat README.
