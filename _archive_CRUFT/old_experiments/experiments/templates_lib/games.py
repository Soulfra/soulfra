#!/usr/bin/env python3
"""
Game Templates - Game Sharing & Peer Review Code Generation

Generates templates for:
- Email notifications (share invitations, review received)
- Share link generation helpers
- Game data formatters
- Analytics reports
- Integration code snippets

Part of the "Send for Advice" game sharing system where users can
share game results with friends for peer feedback and AI analysis.
"""

from typing import Optional


# ==============================================================================
# CATEGORY CONSTANT
# ==============================================================================

CATEGORY = 'games'


# ==============================================================================
# GENERATOR FUNCTIONS
# ==============================================================================

def generate_share_email(
    game_name: str,
    sender_name: Optional[str] = None,
    theme_primary: Optional[str] = None,
    theme_secondary: Optional[str] = None
) -> str:
    """
    Generate HTML email template for game share notification

    Args:
        game_name: Name of the game (e.g., 'cringeproof', 'color_challenge')
        sender_name: Name of sender (defaults to "A friend")
        theme_primary: Primary brand color (hex)
        theme_secondary: Secondary brand color (hex)

    Returns:
        HTML email template as string
    """
    if sender_name is None:
        sender_name = "A friend"
    if theme_primary is None:
        theme_primary = "#667eea"
    if theme_secondary is None:
        theme_secondary = "#764ba2"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Review Request - {game_name}</title>
</head>
<body style="margin: 0; padding: 0; font-family: system-ui, sans-serif; background: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background: #f5f5f5; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {theme_primary} 0%, {theme_secondary} 100%); padding: 40px 30px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="margin: 0; color: white; font-size: 28px;">
                                {{{{ emoji }}}} Get a Second Opinion
                            </h1>
                            <p style="margin: 15px 0 0 0; color: rgba(255,255,255,0.95); font-size: 16px;">
                                {{{{ sender_name }}}} wants your feedback on their {game_name} game
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 1.6; color: #333;">
                                Hi there! 👋
                            </p>
                            <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 1.6; color: #333;">
                                <strong>{{{{ sender_name }}}}</strong> just completed a {game_name} game and would love to get your honest feedback on their answers.
                            </p>
                            <p style="margin: 0 0 30px 0; font-size: 16px; line-height: 1.6; color: #333;">
                                Your review will be analyzed by AI to generate insights about self-awareness, honesty, and areas for growth.
                            </p>

                            <!-- Message from sender -->
                            {{{{ if message }}}}
                            <div style="background: #f8f9fa; border-left: 4px solid {theme_primary}; padding: 20px; margin: 0 0 30px 0; border-radius: 4px;">
                                <p style="margin: 0; font-size: 15px; line-height: 1.6; color: #666; font-style: italic;">
                                    "{{{{ message }}}}"
                                </p>
                            </div>
                            {{{{ endif }}}}

                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center">
                                        <a href="{{{{ review_url }}}}" style="display: inline-block; background: {theme_primary}; color: white; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                                            Review Their Answers →
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 30px 0 0 0; font-size: 14px; line-height: 1.6; color: #999; text-align: center;">
                                This review request will expire in 30 days
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 30px; background: #f8f9fa; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="margin: 0; font-size: 13px; color: #999;">
                                Powered by Neural Networks & Peer Feedback
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''


def generate_review_received_email(
    game_name: str,
    theme_primary: Optional[str] = None,
    theme_secondary: Optional[str] = None
) -> str:
    """
    Generate HTML email template for review completion notification

    Args:
        game_name: Name of the game
        theme_primary: Primary brand color (hex)
        theme_secondary: Secondary brand color (hex)

    Returns:
        HTML email template as string
    """
    if theme_primary is None:
        theme_primary = "#667eea"
    if theme_secondary is None:
        theme_secondary = "#764ba2"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Review Received - {game_name}</title>
</head>
<body style="margin: 0; padding: 0; font-family: system-ui, sans-serif; background: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background: #f5f5f5; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {theme_primary} 0%, {theme_secondary} 100%); padding: 40px 30px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="margin: 0; color: white; font-size: 28px;">
                                🎉 Your Review is Ready!
                            </h1>
                            <p style="margin: 15px 0 0 0; color: rgba(255,255,255,0.95); font-size: 16px;">
                                {{{{ reviewer_name }}}} completed your {game_name} review
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 1.6; color: #333;">
                                Great news! Your peer review is complete and our AI has analyzed the feedback.
                            </p>

                            <!-- Stats -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 30px 0;">
                                <tr>
                                    <td style="padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center; width: 50%;">
                                        <div style="font-size: 32px; font-weight: 700; color: {theme_primary};">
                                            {{{{ overall_rating }}}}/5
                                        </div>
                                        <div style="font-size: 14px; color: #666; margin-top: 5px;">
                                            Overall Rating
                                        </div>
                                    </td>
                                    <td style="width: 20px;"></td>
                                    <td style="padding: 20px; background: #f8f9fa; border-radius: 8px; text-align: center; width: 50%;">
                                        <div style="font-size: 32px; font-weight: 700; color: {theme_primary};">
                                            {{{{ helpfulness_score }}}}%
                                        </div>
                                        <div style="font-size: 14px; color: #666; margin-top: 5px;">
                                            AI Helpfulness
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center">
                                        <a href="{{{{ analysis_url }}}}" style="display: inline-block; background: {theme_primary}; color: white; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                                            View AI Analysis →
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 30px; background: #f8f9fa; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="margin: 0; font-size: 13px; color: #999;">
                                Analyzed by CalRiven, TheAuditor, DeathToData & Soulfra Networks
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''


