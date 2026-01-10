#!/usr/bin/env python3
"""
Newsletter Template Generator - AI Comment Digests

Generates beautiful HTML/text newsletters showing:
- Recent AI comments from brand personas
- API usage stats
- New posts and discussions
- Brand-specific insights

Usage:
    from newsletter_template import generate_newsletter_html, generate_newsletter_text

    html = generate_newsletter_html(brand_slug='calriven', days=7)
    text = generate_newsletter_text(brand_slug='calriven', days=7)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import get_db


def get_recent_ai_comments(brand_slug: Optional[str] = None, days: int = 7) -> List[Dict]:
    """
    Get recent AI comments for newsletter

    Args:
        brand_slug: Filter by brand (None = all brands)
        days: Number of days to look back

    Returns:
        List of comment dicts with post info
    """
    conn = get_db()

    query = '''
        SELECT
            c.id,
            c.content,
            c.created_at,
            u.username as ai_persona,
            u.email as persona_email,
            p.id as post_id,
            p.title as post_title,
            p.slug as post_slug,
            b.slug as brand_slug,
            b.name as brand_name
        FROM comments c
        JOIN users u ON c.user_id = u.id
        JOIN posts p ON c.post_id = p.id
        LEFT JOIN brands b ON b.slug = ?
        WHERE u.is_ai_persona = 1
        AND c.created_at > datetime('now', '-' || ? || ' days')
    '''

    params = []

    if brand_slug:
        query += ' AND b.slug = ?'
        params = [brand_slug, days, brand_slug]
    else:
        params = [None, days]

    query += ' ORDER BY c.created_at DESC LIMIT 50'

    comments = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(c) for c in comments]


def get_api_usage_summary(brand_slug: str, days: int = 7) -> Dict:
    """
    Get API usage stats for newsletter

    Args:
        brand_slug: Brand to get stats for
        days: Number of days to look back

    Returns:
        {
            'total_calls': 150,
            'unique_users': 5,
            'avg_response_time_ms': 45
        }
    """
    conn = get_db()

    stats = conn.execute('''
        SELECT
            COUNT(*) as total_calls,
            COUNT(DISTINCT ak.user_email) as unique_users,
            AVG(acl.response_time_ms) as avg_response_time_ms
        FROM api_call_logs acl
        JOIN api_keys ak ON acl.api_key_id = ak.id
        WHERE ak.brand_slug = ?
        AND acl.created_at > datetime('now', '-' || ? || ' days')
    ''', (brand_slug, days)).fetchone()

    conn.close()

    return dict(stats) if stats else {'total_calls': 0, 'unique_users': 0, 'avg_response_time_ms': 0}


def generate_newsletter_text(
    brand_slug: str,
    subscriber_email: str,
    days: int = 7
) -> str:
    """
    Generate plain text newsletter

    Args:
        brand_slug: Brand for newsletter
        subscriber_email: Email of subscriber
        days: Days to include

    Returns:
        Plain text newsletter content
    """
    comments = get_recent_ai_comments(brand_slug, days)
    stats = get_api_usage_summary(brand_slug, days)

    # Build newsletter
    newsletter = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {brand_slug.upper()} AI Comment Digest
    Week of {datetime.now().strftime('%B %d, %Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi there! 👋

Here's what our AI personas have been discussing this week.

📊 THIS WEEK'S ACTIVITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• {stats['total_calls']} API calls made
• {stats['unique_users']} active developers
• {len(comments)} AI comments generated
• {stats['avg_response_time_ms']:.0f}ms average response time

💬 RECENT AI COMMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    if not comments:
        newsletter += "\nNo AI comments this week. Be the first to generate one!\n"
    else:
        for i, comment in enumerate(comments[:10], 1):
            newsletter += f"""
{i}. {comment['ai_persona']} on "{comment['post_title']}"
   {comment['content'][:150]}{'...' if len(comment['content']) > 150 else ''}

   Read more: http://localhost:5001/post/{comment['post_slug']}
   Posted {comment['created_at']}

"""

    newsletter += f"""
🚀 QUICK ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Generate AI comment: http://localhost:5001/api-tester
• View API docs: http://localhost:5001/api/docs
• Browse brand personas: http://localhost:5001/brands

💡 TIP OF THE WEEK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reply to this email to automatically post a comment! Just write your
thoughts and our AI will add it to the discussion.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Soulfra Platform | Building AI-powered conversation tools

Unsubscribe: http://localhost:5001/unsubscribe?email={subscriber_email}
Manage preferences: http://localhost:5001/newsletter/preferences?email={subscriber_email}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()

    return newsletter


