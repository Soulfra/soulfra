"""
QR Debug Pipeline - Auto-Blog QR Authentication Failures

When QR code auth fails, Calriven (AI agent) analyzes the failure and
auto-publishes a debug blog post to calriven.com.

Workflow:
1. QR auth fails → Error logged to database
2. Calriven analyzes error context
3. Generates blog post explaining bug
4. Pushes to GitHub → auto-deploys

Usage:
    # Log QR error (called from app.py)
    from qr_debug_pipeline import log_qr_error
    log_qr_error(error_type='token_expired', details={...}, user_id=123)

    # Manually trigger debug analysis
    python3 qr_debug_pipeline.py --analyze-recent
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('soulfra.db')
    conn.row_factory = sqlite3.Row
    return conn


def log_qr_error(error_type, details, user_id=None, request_info=None):
    """
    Log QR authentication error to database

    Args:
        error_type: Type of error (token_expired, signature_mismatch, invalid_format, etc.)
        details: Dict with error details
        user_id: User ID if available
        request_info: Request context (IP, user agent, etc.)

    Returns:
        int: Error log ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create qr_error_log table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qr_error_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                details TEXT,
                user_id INTEGER,
                request_info TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                analyzed INTEGER DEFAULT 0,
                blog_post_created INTEGER DEFAULT 0
            )
        ''')

        # Insert error
        cursor.execute('''
            INSERT INTO qr_error_log (error_type, details, user_id, request_info)
            VALUES (?, ?, ?, ?)
        ''', (
            error_type,
            json.dumps(details) if details else None,
            user_id,
            json.dumps(request_info) if request_info else None
        ))

        error_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"✅ QR error logged: {error_type} (ID: {error_id})")
        return error_id

    except Exception as e:
        logger.error(f"Error logging QR failure: {e}")
        return None


def get_recent_qr_errors(hours=24, limit=10):
    """
    Get recent QR errors that haven't been analyzed

    Args:
        hours: Look back this many hours
        limit: Max number of errors to return

    Returns:
        list: Recent error records
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        cursor.execute('''
            SELECT * FROM qr_error_log
            WHERE created_at > ? AND analyzed = 0
            ORDER BY created_at DESC
            LIMIT ?
        ''', (cutoff_time, limit))

        errors = cursor.fetchall()
        conn.close()

        return [dict(error) for error in errors]

    except Exception as e:
        logger.error(f"Error fetching QR errors: {e}")
        return []


def analyze_qr_error_with_calriven(error):
    """
    Use Calriven (AI) to analyze QR error and generate debug explanation

    Args:
        error: Error record from database

    Returns:
        str: Calriven's analysis
    """
    try:
        from ollama_smart_client import ask_ollama

        # Build analysis prompt
        error_details = json.loads(error['details']) if error['details'] else {}

        prompt = f"""You are Calriven, the debugging AI for Soulfra Network.

Analyze this QR authentication failure:

**Error Type:** {error['error_type']}
**Timestamp:** {error['created_at']}
**User ID:** {error['user_id'] or 'Unknown'}
**Details:** {json.dumps(error_details, indent=2)}

Provide a technical analysis:

1. **Root Cause** - What went wrong?
2. **Code Location** - Which part of qr_auth.py failed?
3. **Fix Strategy** - How should this be resolved?
4. **Prevention** - How to avoid this in the future?

Write as a blog post for calriven.com - technical but accessible.
Use markdown formatting. Be direct and practical."""

        logger.info(f"🤖 Asking Calriven to analyze error #{error['id']}")
        analysis = ask_ollama(prompt, model='llama3.2:latest', use_soul=True)

        return analysis

    except Exception as e:
        logger.error(f"Error analyzing with Calriven: {e}")
        return None


def create_blog_post_from_analysis(error, analysis):
    """
    Create blog post file from Calriven's analysis

    Args:
        error: Error record
        analysis: Calriven's analysis text

    Returns:
        str: Path to created blog post, or None if failed
    """
    try:
        from cal_auto_publish import create_blog_post

        # Generate title
        error_type_display = error['error_type'].replace('_', ' ').title()
        title = f"QR Auth Debug: {error_type_display}"

        # Build blog content
        content = f"""# Debugging QR Authentication Issue

**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
**Error Type:** `{error['error_type']}`
**Affected User:** {error['user_id'] or 'Anonymous'}

---

{analysis}

---

## Technical Context

This error was automatically detected and analyzed by Calriven, the Soulfra Network debugging agent.

**Error Log ID:** `{error['id']}`
**Timestamp:** `{error['created_at']}`

## Related Systems

- **QR Auth System:** `qr_auth.py:generate_auth_token()`, `qr_auth.py:verify_auth_token()`
- **Frontend:** `cringeproof.com/login.html`
- **API Route:** `/api/qr/verify/<token>`

## Next Steps

If you're experiencing this issue:
1. Check the error log for your specific case
2. Verify your token hasn't expired (1-hour TTL by default)
3. Ensure you're scanning the latest QR code
4. Report persistent issues to the Soulfra Network GitHub

---

*🤖 Auto-generated by Calriven - [Source Code](https://github.com/soulfra/soulfra-simple/blob/main/qr_debug_pipeline.py)*
"""

        # Create blog post
        filepath = create_blog_post(title, content, author="Calriven")
        logger.info(f"✅ Blog post created: {filepath}")

        return filepath

    except Exception as e:
        logger.error(f"Error creating blog post: {e}")
        return None


def push_blog_post_to_github(filepath):
    """
    Push blog post to GitHub (auto-deploys via GitHub Pages)

    Args:
        filepath: Path to blog post file

    Returns:
        bool: True if successful
    """
    try:
        from cal_auto_publish import push_to_github

        commit_message = f"🤖 Calriven auto-debug: QR auth analysis"
        push_to_github(filepath, commit_message)

        logger.info(f"✅ Pushed to GitHub: {filepath}")
        return True

    except Exception as e:
        logger.error(f"Error pushing to GitHub: {e}")
        return False


def mark_error_as_analyzed(error_id):
    """
    Mark error as analyzed in database

    Args:
        error_id: Error log ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE qr_error_log
            SET analyzed = 1, blog_post_created = 1
            WHERE id = ?
        ''', (error_id,))

        conn.commit()
        conn.close()

        logger.info(f"✅ Marked error #{error_id} as analyzed")

    except Exception as e:
        logger.error(f"Error marking as analyzed: {e}")


