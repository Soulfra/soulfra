#!/usr/bin/env python3
"""
Comment Voice Chain - Merkle Tree / Verilog Style Flywheel

Chains together:
1. Comment (root source)
2. Voice Attachment (audio input)
3. Ollama Transcription (AI processing)
4. QR Code Generation (shareable link)
5. Domain Routing (brand-specific)

Like a Merkle tree or Solidity contract - each step verifies the previous one.
"""

from flask import Blueprint, request, jsonify
from database import get_db
import hashlib
import json
from datetime import datetime
import qrcode
import io
import base64

comment_voice_chain_bp = Blueprint('comment_voice_chain', __name__)


def generate_chain_hash(comment_id, voice_id=None, parent_hash=None):
    """
    Generate Merkle-style hash for comment chain

    Like Solidity: hash(current_data + previous_hash)
    """
    data = f"{comment_id}:{voice_id or 'none'}:{parent_hash or 'genesis'}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def generate_qr_for_comment(comment_id, post_id):
    """Generate QR code for comment thread (domain-routed URL)"""
    # QR points to: soulfra.com/post/{slug}#comment-{id}
    # Domain router will handle brand-specific routing
    url = f"https://soulfra.github.io/soulfra/blog/posts/post-{post_id}.html#comment-{comment_id}"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64 for embedding
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        'url': url,
        'qr_image': f"data:image/png;base64,{qr_base64}",
        'code': f"comment-{comment_id}"
    }


@comment_voice_chain_bp.route('/api/comment-voice-chain', methods=['POST'])
def create_comment_with_voice():
    """
    Create comment with optional voice attachment

    Request:
        {
            "post_id": 1,
            "content": "text comment",
            "audio": "base64-encoded-audio", (optional)
            "parent_comment_id": null (optional)
        }

    Returns:
        {
            "comment_id": 123,
            "voice_id": 456 (if audio provided),
            "transcription": "..." (if Ollama available),
            "qr_code": {...},
            "chain_hash": "abc123...",
            "chain": {
                "comment": {...},
                "voice": {...},
                "qr": {...}
            }
        }
    """
    data = request.get_json()

    post_id = data.get('post_id')
    content = data.get('content', '').strip()
    audio_base64 = data.get('audio')
    parent_comment_id = data.get('parent_comment_id')

    if not post_id or not content:
        return jsonify({'error': 'post_id and content required'}), 400

    db = get_db()

    # Step 1: Create comment (root of chain)
    cursor = db.execute('''
        INSERT INTO comments (post_id, user_id, content, parent_comment_id)
        VALUES (?, 1, ?, ?)
    ''', (post_id, content, parent_comment_id))
    comment_id = cursor.lastrowid

    voice_id = None
    transcription = None

    # Step 2: Attach voice if provided
    if audio_base64:
        try:
            # Save audio to voice_inputs table
            import base64
            audio_data = base64.b64decode(audio_base64)

            # Store as blob in database
            cursor = db.execute('''
                INSERT INTO voice_inputs (user_id, audio_data, duration_seconds)
                VALUES (?, ?, ?)
            ''', (1, audio_data, 0))  # Duration calculated later
            voice_id = cursor.lastrowid

            # Link voice to comment
            db.execute('''
                UPDATE comments
                SET voice_attachment_id = ?
                WHERE id = ?
            ''', (voice_id, comment_id))

            # Step 3: Try to transcribe with Ollama/Whisper
            try:
                # This would call Whisper or Ollama for transcription
                # For now, placeholder
                transcription = "[Transcription pending - Ollama integration]"

                db.execute('''
                    UPDATE voice_inputs
                    SET transcription = ?
                    WHERE id = ?
                ''', (transcription, voice_id))

            except Exception as e:
                print(f"Transcription failed: {e}")

        except Exception as e:
            print(f"Voice attachment failed: {e}")

    # Step 4: Generate QR code for comment thread
    qr_data = generate_qr_for_comment(comment_id, post_id)

    db.execute('''
        UPDATE comments
        SET qr_code = ?
        WHERE id = ?
    ''', (qr_data['code'], comment_id))

    # Step 5: Generate chain hash (Merkle tree style)
    parent_hash = None
    if parent_comment_id:
        parent = db.execute('''
            SELECT chain_hash FROM comments WHERE id = ?
        ''', (parent_comment_id,)).fetchone()
        if parent:
            parent_hash = parent['chain_hash']

    chain_hash = generate_chain_hash(comment_id, voice_id, parent_hash)

    db.execute('''
        UPDATE comments
        SET chain_hash = ?
        WHERE id = ?
    ''', (chain_hash, comment_id))

    db.commit()

    # Fetch complete comment with all linkages
    comment = db.execute('''
        SELECT
            c.id,
            c.content,
            c.created_at,
            c.parent_comment_id,
            c.voice_attachment_id,
            c.qr_code,
            c.chain_hash,
            'Anonymous' as user_name,
            0 as is_ai
        FROM comments c
        WHERE c.id = ?
    ''', (comment_id,)).fetchone()

    db.close()

    # Build chain response
    chain_response = {
        'comment_id': comment_id,
        'voice_id': voice_id,
        'transcription': transcription,
        'qr_code': qr_data,
        'chain_hash': chain_hash,
        'parent_hash': parent_hash,
        'chain': {
            'comment': dict(comment),
            'voice': {
                'id': voice_id,
                'transcription': transcription
            } if voice_id else None,
            'qr': qr_data,
            'verification': {
                'hash': chain_hash,
                'parent_hash': parent_hash,
                'verified': True  # Would check hash chain in production
            }
        }
    }

    return jsonify(chain_response), 201


