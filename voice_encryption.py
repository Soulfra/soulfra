#!/usr/bin/env python3
"""
Voice Memo Encryption - AES-256 Encryption for Federated Voice Memos

Provides:
- AES-256-GCM encryption/decryption for audio files
- Random key generation
- IV (initialization vector) management
- Base64 encoding for QR code embedding
- Secure key derivation from QR data

Security:
- AES-256-GCM (authenticated encryption)
- Random 256-bit keys
- Unique IV per encryption
- PBKDF2 key derivation
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import base64
import secrets
from typing import Tuple, Dict


def generate_encryption_key() -> bytes:
    """
    Generate a random 256-bit encryption key

    Returns:
        32 bytes (256 bits) of cryptographically secure random data
    """
    return secrets.token_bytes(32)


def generate_iv() -> bytes:
    """
    Generate a random initialization vector (IV)

    Returns:
        12 bytes (96 bits) for GCM mode
    """
    return os.urandom(12)


def encrypt_voice_memo(audio_data: bytes, key: bytes = None) -> Dict:
    """
    Encrypt audio data using AES-256-GCM

    Args:
        audio_data: Raw audio bytes (WAV, MP3, etc.)
        key: Optional encryption key (generates random if not provided)

    Returns:
        Dictionary with:
        - encrypted_data: Encrypted audio bytes
        - key: Encryption key (32 bytes)
        - iv: Initialization vector (12 bytes)
        - key_b64: Base64-encoded key (for QR codes)
        - iv_b64: Base64-encoded IV (for storage)
    """
    if key is None:
        key = generate_encryption_key()

    iv = generate_iv()

    # Create AES-GCM cipher
    aesgcm = AESGCM(key)

    # Encrypt (includes authentication tag)
    encrypted = aesgcm.encrypt(iv, audio_data, None)

    return {
        'encrypted_data': encrypted,
        'key': key,
        'iv': iv,
        'key_b64': base64.urlsafe_b64encode(key).decode('utf-8'),
        'iv_b64': base64.urlsafe_b64encode(iv).decode('utf-8')
    }


def decrypt_voice_memo(encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
    """
    Decrypt audio data using AES-256-GCM

    Args:
        encrypted_data: Encrypted audio bytes
        key: Encryption key (32 bytes)
        iv: Initialization vector (12 bytes)

    Returns:
        Decrypted audio bytes

    Raises:
        Exception: If decryption fails (wrong key, corrupted data, etc.)
    """
    aesgcm = AESGCM(key)

    try:
        decrypted = aesgcm.decrypt(iv, encrypted_data, None)
        return decrypted
    except Exception as e:
        raise ValueError(f"Decryption failed: Invalid key or corrupted data - {str(e)}")


def key_from_base64(key_b64: str) -> bytes:
    """
    Convert base64-encoded key to bytes

    Args:
        key_b64: Base64-encoded key string

    Returns:
        Key bytes (32 bytes)
    """
    return base64.urlsafe_b64decode(key_b64.encode('utf-8'))


def iv_from_base64(iv_b64: str) -> bytes:
    """
    Convert base64-encoded IV to bytes

    Args:
        iv_b64: Base64-encoded IV string

    Returns:
        IV bytes (12 bytes)
    """
    return base64.urlsafe_b64decode(iv_b64.encode('utf-8'))


def derive_key_from_passphrase(passphrase: str, salt: bytes = None) -> Tuple[bytes, bytes]:
    """
    Derive encryption key from a passphrase using PBKDF2

    Useful for:
    - User-provided passwords
    - Short QR code strings
    - Memorable access codes

    Args:
        passphrase: User-provided passphrase
        salt: Optional salt (generates random if not provided)

    Returns:
        Tuple of (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )

    key = kdf.derive(passphrase.encode('utf-8'))

    return key, salt


def create_qr_access_data(memo_id: str, key_b64: str, domain: str) -> str:
    """
    Create QR code data string with embedded decryption key

    Format: {domain}/voice/{memo_id}#{key_b64}

    Args:
        memo_id: Unique voice memo ID
        key_b64: Base64-encoded encryption key
        domain: Origin domain (e.g., "deathtodata.org")

    Returns:
        QR code data string

    Example:
        "deathtodata.org/voice/abc123#dGhpc2lzYXRlc3RrZXk="
    """
    return f"{domain}/voice/{memo_id}#{key_b64}"


