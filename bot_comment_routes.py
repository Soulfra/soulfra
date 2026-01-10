"""
Bot Comment Routes - API endpoints for bot-generated social proof

Routes:
- POST /api/bot/comment - Generate comment for content
- GET /api/bot/comments/<target_type>/<target_id> - Get all bot comments
- POST /api/bot/auto-comment - Auto-generate comments on new content

Usage in app.py:
    from bot_comment_routes import register_bot_routes
    register_bot_routes(app)
"""

from flask import jsonify, request
from bot_comment_generator import BotCommentGenerator


def register_bot_routes(app):
    """Register bot comment routes with Flask app"""

    bot = BotCommentGenerator()

    @app.route('/api/bot/comment', methods=['POST'])
    def api_bot_comment():
        """
        Generate bot comment for content

        POST body:
        {
            "content": "The content to comment on",
            "target_type": "voice_memo",
            "target_id": 42
        }

        Returns:
        {
            "success": true,
            "comment_id": 123,
            "comment_text": "This is really cool!",
            "generated_at": "2026-01-03T15:30:00"
        }
        """
        data = request.json

        content = data.get('content')
        target_type = data.get('target_type', 'voice_memo')
        target_id = data.get('target_id')

        if not content or not target_id:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: content, target_id'
            }), 400

        try:
            result = bot.generate_and_save(
                content=content,
                target_type=target_type,
                target_id=target_id
            )

            return jsonify({
                'success': True,
                **result
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/bot/comments/<target_type>/<int:target_id>')
    def api_get_bot_comments(target_type, target_id):
        """
        Get all bot comments for target

        Returns:
        {
            "success": true,
            "comments": [
                {
                    "id": 1,
                    "comment_text": "This is cool!",
                    "generated_at": "2026-01-03T15:30:00"
                }
            ]
        }
        """
        try:
            comments = bot.get_comments_for_target(target_type, target_id)

            return jsonify({
                'success': True,
                'comments': comments
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/bot/auto-comment', methods=['POST'])
    def api_auto_comment():
        """
        Auto-generate multiple bot comments on new content

        POST body:
        {
            "content": "The content",
            "target_type": "voice_memo",
            "target_id": 42,
            "count": 3
        }

        Returns:
        {
            "success": true,
            "comments_generated": 3,
            "comments": [...]
        }
        """
        data = request.json

        content = data.get('content')
        target_type = data.get('target_type', 'voice_memo')
        target_id = data.get('target_id')
        count = data.get('count', 2)  # Default: 2 bot comments

        if not content or not target_id:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: content, target_id'
            }), 400

        try:
            comments = []

            for i in range(count):
                result = bot.generate_and_save(
                    content=content,
                    target_type=target_type,
                    target_id=target_id
                )
                comments.append(result)

            return jsonify({
                'success': True,
                'comments_generated': len(comments),
                'comments': comments
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    print("✅ Bot comment routes registered:")
    print("   - POST /api/bot/comment (Generate single comment)")
    print("   - GET /api/bot/comments/<type>/<id> (Get comments)")
    print("   - POST /api/bot/auto-comment (Auto-generate multiple)")