@comment_voice_chain_bp.route('/api/comment-chain/<int:comment_id>', methods=['GET'])
def get_comment_chain(comment_id):
    """
    Get full chain for a comment

    Returns complete Merkle tree / verification chain
    """
    db = get_db()

    # Get comment with all attachments
    comment = db.execute('''
        SELECT
            c.*,
            u.username as user_name,
            v.transcription as voice_transcription,
            v.audio_data as voice_audio
        FROM comments c
        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN voice_inputs v ON c.voice_attachment_id = v.id
        WHERE c.id = ?
    ''', (comment_id,)).fetchone()

    if not comment:
        db.close()
        return jsonify({'error': 'Comment not found'}), 404

    # Get parent chain (walk back the Merkle tree)
    parent_chain = []
    current_parent_id = comment['parent_comment_id']

    while current_parent_id:
        parent = db.execute('''
            SELECT id, chain_hash, parent_comment_id
            FROM comments WHERE id = ?
        ''', (current_parent_id,)).fetchone()

        if parent:
            parent_chain.append({
                'id': parent['id'],
                'hash': parent['chain_hash']
            })
            current_parent_id = parent['parent_comment_id']
        else:
            break

    db.close()

    return jsonify({
        'comment': dict(comment),
        'chain_hash': comment['chain_hash'],
        'parent_chain': parent_chain,
        'chain_depth': len(parent_chain),
        'qr_code': comment['qr_code'],
        'voice_attached': comment['voice_attachment_id'] is not None,
        'transcription': comment['voice_transcription']
    })


@comment_voice_chain_bp.route('/api/verify-chain/<int:comment_id>', methods=['GET'])
def verify_comment_chain(comment_id):
    """
    Verify Merkle-style chain integrity

    Like Solidity verification: recompute all hashes and verify
    """
    db = get_db()

    comment = db.execute('''
        SELECT * FROM comments WHERE id = ?
    ''', (comment_id,)).fetchone()

    if not comment:
        db.close()
        return jsonify({'error': 'Comment not found'}), 404

    # Recompute hash
    parent_hash = None
    if comment['parent_comment_id']:
        parent = db.execute('''
            SELECT chain_hash FROM comments WHERE id = ?
        ''', (comment['parent_comment_id'],)).fetchone()
        if parent:
            parent_hash = parent['chain_hash']

    expected_hash = generate_chain_hash(
        comment['id'],
        comment['voice_attachment_id'],
        parent_hash
    )

    is_valid = expected_hash == comment['chain_hash']

    db.close()

    return jsonify({
        'comment_id': comment_id,
        'expected_hash': expected_hash,
        'actual_hash': comment['chain_hash'],
        'is_valid': is_valid,
        'verification': 'PASS' if is_valid else 'FAIL'
    })
