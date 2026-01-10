#!/usr/bin/env python3
"""
Daily Summary Automation

Automatically:
1. Scans all voice memos created today
2. Auto-categorizes them into buckets (work, ideas, personal, etc.)
3. Generates a daily summary
4. Emails it out

This is the automation the user wants: "whatever i work on for the day and
summarize it into that then email everything out"
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Paths
DB_PATH = Path(__file__).parent / 'soulfra.db'
VOICE_ARCHIVE = Path(__file__).parent / 'voice-archive'
MEDIA_DIR = VOICE_ARCHIVE / 'media'

# AI Categorization Buckets (like Pinterest)
CATEGORIES = {
    'work': ['project', 'task', 'meeting', 'deadline', 'client', 'code', 'bug', 'feature'],
    'ideas': ['idea', 'thought', 'maybe', 'could', 'brainstorm', 'concept', 'vision'],
    'personal': ['feeling', 'tired', 'happy', 'think about', 'remember', 'family', 'friend'],
    'learning': ['learn', 'read', 'study', 'research', 'understand', 'figure out'],
    'goals': ['goal', 'plan', 'want to', 'need to', 'should', 'will', 'going to'],
    'random': []  # catch-all
}

def get_todays_voice_memos():
    """Get all voice memos created today from Git-based media library"""
    today = datetime.now().date()
    memos = []

    # Read from media/voice/ directories
    voice_dir = MEDIA_DIR / 'voice'
    if not voice_dir.exists():
        return []

    for memo_dir in voice_dir.glob('*/'):
        metadata_file = memo_dir / 'metadata.json'
        if not metadata_file.exists():
            continue

        with open(metadata_file) as f:
            metadata = json.load(f)

        # Parse created_at date
        created_str = metadata.get('created_at', '')
        try:
            # Handle both formats: "2026-01-02 20:39:37" and "2026-01-02T20:55:53.672455"
            if 'T' in created_str:
                created_at = datetime.fromisoformat(created_str.split('.')[0])
            else:
                created_at = datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S')

            # Check if created today
            if created_at.date() == today:
                # Load transcript if available
                transcript = ''
                transcript_file = memo_dir / 'transcript.txt'
                if transcript_file.exists():
                    with open(transcript_file) as f:
                        transcript = f.read().strip()

                memos.append({
                    'id': metadata.get('id'),
                    'short_id': metadata.get('short_id'),
                    'filename': metadata.get('filename'),
                    'transcript': transcript,
                    'created_at': created_at,
                    'url': metadata.get('url')
                })
        except (ValueError, KeyError) as e:
            print(f"⚠️  Skipping {memo_dir.name}: {e}")
            continue

    return sorted(memos, key=lambda m: m['created_at'])

def categorize_memo(transcript):
    """Auto-categorize based on transcript keywords"""
    if not transcript:
        return 'random'

    transcript_lower = transcript.lower()

    # Score each category
    scores = {}
    for category, keywords in CATEGORIES.items():
        score = sum(1 for keyword in keywords if keyword in transcript_lower)
        scores[category] = score

    # Return highest scoring category (or 'random' if tied at 0)
    max_category = max(scores, key=scores.get)
    return max_category if scores[max_category] > 0 else 'random'

def generate_summary_html(categorized_memos):
    """Generate HTML email with categorized memos"""

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 2rem;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            h1 {
                color: #ff006e;
                border-bottom: 3px solid #ff006e;
                padding-bottom: 0.5rem;
            }
            h2 {
                color: #8338ec;
                margin-top: 2rem;
            }
            .category {
                background: #f9f9f9;
                border-left: 4px solid #8338ec;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 4px;
            }
            .memo {
                background: white;
                border: 1px solid #ddd;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 4px;
            }
            .memo-time {
                color: #666;
                font-size: 0.85rem;
            }
            .memo-link {
                color: #ff006e;
                text-decoration: none;
                font-weight: 600;
            }
            .stats {
                background: #f0f0f0;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📝 Daily Summary - {date}</h1>

            <div class="stats">
                <strong>Total Voice Memos:</strong> {total}<br>
                <strong>Categories:</strong> {category_count}
            </div>
    """

    today = datetime.now().strftime('%B %d, %Y')
    total = sum(len(memos) for memos in categorized_memos.values())
    category_count = len([cat for cat, memos in categorized_memos.items() if memos])

    html = html.format(date=today, total=total, category_count=category_count)

    # Add each category section
    for category, memos in categorized_memos.items():
        if not memos:
            continue

        emoji_map = {
            'work': '💼',
            'ideas': '💡',
            'personal': '🧘',
            'learning': '📚',
            'goals': '🎯',
            'random': '🎲'
        }

        html += f"""
        <div class="category">
            <h2>{emoji_map.get(category, '📌')} {category.title()} ({len(memos)})</h2>
        """

        for memo in memos:
            time = memo['created_at'].strftime('%I:%M %p')
            url = memo['url']
            transcript = memo['transcript']

            preview = (transcript[:150] + '...') if transcript and len(transcript) > 150 else (transcript or 'No transcript')

            html += f"""
            <div class="memo">
                <div class="memo-time">{time}</div>
                <p>{preview}</p>
                <a href="{url}" class="memo-link">Listen →</a>
            </div>
            """

        html += "</div>"

    html += """
        </div>
    </body>
    </html>
    """

    return html

def send_email(html_content, recipient):
    """Send email with daily summary"""

    # For now, just save to file (email sending requires SMTP config)
    output_file = VOICE_ARCHIVE / f"daily-summary-{datetime.now().strftime('%Y-%m-%d')}.html"
    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"✅ Summary saved to: {output_file}")
    print(f"📧 Email sending not configured yet - add SMTP settings to send")

    # TODO: Uncomment when email is configured
    # msg = MIMEMultipart('alternative')
    # msg['Subject'] = f"Daily Summary - {datetime.now().strftime('%B %d, %Y')}"
    # msg['From'] = 'noreply@cringeproof.com'
    # msg['To'] = recipient
    #
    # msg.attach(MIMEText(html_content, 'html'))
    #
    # with smtplib.SMTP('smtp.gmail.com', 587) as server:
    #     server.starttls()
    #     server.login('your-email@gmail.com', 'your-password')
    #     server.send_message(msg)

def main():
    """Main automation workflow"""
    print("🤖 Running daily summary automation...")

    # 1. Get today's voice memos
    memos = get_todays_voice_memos()

    if not memos:
        print("📭 No voice memos created today")
        return

    print(f"📥 Found {len(memos)} voice memos from today")

    # 2. Auto-categorize
    categorized = {cat: [] for cat in CATEGORIES.keys()}

    for memo in memos:
        category = categorize_memo(memo['transcript'])
        categorized[category].append(memo)
        print(f"  📌 {memo['filename']}: {category}")

    # 3. Generate summary
    html = generate_summary_html(categorized)

    # 4. Send email (or save to file)
    send_email(html, recipient='your-email@example.com')

    print("✅ Daily summary complete!")

if __name__ == '__main__':
    main()