def generate_share_helper(language: str = 'python') -> str:
    """
    Generate helper function for creating game shares

    Args:
        language: Programming language ('python', 'javascript', 'go')

    Returns:
        Code snippet as string
    """
    if language == 'python':
        return '''# Game Sharing Helper
from game_sharing import create_game_share
from typing import Dict, Any, Tuple

def share_game_with_friend(
    game_type: str,
    game_data: Dict[str, Any],
    friend_email: str,
    sender_email: str,
    message: str = None
) -> Tuple[int, str]:
    """
    Share a game with a friend for peer review

    Args:
        game_type: Type of game ('cringeproof', 'color_challenge', etc.)
        game_data: Game results and answers
        friend_email: Friend's email address
        sender_email: Your email address
        message: Optional personal message

    Returns:
        Tuple of (share_id, share_code)

    Example:
        share_id, code = share_game_with_friend(
            game_type='cringeproof',
            game_data={'answers': [1, 2, 3], 'score': 75},
            friend_email='friend@example.com',
            sender_email='me@example.com',
            message='Can you review my self-assessment?'
        )

        print(f"Share link: https://cringeproof.com/review/{code}")
    """
    share_id, share_code = create_game_share(
        game_type=game_type,
        game_data=game_data,
        recipient_email=friend_email,
        sender_email=sender_email,
        message=message,
        expires_in_days=30
    )

    return share_id, share_code
'''

    elif language == 'javascript':
        return '''// Game Sharing Helper
async function shareGameWithFriend({
    gameType,
    gameData,
    friendEmail,
    senderEmail,
    message = null
}) {
    /**
     * Share a game with a friend for peer review
     *
     * @param {string} gameType - Type of game ('cringeproof', 'color_challenge', etc.)
     * @param {Object} gameData - Game results and answers
     * @param {string} friendEmail - Friend's email address
     * @param {string} senderEmail - Your email address
     * @param {string} message - Optional personal message
     * @returns {Promise<{shareId: number, shareCode: string}>}
     */
    const response = await fetch('/games/share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            game_type: gameType,
            game_data: gameData,
            recipient_email: friendEmail,
            sender_email: senderEmail,
            message: message
        })
    });

    if (!response.ok) {
        throw new Error('Failed to create game share');
    }

    const data = await response.json();
    return {
        shareId: data.share_id,
        shareCode: data.share_code
    };
}

// Example usage
const { shareId, shareCode } = await shareGameWithFriend({
    gameType: 'cringeproof',
    gameData: { answers: [1, 2, 3], score: 75 },
    friendEmail: 'friend@example.com',
    senderEmail: 'me@example.com',
    message: 'Can you review my self-assessment?'
});

console.log(`Share link: https://cringeproof.com/review/${shareCode}`);
'''

    else:
        return f'# Language "{language}" not yet supported. Try: python, javascript'


