#!/usr/bin/env python3
"""
Hash Asset - Generate cryptographic proof for media files

Usage:
    python3 hash-asset.py assets/screenshots/mobile-recorder.png

Creates:
    assets/screenshots/mobile-recorder.png.hash (JSON proof file)
"""

import hashlib
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

def sha256_file(filepath):
    """Calculate SHA-256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def get_git_commit():
    """Get current git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return None

def merkle_root(hashes):
    """
    Calculate merkle root from list of hashes

    Simple implementation: Hash pairs recursively until one root remains
    """
    if len(hashes) == 0:
        return hashlib.sha256(b"").hexdigest()

    if len(hashes) == 1:
        return hashes[0]

    # Pair up hashes and hash each pair
    next_level = []
    for i in range(0, len(hashes), 2):
        if i + 1 < len(hashes):
            # Hash pair
            combined = hashes[i] + hashes[i+1]
            pair_hash = hashlib.sha256(combined.encode()).hexdigest()
            next_level.append(pair_hash)
        else:
            # Odd one out - duplicate it
            combined = hashes[i] + hashes[i]
            pair_hash = hashlib.sha256(combined.encode()).hexdigest()
            next_level.append(pair_hash)

    # Recurse
    return merkle_root(next_level)

def hash_asset(filepath):
    """Generate hash proof for asset file"""
    file_path = Path(filepath)

    if not file_path.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    # Calculate file hash
    file_hash = sha256_file(filepath)

    # Get git info
    git_commit = get_git_commit()

    # Calculate merkle root (for now, just this single file)
    # In future, include all assets in merkle tree
    root = merkle_root([file_hash])

    # Create proof object
    proof = {
        "file": str(file_path),
        "sha256": file_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "merkle_root": root,
        "git_commit": git_commit,
        "algorithm": "sha256",
        "version": "1.0"
    }

    # Write proof file
    proof_path = f"{filepath}.hash"
    with open(proof_path, 'w') as f:
        json.dump(proof, f, indent=2)

    print(f"✅ Generated proof: {proof_path}")
    print(f"   SHA-256: {file_hash}")
    print(f"   Merkle root: {root}")
    if git_commit:
        print(f"   Git commit: {git_commit}")

    return proof

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 hash-asset.py <filepath>")
        print("Example: python3 hash-asset.py assets/screenshots/mobile.png")
        sys.exit(1)

    filepath = sys.argv[1]
    hash_asset(filepath)
