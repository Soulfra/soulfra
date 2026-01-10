#!/usr/bin/env python3
"""
Daily Worklog System
Auto-categorize voice recordings into work/ideas/personal/learning/goals
Generate daily summary for review
"""

from database import get_db
from datetime import datetime, timezone, date
import json
import requests


# AI Categorization Keywords (Pinterest-style buckets)
CATEGORIES = {
    'work': ['project', 'task', 'meeting', 'deadline', 'client', 'code', 'bug', 'feature', 'deploy', 'fix', 'build', 'test'],
    'ideas': ['idea', 'thought', 'maybe', 'could', 'brainstorm', 'concept', 'vision', 'what if', 'imagine', 'future'],
    'personal': ['feeling', 'tired', 'happy', 'think about', 'remember', 'family', 'friend', 'home', 'health'],
    'learning': ['learn', 'read', 'study', 'research', 'understand', 'figure out', 'tutorial', 'course', 'book'],
    'goals': ['goal', 'plan', 'want to', 'need to', 'should', 'will', 'going to', 'tomorrow', 'this week']
}


def categorize_transcript(transcript):
    """
    Categorize a transcript based on keywords

    Returns: (category, confidence)
    """
    if not transcript:
        return ('unknown', 0.0)

    text_lower = transcript.lower()
    scores = {}

    for category, keywords in CATEGORIES.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return ('random', 0.1)

    # Get category with highest score
    top_category = max(scores.items(), key=lambda x: x[1])
    total_keywords = sum(scores.values())
    confidence = top_category[1] / total_keywords if total_keywords > 0 else 0.0

    return (top_category[0], confidence)


def get_todays_recordings(user_id=None):
    """
    Get all voice recordings from today

    Returns: List of recording dicts with categorization
    """
    db = get_db()
    today = date.today().isoformat()

    query = '''
        SELECT *
        FROM simple_voice_recordings
        WHERE DATE(created_at) = ?
    '''
    params = [today]

    if user_id:
        query += ' AND user_id = ?'
        params.append(user_id)

    query += ' ORDER BY created_at ASC'

    recordings = db.execute(query, params).fetchall()

    # Categorize each recording
    categorized = []
    for rec in recordings:
        category, confidence = categorize_transcript(rec['transcription'])

        # Convert sqlite3.Row to dict to access with .get()
        rec_dict = dict(rec)

        categorized.append({
            'id': rec['id'],
            'created_at': rec['created_at'],
            'transcription': rec['transcription'],
            'duration': rec_dict.get('duration', 0),
            'category': category,
            'confidence': confidence
        })

    return categorized


def generate_daily_summary(user_id=None):
    """
    Generate daily worklog summary with Ollama

    Returns: Dict with categorized items and AI summary
    """
    recordings = get_todays_recordings(user_id)

    if not recordings:
        return {
            'date': date.today().isoformat(),
            'total_recordings': 0,
            'summary': 'No recordings today',
            'categories': {}
        }

    # Group by category
    categories = {}
    for rec in recordings:
        cat = rec['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(rec)

    # Generate AI summary with Ollama
    all_transcripts = '\n\n'.join([
        f"[{rec['created_at'][11:16]}] {rec['transcription']}"
        for rec in recordings
    ])

    prompt = f"""You are reviewing someone's voice memos from today. Auto-categorize and summarize their workday.

Voice Memos:
{all_transcripts}

Generate a concise daily summary in this format:

## Work Accomplished
[Bullet points of work items]

## Ideas & Brainstorms
[Bullet points of ideas]

## Personal Notes
[Brief personal highlights]

## Learning & Research
[What they learned/researched]

## Goals for Tomorrow
[Extracted action items]

Keep it concise and actionable."""

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': 'llama3.2', 'prompt': prompt, 'stream': False},
            timeout=30
        )

        if response.status_code == 200:
            ai_summary = response.json().get('response', '')
        else:
            ai_summary = _generate_fallback_summary(categories)

    except Exception as e:
        print(f"⚠️  Ollama error: {e}")
        ai_summary = _generate_fallback_summary(categories)

    return {
        'date': date.today().isoformat(),
        'total_recordings': len(recordings),
        'summary': ai_summary,
        'categories': {
            cat: [
                {
                    'id': r['id'],
                    'time': r['created_at'][11:16],
                    'text': r['transcription'][:100] + '...' if len(r['transcription']) > 100 else r['transcription']
                }
                for r in items
            ]
            for cat, items in categories.items()
        }
    }


