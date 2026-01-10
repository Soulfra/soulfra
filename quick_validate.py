#!/usr/bin/env python3
"""Quick Link Validation - Local Files Only"""

import re
from pathlib import Path

def validate_voice_archive():
    """Validate voice-archive directory structure"""
    errors = []

    # Check ideas hub
    ideas_index = Path("voice-archive/ideas/index.html")
    if ideas_index.exists():
        content = ideas_index.read_text()

        # Find all audio links
        audio_links = re.findall(r'href="\.\.\/audio\/(\d+)\/"', content)

        for recording_id in audio_links:
            audio_dir = Path(f"voice-archive/audio/{recording_id}")
            if not audio_dir.exists():
                errors.append(f"Missing audio directory: audio/{recording_id}/")
            else:
                # Check for required files
                if not (audio_dir / "index.html").exists():
                    errors.append(f"Missing index.html in audio/{recording_id}/")
                if not (audio_dir / "metadata.json").exists():
                    errors.append(f"Missing metadata.json in audio/{recording_id}/")
    else:
        errors.append("Missing voice-archive/ideas/index.html")

    # Check main gallery
    main_index = Path("voice-archive/index.html")
    if main_index.exists():
        content = main_index.read_text()

        # Find all prediction links
        pred_links = re.findall(r'href="([a-f0-9]{8})\/"', content)

        for hash_dir in pred_links:
            pred_dir = Path(f"voice-archive/{hash_dir}")
            if not pred_dir.exists():
                errors.append(f"Missing prediction directory: {hash_dir}/")

    # Print results
    print("\n" + "="*60)
    print("🔍 QUICK LINK VALIDATION")
    print("="*60)

    if errors:
        print(f"\n❌ Found {len(errors)} issues:\n")
        for error in errors:
            print(f"   • {error}")
    else:
        print("\n✅ All critical links are valid!")

    print("\n" + "="*60 + "\n")

    return len(errors) == 0

if __name__ == '__main__':
    validate_voice_archive()
