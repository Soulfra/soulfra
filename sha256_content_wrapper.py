#!/usr/bin/env python3
"""
SHA256 Content Wrapper - Voice Signature Filtering System

Uses your 256-word wordmap SHA256 hash as content filtering layer:
1. Your wordmap → SHA256 hash (deterministic voice signature)
2. Incoming content → Calculate alignment % with your wordmap
3. Auto accept/reject based on alignment threshold
4. Wrap content with metadata (hash, alignment, approval)

Usage:
    # Wrap AI debate response
    python3 sha256_content_wrapper.py --wrap-text "Some AI response..."

    # Filter multiple responses
    python3 sha256_content_wrapper.py --filter-debate 7

    # Check alignment for any text
    python3 sha256_content_wrapper.py --check "Your text here"

    # Show user's voice signature
    python3 sha256_content_wrapper.py --show-signature

Like:
- Self-authenticating content (SHA256 proves ownership)
- Deterministic filtering (same wordmap = same decisions)
- Agent router decision layer (alignment % = payment tier)
- Character/lore consistency checks
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from database import get_db
from user_wordmap_engine import get_user_wordmap
from wordmap_pitch_integrator import calculate_wordmap_alignment, extract_wordmap_from_transcript


# ==============================================================================
# CONFIG
# ==============================================================================

# Alignment thresholds
ALIGNMENT_THRESHOLDS = {
    'premium': 0.80,    # >80% = Premium tier (sounds exactly like user)
    'standard': 0.50,   # 50-80% = Standard tier (similar style)
    'basic': 0.30,      # 30-50% = Basic tier (somewhat relevant)
    'reject': 0.0       # <30% = Reject (doesn't match at all)
}

WRAPPED_CONTENT_DIR = Path('./wrapped_content')
WRAPPED_CONTENT_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# SHA256 CONTENT WRAPPER
# ==============================================================================

class SHA256ContentWrapper:
    """Wrap and filter content using SHA256 voice signature"""

    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.db = get_db()

        # Load user's wordmap and signature
        self.wordmap_data = get_user_wordmap(user_id)

        if not self.wordmap_data:
            raise ValueError(f"No wordmap found for user {user_id}. Create by recording voice memos.")

        self.wordmap = self.wordmap_data['wordmap']
        self.word_count = len(self.wordmap)
        self.signature_hash = self._calculate_signature_hash()

    def _calculate_signature_hash(self) -> str:
        """Calculate SHA256 hash of user's wordmap (voice signature)"""
        # Sort for deterministic hashing
        sorted_wordmap = dict(sorted(self.wordmap.items()))
        wordmap_json = json.dumps(sorted_wordmap, sort_keys=True)
        return hashlib.sha256(wordmap_json.encode()).hexdigest()

    def get_signature_info(self) -> Dict:
        """Get user's voice signature information"""
        return {
            'user_id': self.user_id,
            'word_count': self.word_count,
            'sha256_hash': self.signature_hash,
            'status': 'complete' if self.word_count >= 256 else 'building',
            'completion_pct': (self.word_count / 256) * 100,
            'top_words': sorted(
                self.wordmap.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
        }

    def calculate_content_alignment(self, content: str) -> float:
        """Calculate how well content aligns with user's wordmap (0.0 - 1.0)"""
        return calculate_wordmap_alignment(self.wordmap, content)

    def get_tier_from_alignment(self, alignment: float) -> str:
        """Determine content tier from alignment score"""
        if alignment >= ALIGNMENT_THRESHOLDS['premium']:
            return 'premium'
        elif alignment >= ALIGNMENT_THRESHOLDS['standard']:
            return 'standard'
        elif alignment >= ALIGNMENT_THRESHOLDS['basic']:
            return 'basic'
        else:
            return 'reject'

    def wrap_content(
        self,
        content: str,
        content_type: str = 'text',
        metadata: Optional[Dict] = None,
        auto_approve: bool = True
    ) -> Dict:
        """
        Wrap content with SHA256 signature and alignment metadata

        Args:
            content: The content to wrap
            content_type: Type (text, ai_response, debate, etc.)
            metadata: Additional metadata to include
            auto_approve: Auto-approve if alignment meets threshold

        Returns:
            Wrapped content dict with signature, alignment, approval
        """
        # Calculate alignment
        alignment = self.calculate_content_alignment(content)
        tier = self.get_tier_from_alignment(alignment)

        # Auto-approve decision
        approved = False
        if auto_approve:
            approved = tier != 'reject'

        # Build wrapped content
        wrapped = {
            'content': content,
            'content_type': content_type,
            'signature': {
                'user_id': self.user_id,
                'sha256_hash': self.signature_hash,
                'wordmap_size': self.word_count,
                'wordmap_complete': self.word_count >= 256
            },
            'alignment': {
                'score': alignment,
                'percentage': f"{alignment:.1%}",
                'tier': tier,
                'threshold_met': alignment >= ALIGNMENT_THRESHOLDS['standard']
            },
            'approval': {
                'approved': approved,
                'auto_approved': auto_approve,
                'reason': self._get_approval_reason(tier, alignment)
            },
            'metadata': metadata or {},
            'wrapped_at': datetime.now().isoformat()
        }

        return wrapped

    def _get_approval_reason(self, tier: str, alignment: float) -> str:
        """Get human-readable approval reason"""
        if tier == 'premium':
            return f"Premium tier ({alignment:.1%}) - Sounds exactly like your voice"
        elif tier == 'standard':
            return f"Standard tier ({alignment:.1%}) - Similar style and vocabulary"
        elif tier == 'basic':
            return f"Basic tier ({alignment:.1%}) - Somewhat relevant to your topics"
        else:
            return f"Rejected ({alignment:.1%}) - Doesn't match your voice signature"

    def filter_ai_responses(
        self,
        responses: List[str],
        min_tier: str = 'standard'
    ) -> List[Dict]:
        """
        Filter multiple AI responses by alignment threshold

        Args:
            responses: List of AI response texts
            min_tier: Minimum tier to accept (premium, standard, basic)

        Returns:
            List of wrapped responses that meet threshold
        """
        tier_order = ['reject', 'basic', 'standard', 'premium']
        min_tier_index = tier_order.index(min_tier)

        filtered = []

        for i, response in enumerate(responses):
            wrapped = self.wrap_content(
                content=response,
                content_type='ai_response',
                metadata={'response_index': i},
                auto_approve=True
            )

            response_tier_index = tier_order.index(wrapped['alignment']['tier'])

            if response_tier_index >= min_tier_index:
                filtered.append(wrapped)

        return filtered

    def wrap_debate_responses(self, recording_id: int) -> Dict:
        """Wrap AI debate responses for a recording"""
        # Get recording
        recording = self.db.execute('''
            SELECT id, filename, transcription
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        if not recording or not recording['transcription']:
            return {'error': f"Recording {recording_id} not found or has no transcription"}

        # Get AI debate responses (if any exist)
        # This assumes ai_debate_generator.py has created debates
        from pathlib import Path
        debates_dir = Path('./debates')

        if not debates_dir.exists():
            return {
                'error': 'No debates directory found',
                'help': 'Run: python3 ai_debate_generator.py --recording <ID>'
            }

        # Find debate files for this recording
        debate_files = list(debates_dir.glob(f'debate_{recording_id}_*.json'))

        if not debate_files:
            return {
                'error': f'No debate files found for recording {recording_id}',
                'help': f'Run: python3 ai_debate_generator.py --recording {recording_id}'
            }

        # Wrap each debate response
        wrapped_debates = []

        for debate_file in debate_files:
            debate_data = json.loads(debate_file.read_text())

            ai_response = debate_data.get('ai_response', {}).get('counter_argument', '')

            if ai_response:
                wrapped = self.wrap_content(
                    content=ai_response,
                    content_type='ai_debate_response',
                    metadata={
                        'recording_id': recording_id,
                        'debate_file': str(debate_file),
                        'persona': debate_data.get('ai_response', {}).get('persona', 'unknown'),
                        'original_controversy_score': debate_data.get('ai_response', {}).get('controversy_score', 0)
                    },
                    auto_approve=True
                )

                wrapped_debates.append(wrapped)

        return {
            'recording_id': recording_id,
            'original_transcript': recording['transcription'],
            'debates_found': len(wrapped_debates),
            'wrapped_responses': wrapped_debates,
            'approved_count': sum(1 for w in wrapped_debates if w['approval']['approved']),
            'signature_hash': self.signature_hash
        }

    def save_wrapped_content(self, wrapped: Dict, filename: Optional[str] = None) -> Path:
        """Save wrapped content to file"""
        if not filename:
            timestamp = int(datetime.now().timestamp())
            content_type = wrapped.get('content_type', 'content')
            filename = f"wrapped_{content_type}_{timestamp}.json"

        output_file = WRAPPED_CONTENT_DIR / filename

        output_file.write_text(json.dumps(wrapped, indent=2))

        return output_file

    def generate_content_report(self, wrapped_items: List[Dict]) -> Dict:
        """Generate summary report of wrapped content"""
        total = len(wrapped_items)
        approved = sum(1 for w in wrapped_items if w['approval']['approved'])
        rejected = total - approved

        # Tier breakdown
        tier_counts = {}
        for item in wrapped_items:
            tier = item['alignment']['tier']
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Average alignment
        avg_alignment = sum(w['alignment']['score'] for w in wrapped_items) / total if total > 0 else 0

        return {
            'total_items': total,
            'approved': approved,
            'rejected': rejected,
            'approval_rate': (approved / total) * 100 if total > 0 else 0,
            'tier_breakdown': tier_counts,
            'average_alignment': avg_alignment,
            'signature_hash': self.signature_hash
        }


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='SHA256 Content Wrapper - Voice Signature Filtering'
    )

    parser.add_argument(
        '--show-signature',
        action='store_true',
        help='Show user voice signature (SHA256 hash)'
    )

    parser.add_argument(
        '--wrap-text',
        type=str,
        metavar='TEXT',
        help='Wrap and filter text content'
    )

    parser.add_argument(
        '--check',
        type=str,
        metavar='TEXT',
        help='Check alignment for text (no wrapping)'
    )

    parser.add_argument(
        '--filter-debate',
        type=int,
        metavar='ID',
        help='Filter AI debate responses for recording ID'
    )

    parser.add_argument(
        '--min-tier',
        type=str,
        default='standard',
        choices=['basic', 'standard', 'premium'],
        help='Minimum tier to accept (default: standard)'
    )

    parser.add_argument(
        '--save',
        action='store_true',
        help='Save wrapped content to file'
    )

    parser.add_argument(
        '--user-id',
        type=int,
        default=1,
        help='User ID (default: 1)'
    )

    args = parser.parse_args()

    try:
        wrapper = SHA256ContentWrapper(user_id=args.user_id)

        # Show signature
        if args.show_signature:
            print("\n" + "="*70)
            print("  🔐 USER VOICE SIGNATURE")
            print("="*70 + "\n")

            sig_info = wrapper.get_signature_info()

            print(f"User ID: {sig_info['user_id']}")
            print(f"Wordmap size: {sig_info['word_count']} words")
            print(f"Status: {sig_info['status']} ({sig_info['completion_pct']:.1f}% to 256)")
            print(f"\nSHA256 Hash:")
            print(f"   {sig_info['sha256_hash']}")

            print(f"\nTop 20 words:")
            for word, freq in sig_info['top_words']:
                bar = '█' * min(int(freq), 20)
                print(f"   {word:15} {bar} ({freq})")

            print(f"\n💡 This hash is your deterministic voice identity")
            print(f"   Use it to filter content by alignment %\n")

        # Check alignment
        elif args.check:
            alignment = wrapper.calculate_content_alignment(args.check)
            tier = wrapper.get_tier_from_alignment(alignment)

            print(f"\n📊 ALIGNMENT CHECK")
            print(f"{'='*70}\n")

            # Visual bar
            bar_length = int(alignment * 50)
            bar = '█' * bar_length + '░' * (50 - bar_length)

            print(f"Text: {args.check[:100]}...")
            print(f"\nAlignment: {bar} {alignment:.1%}")
            print(f"Tier: {tier.upper()}")

            if tier == 'premium':
                print(f"✅ PREMIUM - Sounds exactly like your voice")
            elif tier == 'standard':
                print(f"✅ STANDARD - Similar style and vocabulary")
            elif tier == 'basic':
                print(f"⚠️  BASIC - Somewhat relevant")
            else:
                print(f"❌ REJECT - Doesn't match your voice")

            print()

        # Wrap text
        elif args.wrap_text:
            print(f"\n🎁 WRAPPING CONTENT")
            print(f"{'='*70}\n")

            wrapped = wrapper.wrap_content(
                content=args.wrap_text,
                content_type='text',
                auto_approve=True
            )

            print(f"Content: {args.wrap_text[:100]}...")
            print(f"\n✅ Alignment: {wrapped['alignment']['percentage']}")
            print(f"   Tier: {wrapped['alignment']['tier'].upper()}")
            print(f"   Approved: {wrapped['approval']['approved']}")
            print(f"   Reason: {wrapped['approval']['reason']}")
            print(f"\n🔐 Signature: {wrapped['signature']['sha256_hash'][:16]}...")

            if args.save:
                output_file = wrapper.save_wrapped_content(wrapped)
                print(f"\n💾 Saved to: {output_file}")

            print()

        # Filter debate
        elif args.filter_debate:
            print(f"\n🥊 FILTERING AI DEBATE RESPONSES")
            print(f"{'='*70}\n")

            result = wrapper.wrap_debate_responses(args.filter_debate)

            if 'error' in result:
                print(f"❌ {result['error']}")
                if 'help' in result:
                    print(f"   💡 {result['help']}")
                sys.exit(1)

            print(f"Recording ID: {result['recording_id']}")
            print(f"Debates found: {result['debates_found']}")
            print(f"Approved: {result['approved_count']}/{result['debates_found']}")
            print(f"Signature: {result['signature_hash'][:16]}...\n")

            # Show each wrapped response
            for i, wrapped in enumerate(result['wrapped_responses'], 1):
                print(f"{'─'*70}")
                print(f"RESPONSE {i}: {wrapped['metadata'].get('persona', 'unknown').upper()}")
                print(f"{'─'*70}")

                print(f"\nContent preview:")
                print(f"   {wrapped['content'][:200]}...")

                print(f"\n📊 Alignment: {wrapped['alignment']['percentage']}")
                print(f"   Tier: {wrapped['alignment']['tier'].upper()}")
                print(f"   Approved: {'✅ YES' if wrapped['approval']['approved'] else '❌ NO'}")
                print(f"   {wrapped['approval']['reason']}\n")

            # Save report
            if args.save:
                report_file = wrapper.save_wrapped_content(
                    result,
                    filename=f"debate_{args.filter_debate}_wrapped.json"
                )
                print(f"💾 Full report saved to: {report_file}\n")

        else:
            parser.print_help()

    except ValueError as e:
        print(f"\n❌ {e}")
        print(f"   💡 Create wordmap first:")
        print(f"      python3 wordmap_transcript_generator.py --build-to-256\n")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