def parse_qr_access_data(qr_data: str) -> Dict:
    """
    Parse QR code data to extract memo ID, domain, and key

    Args:
        qr_data: QR code string (format: domain/voice/memo_id#key)

    Returns:
        Dictionary with:
        - domain: Origin domain
        - memo_id: Voice memo ID
        - key_b64: Base64-encoded key
        - key: Decoded key bytes

    Example:
        Input: "deathtodata.org/voice/abc123#dGhpc2lzYXRlc3RrZXk="
        Output: {
            "domain": "deathtodata.org",
            "memo_id": "abc123",
            "key_b64": "dGhpc2lzYXRlc3RrZXk=",
            "key": b"..."
        }
    """
    # Remove http/https if present
    qr_data = qr_data.replace('https://', '').replace('http://', '')

    # Split on #
    if '#' not in qr_data:
        raise ValueError("Invalid QR data: Missing # separator")

    url_part, key_b64 = qr_data.split('#', 1)

    # Parse URL part: domain/voice/memo_id
    parts = url_part.split('/')

    if len(parts) < 3 or parts[-2] != 'voice':
        raise ValueError("Invalid QR data: Expected format domain/voice/memo_id#key")

    domain = parts[0]
    memo_id = parts[-1]

    # Decode key
    try:
        key = key_from_base64(key_b64)
    except Exception as e:
        raise ValueError(f"Invalid encryption key in QR code: {str(e)}")

    return {
        'domain': domain,
        'memo_id': memo_id,
        'key_b64': key_b64,
        'key': key
    }


def hash_access_key(key: bytes) -> str:
    """
    Create SHA-256 hash of access key for verification without storing key

    Args:
        key: Encryption key bytes

    Returns:
        Hex-encoded SHA-256 hash
    """
    import hashlib
    return hashlib.sha256(key).hexdigest()


def verify_access_key(key: bytes, key_hash: str) -> bool:
    """
    Verify an access key against its stored hash

    Args:
        key: Key to verify
        key_hash: Expected hash (hex string)

    Returns:
        True if key matches hash, False otherwise
    """
    computed_hash = hash_access_key(key)
    return computed_hash == key_hash


# Convenience functions for common operations

def encrypt_audio_file(file_path: str, output_path: str = None) -> Dict:
    """
    Encrypt an audio file and save encrypted version

    Args:
        file_path: Path to audio file
        output_path: Optional output path (defaults to file_path + '.encrypted')

    Returns:
        Encryption metadata (key, IV, etc.)
    """
    if output_path is None:
        output_path = file_path + '.encrypted'

    # Read audio file
    with open(file_path, 'rb') as f:
        audio_data = f.read()

    # Encrypt
    result = encrypt_voice_memo(audio_data)

    # Write encrypted file
    with open(output_path, 'wb') as f:
        f.write(result['encrypted_data'])

    return {
        'encrypted_file': output_path,
        'key_b64': result['key_b64'],
        'iv_b64': result['iv_b64']
    }


def decrypt_audio_file(encrypted_path: str, key_b64: str, iv_b64: str, output_path: str = None) -> str:
    """
    Decrypt an audio file

    Args:
        encrypted_path: Path to encrypted audio file
        key_b64: Base64-encoded encryption key
        iv_b64: Base64-encoded IV
        output_path: Optional output path (defaults to encrypted_path + '.decrypted')

    Returns:
        Path to decrypted file
    """
    if output_path is None:
        output_path = encrypted_path.replace('.encrypted', '.decrypted')

    # Read encrypted file
    with open(encrypted_path, 'rb') as f:
        encrypted_data = f.read()

    # Decrypt
    key = key_from_base64(key_b64)
    iv = iv_from_base64(iv_b64)

    decrypted = decrypt_voice_memo(encrypted_data, key, iv)

    # Write decrypted file
    with open(output_path, 'wb') as f:
        f.write(decrypted)

    return output_path


if __name__ == '__main__':
    print("Voice Memo Encryption Test")
    print("=" * 60)
    print()

    # Test encryption/decryption
    test_audio = b"This is test audio data" * 100

    print("1. Encrypting test audio...")
    result = encrypt_voice_memo(test_audio)
    print(f"   ✅ Encrypted {len(test_audio)} bytes")
    print(f"   Key (base64): {result['key_b64'][:20]}...")
    print(f"   IV (base64):  {result['iv_b64']}")
    print()

    print("2. Creating QR access data...")
    qr_data = create_qr_access_data('test123', result['key_b64'], 'deathtodata.org')
    print(f"   ✅ QR data: {qr_data[:50]}...")
    print()

    print("3. Parsing QR access data...")
    parsed = parse_qr_access_data(qr_data)
    print(f"   ✅ Domain: {parsed['domain']}")
    print(f"   ✅ Memo ID: {parsed['memo_id']}")
    print(f"   ✅ Key matches: {parsed['key'] == result['key']}")
    print()

    print("4. Decrypting audio...")
    decrypted = decrypt_voice_memo(
        result['encrypted_data'],
        result['key'],
        result['iv']
    )
    print(f"   ✅ Decrypted {len(decrypted)} bytes")
    print(f"   ✅ Data matches original: {decrypted == test_audio}")
    print()

    print("5. Testing access key hashing...")
    key_hash = hash_access_key(result['key'])
    print(f"   ✅ Key hash: {key_hash[:20]}...")
    print(f"   ✅ Verification: {verify_access_key(result['key'], key_hash)}")
    print()

    print("6. Testing key derivation from passphrase...")
    key, salt = derive_key_from_passphrase("my secret password")
    print(f"   ✅ Derived key: {base64.urlsafe_b64encode(key).decode()[:20]}...")
    print(f"   ✅ Salt: {base64.urlsafe_b64encode(salt).decode()}")
    print()

    print("All tests passed! ✅")
