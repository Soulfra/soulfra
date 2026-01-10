#!/usr/bin/env python3
"""
Soulfra Universal AI Assistant - Command Router

Routes natural language + commands to the appropriate backend capability:
- QR code generation
- Neural network training/prediction
- Research (search posts/comments)
- Brand voice generation
- URL shortening
- Ollama chat
- Automations

Context-aware: Knows what page user is on, suggests relevant actions
"""

import json
import urllib.request
import urllib.error
import base64
from io import BytesIO
from datetime import datetime
import logging
import traceback
import os

# Setup logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'assistant_errors.log')),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger('SoulAssistant')


class SoulAssistant:
    """Universal AI assistant that routes to all system capabilities"""

    # Assistant AI user ID (created by create_assistant_user.py)
    ASSISTANT_USER_ID = 14

    def __init__(self, user_id=None, context=None, session_id=None):
        """
        Initialize assistant

        Args:
            user_id: Current user ID (the human user, not the assistant)
            context: Dict with page context (url, post_id, etc.)
            session_id: Existing session ID to resume (optional)
        """
        self.user_id = user_id or self.ASSISTANT_USER_ID
        self.context = context or {}
        self.session_id = session_id

        # Create or load session if on a post page
        if self.context.get('post_id') and not self.session_id:
            self.session_id = self._create_or_load_session()

    def _create_or_load_session(self):
        """Create or load discussion session for current post"""
        from database import get_db

        post_id = self.context.get('post_id')
        if not post_id:
            return None

        db = get_db()

        # Try to load existing session for this user+post
        session = db.execute('''
            SELECT id FROM discussion_sessions
            WHERE post_id = ? AND user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (post_id, self.user_id)).fetchone()

        if session:
            db.close()
            return session['id']

        # Create new session
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO discussion_sessions (post_id, user_id, persona_name, status)
            VALUES (?, ?, 'soulassistant', 'active')
        ''', (post_id, self.user_id))

        session_id = cursor.lastrowid
        db.commit()
        db.close()

        return session_id

    def _save_message(self, sender, content, message_type='chat', metadata=None):
        """Save message to discussion_messages table"""
        if not self.session_id:
            return  # No session = ephemeral chat

        from database import get_db

        db = get_db()
        db.execute('''
            INSERT INTO discussion_messages (session_id, sender, content, message_type, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.session_id, sender, content, message_type, json.dumps(metadata) if metadata else None))
        db.commit()
        db.close()

    def get_conversation_history(self):
        """Load conversation history from database"""
        if not self.session_id:
            return []

        from database import get_db

        db = get_db()
        messages = db.execute('''
            SELECT sender, content, message_type, created_at
            FROM discussion_messages
            WHERE session_id = ?
            ORDER BY created_at ASC
        ''', (self.session_id,)).fetchall()
        db.close()

        return [dict(msg) for msg in messages]

    def post_comment(self, comment_text):
        """
        Post the assistant's comment to the current post

        Args:
            comment_text: The comment to post

        Returns:
            Dict with success status and comment_id
        """
        post_id = self.context.get('post_id')
        if not post_id:
            return {'success': False, 'error': 'No post context'}

        from database import get_db

        db = get_db()
        cursor = db.cursor()

        # Insert comment as the assistant user
        cursor.execute('''
            INSERT INTO comments (post_id, user_id, content)
            VALUES (?, ?, ?)
        ''', (post_id, self.ASSISTANT_USER_ID, comment_text))

        comment_id = cursor.lastrowid

        # Update session with final comment
        if self.session_id:
            cursor.execute('''
                UPDATE discussion_sessions
                SET final_comment_id = ?, finalized_at = CURRENT_TIMESTAMP, status = 'completed'
                WHERE id = ?
            ''', (comment_id, self.session_id))

        db.commit()
        db.close()

        return {
            'success': True,
            'comment_id': comment_id,
            'message': 'Comment posted successfully'
        }

    def handle_message(self, message):
        """
        Process user message and route to appropriate handler

        Args:
            message: User's message (command or natural language)

        Returns:
            Dict with response, artifacts, actions
        """
        message = message.strip()

        # Save user message
        self._save_message('user', message)

        # Check if it's a command
        if message.startswith('/'):
            result = self._handle_command(message)
        else:
            # Otherwise, route to Ollama chat
            result = self._handle_chat(message)

        # Save AI response
        if result.get('success'):
            self._save_message('ai', result.get('response', ''), metadata=result.get('artifact'))

        # Add session_id to result
        if self.session_id:
            result['session_id'] = self.session_id

        return result

    def _handle_command(self, command):
        """Route slash commands to appropriate handlers"""

        # Parse command
        parts = command[1:].split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        # Route to handlers
        handlers = {
            'qr': self._cmd_qr,
            'neural': self._cmd_neural,
            'research': self._cmd_research,
            'brand': self._cmd_brand,
            'shorturl': self._cmd_shorturl,
            'generate': self._cmd_generate,
            'dnd': self._cmd_dnd,
            'help': self._cmd_help,
            'context': self._cmd_context,
        }

        handler = handlers.get(cmd)
        if handler:
            return handler(args)
        else:
            return {
                'success': False,
                'response': f"Unknown command: /{cmd}\n\nAvailable commands:\n{self._get_help_text()}"
            }

    def _cmd_qr(self, args):
        """Generate QR code"""
        if not args:
            # Use current post/page if available
            if self.context.get('post'):
                args = self.context['post'].get('title', '')
            else:
                args = self.context.get('url', 'Hello from Soulfra!')

        try:
            # Import QR generator
            from qr_encoder_stdlib import generate_qr_code_base64

            # Generate QR code as base64
            qr_base64 = generate_qr_code_base64(args)

            return {
                'success': True,
                'response': f"✅ QR Code generated for: {args[:50]}...",
                'artifact': {
                    'type': 'qr_code',
                    'data': qr_base64,
                    'text': args
                }
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"❌ Error generating QR code: {str(e)}"
            }

    def _cmd_neural(self, args):
        """Neural network operations"""
        if not args:
            return {
                'success': False,
                'response': "Usage:\n/neural predict <text>\n/neural train\n/neural status"
            }

        parts = args.split(maxsplit=1)
        operation = parts[0].lower()

        if operation == 'predict' and len(parts) > 1:
            text = parts[1]
            try:
                from brand_voice_generator import predict_brand_voice
                result = predict_brand_voice(text)

                return {
                    'success': True,
                    'response': f"🧠 Neural Network Prediction:\n\nBrand: {result.get('brand', 'unknown')}\nConfidence: {result.get('confidence', 0)*100:.1f}%",
                    'artifact': {
                        'type': 'neural_prediction',
                        'data': result
                    }
                }
            except Exception as e:
                return {
                    'success': False,
                    'response': f"❌ Prediction error: {str(e)}"
                }

        elif operation == 'status':
            try:
                from database import get_db

                db = get_db()
                networks = db.execute('''
                    SELECT model_name, description, trained_at
                    FROM neural_networks
                    ORDER BY model_name
                ''').fetchall()
                db.close()

                if not networks:
                    return {
                        'success': True,
                        'response': "❌ No neural networks found in database"
                    }

                response = f"🧠 Neural Network Status ({len(networks)} models loaded):\n\n"
                for net in networks:
                    trained_date = net['trained_at'][:10] if net['trained_at'] else 'unknown'
                    desc = net['description'] or 'No description'
                    response += f"✅ **{net['model_name']}**\n"
                    response += f"   {desc}\n"
                    response += f"   Trained: {trained_date}\n\n"

                # If viewing a post, offer to classify it
                if self.context.get('post'):
                    post_title = self.context['post'].get('title', '')
                    response += f"\n💡 **Tip**: Type `/neural classify` to analyze this post with all networks!"

                return {
                    'success': True,
                    'response': response.strip()
                }
            except Exception as e:
                return {
                    'success': False,
                    'response': f"❌ Error loading neural networks: {str(e)}"
                }

        elif operation == 'classify':
            # Classify current post with all neural networks
            if not self.context.get('post'):
                return {
                    'success': False,
                    'response': "❌ Not viewing a post. Navigate to a post page first."
                }

            try:
                post = self.context['post']
                post_content = f"{post.get('title', '')} {post.get('content', '')}"

                from brand_voice_generator import predict_brand_voice

                # Get predictions from all classifiers
                result = predict_brand_voice(post_content)

                response = f"🧠 Neural Network Analysis of \"{post.get('title', 'this post')[:50]}...\"\n\n"
                response += f"**Primary Classification**: {result.get('brand', 'unknown').title()}\n"
                response += f"**Confidence**: {result.get('confidence', 0)*100:.1f}%\n\n"

                if result.get('all_predictions'):
                    response += "**All Network Predictions**:\n"
                    for pred in result.get('all_predictions', []):
                        confidence = pred.get('confidence', 0) * 100
                        bar = '█' * int(confidence / 10) + '░' * (10 - int(confidence / 10))
                        response += f"  {pred['brand']:20s} {bar} {confidence:.1f}%\n"

                return {
                    'success': True,
                    'response': response,
                    'artifact': {
                        'type': 'neural_classification',
                        'data': result
                    }
                }
            except Exception as e:
                return {
                    'success': False,
                    'response': f"❌ Classification error: {str(e)}"
                }

        else:
            return {
                'success': False,
                'response': "Usage:\n/neural status - Show all neural networks\n/neural classify - Analyze current post\n/neural predict <text> - Predict brand from text"
            }

    def _cmd_research(self, args):
        """Research/search posts and comments"""
        if not args:
            return {
                'success': False,
                'response': "Usage: /research <topic>"
            }

        try:
            from database import get_db

            # Search posts
            db = get_db()
            posts = db.execute('''
                SELECT id, title, content
                FROM posts
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY published_at DESC
                LIMIT 5
            ''', (f'%{args}%', f'%{args}%')).fetchall()

            # Search comments
            comments = db.execute('''
                SELECT c.content, p.title as post_title, u.display_name
                FROM comments c
                JOIN posts p ON c.post_id = p.id
                JOIN users u ON c.user_id = u.id
                WHERE c.content LIKE ?
                ORDER BY c.created_at DESC
                LIMIT 5
            ''', (f'%{args}%',)).fetchall()

            db.close()

            # Format results
            response = f"🔍 Research Results for '{args}':\n\n"

            if posts:
                response += f"**Posts ({len(posts)}):**\n"
                for post in posts:
                    response += f"• {post['title']}\n"
                response += "\n"
            else:
                response += "No matching posts found.\n\n"

            if comments:
                response += f"**Comments ({len(comments)}):**\n"
                for comment in comments:
                    preview = comment['content'][:100] + "..." if len(comment['content']) > 100 else comment['content']
                    response += f"• {comment['display_name']} on '{comment['post_title']}': {preview}\n"
            else:
                response += "No matching comments found.\n"

            return {
                'success': True,
                'response': response,
                'artifact': {
                    'type': 'research_results',
                    'data': {
                        'posts': [dict(p) for p in posts],
                        'comments': [dict(c) for c in comments]
                    }
                }
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"❌ Research error: {str(e)}"
            }

    def _cmd_brand(self, args):
        """Generate content in brand voice"""
        if not args:
            return {
                'success': False,
                'response': "Usage: /brand <brand-name> <topic>"
            }

        parts = args.split(maxsplit=1)
        brand = parts[0]
        topic = parts[1] if len(parts) > 1 else "general update"

        try:
            from brand_voice_generator import generate_brand_content
            content = generate_brand_content(brand, topic, length='short')

            return {
                'success': True,
                'response': f"✨ {brand.title()} Brand Voice:\n\n{content}",
                'artifact': {
                    'type': 'brand_content',
                    'data': {
                        'brand': brand,
                        'content': content
                    }
                }
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"❌ Brand generation error: {str(e)}\n\nAvailable brands: soulfra, calriven, deathtodata, theauditor"
            }

    def _cmd_shorturl(self, args):
        """Shorten a URL"""
        if not args:
            # Use current page URL if available
            args = self.context.get('url', '')

        if not args:
            return {
                'success': False,
                'response': "Usage: /shorturl <url>"
            }

        try:
            from url_shortener import generate_short_url
            short_url = generate_short_url('admin')  # TODO: Use actual username

            return {
                'success': True,
                'response': f"✂️ Shortened URL:\n\n{short_url}",
                'artifact': {
                    'type': 'short_url',
                    'data': {
                        'original': args,
                        'shortened': short_url
                    }
                }
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"❌ URL shortening error: {str(e)}"
            }

    def _cmd_dnd(self, args):
        """
        D&D Campaign commands

        /dnd start <quest> - Start a quest
        /dnd action <text> - Take action in current quest
        /dnd inventory - Show items and character
        /dnd quests - List available quests
        """
        if not args:
            return {
                'success': False,
                'response': "**D&D Commands:**\n\n/dnd start <quest> - Start a quest\n/dnd action <text> - Take an action\n/dnd inventory - Show your items\n/dnd quests - List available quests"
            }

        parts = args.split(maxsplit=1)
        operation = parts[0].lower()

        try:
            from simple_games.dnd_campaign import DNDCampaign, get_available_quests, create_dnd_game, get_user_active_game
            from aging_curves import get_all_attributes
            from trading_system import get_user_inventory
            from database import get_db

            if operation == 'quests':
                # List available quests
                quests = get_available_quests()
                response = "⚔️ **Available D&D Quests:**\n\n"
                for i, quest in enumerate(quests, 1):
                    response += f"**{i}. {quest['name']}** ({quest['difficulty'].upper()})\n"
                    response += f"   Ages character: +{quest['aging_years']} years\n"
                    response += f"   Rewards: {len(quest['rewards'].get('items', []))} items, {quest['rewards'].get('xp', 0)} XP\n\n"

                response += "\nStart with: `/dnd start <quest-slug>`"
                return {
                    'success': True,
                    'response': response
                }

            elif operation == 'start':
                if len(parts) < 2:
                    return {
                        'success': False,
                        'response': "Usage: /dnd start <quest-slug>\n\nSee available quests: /dnd quests"
                    }

                quest_slug = parts[1].strip()

                # Create game
                game_id = create_dnd_game(self.user_id, quest_slug)

                # Start quest
                campaign = DNDCampaign(game_id, self.user_id, quest_slug)
                result = campaign.start_quest()

                response = f"🐉 **Quest Started: {quest_slug.replace('-', ' ').title()}**\n\n"
                response += f"{result['narration']}\n\n"
                response += "Take action with: `/dnd action <your action>`"

                return {
                    'success': True,
                    'response': response,
                    'artifact': {
                        'type': 'dnd_quest_start',
                        'game_id': game_id,
                        'quest': result
                    }
                }

            elif operation == 'action':
                if len(parts) < 2:
                    return {
                        'success': False,
                        'response': "Usage: /dnd action <describe your action>"
                    }

                action_text = parts[1].strip()

                # Get active game
                game = get_user_active_game(self.user_id)
                if not game:
                    return {
                        'success': False,
                        'response': "❌ No active quest! Start one with: /dnd start <quest-slug>"
                    }

                # Parse quest slug from game
                db = get_db()
                game_row = db.execute('SELECT quest_slug FROM dnd_games WHERE id = ?', (game['id'],)).fetchone()
                quest_slug = game_row['quest_slug'] if game_row else None
                db.close()

                if not quest_slug:
                    return {
                        'success': False,
                        'response': "❌ Could not find quest info"
                    }

                # Take action
                campaign = DNDCampaign(game['id'], self.user_id, quest_slug)
                result = campaign.take_action('attack', action_text, 'enemy')

                response = f"⚔️ **Action: {action_text}**\n\n"
                response += f"**Verdict:** {result['verdict'].upper()}\n\n"
                response += f"{result['narration']}\n\n"

                if result.get('completion'):
                    completion = result['completion']
                    response += f"\n🎉 **Quest Completed!**\n\n"
                    response += f"**Character aged:** {completion['age_before']} → {completion['age_after']} years\n\n"
                    response += f"**Items earned:**\n"
                    for item in completion['items_earned']:
                        response += f"  • {item['name']} ({item['rarity']}) x{item['quantity']}\n"
                    response += f"\n**XP:** +{completion['xp_earned']}"

                return {
                    'success': True,
                    'response': response,
                    'artifact': {
                        'type': 'dnd_action_result',
                        'result': result
                    }
                }

            elif operation == 'inventory':
                # Show character + inventory
                db = get_db()
                user = db.execute('SELECT character_age FROM users WHERE id = ?', (self.user_id,)).fetchone()
                db.close()

                age = user['character_age'] or 20
                attrs = get_all_attributes(age)
                inventory = get_user_inventory(self.user_id)

                response = f"👤 **Your Character**\n\n"
                response += f"**Age:** {age} years\n\n"
                response += f"**Attributes:**\n"
                for attr, value in attrs.items():
                    response += f"  • {attr.capitalize()}: {value:.2f}\n"

                response += f"\n🎒 **Inventory ({len(inventory)} items):**\n\n"
                if inventory:
                    for item in inventory[:10]:
                        response += f"  • {item['name']} ({item['rarity']}) x{item['quantity']}\n"
                else:
                    response += "  Empty inventory. Complete quests to earn items!"

                return {
                    'success': True,
                    'response': response
                }

            else:
                return {
                    'success': False,
                    'response': f"Unknown D&D operation: {operation}\n\nUse /dnd (no args) for help"
                }

        except Exception as e:
            return {
                'success': False,
                'response': f"❌ D&D error: {str(e)}"
            }

    def _cmd_context(self, args):
        """Show current context"""
        return {
            'success': True,
            'response': f"📍 Current Context:\n\n{json.dumps(self.context, indent=2)}"
        }

    def _cmd_help(self, args):
        """Show help"""
        return {
            'success': True,
            'response': self._get_help_text()
        }

    def _handle_chat(self, message):
        """Handle natural language chat via Ollama"""
        try:
            # Build context-aware prompt with full post content
            prompt = message
            if self.context.get('post'):
                post = self.context['post']
                # Include title and excerpt of content (first 800 chars to fit in context)
                content_excerpt = post.get('content', '')[:800]
                if len(post.get('content', '')) > 800:
                    content_excerpt += '...'

                prompt = f"""You are viewing a blog post titled: "{post.get('title', 'Untitled')}"

Post content excerpt:
{content_excerpt}

User question: {message}

Please answer based on the post content above."""

            # Call Ollama
            request_data = {
                'model': 'llama2',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 300
                }
            }

            req = urllib.request.Request(
                'http://localhost:11434/api/generate',
                data=json.dumps(request_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            response = urllib.request.urlopen(req, timeout=60)
            result = json.loads(response.read().decode('utf-8'))
            ai_response = result.get('response', '').strip()

            return {
                'success': True,
                'response': ai_response
            }

        except urllib.error.URLError:
            return {
                'success': False,
                'response': "❌ Ollama not connected. Start with: ollama serve"
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"❌ Chat error: {str(e)}"
            }

    def _cmd_generate(self, args):
        """
        Content generation commands

        /generate post - Turn current conversation into blog post
        /generate feed - Generate RSS feed
        /generate sessions - Show all widget sessions
        """
        if not args:
            return {
                'success': False,
                'response': "Usage:\n/generate post [template]\n/generate feed\n/generate sessions"
            }

        parts = args.split(maxsplit=1)
        operation = parts[0].lower()

        try:
            logger.info(f"Starting /generate {operation} command")

            from content_generator import ContentGenerator
            logger.info("ContentGenerator imported successfully")

            generator = ContentGenerator()
            logger.info("ContentGenerator initialized")

            if operation == 'post':
                # Get template if specified, default to 'qa_format'
                template = parts[1] if len(parts) > 1 else 'qa_format'
                valid_templates = ['qa_format', 'tutorial', 'insight', 'story']

                logger.info(f"Template: {template}")

                if template not in valid_templates:
                    return {
                        'success': False,
                        'response': f"Invalid template: {template}\n\nValid templates: {', '.join(valid_templates)}"
                    }

                # Get current session_id from context
                session_id = self.context.get('session_id')
                logger.info(f"Session ID from context: {session_id}")
                logger.info(f"Full context: {self.context}")

                if not session_id:
                    logger.warning("No session_id found in context")
                    return {
                        'success': False,
                        'response': "❌ No conversation session found. Start chatting first!"
                    }

                # Get brand from context (if available)
                brand_slug = self.context.get('brand_slug') or self.context.get('brand', {}).get('slug')

                # Generate post from conversation
                logger.info(f"Calling conversation_to_post(session_id={session_id}, author_id={self.user_id or 6}, template={template}, brand_slug={brand_slug})")

                post = generator.conversation_to_post(
                    session_id=session_id,
                    author_id=self.user_id or 6,  # Default to SoulAssistant
                    template=template,
                    auto_publish=False,  # Save as draft
                    brand_slug=brand_slug,  # Pass brand for colors
                    generate_images=True  # Generate procedural images
                )

                logger.info(f"conversation_to_post returned: {post}")

                if not post:
                    return {
                        'success': False,
                        'response': "❌ Could not generate post from conversation (may be too short)"
                    }

                response = f"""✨ **Blog Post Generated!**

**Title:** {post.title}
**Slug:** {post.slug}
**Status:** {post.status.value}
**Template:** {template}
**Tags:** {', '.join(post.tags[:3]) if post.tags else 'None'}

**Excerpt:**
{post.excerpt}

The post has been saved as a draft. Visit /admin to publish it!"""

                return {
                    'success': True,
                    'response': response,
                    'artifact': {
                        'type': 'blog_post_draft',
                        'data': post.to_dict()
                    }
                }

            elif operation == 'feed':
                # Generate RSS feed preview
                feed = generator.generate_feed(format='rss', limit=5)
                return {
                    'success': True,
                    'response': f"📡 **RSS Feed Generated**\n\nGenerated {len(feed)} characters of RSS XML\n\nPreview:\n```xml\n{feed[:300]}...\n```"
                }

            elif operation == 'sessions':
                # Show all widget sessions
                sessions = generator.get_conversation_sessions()

                if not sessions:
                    return {
                        'success': True,
                        'response': "No widget conversation sessions found yet."
                    }

                response = "📊 **Widget Conversation Sessions:**\n\n"
                for session in sessions[:10]:
                    response += f"**Session {session['id']}**\n"
                    response += f"  • Created: {session['created_at']}\n"
                    response += f"  • Messages: {session['message_count']}\n"
                    response += f"  • Last activity: {session.get('last_activity', 'N/A')}\n"
                    response += f"  • Generate: `/generate post` (from session {session['id']})\n\n"

                return {
                    'success': True,
                    'response': response
                }

            else:
                return {
                    'success': False,
                    'response': f"Unknown generate operation: {operation}\n\nValid operations: post, feed, sessions"
                }

        except Exception as e:
            # Log full error with stack trace
            error_msg = f"Error in /generate {operation}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())

            # Return detailed error to user
            return {
                'success': False,
                'response': f"""❌ Generation error: {str(e)}

**Error Details:**
- Operation: /generate {operation}
- Session ID: {self.context.get('session_id', 'MISSING')}
- User ID: {self.user_id or 'MISSING'}

**Debug:**
Check logs/assistant_errors.log for full stack trace.

**Common Fixes:**
1. Make sure you've had a conversation first (need 3+ messages)
2. Check if Ollama is running: `curl http://localhost:11434/api/tags`
3. Verify content_generator.py exists"""
            }

    def _get_help_text(self):
        """Get help text"""
        return """**Available Commands:**

🔍 **Research & Analysis**
  /research <topic> - Search posts and comments
  /neural predict <text> - Classify text with neural net
  /neural status - Check neural network status

📱 **Generation**
  /qr [text] - Generate QR code
  /brand <name> <topic> - Generate in brand voice
  /shorturl [url] - Shorten URL

✨ **Content Creation**
  /generate post [template] - Turn conversation into blog post
  /generate feed - Generate RSS feed
  /generate sessions - Show all conversations

🎮 **D&D Campaign** (NEW!)
  /dnd quests - List available quests
  /dnd start <quest> - Start a quest
  /dnd action <text> - Take action in quest
  /dnd inventory - Show character & items

ℹ️ **Utility**
  /context - Show current page context
  /help - Show this help

**Context-Aware Actions:**
• On post page: Analyze, generate QR, research related
• Anywhere: Ask questions, get AI responses, play D&D!
• After chatting: Use /generate post to create content!

Just type naturally to chat with AI!"""

    def get_quick_actions(self):
        """Get quick actions based on current context"""
        actions = []

        # Universal actions
        actions.append({
            'label': '🔍 Research',
            'command': '/research '
        })
        actions.append({
            'label': '🧠 Neural Net',
            'command': '/neural predict '
        })

        # Context-specific actions
        if self.context.get('post'):
            post = self.context['post']
            actions.insert(0, {
                'label': '📱 Generate QR for this post',
                'command': f"/qr {post.get('title', '')}"
            })
            actions.insert(1, {
                'label': '🔍 Research related topics',
                'command': f"/research {post.get('title', '').split()[0]}"
            })

        return actions


# For quick testing
if __name__ == '__main__':
    print("🤖 Soulfra Assistant Test")
    print("=" * 70)

    assistant = SoulAssistant(user_id=1, context={'url': '/test'})

    # Test commands
    tests = [
        '/help',
        '/research privacy',
        '/neural status',
        '/qr Hello World',
    ]

    for test in tests:
        print(f"\n> {test}")
        result = assistant.handle_message(test)
        print(result['response'])
