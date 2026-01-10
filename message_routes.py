#!/usr/bin/env python3
"""
Message Routes - IRC/Usenet-style API endpoints

Enables cross-domain messaging for the 2045 Email System:
- Send messages to any domain/channel
- Retrieve messages (like NNTP newsreader)
- Export to JSON for GitHub Pages polling
- Device fingerprint authentication

Usage:
    POST /api/send-message
    GET  /api/messages/<domain>.json
    GET  /api/messages/<domain>/<channel>
    GET  /api/channels
"""

from flask import Blueprint, request, jsonify
from database import get_db
from device_hash import capture_device_info, get_or_create_device
from datetime import datetime
import json
import os

message_bp = Blueprint('messages', __name__)


@message_bp.route('/api/send-message', methods=['POST'])
def send_message():
    """
    Send a message to a domain/channel

    POST Body:
    {
        "to_domain": "soulfra",
        "channel": "general",
        "subject": "Hello!",
        "body": "This is a test message",
        "from_user": "matt@soulfra.com"  // Optional
    }

    Returns:
        {
            "success": true,
            "message_id": 123,
            "channel": "alt.soulfra.general"
        }
    """
    try:
        data = request.json

        # Required fields
        to_domain = data.get('to_domain')
        body = data.get('body')

        if not to_domain or not body:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: to_domain, body'
            }), 400

        # Optional fields
        channel = data.get('channel', 'general')
        subject = data.get('subject', '')
        from_user = data.get('from_user', 'anonymous')
        message_type = data.get('message_type', 'text')
        parent_id = data.get('parent_id')  # For threading

        # Get device fingerprint
        device_info = capture_device_info(request)
        device_record = get_or_create_device(device_info)
        device_hash = device_info['device_hash']

        # Insert message
        db = get_db()
        cursor = db.execute('''
            INSERT INTO domain_messages
            (from_user, from_device_hash, to_domain, channel, subject, body, created_at, message_type, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (from_user, device_hash, to_domain, channel, subject, body,
              datetime.now().isoformat(), message_type, parent_id))

        message_id = cursor.lastrowid
        db.commit()

        # Export to JSON for GitHub Pages
        export_messages_to_json(to_domain)

        return jsonify({
            'success': True,
            'message_id': message_id,
            'channel': f'alt.{to_domain}.{channel}',
            'device_hash': device_hash
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to send message: {str(e)}'
        }), 500


@message_bp.route('/api/messages/<domain>.json')
def get_messages_json(domain):
    """
    Get all messages for a domain as JSON

    Used by GitHub Pages for polling

    Returns:
        {
            "domain": "soulfra",
            "total_messages": 10,
            "channels": {
                "general": [...],
                "dev": [...],
                "voice": [...]
            },
            "updated_at": "2026-01-09T12:00:00"
        }
    """
    try:
        db = get_db()

        # Get all messages for this domain, grouped by channel
        messages = db.execute('''
            SELECT
                id,
                from_user,
                to_domain,
                channel,
                subject,
                body,
                created_at,
                message_type,
                parent_id
            FROM domain_messages
            WHERE to_domain = ?
            ORDER BY created_at DESC
        ''', (domain,)).fetchall()

        # Group by channel
        channels = {}
        for msg in messages:
            channel_name = msg['channel']
            if channel_name not in channels:
                channels[channel_name] = []

            channels[channel_name].append({
                'id': msg['id'],
                'from': msg['from_user'],
                'subject': msg['subject'],
                'body': msg['body'],
                'created_at': msg['created_at'],
                'type': msg['message_type'],
                'parent_id': msg['parent_id']
            })

        return jsonify({
            'domain': domain,
            'total_messages': len(messages),
            'channels': channels,
            'updated_at': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get messages: {str(e)}'
        }), 500


@message_bp.route('/api/messages/<domain>/<channel>')
def get_channel_messages(domain, channel):
    """
    Get messages for specific channel (like NNTP)

    Query params:
        limit: Max messages to return (default 50)
        offset: Pagination offset (default 0)
        since: ISO timestamp - only messages after this time

    Returns:
        {
            "channel": "alt.soulfra.general",
            "messages": [...],
            "total": 100,
            "limit": 50,
            "offset": 0
        }
    """
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        since = request.args.get('since')

        db = get_db()

        # Build query
        query = '''
            SELECT
                id,
                from_user,
                to_domain,
                channel,
                subject,
                body,
                created_at,
                message_type,
                parent_id
            FROM domain_messages
            WHERE to_domain = ? AND channel = ?
        '''
        params = [domain, channel]

        if since:
            query += ' AND created_at > ?'
            params.append(since)

        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        messages = db.execute(query, params).fetchall()

        # Get total count
        count_query = 'SELECT COUNT(*) as total FROM domain_messages WHERE to_domain = ? AND channel = ?'
        total = db.execute(count_query, (domain, channel)).fetchone()['total']

        return jsonify({
            'channel': f'alt.{domain}.{channel}',
            'messages': [{
                'id': msg['id'],
                'from': msg['from_user'],
                'subject': msg['subject'],
                'body': msg['body'],
                'created_at': msg['created_at'],
                'type': msg['message_type'],
                'parent_id': msg['parent_id']
            } for msg in messages],
            'total': total,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get channel messages: {str(e)}'
        }), 500


@message_bp.route('/api/channels')
def get_channels():
    """
    List all channels (like IRC /list or NNTP LIST)

    Returns:
        {
            "total_channels": 15,
            "channels": [
                {
                    "name": "alt.soulfra.general",
                    "domain": "soulfra",
                    "channel": "general",
                    "description": "General discussion",
                    "message_count": 42
                },
                ...
            ]
        }
    """
    try:
        db = get_db()

        # Get all channels with message counts
        channels = db.execute('''
            SELECT
                c.domain,
                c.channel_name,
                c.description,
                c.is_public,
                COUNT(dm.id) as message_count
            FROM channels c
            LEFT JOIN domain_messages dm
                ON c.domain = dm.to_domain
                AND c.channel_name = dm.channel
            GROUP BY c.domain, c.channel_name
            ORDER BY c.domain, c.channel_name
        ''').fetchall()

        return jsonify({
            'total_channels': len(channels),
            'channels': [{
                'name': f'alt.{ch["domain"]}.{ch["channel_name"]}',
                'domain': ch['domain'],
                'channel': ch['channel_name'],
                'description': ch['description'],
                'message_count': ch['message_count'],
                'is_public': bool(ch['is_public'])
            } for ch in channels]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get channels: {str(e)}'
        }), 500


def export_messages_to_json(domain):
    """
    Export messages to JSON file for GitHub Pages

    Creates: voice-archive/messages/{domain}.json

    This allows GitHub Pages to poll for new messages without hitting Flask
    """
    try:
        db = get_db()

        # Get all messages for domain
        messages = db.execute('''
            SELECT
                id,
                from_user,
                to_domain,
                channel,
                subject,
                body,
                created_at,
                message_type,
                parent_id
            FROM domain_messages
            WHERE to_domain = ?
            ORDER BY created_at DESC
        ''', (domain,)).fetchall()

        # Group by channel
        channels = {}
        for msg in messages:
            channel_name = msg['channel']
            if channel_name not in channels:
                channels[channel_name] = []

            channels[channel_name].append({
                'id': msg['id'],
                'from': msg['from_user'],
                'subject': msg['subject'],
                'body': msg['body'],
                'created_at': msg['created_at'],
                'type': msg['message_type'],
                'parent_id': msg['parent_id']
            })

        # Create output directory
        os.makedirs('voice-archive/messages', exist_ok=True)

        # Write JSON file
        output_path = f'voice-archive/messages/{domain}.json'
        with open(output_path, 'w') as f:
            json.dump({
                'domain': domain,
                'total_messages': len(messages),
                'channels': channels,
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)

        print(f"📤 Exported {len(messages)} messages to {output_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to export messages: {e}")
        return False


@message_bp.route('/api/export-all-messages', methods=['POST'])
def export_all_messages():
    """
    Export all domain messages to JSON files

    Useful for batch updates to GitHub Pages
    """
    try:
        db = get_db()

        # Get all unique domains
        domains = db.execute('''
            SELECT DISTINCT to_domain FROM domain_messages
        ''').fetchall()

        exported = []
        for domain_row in domains:
            domain = domain_row['to_domain']
            if export_messages_to_json(domain):
                exported.append(domain)

        return jsonify({
            'success': True,
            'exported_domains': exported,
            'total_exports': len(exported)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to export: {str(e)}'
        }), 500


@message_bp.route('/api/messages/<domain>/feed.xml')
def get_messages_rss(domain):
    """
    Generate RSS feed from IRC/Usenet messages + Voice Recordings

    Merges both IRC messages and voice recordings into unified RSS feed

    Returns:
        RSS 2.0 XML feed with all messages from domain
    """
    try:
        from flask import Response
        import html as html_lib

        db = get_db()

        # Get all IRC messages for domain
        irc_messages = db.execute('''
            SELECT
                id,
                from_user,
                to_domain,
                channel,
                subject,
                body,
                created_at,
                message_type,
                'irc' as source
            FROM domain_messages
            WHERE to_domain = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (domain,)).fetchall()

        # Get voice recordings (we'll show all for now, could add domain detection later)
        # Join with users table to get email/username if available
        voice_messages = db.execute('''
            SELECT
                svr.id,
                COALESCE(u.email, 'anonymous') as from_user,
                ? as to_domain,
                'voice' as channel,
                '' as subject,
                svr.transcription as body,
                svr.created_at,
                'voice' as message_type,
                'voice' as source
            FROM simple_voice_recordings svr
            LEFT JOIN users u ON svr.user_id = u.id
            WHERE svr.transcription IS NOT NULL
            ORDER BY svr.created_at DESC
            LIMIT 50
        ''', (domain,)).fetchall()

        # Merge and sort by created_at - convert Row objects to dicts
        all_items = [dict(row) for row in irc_messages] + [dict(row) for row in voice_messages]
        all_items = sorted(all_items, key=lambda x: x['created_at'], reverse=True)[:50]

        messages = all_items

        # Domain metadata
        domain_metadata = {
            'soulfra': {
                'title': 'Soulfra Messages',
                'link': 'https://soulfra.com',
                'description': 'IRC/Usenet messages from the Soulfra network'
            },
            'cringeproof': {
                'title': 'CringeProof Ideas',
                'link': 'https://cringeproof.com',
                'description': 'AI-extracted insights from voice recordings. Zero cringe, maximum authenticity.'
            },
            'deathtodata': {
                'title': 'DeathToData Messages',
                'link': 'https://deathtodata.com',
                'description': 'Privacy-first messaging from DeathToData'
            },
            'calriven': {
                'title': 'CalRiven Messages',
                'link': 'https://calriven.com',
                'description': 'Messages from the CalRiven network'
            },
            'stpetepros': {
                'title': 'StPetePros Messages',
                'link': 'https://stpetepros.com',
                'description': 'Professional services messages and announcements'
            }
        }

        metadata = domain_metadata.get(domain, {
            'title': f'{domain.title()} Messages',
            'link': f'https://{domain}.com',
            'description': f'IRC/Usenet messages from {domain}'
        })

        # Get last build date
        last_build_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        if messages:
            last_msg_date = datetime.fromisoformat(messages[0]['created_at'])
            last_build_date = last_msg_date.strftime('%a, %d %b %Y %H:%M:%S +0000')

        # Build RSS XML
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{html_lib.escape(metadata["title"])}</title>
    <link>{html_lib.escape(metadata["link"])}</link>
    <description>{html_lib.escape(metadata["description"])}</description>
    <language>en-us</language>
    <lastBuildDate>{last_build_date}</lastBuildDate>
    <atom:link href="https://192.168.1.87:5002/api/messages/{domain}/feed.xml" rel="self" type="application/rss+xml"/>