def generate_analytics_report(report_type: str = 'summary') -> str:
    """
    Generate analytics report template for game sharing stats

    Args:
        report_type: Type of report ('summary', 'detailed', 'export')

    Returns:
        Python code for generating report
    """
    if report_type == 'summary':
        return r'''# Game Sharing Analytics - Summary Report
from game_sharing import get_share_stats
from typing import Dict, Any
import json

def generate_summary_report() -> Dict[str, Any]:
    """
    Generate summary analytics report for game sharing

    Returns:
        Dict with key metrics
    """
    stats = get_share_stats()

    report = {
        'overview': {
            'total_shares': stats['total_shares'],
            'completion_rate': str(round(stats['completion_rate'], 1)) + '%',
            'avg_helpfulness': str(round(stats['avg_helpfulness'], 2))
        },
        'by_game_type': stats['by_game_type'],
        'recommendations': []
    }

    # Add insights
    if stats['completion_rate'] > 80:
        report['recommendations'].append('✅ Excellent completion rate!')
    elif stats['completion_rate'] > 50:
        report['recommendations'].append('⚠️ Consider sending reminder emails')
    else:
        report['recommendations'].append('❌ Review share invitation copy')

    if stats['avg_helpfulness'] > 0.7:
        report['recommendations'].append('✅ High quality peer reviews')
    elif stats['avg_helpfulness'] > 0.5:
        report['recommendations'].append('⚠️ Review questions could be improved')
    else:
        report['recommendations'].append('❌ Consider revising review prompts')

    return report

# Usage
if __name__ == '__main__':
    report = generate_summary_report()
    print(json.dumps(report, indent=2))
'''

    elif report_type == 'detailed':
        code = """# Game Sharing Analytics - Detailed Report
from game_sharing import get_share_stats, get_reviews_for_share
from database import get_db
import json

def generate_detailed_report(time_period: str = '30d') -> dict:
    \"\"\"
    Generate detailed analytics report with breakdowns

    Args:
        time_period: Time period ('7d', '30d', '90d', 'all')

    Returns:
        Comprehensive analytics dict
    \"\"\"
    db = get_db()
    stats = get_share_stats()

    # Get shares by status
    shares_by_status = db.execute(\"\"\"
        SELECT status, COUNT(*) as count
        FROM game_shares
        GROUP BY status
    \"\"\").fetchall()

    # Get average review quality
    review_quality = db.execute(\"\"\"
        SELECT
            AVG(overall_rating) as avg_rating,
            AVG(helpfulness_score) as avg_helpfulness,
            COUNT(*) as total_reviews
        FROM game_reviews
    \"\"\").fetchone()

    # Get top reviewers
    top_reviewers = db.execute(\"\"\"
        SELECT
            reviewer_email,
            COUNT(*) as review_count,
            AVG(helpfulness_score) as avg_quality
        FROM game_reviews
        GROUP BY reviewer_email
        ORDER BY review_count DESC
        LIMIT 10
    \"\"\").fetchall()

    return {
        'overview': stats,
        'shares_by_status': {row[0]: row[1] for row in shares_by_status},
        'review_quality': dict(review_quality),
        'top_reviewers': [dict(row) for row in top_reviewers],
        'time_period': time_period
    }

# Usage
if __name__ == '__main__':
    report = generate_detailed_report('30d')
    print(json.dumps(report, indent=2))
"""
        return code

    else:
        return f'# Report type "{report_type}" not supported. Try: summary, detailed'


# ==============================================================================
# TEMPLATE DEFINITIONS
# ==============================================================================

TEMPLATES = {
    'share-email': {
        'description': 'HTML email template for game share invitation',
        'generator': generate_share_email,
        'parameters': ['game_name', 'sender_name?', 'theme_primary?', 'theme_secondary?'],
        'examples': [
            "generate_template('games', 'share-email', game_name='cringeproof')",
            "generate_template('games', 'share-email', game_name='color_challenge', sender_name='Alex', theme_primary='#FF6B6B')"
        ],
        'tags': ['email', 'html', 'notification', 'games', 'sharing']
    },

    'review-received-email': {
        'description': 'HTML email template for review completion notification',
        'generator': generate_review_received_email,
        'parameters': ['game_name', 'theme_primary?', 'theme_secondary?'],
        'examples': [
            "generate_template('games', 'review-received-email', game_name='cringeproof')",
            "generate_template('games', 'review-received-email', game_name='color_challenge', theme_primary='#4ECDC4')"
        ],
        'tags': ['email', 'html', 'notification', 'games', 'review']
    },

    'share-helper': {
        'description': 'Helper function for creating game shares',
        'generator': generate_share_helper,
        'parameters': ['language?'],
        'examples': [
            "generate_template('games', 'share-helper')",
            "generate_template('games', 'share-helper', language='javascript')"
        ],
        'tags': ['python', 'javascript', 'helper', 'games', 'sharing', 'api']
    },

    'analytics-report': {
        'description': 'Analytics report generator for game sharing stats',
        'generator': generate_analytics_report,
        'parameters': ['report_type?'],
        'examples': [
            "generate_template('games', 'analytics-report')",
            "generate_template('games', 'analytics-report', report_type='detailed')"
        ],
        'tags': ['analytics', 'reporting', 'stats', 'games', 'python']
    }
}


# ==============================================================================
# TEST CODE
# ==============================================================================

if __name__ == '__main__':
    print("🎮 Game Templates\n")

    print("=" * 70)
    print("1. Share Email Template")
    print("=" * 70)
    email = generate_share_email('cringeproof', 'Alex', '#FF6B6B', '#4ECDC4')
    print(f"Generated {len(email)} characters")
    print(email[:300] + "...\n")

    print("=" * 70)
    print("2. Review Received Email")
    print("=" * 70)
    email2 = generate_review_received_email('cringeproof', '#FF6B6B', '#4ECDC4')
    print(f"Generated {len(email2)} characters")
    print(email2[:300] + "...\n")

    print("=" * 70)
    print("3. Share Helper (Python)")
    print("=" * 70)
    helper = generate_share_helper('python')
    print(helper)

    print("\n" + "=" * 70)
    print("4. Analytics Report")
    print("=" * 70)
    report = generate_analytics_report('summary')
    print(report[:400] + "...")

    print("\n✅ All game templates working!")
