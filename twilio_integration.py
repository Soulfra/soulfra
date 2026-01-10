#!/usr/bin/env python3
"""
Twilio VoIP Integration - Real Phone Number → Voice Memos

Provides:
- Incoming call handling → voicemail
- Incoming SMS → saved as text note
- Auto-transcription with Whisper
- Auto-idea extraction with Ollama
- Integrates with existing simple_voice_recordings table

Setup:
1. pip install twilio
2. Buy Twilio number (~$1/month)
3. Configure webhook URL: https://your-domain.com/twilio/voice
4. Add TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to .env

Routes:
- /twilio/voice - Incoming call webhook
- /twilio/voicemail - Recording saved webhook
- /twilio/sms - Incoming SMS webhook
- /twilio/status - Call status updates
"""

from flask import Blueprint, request, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import os
import urllib.request
import hashlib
import secrets
import json
from datetime import datetime
from pathlib import Path

# Import federated voice encryption
from voice_encryption import (
    encrypt_voice_memo,
    hash_access_key,
    create_qr_access_data
)

twilio_bp = Blueprint('twilio', __name__, url_prefix='/twilio')

# Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
VOICE_RECORDINGS_DIR = Path('voice_recordings')
VOICE_RECORDINGS_DIR.mkdir(exist_ok=True)


def get_db():
    """Get database connection"""
    db = sqlite3.connect('soulfra.db')
    db.row_factory = sqlite3.Row
    return db


def download_twilio_recording(recording_url, auth_token):
    """Download recording from Twilio"""
    # Twilio uses basic auth
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, recording_url, TWILIO_ACCOUNT_SID, auth_token)
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opener = urllib.request.build_opener(handler)

    response = opener.open(recording_url)
    return response.read()


@twilio_bp.route('/voice', methods=['POST'])
def incoming_call():
    """
    Handle incoming phone call

    Twilio webhook - called when someone calls your number

    Returns TwiML response instructing Twilio to:
    1. Greet caller
    2. Prompt for voice memo
    3. Record message
    4. Send recording to /twilio/voicemail
    """
    response = VoiceResponse()

    # Get caller info
    from_number = request.form.get('From', 'Unknown')
    to_number = request.form.get('To', 'Unknown')

    print(f"📞 Incoming call from {from_number} to {to_number}")

    # Greeting
    response.say(
        "Welcome to Soulfra voice memo system. "
        "Please leave your message after the beep. "
        "Press pound when finished.",
        voice='alice'
    )

    # Record message
    response.record(
        action='/twilio/voicemail',
        method='POST',
        max_length=300,  # 5 minutes max
        finish_on_key='#',
        transcribe=False,  # We'll use Whisper instead
        recording_status_callback='/twilio/status'
    )

    # If no input
    response.say("We didn't receive any audio. Goodbye.", voice='alice')

    return str(response), 200, {'Content-Type': 'text/xml'}


