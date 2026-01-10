#!/usr/bin/env python3
"""
VoiceProof Archiver - Upload predictions to Archive.org

This script uploads VoiceProof predictions (voice recordings + metadata) to the
Internet Archive for permanent preservation.

Usage:
    python3 voiceproof_archiver.py <prediction_directory>
    python3 voiceproof_archiver.py predictions/2024-01-15-gpt5-prediction/

Requirements:
    pip install internetarchive

Setup:
    ia configure  # Enter Archive.org credentials
"""

from internetarchive import upload, get_item
import json
from pathlib import Path
from datetime import datetime
import sys
import argparse


def slugify(text):
    """Convert text to URL-safe slug"""
    return text.lower().replace(' ', '-').replace('_', '-')


def upload_prediction(prediction_dir, dry_run=False, skip_existing=True):
    """
    Upload a VoiceProof prediction to Archive.org

    Args:
        prediction_dir: Path to directory containing .webm, .json, .md files
        dry_run: If True, print metadata but don't upload
        skip_existing: If True, skip upload if item already exists

    Returns:
        Archive.org URL (or None if dry run)
    """
    prediction_dir = Path(prediction_dir)

    if not prediction_dir.exists():
        raise ValueError(f"Directory not found: {prediction_dir}")

    # Find metadata file
    json_files = list(prediction_dir.glob('*.json'))
    if not json_files:
        raise ValueError(f"No JSON metadata found in {prediction_dir}")

    metadata_file = json_files[0]

    # Load VoiceProof metadata
    with open(metadata_file) as f:
        vp_metadata = json.load(f)

    # Extract components for identifier
    prediction_id = vp_metadata.get('id', 'unknown')
    creator_name = vp_metadata.get('creator', {}).get('name', 'anonymous')
    creator_slug = slugify(creator_name)

    recorded_at = vp_metadata.get('recorded_at', datetime.now().isoformat())
    recorded_date = recorded_at[:10]  # YYYY-MM-DD

    # Build Archive.org identifier
    identifier = f"voiceproof-{creator_slug}-{recorded_date}-{slugify(prediction_id)}"

    # Check if already exists
    if skip_existing:
        item = get_item(identifier)
        if item.exists:
            print(f"⚠️  Item already exists: https://archive.org/details/{identifier}")
            return f"https://archive.org/details/{identifier}"

    # Map to Archive.org metadata
    ia_metadata = {
        'mediatype': 'audio',
        'collection': f'opensource',  # Default collection (change to voiceproof-predictions when collection created)
        'title': f"{vp_metadata.get('prediction', 'VoiceProof Prediction')} (VoiceProof)",
        'creator': f"{creator_name} (VoiceProof)",
        'date': recorded_date,
        'description': build_description(vp_metadata),
        'subject': build_subjects(vp_metadata),
        'licenseurl': 'https://creativecommons.org/licenses/by/4.0/',
        'source': vp_metadata.get('article', {}).get('url', ''),

        # Custom VoiceProof fields
        'voiceproof_version': vp_metadata.get('version', '1.0'),
        'voiceproof_score': vp_metadata.get('cringe_score', 0.0),
        'voiceproof_cringe_votes': vp_metadata.get('votes', {}).get('cringe', 0),
        'voiceproof_based_votes': vp_metadata.get('votes', {}).get('based', 0),
        'voiceproof_article_url': vp_metadata.get('article', {}).get('url', ''),
        'voiceproof_article_source': vp_metadata.get('article', {}).get('source', ''),
        'voiceproof_time_lock': vp_metadata.get('time_locked_until', ''),
    }

    # Collect all files to upload
    files = []
    for ext in ['webm', 'mp3', 'wav', 'json', 'md', 'txt']:
        matching = list(prediction_dir.glob(f'*.{ext}'))
        files.extend([str(f) for f in matching])

    if not files:
        raise ValueError(f"No files to upload in {prediction_dir}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"VoiceProof → Archive.org Upload")
    print(f"{'='*60}")
    print(f"Identifier: {identifier}")
    print(f"Creator: {creator_name}")
    print(f"Prediction: {vp_metadata.get('prediction', 'N/A')[:80]}...")
    print(f"Files: {len(files)} files")
    for f in files:
        print(f"  - {Path(f).name}")
    print(f"{'='*60}\n")

    if dry_run:
        print("🔍 DRY RUN - Metadata preview:")
        print(json.dumps(ia_metadata, indent=2))
        print("\nTo actually upload, run without --dry-run flag")
        return None

    # Upload to Archive.org
    print(f"📤 Uploading to Archive.org...")

    try:
        result = upload(
            identifier,
            files=files,
            metadata=ia_metadata,
            verify=True,
            verbose=True
        )

        # Return permanent URL
        url = f"https://archive.org/details/{identifier}"
        print(f"\n✅ Upload complete!")
        print(f"🔗 Permanent URL: {url}")
        print(f"📥 Download: https://archive.org/download/{identifier}/")

        return url

    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        raise


def build_description(vp_metadata):
    """Build Archive.org description from VoiceProof metadata"""

    article = vp_metadata.get('article', {})
    prediction = vp_metadata.get('prediction', 'No prediction text')
    votes = vp_metadata.get('votes', {})
    cringe_score = vp_metadata.get('cringe_score', 0.0)

    description = f"""VoiceProof Prediction

Prediction: {prediction}

"""

    if article:
        description += f"""About Article: {article.get('title', 'Unknown')}
Source: {article.get('source', 'Unknown')}
URL: {article.get('url', 'Unknown')}

"""

    description += f"""Recorded: {vp_metadata.get('recorded_at', 'Unknown')}
Time-locked until: {vp_metadata.get('time_locked_until', 'Not time-locked')}

CringeProof Score: {cringe_score:.2f} (0.0 = based, 1.0 = cringe)
Votes: {votes.get('cringe', 0)} cringe | {votes.get('based', 0)} based

---

This is a VoiceProof Protocol prediction - a decentralized, Git-based system for preserving voice reactions to news events.

VoiceProof enables anyone to:
- Record voice predictions about future events
- Time-lock them until the outcome is known
- Vote on accuracy (cringe vs based)
- Preserve predictions permanently on Archive.org

Learn more: https://github.com/voiceproof/protocol
"""

    return description.strip()


def build_subjects(vp_metadata):
    """Build Archive.org subject tags from VoiceProof metadata"""

    subjects = ['voiceproof', 'predictions', 'voice', 'audio']

    # Add article topics
    article = vp_metadata.get('article', {})
    if 'topics' in article and article['topics']:
        topics = article['topics']
        if isinstance(topics, str):
            subjects.append(topics)
        elif isinstance(topics, list):
            subjects.extend(topics)

    # Add source
    if 'source' in article:
        subjects.append(article['source'])

    return subjects


def bulk_upload(predictions_dir, **kwargs):
    """Upload all predictions in a directory"""

    predictions_dir = Path(predictions_dir)

    if not predictions_dir.exists():
        raise ValueError(f"Directory not found: {predictions_dir}")

    # Find all subdirectories with JSON files
    prediction_dirs = []
    for json_file in predictions_dir.rglob('*.json'):
        prediction_dirs.append(json_file.parent)

    prediction_dirs = list(set(prediction_dirs))  # Deduplicate

    print(f"Found {len(prediction_dirs)} predictions to upload\n")

    results = []
    for i, pred_dir in enumerate(prediction_dirs, 1):
        print(f"\n[{i}/{len(prediction_dirs)}] Processing {pred_dir.name}")
        try:
            url = upload_prediction(pred_dir, **kwargs)
            results.append({'dir': str(pred_dir), 'url': url, 'success': True})
        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append({'dir': str(pred_dir), 'error': str(e), 'success': False})

    # Summary
    print(f"\n{'='*60}")
    print("UPLOAD SUMMARY")
    print(f"{'='*60}")
    successful = len([r for r in results if r['success']])
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")

    if successful > 0:
        print("\n📋 Uploaded predictions:")
        for r in results:
            if r['success']:
                print(f"  {r['url']}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Upload VoiceProof predictions to Archive.org',
        epilog='Example: python3 voiceproof_archiver.py predictions/2024-01-15-gpt5/'
    )

    parser.add_argument(
        'prediction_dir',
        help='Path to prediction directory (or parent directory for --bulk)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print metadata without uploading'
    )

    parser.add_argument(
        '--bulk',
        action='store_true',
        help='Upload all predictions in directory tree'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Upload even if item already exists'
    )

    args = parser.parse_args()

    try:
        if args.bulk:
            bulk_upload(
                args.prediction_dir,
                dry_run=args.dry_run,
                skip_existing=not args.force
            )
        else:
            url = upload_prediction(
                args.prediction_dir,
                dry_run=args.dry_run,
                skip_existing=not args.force
            )

            if url:
                print(f"\n🎉 Done! Share your prediction:")
                print(f"   {url}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