def process_qr_errors(auto_publish=True):
    """
    Process recent QR errors with Calriven analysis

    Args:
        auto_publish: Whether to auto-publish to GitHub

    Returns:
        int: Number of errors processed
    """
    logger.info("=" * 60)
    logger.info("QR Debug Pipeline - Processing Errors")
    logger.info("=" * 60)

    # Get recent unanalyzed errors
    errors = get_recent_qr_errors(hours=24, limit=5)

    if not errors:
        logger.info("No unanalyzed QR errors found")
        return 0

    logger.info(f"Found {len(errors)} unanalyzed errors")

    processed_count = 0

    for error in errors:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing error #{error['id']}: {error['error_type']}")

        # 1. Analyze with Calriven
        analysis = analyze_qr_error_with_calriven(error)
        if not analysis:
            logger.warning(f"Failed to analyze error #{error['id']}")
            continue

        # 2. Create blog post
        filepath = create_blog_post_from_analysis(error, analysis)
        if not filepath:
            logger.warning(f"Failed to create blog post for error #{error['id']}")
            continue

        # 3. Push to GitHub
        if auto_publish:
            success = push_blog_post_to_github(filepath)
            if not success:
                logger.warning(f"Failed to push blog post for error #{error['id']}")
                continue

        # 4. Mark as analyzed
        mark_error_as_analyzed(error['id'])

        processed_count += 1
        logger.info(f"✅ Successfully processed error #{error['id']}")

    logger.info(f"\n{'='*60}")
    logger.info(f"Processed {processed_count}/{len(errors)} errors")
    logger.info("=" * 60)

    return processed_count


def main():
    parser = argparse.ArgumentParser(description='QR Debug Pipeline')
    parser.add_argument('--analyze-recent', action='store_true', help='Analyze recent QR errors')
    parser.add_argument('--no-publish', action='store_true', help='Skip GitHub publishing')
    parser.add_argument('--hours', type=int, default=24, help='Look back N hours')

    args = parser.parse_args()

    if args.analyze_recent:
        process_qr_errors(auto_publish=not args.no_publish)
    else:
        print("Usage: python3 qr_debug_pipeline.py --analyze-recent")
        print("       python3 qr_debug_pipeline.py --analyze-recent --no-publish")


if __name__ == '__main__':
    main()
