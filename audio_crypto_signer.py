#!/usr/bin/env python3
"""
Decentralized Audio Crypto Signer
Like Bitcoin signatures for voice memos

Features:
- Ed25519 cryptographic signatures
- IPFS hash verification
- Timestamp signing
- Proof of authorship
- Verification without trust

Usage:
    from audio_crypto_signer import AudioSigner

    # Create signer
    signer = AudioSigner()

    # Sign audio file
    signature = signer.sign_audio(audio_data, user_id="matt")

    # Verify signature
    is_valid = signer.verify_audio(audio_data, signature)

    # Publish to IPFS
    ipfs_hash = signer.publish_to_ipfs(audio_data)
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
import base64

# Cryptography imports
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("⚠️  cryptography not installed. Install with: pip install cryptography")

import subprocess


class AudioSigner:
    """
    Bitcoin-style cryptographic signing for audio files

    Each audio gets:
    - SHA-256 hash (content fingerprint)
    - Ed25519 signature (proof of authorship)
    - Unix timestamp (when signed)
    - IPFS hash (decentralized storage)
    """

    def __init__(self, keys_dir: Path = Path("./crypto_keys")):
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(exist_ok=True)

        if not HAS_CRYPTO:
            raise ImportError("cryptography library required. Install with: pip install cryptography")

    def generate_keypair(self, user_id: str) -> Tuple[bytes, bytes]:
        """
        Generate Ed25519 keypair for user (like Bitcoin wallet)

        Returns:
            (private_key_bytes, public_key_bytes)
        """
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize keys
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # Save keys
        private_file = self.keys_dir / f"{user_id}.private.key"
        public_file = self.keys_dir / f"{user_id}.public.key"

        private_file.write_bytes(private_bytes)
        public_file.write_bytes(public_bytes)

        # Also save as base64 for easy sharing
        (self.keys_dir / f"{user_id}.public.txt").write_text(
            base64.b64encode(public_bytes).decode()
        )

        print(f"✅ Generated keypair for {user_id}")
        print(f"   Private: {private_file}")
        print(f"   Public:  {public_file}")

        return private_bytes, public_bytes

    def load_private_key(self, user_id: str) -> Optional[Ed25519PrivateKey]:
        """Load user's private key"""
        private_file = self.keys_dir / f"{user_id}.private.key"

        if not private_file.exists():
            print(f"⚠️  No key found for {user_id}, generating new keypair...")
            private_bytes, _ = self.generate_keypair(user_id)
        else:
            private_bytes = private_file.read_bytes()

        return Ed25519PrivateKey.from_private_bytes(private_bytes)

    def load_public_key(self, user_id: str) -> Optional[Ed25519PublicKey]:
        """Load user's public key"""
        public_file = self.keys_dir / f"{user_id}.public.key"

        if not public_file.exists():
            return None

        public_bytes = public_file.read_bytes()
        return Ed25519PublicKey.from_public_bytes(public_bytes)

    def hash_audio(self, audio_data: bytes) -> str:
        """SHA-256 hash of audio content (like Bitcoin transaction hash)"""
        return hashlib.sha256(audio_data).hexdigest()

    def sign_audio(self, audio_data: bytes, user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Sign audio file with Ed25519 signature

        Returns signature package:
        {
            'audio_hash': sha256 hash,
            'signature': ed25519 signature (base64),
            'public_key': user's public key (base64),
            'timestamp': unix timestamp,
            'user_id': user identifier,
            'metadata': optional metadata
        }
        """
        # Hash the audio
        audio_hash = self.hash_audio(audio_data)

        # Load private key
        private_key = self.load_private_key(user_id)

        # Create signing payload (hash + timestamp)
        timestamp = int(time.time())
        payload = f"{audio_hash}:{timestamp}".encode()

        # Sign payload
        signature = private_key.sign(payload)

        # Get public key
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        signature_package = {
            'audio_hash': audio_hash,
            'signature': base64.b64encode(signature).decode(),
            'public_key': base64.b64encode(public_bytes).decode(),
            'timestamp': timestamp,
            'timestamp_iso': datetime.fromtimestamp(timestamp).isoformat(),
            'user_id': user_id,
            'metadata': metadata or {},
            'version': '1.0',
            'algorithm': 'Ed25519+SHA256'
        }

        return signature_package

    def verify_audio(self, audio_data: bytes, signature_package: Dict) -> bool:
        """
        Verify audio signature (like Bitcoin transaction verification)

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Hash the audio
            audio_hash = self.hash_audio(audio_data)

            # Check if hash matches
            if audio_hash != signature_package['audio_hash']:
                print("❌ Audio hash mismatch - file has been modified")
                return False

            # Reconstruct payload
            timestamp = signature_package['timestamp']
            payload = f"{audio_hash}:{timestamp}".encode()

            # Decode signature and public key
            signature = base64.b64decode(signature_package['signature'])
            public_bytes = base64.b64decode(signature_package['public_key'])

            # Reconstruct public key
            public_key = Ed25519PublicKey.from_public_bytes(public_bytes)

            # Verify signature
            public_key.verify(signature, payload)

            print(f"✅ Signature valid")
            print(f"   Signed by: {signature_package['user_id']}")
            print(f"   At: {signature_package['timestamp_iso']}")

            return True

        except Exception as e:
            print(f"❌ Signature verification failed: {e}")
            return False

    def publish_to_ipfs(self, audio_data: bytes, signature_package: Dict) -> Optional[str]:
        """
        Publish audio + signature to IPFS (decentralized storage)

        Returns:
            IPFS hash (like ipfs://QmXXX...)
        """
        import tempfile

        try:
            # Create temp directory for IPFS add
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)

                # Write audio file
                audio_file = tmpdir / "recording.webm"
                audio_file.write_bytes(audio_data)

                # Write signature file
                sig_file = tmpdir / "signature.json"
                sig_file.write_text(json.dumps(signature_package, indent=2))

                # Add to IPFS
                result = subprocess.run(
                    ['ipfs', 'add', '-r', '-Q', str(tmpdir)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode != 0:
                    print(f"❌ IPFS add failed: {result.stderr}")
                    return None

                ipfs_hash = result.stdout.strip()

                # Pin it
                subprocess.run(
                    ['ipfs', 'pin', 'add', ipfs_hash],
                    capture_output=True,
                    timeout=30
                )

                print(f"✅ Published to IPFS")
                print(f"   Hash: {ipfs_hash}")
                print(f"   URL:  ipfs://{ipfs_hash}")
                print(f"   Gateway: https://ipfs.io/ipfs/{ipfs_hash}")

                return ipfs_hash

        except Exception as e:
            print(f"❌ IPFS publish failed: {e}")
            return None

    def get_ipfs_url(self, ipfs_hash: str) -> Dict[str, str]:
        """Get various IPFS URLs for a hash"""
        return {
            'ipfs_uri': f'ipfs://{ipfs_hash}',
            'gateway_url': f'https://ipfs.io/ipfs/{ipfs_hash}',
            'cloudflare_gateway': f'https://cloudflare-ipfs.com/ipfs/{ipfs_hash}',
            'local_gateway': f'http://localhost:8080/ipfs/{ipfs_hash}'
        }


def main():
    """Test the audio signer"""
    signer = AudioSigner()

    # Create test audio
    test_audio = b"This is test audio content for Bitcoin-style signing"

    # Sign it
    print("\n🔐 Signing audio...")
    signature = signer.sign_audio(test_audio, user_id="satoshi", metadata={
        'title': 'Test Recording',
        'description': 'Decentralized audio signature test'
    })

    print(f"\n📋 Signature Package:")
    print(json.dumps(signature, indent=2))

    # Verify it
    print(f"\n✓ Verifying signature...")
    is_valid = signer.verify_audio(test_audio, signature)

    if is_valid:
        print("\n✅ Audio signature is valid!")
    else:
        print("\n❌ Audio signature is INVALID!")

    # Publish to IPFS
    print(f"\n📡 Publishing to IPFS...")
    ipfs_hash = signer.publish_to_ipfs(test_audio, signature)

    if ipfs_hash:
        urls = signer.get_ipfs_url(ipfs_hash)
        print(f"\n🌐 Access your audio:")
        for name, url in urls.items():
            print(f"   {name}: {url}")


if __name__ == '__main__':
    main()