'''

        # Add items
        for msg in messages:
            # Parse date
            try:
                pub_date = datetime.fromisoformat(msg['created_at']).strftime('%a, %d %b %Y %H:%M:%S +0000')
            except:
                pub_date = last_build_date

            # Create item title based on source
            source_type = msg.get('source', 'irc')

            if source_type == 'voice':
                # Voice recording - use first 50 chars of transcript as title
                title = html_lib.escape(msg['body'][:50] + '...' if len(msg['body']) > 50 else msg['body'])
                item_type_prefix = '🎤 '
            else:
                # IRC message
                if msg['subject']:
                    title = html_lib.escape(msg['subject'])
                else:
                    title = f"Message to alt.{domain}.{msg['channel']}"
                item_type_prefix = '💬 '

            # Escape body
            body = html_lib.escape(msg['body']) if msg['body'] else ''

            # Channel name for link
            channel_slug = msg['channel'].replace(' ', '-').lower()

            # Link path depends on source
            if source_type == 'voice':
                link_path = f"/voice/{msg['id']}"
            else:
                link_path = f"/messages/{msg['id']}"

            xml += f'''    <item>
      <title>{item_type_prefix}{title}</title>
      <link>{html_lib.escape(metadata["link"])}{link_path}/</link>
      <description>{body}</description>
      <pubDate>{pub_date}</pubDate>
      <guid>{html_lib.escape(metadata["link"])}{link_path}/</guid>
      <category>alt.{html_lib.escape(domain)}.{html_lib.escape(msg["channel"])}</category>
      <author>{html_lib.escape(msg["from_user"])}</author>
    </item>