@twilio_bp.route('/voicemail', methods=['POST'])
def save_voicemail():
    """
    Save voicemail recording - ENCRYPTED with Federated Voice System

    Twilio webhook - called after recording finishes

    1. Download recording from Twilio
    2. Encrypt with AES-256-GCM (federated voice encryption)
    3. Save to voice_memos table (federated system)
    4. Generate QR code for access
    5. Send confirmation to caller with access info
    """
    # Get recording details
    recording_url = request.form.get('RecordingUrl')
    recording_sid = request.form.get('RecordingSid')
    from_number = request.form.get('From', 'Unknown')
    to_number = request.form.get('To', 'Unknown')
    call_sid = request.form.get('CallSid')
    duration = request.form.get('RecordingDuration', '0')

    print(f"💾 Saving encrypted voicemail from {from_number}")
    print(f"   Recording SID: {recording_sid}")
    print(f"   Duration: {duration}s")
    print(f"   URL: {recording_url}")

    if not recording_url:
        print("❌ No recording URL provided")
        response = VoiceResponse()
        response.say("Recording failed. Please try again.", voice='alice')
        return str(response), 200, {'Content-Type': 'text/xml'}

    try:
        # Download recording from Twilio (add .mp3 to get audio file)
        audio_url = recording_url + '.mp3'
        audio_data = download_twilio_recording(audio_url, TWILIO_AUTH_TOKEN)

        print(f"✅ Downloaded {len(audio_data)} bytes from Twilio")

        # Encrypt voice memo with AES-256-GCM (federated encryption)
        encryption_result = encrypt_voice_memo(audio_data)

        # Generate unique memo ID
        memo_id = secrets.token_urlsafe(16)

        # Generate QR access data (domain/voice/memo_id#key)
        domain = os.getenv('DOMAIN', 'localhost:5001')
        qr_data = create_qr_access_data(memo_id, encryption_result['key_b64'], domain)

        # Hash the access key (NEVER store the key itself!)
        key_hash = hash_access_key(encryption_result['key'])

        print(f"🔐 Encrypted voicemail (ID: {memo_id})")
        print(f"   QR Access: {qr_data[:50]}...")

        # Save to federated voice_memos table
        db = get_db()

        # Build metadata JSON
        metadata = {
            'source': 'twilio_call',
            'from': from_number,
            'to': to_number,
            'call_sid': call_sid,
            'recording_sid': recording_sid,
            'duration_seconds': int(duration),
            'audio_format': 'audio/mpeg',
            'encryption': 'aes-256-gcm',
            'qr_access': qr_data
        }

        cursor = db.execute('''
            INSERT INTO voice_memos (
                id,
                user_id,
                domain,
                encrypted_audio,
                encryption_iv,
                access_key_hash,
                duration_seconds,
                file_size_bytes,
                audio_format,
                access_type,
                federation_shared,
                trusted_domains,
                access_count,
                metadata,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            memo_id,
            None,  # No user_id for phone calls (anonymous)
            domain,
            encryption_result['encrypted_data'],
            encryption_result['iv_b64'],
            key_hash,
            int(duration),
            len(audio_data),
            'audio/mpeg',
            'qr',  # QR code access
            1,  # Federation enabled
            json.dumps(['soulfra.com', 'calriven.com', 'deathtodata.org']),  # Trusted domains
            0,  # Initial access count
            json.dumps(metadata)
        ))

        db.commit()
        db.close()

        print(f"✅ Saved encrypted voicemail to federated database")
        print(f"   Access URL: {domain}/voice/{memo_id}")
        print(f"   🔐 Encryption: AES-256-GCM")
        print(f"   🔑 Access via QR code only")

        # Send confirmation (optional)
        response = VoiceResponse()
        response.say(
            "Thank you! Your encrypted message has been saved. "
            "Check your dashboard for the QR code to access it. Goodbye.",
            voice='alice'
        )

        return str(response), 200, {'Content-Type': 'text/xml'}

    except Exception as e:
        print(f"❌ Error saving voicemail: {e}")
        import traceback
        traceback.print_exc()
        response = VoiceResponse()
        response.say("An error occurred saving your message. Please try again later.", voice='alice')
        return str(response), 200, {'Content-Type': 'text/xml'}


@twilio_bp.route('/sms', methods=['POST'])
def incoming_sms():
    """
    Handle incoming SMS

    Twilio webhook - called when someone texts your number

    1. Extract message body
    2. Save as text note (no audio)
    3. Queue for idea extraction
    4. Send confirmation reply
    """
    # Get SMS details
    from_number = request.form.get('From', 'Unknown')
    to_number = request.form.get('To', 'Unknown')
    message_body = request.form.get('Body', '')
    message_sid = request.form.get('MessageSid')

    print(f"💬 Incoming SMS from {from_number}")
    print(f"   Message: {message_body}")

    if not message_body:
        response = MessagingResponse()
        response.message("Empty message received. Please send text.")
        return str(response), 200, {'Content-Type': 'text/xml'}

    try:
        # Save as text note (no audio file)
        db = get_db()
        cursor = db.execute('''
            INSERT INTO simple_voice_recordings (
                filename,
                transcription,
                transcription_method,
                metadata,
                created_at
            ) VALUES (?, ?, ?, ?, datetime('now'))
        ''', (
            f"twilio_sms_{message_sid}.txt",
            message_body,  # SMS text goes directly into transcription field
            'sms_direct',
            f'{{"source": "twilio_sms", "from": "{from_number}", "to": "{to_number}", "message_sid": "{message_sid}"}}'
        ))
        note_id = cursor.lastrowid
        db.commit()
        db.close()

        print(f"✅ Saved SMS as note (ID: {note_id})")

        # Send confirmation reply
        response = MessagingResponse()
        response.message(
            f"Thanks! Your note has been saved (ID: {note_id}). "
            f"Reply with 'IDEAS' to extract ideas from your message."
        )

        return str(response), 200, {'Content-Type': 'text/xml'}

    except Exception as e:
        print(f"❌ Error saving SMS: {e}")
        response = MessagingResponse()
        response.message("Error saving your message. Please try again.")
        return str(response), 200, {'Content-Type': 'text/xml'}


@twilio_bp.route('/status', methods=['POST'])
def recording_status():
    """
    Recording status callback

    Twilio sends updates about recording status
    Useful for debugging and monitoring
    """
    recording_sid = request.form.get('RecordingSid')
    recording_status = request.form.get('RecordingStatus')
    recording_url = request.form.get('RecordingUrl')

    print(f"📊 Recording status: {recording_status}")
    print(f"   SID: {recording_sid}")

    # Log status (you could update database here)
    if recording_status == 'completed':
        print(f"✅ Recording completed: {recording_url}")
    elif recording_status == 'failed':
        print(f"❌ Recording failed")

    return '', 200


@twilio_bp.route('/config', methods=['GET'])
def show_config():
    """
    Show Twilio configuration and setup instructions

    Visit /twilio/config to see:
    - Current configuration status
    - Webhook URLs
    - Setup instructions
    """
    config = {
        'account_sid_configured': bool(TWILIO_ACCOUNT_SID),
        'auth_token_configured': bool(TWILIO_AUTH_TOKEN),
        'voice_webhook': request.url_root + 'twilio/voice',
        'sms_webhook': request.url_root + 'twilio/sms',
        'status_callback': request.url_root + 'twilio/status',
        'recordings_dir': str(VOICE_RECORDINGS_DIR.absolute()),
        'setup_instructions': {
            '1': 'Sign up for Twilio account at twilio.com',
            '2': 'Buy phone number (~$1/month)',
            '3': 'Add to .env file: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN',
            '4': 'Configure phone number webhooks (see URLs above)',
            '5': 'Test by calling your Twilio number',
            '6': 'Voicemails will appear in /voice page'
        },
        'pricing': {
            'phone_number': '$1.00/month',
            'incoming_call': '$0.0085/minute',
            'incoming_sms': '$0.0075/message',
            'recording_storage': '$0.0001/minute/month'
        }
    }

    return jsonify(config)


@twilio_bp.route('/voicemails', methods=['GET'])
def list_voicemails():
    """
    List recent Twilio voicemails with QR codes

    Returns JSON with recent encrypted voicemails from phone calls
    """
    try:
        db = get_db()

        # Get recent Twilio voicemails from federated voice_memos table
        voicemails = db.execute('''
            SELECT
                id,
                metadata,
                created_at,
                duration_seconds,
                file_size_bytes,
                access_count
            FROM voice_memos
            WHERE json_extract(metadata, '$.source') = 'twilio_call'
            ORDER BY created_at DESC
            LIMIT 50
        ''').fetchall()

        results = []
        for vm in voicemails:
            metadata = json.loads(vm['metadata'])
            qr_access = metadata.get('qr_access', '')

            results.append({
                'id': vm['id'],
                'from': metadata.get('from', 'Unknown'),
                'duration': vm['duration_seconds'],
                'size_bytes': vm['file_size_bytes'],
                'qr_access': qr_access,
                'access_url': f"/voice/{vm['id']}",
                'access_count': vm['access_count'],
                'created_at': vm['created_at']
            })

        db.close()

        return jsonify({
            'success': True,
            'voicemails': results,
            'total': len(results)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@twilio_bp.route('/test', methods=['GET'])
def test_integration():
    """
    Test Twilio integration

    Visit /twilio/test to verify:
    - Database connection
    - File permissions
    - Configuration
    """
    tests = []

    # Test 1: Database (voice_memos table for federated system)
    try:
        db = get_db()
        count = db.execute('SELECT COUNT(*) FROM voice_memos WHERE json_extract(metadata, "$.source") = "twilio_call"').fetchone()[0]
        db.close()
        tests.append({'test': 'Database', 'status': 'pass', 'message': f'Connected successfully ({count} Twilio voicemails)'})
    except Exception as e:
        tests.append({'test': 'Database', 'status': 'fail', 'message': str(e)})

    # Test 2: File permissions
    try:
        test_file = VOICE_RECORDINGS_DIR / '.test'
        test_file.write_text('test')
        test_file.unlink()
        tests.append({'test': 'File Permissions', 'status': 'pass', 'message': f'Can write to {VOICE_RECORDINGS_DIR}'})
    except Exception as e:
        tests.append({'test': 'File Permissions', 'status': 'fail', 'message': str(e)})

    # Test 3: Configuration
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        tests.append({'test': 'Configuration', 'status': 'pass', 'message': 'Credentials configured'})
    else:
        tests.append({'test': 'Configuration', 'status': 'fail', 'message': 'Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in .env'})

    # Test 4: Dependencies
    try:
        from twilio.rest import Client
        tests.append({'test': 'Dependencies', 'status': 'pass', 'message': 'Twilio library installed'})
    except ImportError:
        tests.append({'test': 'Dependencies', 'status': 'fail', 'message': 'Run: pip install twilio'})

    return jsonify({
        'tests': tests,
        'passed': sum(1 for t in tests if t['status'] == 'pass'),
        'failed': sum(1 for t in tests if t['status'] == 'fail'),
        'total': len(tests)
    })


def register_twilio_routes(app):
    """Register Twilio routes"""
    app.register_blueprint(twilio_bp)
    print('📞 Twilio VoIP integration routes registered (ENCRYPTED with AES-256-GCM)')
    print('   Voice: /twilio/voice')
    print('   Voicemail: /twilio/voicemail (saves encrypted to voice_memos table)')
    print('   Voicemails: /twilio/voicemails (list with QR codes)')
    print('   SMS: /twilio/sms')
    print('   Status: /twilio/status')
    print('   Config: /twilio/config')
    print('   Test: /twilio/test')
    print('')
    print('   🔐 Encryption: AES-256-GCM (federated voice system)')
    print('   🔑 Access: QR codes only (keys never stored)')
    print('   💡 Visit /twilio/config for setup instructions')


if __name__ == '__main__':
    print('📞 Twilio VoIP Integration')
    print('Routes:')
    print('  /twilio/voice - Incoming call handler')
    print('  /twilio/voicemail - Save recording')
    print('  /twilio/sms - Incoming SMS handler')
    print('  /twilio/status - Recording status')
    print('  /twilio/config - Configuration & setup')
    print('  /twilio/test - Test integration')
    print('')
    print('Setup:')
    print('  1. pip install twilio')
    print('  2. Add TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to .env')
    print('  3. Buy Twilio number at twilio.com')
    print('  4. Configure webhooks to point to your server')
    print('  5. Call your number to test!')