def generate_newsletter_html(
    brand_slug: str,
    subscriber_email: str,
    days: int = 7
) -> str:
    """
    Generate HTML newsletter (beautiful formatted version)

    Args:
        brand_slug: Brand for newsletter
        subscriber_email: Email of subscriber
        days: Days to include

    Returns:
        HTML newsletter content
    """
    comments = get_recent_ai_comments(brand_slug, days)
    stats = get_api_usage_summary(brand_slug, days)

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{brand_slug.upper()} AI Comment Digest</title>
</head>
<body style="font-family: system-ui, -apple-system, sans-serif; background: #f5f5f5; padding: 20px; margin: 0;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 28px; font-weight: 700;">{brand_slug.upper()}</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">AI Comment Digest</p>
            <p style="margin: 5px 0 0 0; opacity: 0.7; font-size: 14px;">{datetime.now().strftime('%B %d, %Y')}</p>
        </div>

        <!-- Stats -->
        <div style="padding: 30px; border-bottom: 1px solid #e0e0e0;">
            <h2 style="margin: 0 0 20px 0; font-size: 20px; color: #333;">📊 This Week's Activity</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 700; color: #667eea;">{stats['total_calls']}</div>
                    <div style="font-size: 13px; color: #666; margin-top: 5px;">API Calls</div>
                </div>
                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 700; color: #667eea;">{stats['unique_users']}</div>
                    <div style="font-size: 13px; color: #666; margin-top: 5px;">Active Developers</div>
                </div>
                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 700; color: #667eea;">{len(comments)}</div>
                    <div style="font-size: 13px; color: #666; margin-top: 5px;">AI Comments</div>
                </div>
                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 700; color: #667eea;">{stats['avg_response_time_ms']:.0f}ms</div>
                    <div style="font-size: 13px; color: #666; margin-top: 5px;">Avg Response</div>
                </div>
            </div>
        </div>

        <!-- Comments -->
        <div style="padding: 30px;">
            <h2 style="margin: 0 0 20px 0; font-size: 20px; color: #333;">💬 Recent AI Comments</h2>
"""

    if not comments:
        html += """
            <div style="background: #f9f9f9; padding: 30px; border-radius: 8px; text-align: center; color: #666;">
                <p style="margin: 0;">No AI comments this week. Be the first to generate one!</p>
                <a href="http://localhost:5001/api-tester" style="display: inline-block; margin-top: 15px; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; font-weight: 600;">Try API Tester</a>
            </div>
"""
    else:
        for comment in comments[:10]:
            html += f"""
            <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #667eea; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 16px; margin-right: 12px;">
                        {comment['ai_persona'][0].upper()}
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #333; font-size: 15px;">{comment['ai_persona']}</div>
                        <div style="font-size: 13px; color: #666;">{comment['created_at']}</div>
                    </div>
                </div>
                <div style="color: #333; line-height: 1.6; font-size: 14px; margin-bottom: 10px;">
                    {comment['content'][:200]}{'...' if len(comment['content']) > 200 else ''}
                </div>
                <div style="font-size: 13px; color: #666;">
                    on <a href="http://localhost:5001/post/{comment['post_slug']}" style="color: #667eea; text-decoration: none; font-weight: 600;">"{comment['post_title']}"</a>
                </div>
            </div>
"""

    html += f"""
        </div>

        <!-- CTA -->
        <div style="background: #f0f4ff; padding: 30px; text-align: center;">
            <h3 style="margin: 0 0 15px 0; font-size: 18px; color: #333;">🚀 Quick Actions</h3>
            <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                <a href="http://localhost:5001/api-tester" style="display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;">Test API</a>
                <a href="http://localhost:5001/api/docs" style="display: inline-block; padding: 12px 24px; background: white; color: #667eea; text-decoration: none; border-radius: 6px; font-weight: 600; border: 2px solid #667eea; font-size: 14px;">View Docs</a>
                <a href="http://localhost:5001/brands" style="display: inline-block; padding: 12px 24px; background: white; color: #667eea; text-decoration: none; border-radius: 6px; font-weight: 600; border: 2px solid #667eea; font-size: 14px;">Browse Personas</a>
            </div>
        </div>

        <!-- Tip -->
        <div style="padding: 30px; background: #fffbea; border-top: 3px solid #ffd700;">
            <h3 style="margin: 0 0 10px 0; font-size: 16px; color: #333;">💡 Tip of the Week</h3>
            <p style="margin: 0; color: #666; line-height: 1.6; font-size: 14px;">
                Reply to this email to automatically post a comment! Just write your thoughts and our AI will add it to the discussion.
            </p>
        </div>

        <!-- Footer -->
        <div style="padding: 30px; background: #f5f5f5; text-align: center; border-top: 1px solid #e0e0e0;">
            <p style="margin: 0; font-size: 14px; color: #666;">Soulfra Platform | Building AI-powered conversation tools</p>
            <p style="margin: 15px 0 0 0; font-size: 13px;">
                <a href="http://localhost:5001/unsubscribe?email={subscriber_email}" style="color: #999; text-decoration: none;">Unsubscribe</a>
                <span style="color: #ccc; margin: 0 10px;">|</span>
                <a href="http://localhost:5001/newsletter/preferences?email={subscriber_email}" style="color: #999; text-decoration: none;">Manage Preferences</a>
            </p>
        </div>

    </div>
</body>
</html>
""".strip()

    return html


if __name__ == '__main__':
    # Test newsletter generation
    print("Testing Newsletter Generation...")
    print("=" * 60)

    # Generate text version
    text = generate_newsletter_text(
        brand_slug='calriven',
        subscriber_email='test@example.com',
        days=7
    )

    print("\n📧 PLAIN TEXT VERSION:\n")
    print(text)

    print("\n" + "=" * 60)
    print("\n✅ HTML version also generated (view in browser)")
    print("    Test by opening the HTML in a browser\n")