'''

        xml += '''  </channel>
</rss>'''

        return Response(xml, mimetype='application/rss+xml')

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate RSS feed: {str(e)}'
        }), 500


@message_bp.route('/api/messages/<domain>/<post_id>/comments', methods=['GET'])
def get_comments(domain, post_id):
    """
    Get comments for a specific post (IRC threading)

    Comments are stored as IRC messages with parent_id = post_id

    Returns:
        {
            "comments": [
                {
                    "id": 123,
                    "from_user": "alice@soulfra.com",
                    "body": "Great post!",
                    "created_at": "2026-01-09T12:00:00",
                    "replies": [...]  // Nested replies
                }
            ],
            "total": 5
        }
    """
    try:
        db = get_db()

        # Get all comments for this post (parent_id = post_id)
        comments = db.execute('''
            SELECT
                id,
                from_user,
                body,
                created_at,
                parent_id
            FROM domain_messages
            WHERE to_domain = ?
            AND (parent_id = ? OR id IN (
                SELECT id FROM domain_messages WHERE parent_id = ?
            ))
            ORDER BY created_at ASC
        ''', (domain, post_id, post_id)).fetchall()

        # Build threaded comment structure
        comment_dict = {}
        root_comments = []

        for comment in comments:
            comment_data = {
                'id': comment['id'],
                'from_user': comment['from_user'],
                'body': comment['body'],
                'created_at': comment['created_at'],
                'replies': []
            }
            comment_dict[comment['id']] = comment_data

            if comment['parent_id'] == int(post_id):
                # Top-level comment
                root_comments.append(comment_data)
            elif comment['parent_id'] in comment_dict:
                # Reply to another comment
                comment_dict[comment['parent_id']]['replies'].append(comment_data)

        return jsonify({
            'comments': root_comments,
            'total': len(comments)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get comments: {str(e)}'
        }), 500


@message_bp.route('/api/messages/<domain>/<post_id>/comments', methods=['POST'])
def post_comment(domain, post_id):
    """
    Post a comment on a blog post/message

    POST Body:
        {
            "body": "This is a great post!",
            "from_user": "alice@soulfra.com",  // Optional
            "parent_comment_id": 456  // Optional - for replies to comments
        }

    Returns:
        {
            "success": true,
            "comment_id": 123
        }
    """
    try:
        data = request.json

        body = data.get('body')
        if not body:
            return jsonify({
                'success': False,
                'error': 'body is required'
            }), 400

        from_user = data.get('from_user', 'anonymous')
        parent_comment_id = data.get('parent_comment_id')  # For nested replies

        # Get device fingerprint for anonymous comments
        from device_hash import capture_device_info
        device_info = capture_device_info(request)
        device_hash = device_info['device_hash']

        # If replying to a comment, use that as parent_id
        # Otherwise, use the post_id
        if parent_comment_id:
            parent_id = parent_comment_id
        else:
            parent_id = int(post_id)

        # Insert comment as IRC message
        db = get_db()
        cursor = db.execute('''
            INSERT INTO domain_messages
            (from_user, from_device_hash, to_domain, channel, subject, body, created_at, message_type, parent_id)
            VALUES (?, ?, ?, 'comments', '', ?, ?, 'comment', ?)
        ''', (from_user, device_hash, domain, body, datetime.now().isoformat(), parent_id))

        comment_id = cursor.lastrowid
        db.commit()

        # Export updated messages to JSON
        export_messages_to_json(domain)

        return jsonify({
            'success': True,
            'comment_id': comment_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to post comment: {str(e)}'
        }), 500
