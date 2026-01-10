#!/usr/bin/env python3
"""
Unified Multi-Modal Input Pipeline

Accepts voice, screenshot, drawing, and text inputs.
Routes to appropriate extractors (Whisper, OCR, etc.)
Stores in training_contributions table with cryptographic proof.

Endpoints:
- POST /api/unified-input - Universal input handler
- GET /api/training-data - List all training contributions
- POST /api/training-data/export - Export for fine-tuning
"""

from flask import Blueprint, request, jsonify
from database import get_db
import hashlib
import json
from datetime import datetime
import base64
import io
import tempfile
import os

unified_bp = Blueprint('unified', __name__)


def generate_content_hash(content: str) -> str:
    """Generate SHA-256 hash of content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def generate_qr_code(content_hash: str) -> str:
    """
    Generate QR verification code
    Format: https://cringeproof.com/verify/{hash}
    """
    return f"https://cringeproof.com/verify/{content_hash[:16]}"


def generate_upc_barcode(content_hash: str) -> str:
    """
    Convert hash to UPC-compatible barcode
    UPC uses 12 digits, so we extract numeric portion of hash
    """
    # Convert hex hash to decimal, take first 11 digits
    numeric = int(content_hash[:16], 16) % (10**11)

    # Calculate UPC check digit
    upc = str(numeric).zfill(11)
    odd_sum = sum(int(upc[i]) for i in range(0, 11, 2))
    even_sum = sum(int(upc[i]) for i in range(1, 11, 2))
    check_digit = (10 - ((odd_sum * 3 + even_sum) % 10)) % 10

    return upc + str(check_digit)


def generate_bip39_hash(content_hash: str) -> str:
    """
    Convert hash to BIP-39 Bitcoin mnemonic format
    (Simplified - would use actual BIP-39 wordlist in production)
    """
    # For now, just return the hash in a readable format
    # TODO: Implement actual BIP-39 encoding with wordlist
    return f"BIP39:{content_hash[:32]}"


def generate_ethereum_checksum(content_hash: str) -> str:
    """
    Convert hash to Ethereum checksum address format
    """
    return f"0x{content_hash[:40]}"


@unified_bp.route('/api/unified-input', methods=['POST'])
def unified_input():
    """
    Universal multi-modal input handler

    POST /api/unified-input
    Body: {
        "modality": "voice|screenshot|drawing|text",
        "data": "<base64 encoded data or text>",
        "user_id": 1,
        "metadata": {
            "filename": "optional",
            "source": "optional"
        }
    }

    Returns:
        {
            "success": true,
            "contribution_id": 123,
            "content_hash": "abc123...",
            "qr_code": "https://cringeproof.com/verify/abc123",
            "upc": "012345678905",
            "proofs": {
                "sha256": "abc123...",
                "bip39": "abandon ability...",
                "ethereum": "0xabc123..."
            }
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        modality = data.get('modality')
        input_data = data.get('data')
        user_id = data.get('user_id')
        metadata = data.get('metadata', {})

        if not modality or not input_data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: modality, data'
            }), 400

        if modality not in ['voice', 'screenshot', 'drawing', 'text']:
            return jsonify({
                'success': False,
                'error': f'Invalid modality: {modality}. Must be voice|screenshot|drawing|text'
            }), 400

        # Extract text based on modality
        extracted_text = None
        processing_method = None
        file_size = 0

        if modality == 'text':
            # Direct text input
            extracted_text = input_data
            processing_method = 'direct'
            file_size = len(input_data.encode('utf-8'))

        elif modality == 'voice':
            # Voice memo - use Whisper transcription
            extracted_text = extract_voice(input_data, metadata)
            processing_method = 'whisper'
            file_size = len(base64.b64decode(input_data)) if input_data else 0

        elif modality == 'screenshot':
            # Screenshot - use OCR
            extracted_text = extract_screenshot(input_data, metadata)
            processing_method = 'easyocr'
            file_size = len(base64.b64decode(input_data)) if input_data else 0

        elif modality == 'drawing':
            # Drawing - use shape recognition or OCR
            extracted_text = extract_drawing(input_data, metadata)
            processing_method = 'shape_recognition'
            file_size = len(base64.b64decode(input_data)) if input_data else 0

        if not extracted_text:
            return jsonify({
                'success': False,
                'error': f'Failed to extract text from {modality} input'
            }), 500

        # Generate cryptographic proofs
        content_hash = generate_content_hash(extracted_text)
        qr_code = generate_qr_code(content_hash)
        upc = generate_upc_barcode(content_hash)
        bip39 = generate_bip39_hash(content_hash)
        ethereum = generate_ethereum_checksum(content_hash)

        # Store in training_contributions table
        db = get_db()
        cursor = db.execute('''
            INSERT INTO training_contributions (
                user_id, modality, extracted_text, content_hash,
                qr_verification_code, upc_barcode, bip39_hash, ethereum_checksum,
                file_size, processing_method,
                user_can_export, user_can_delete, included_in_training
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 1)
        ''', (
            user_id, modality, extracted_text, content_hash,
            qr_code, upc, bip39, ethereum,
            file_size, processing_method
        ))

        contribution_id = cursor.lastrowid
        db.commit()

        return jsonify({
            'success': True,
            'contribution_id': contribution_id,
            'modality': modality,
            'content_hash': content_hash,
            'qr_code': qr_code,
            'upc': upc,
            'proofs': {
                'sha256': content_hash,
                'bip39': bip39,
                'ethereum': ethereum
            },
            'extracted_text_preview': extracted_text[:100] + '...' if len(extracted_text) > 100 else extracted_text,
            'message': f'Successfully processed {modality} input and added to training data'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def extract_voice(base64_audio: str, metadata: dict) -> str:
    """
    Extract text from voice input using Whisper
    """
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(base64_audio)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Run Whisper transcription
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(tmp_path)

        # Clean up temp file
        os.unlink(tmp_path)

        return result['text']

    except Exception as e:
        print(f"Voice extraction error: {e}")
        return f"[Voice transcription failed: {str(e)}]"


def extract_screenshot(base64_image: str, metadata: dict) -> str:
    """
    Extract text from screenshot using OCR
    """
    try:
        from ocr_extractor import OCRExtractor

        # Decode base64 image
        image_bytes = base64.b64decode(base64_image)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        # Run OCR
        ocr = OCRExtractor()
        text = ocr.extract_text(tmp_path)

        # Clean up
        os.unlink(tmp_path)

        return text

    except Exception as e:
        print(f"Screenshot OCR error: {e}")
        return f"[OCR extraction failed: {str(e)}]"


def extract_drawing(base64_image: str, metadata: dict) -> str:
    """
    Extract text from drawing using shape recognition or OCR
    """
    try:
        from ocr_extractor import OCRExtractor

        # For now, use OCR (can add shape recognition later)
        image_bytes = base64.b64decode(base64_image)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        ocr = OCRExtractor()
        text = ocr.extract_text(tmp_path)

        os.unlink(tmp_path)

        return text

    except Exception as e:
        print(f"Drawing extraction error: {e}")
        return f"[Drawing extraction failed: {str(e)}]"


@unified_bp.route('/api/training-data', methods=['GET'])
def get_training_data():
    """
    List all training contributions

    GET /api/training-data?user_id=1&modality=voice&limit=50

    Returns list of contributions with metadata
    """
    try:
        db = get_db()

        # Parse query parameters
        user_id = request.args.get('user_id', type=int)
        modality = request.args.get('modality')
        limit = request.args.get('limit', 50, type=int)
        include_text = request.args.get('include_text', 'false').lower() == 'true'

        # Build query
        query = 'SELECT * FROM training_contributions WHERE 1=1'
        params = []

        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)

        if modality:
            query += ' AND modality = ?'
            params.append(modality)

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        cursor = db.execute(query, params)
        contributions = [dict(row) for row in cursor.fetchall()]

        # Remove full text if not requested (for privacy/performance)
        if not include_text:
            for c in contributions:
                if c.get('extracted_text'):
                    text = c['extracted_text']
                    c['extracted_text_preview'] = text[:100] + '...' if len(text) > 100 else text
                    del c['extracted_text']

        # Count by modality
        cursor = db.execute('''
            SELECT modality, COUNT(*) as count
            FROM training_contributions
            GROUP BY modality
        ''')
        modality_counts = {row['modality']: row['count'] for row in cursor.fetchall()}

        return jsonify({
            'success': True,
            'contributions': contributions,
            'total': len(contributions),
            'statistics': {
                'by_modality': modality_counts,
                'total_contributions': sum(modality_counts.values())
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@unified_bp.route('/api/training-data/export', methods=['POST'])
def export_training_data():
    """
    Export training data for fine-tuning

    POST /api/training-data/export
    Body: {
        "format": "jsonl|csv|txt",
        "user_id": 1,  // optional: filter by user
        "modalities": ["voice", "text"],  // optional: filter by modality
        "min_quality": 0.7  // optional: minimum quality score
    }

    Returns downloadable file in requested format
    """
    try:
        data = request.get_json() or {}

        format_type = data.get('format', 'jsonl')
        user_id = data.get('user_id')
        modalities = data.get('modalities', [])
        min_quality = data.get('min_quality', 0.0)

        db = get_db()

        # Build query
        query = '''
            SELECT modality, extracted_text, content_hash, created_at, quality_score
            FROM training_contributions
            WHERE included_in_training = 1
        '''
        params = []

        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)

        if modalities:
            placeholders = ','.join(['?' for _ in modalities])
            query += f' AND modality IN ({placeholders})'
            params.extend(modalities)

        if min_quality > 0:
            query += ' AND (quality_score IS NULL OR quality_score >= ?)'
            params.append(min_quality)

        query += ' ORDER BY created_at ASC'

        cursor = db.execute(query, params)
        rows = cursor.fetchall()

        # Format output
        if format_type == 'jsonl':
            # JSONL format for fine-tuning
            output = '\n'.join([
                json.dumps({
                    'text': row['extracted_text'],
                    'modality': row['modality'],
                    'hash': row['content_hash']
                }) for row in rows
            ])

        elif format_type == 'csv':
            # CSV format
            import csv
            from io import StringIO

            output_io = StringIO()
            writer = csv.writer(output_io)
            writer.writerow(['modality', 'text', 'hash', 'created_at'])

            for row in rows:
                writer.writerow([
                    row['modality'],
                    row['extracted_text'],
                    row['content_hash'],
                    row['created_at']
                ])

            output = output_io.getvalue()

        elif format_type == 'txt':
            # Plain text format
            output = '\n\n---\n\n'.join([row['extracted_text'] for row in rows])

        else:
            return jsonify({
                'success': False,
                'error': f'Invalid format: {format_type}. Must be jsonl|csv|txt'
            }), 400

        return jsonify({
            'success': True,
            'format': format_type,
            'total_records': len(rows),
            'data': output,
            'message': f'Exported {len(rows)} training records as {format_type}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@unified_bp.route('/verify/<hash_code>')
def verify_contribution(hash_code):
    """
    Public verification page for training contributions

    GET /verify/7c412f19ab04731f

    Shows:
    - QR card visual (trading card style)
    - Contribution details (modality, timestamp, proof)
    - Verification status
    """
    from flask import render_template

    try:
        db = get_db()

        # Look up contribution by hash (first 16 chars of content_hash or qr_verification_code)
        cursor = db.execute('''
            SELECT * FROM training_contributions
            WHERE content_hash LIKE ? OR qr_verification_code LIKE ?
            LIMIT 1
        ''', (f'{hash_code}%', f'%{hash_code}%'))

        contribution = cursor.fetchone()

        if not contribution:
            return jsonify({
                'success': False,
                'error': 'Contribution not found',
                'hash': hash_code
            }), 404

        # Convert to dict
        contrib_data = dict(contribution)

        # Get user info (if not anonymous)
        user_data = None
        if contrib_data.get('user_id'):
            user_cursor = db.execute('SELECT username, email FROM users WHERE id = ?', (contrib_data['user_id'],))
            user_row = user_cursor.fetchone()
            if user_row:
                user_data = dict(user_row)

        # Return JSON for now (will add HTML template later)
        return jsonify({
            'success': True,
            'contribution': {
                'id': contrib_data['id'],
                'modality': contrib_data['modality'],
                'timestamp': contrib_data['created_at'],
                'content_hash': contrib_data['content_hash'],
                'qr_code': contrib_data.get('qr_verification_code'),
                'upc': contrib_data.get('upc_barcode'),
                'district': contrib_data.get('district', 'General'),
                'zone': contrib_data.get('zone', 'Global'),
                'cringe_score': contrib_data.get('cringe_score', 0.5),
                'reward_tier': contrib_data.get('reward_tier', 'free'),
                'verified': True,
                'user': user_data.get('username') if user_data else 'Anonymous'
            },
            'proofs': {
                'sha256': contrib_data['content_hash'],
                'bip39': contrib_data.get('bip39_hash'),
                'ethereum': contrib_data.get('ethereum_checksum')
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_unified_routes(app):
    """Register unified multi-modal input routes"""
    app.register_blueprint(unified_bp)
    print("🎯 Unified multi-modal input routes registered:")
    print("   Input: POST /api/unified-input")
    print("   List: GET /api/training-data")
    print("   Export: POST /api/training-data/export")
    print("   Verify: GET /verify/<hash>")