def _generate_fallback_summary(categories):
    """Generate simple summary without Ollama"""
    summary = f"# Daily Summary - {date.today().isoformat()}\n\n"

    for category, items in categories.items():
        summary += f"## {category.upper()} ({len(items)} items)\n"
        for item in items:
            summary += f"- {item['transcription'][:80]}...\n"
        summary += "\n"

    return summary


def save_daily_worklog(user_id=None):
    """
    Save today's worklog to database

    Returns: worklog_id
    """
    db = get_db()
    today = date.today().isoformat()
    summary_data = generate_daily_summary(user_id)

    # Extract category items as JSON
    work_items = json.dumps(summary_data['categories'].get('work', []))
    ideas_items = json.dumps(summary_data['categories'].get('ideas', []))
    personal_items = json.dumps(summary_data['categories'].get('personal', []))
    learning_items = json.dumps(summary_data['categories'].get('learning', []))
    goals_items = json.dumps(summary_data['categories'].get('goals', []))

    cursor = db.execute('''
        INSERT OR REPLACE INTO daily_worklogs
        (user_id, date, summary, work_items, ideas_items, personal_items,
         learning_items, goals_items, total_recordings, generated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        today,
        summary_data['summary'],
        work_items,
        ideas_items,
        personal_items,
        learning_items,
        goals_items,
        summary_data['total_recordings'],
        datetime.now(timezone.utc).isoformat()
    ))

    db.commit()
    return cursor.lastrowid


def get_daily_worklog(target_date=None, user_id=None):
    """
    Get worklog for specific date

    Returns: Worklog dict or None
    """
    db = get_db()

    if not target_date:
        target_date = date.today().isoformat()

    query = 'SELECT * FROM daily_worklogs WHERE date = ?'
    params = [target_date]

    if user_id:
        query += ' AND user_id = ?'
        params.append(user_id)

    worklog = db.execute(query, params).fetchone()

    if not worklog:
        return None

    return {
        'id': worklog['id'],
        'date': worklog['date'],
        'summary': worklog['summary'],
        'work': json.loads(worklog['work_items']) if worklog['work_items'] else [],
        'ideas': json.loads(worklog['ideas_items']) if worklog['ideas_items'] else [],
        'personal': json.loads(worklog['personal_items']) if worklog['personal_items'] else [],
        'learning': json.loads(worklog['learning_items']) if worklog['learning_items'] else [],
        'goals': json.loads(worklog['goals_items']) if worklog['goals_items'] else [],
        'total_recordings': worklog['total_recordings'],
        'generated_at': worklog['generated_at']
    }


# CLI
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Daily Worklog System")
        print("\nUsage:")
        print("  python3 daily_worklog.py today")
        print("  python3 daily_worklog.py generate")
        print("  python3 daily_worklog.py save")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'today':
        recordings = get_todays_recordings()
        print(f"\n📅 Today's Recordings: {len(recordings)}\n")

        for rec in recordings:
            print(f"[{rec['created_at'][11:16]}] {rec['category'].upper()} ({rec['confidence']:.0%})")
            print(f"   {rec['transcription'][:100]}...")
            print()

    elif command == 'generate':
        summary = generate_daily_summary()
        print(f"\n{summary['summary']}\n")
        print(f"Total recordings: {summary['total_recordings']}")

    elif command == 'save':
        worklog_id = save_daily_worklog()
        print(f"✅ Daily worklog saved (ID: {worklog_id})")
        print(f"   Date: {date.today().isoformat()}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
