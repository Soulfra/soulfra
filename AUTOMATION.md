# Daily Summary Automation

## What It Does

Automatically generates a daily summary of your voice memos, categorized into buckets like Pinterest/MySpace:

- 💼 **Work**: Projects, tasks, meetings, deadlines, code, bugs
- 💡 **Ideas**: Brainstorms, concepts, visions, maybes
- 🧘 **Personal**: Feelings, thoughts, family, friends
- 📚 **Learning**: Research, studying, understanding
- 🎯 **Goals**: Plans, wants, shoulds, going-to's
- 🎲 **Random**: Everything else

## How It Works

```
Record voice memos throughout the day
          ↓
   End of day (11:59 PM)
          ↓
GitHub Action runs daily_summary.py
          ↓
  Auto-categorizes by keywords
          ↓
 Generates beautiful HTML summary
          ↓
    Commits to Git repo
          ↓
   (Optional) Emails you
```

## Files

### `daily_summary.py`
Main automation script that:
1. Scans `media/voice/` for today's memos
2. Reads transcripts from `transcript.txt` files
3. Auto-categorizes based on keyword matching
4. Generates HTML with links to each memo
5. Saves to `voice-archive/daily-summary-YYYY-MM-DD.html`

### `.github/workflows/daily-summary.yml`
GitHub Action that runs the script daily at 11:59 PM and commits the result.

## Running Manually

```bash
# From soulfra-simple/ directory
python3 daily_summary.py
```

This will:
- Check for voice memos created today
- Generate summary HTML
- Save to `voice-archive/daily-summary-2026-01-04.html`

## Auto-Categorization

The script uses simple keyword matching:

```python
CATEGORIES = {
    'work': ['project', 'task', 'meeting', 'deadline', 'client', 'code', 'bug'],
    'ideas': ['idea', 'thought', 'maybe', 'could', 'brainstorm', 'concept'],
    'personal': ['feeling', 'tired', 'happy', 'think about', 'remember'],
    'learning': ['learn', 'read', 'study', 'research', 'understand'],
    'goals': ['goal', 'plan', 'want to', 'need to', 'should', 'will'],
}
```

Scores each category by counting keyword matches in the transcript, then assigns to highest-scoring category.

## Email Setup (Optional)

To enable email delivery:

1. **Add GitHub Secrets:**
   - `EMAIL_USERNAME`: Your Gmail address
   - `EMAIL_PASSWORD`: App-specific password

2. **Uncomment email step** in `.github/workflows/daily-summary.yml`:

```yaml
- name: Send email
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 587
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: Daily Summary
    to: your-email@example.com
    from: CringeProof <noreply@cringeproof.com>
    html_body: file://daily-summary-$(date +%Y-%m-%d).html
```

3. **Update recipient** in `daily_summary.py:264`:

```python
send_email(html, recipient='your-real-email@example.com')
```

## Example Output

```html
📝 Daily Summary - January 4, 2026

Total Voice Memos: 5
Categories: 3

💼 Work (2)
  • 08:30 AM - Discussed new feature for user dashboard...
    Listen → https://cringeproof.com/voice/071323f8

  • 02:15 PM - Bug fix for authentication flow...
    Listen → https://cringeproof.com/voice/e85841dc

💡 Ideas (2)
  • 10:45 AM - Maybe we could build a TikTok-style...
    Listen → https://cringeproof.com/voice/50bf7674

🧘 Personal (1)
  • 06:00 PM - Feeling tired but accomplished today...
    Listen → https://cringeproof.com/voice/7666a5f9
```

## Integration with Google Credential Sharing

Future enhancement (mentioned in user request):

> "i am just thinking -> https://developers.google.com/identity/credential-sharing
> this is basically what i want to do for ideas"

This would enable:
- Google One Tap sign-in
- Automatic credential sharing across domains
- Seamless authentication for recording ideas

To implement:
1. Add Google Client ID to repo secrets
2. Update `voice-recorder.html` with Google One Tap
3. Store user identity in localStorage
4. Associate memos with Google account

## Philosophy

This is the automation you described:

> "we're basically just going to reskin that because thats going to be
> whatever i work on for the day and summarize it into that then email
> everything out idk"

Record your thoughts throughout the day → System auto-categorizes → Daily summary → Email recap

Like a personal Pinterest board for your brain.

## Next Steps

1. ✅ Voice viewer page (`voice.html`)
2. ✅ GitHub Pages routing (`404.html`)
3. ✅ Daily summary script (`daily_summary.py`)
4. ✅ GitHub Action workflow
5. ⏳ Email delivery (ready, needs secrets)
6. ⏳ Google Credential Sharing integration
7. ⏳ AI-powered categorization (upgrade from keywords to GPT/Ollama)

---

**Status:** ✅ Fully automated workflow ready
**Next:** Add email secrets to enable delivery
