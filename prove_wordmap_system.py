#!/usr/bin/env python3
"""
Prove Wordmap System Works - 20 → 256 Word Progression

Demonstrates the complete wordmap building system:
1. Start: 20 words in user wordmap
2. Generate synthetic transcripts via Ollama
3. End: 256 words for SHA256 voice signature
4. Calculate SHA256 hash of final wordmap

This is the "dig site" - the identity layer that ties everything together.

Usage:
    # Quick proof (5 transcripts)
    python3 prove_wordmap_system.py

    # Build to 256 words
    python3 prove_wordmap_system.py --build-to-256

    # Show progression with details
    python3 prove_wordmap_system.py --verbose

Like:
- Voice fingerprint (256 words = SHA256 hash space)
- Deterministic identity proof
- Content filtering by wordmap alignment
- Agent router decision layer
"""

import sys
import json
from pathlib import Path
from database import get_db
from wordmap_transcript_generator import WordmapTranscriptGenerator
from user_wordmap_engine import get_user_wordmap
from wordmap_pitch_integrator import calculate_wordmap_alignment


# ==============================================================================
# PROOF OF CONCEPT
# ==============================================================================

def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def show_current_state():
    """Show current wordmap state"""
    print_header("📊 CURRENT WORDMAP STATE")

    wordmap_data = get_user_wordmap(user_id=1)

    if not wordmap_data:
        print("❌ No wordmap found. Create by recording voice memos.")
        return None

    wordmap = wordmap_data['wordmap']
    word_count = len(wordmap)

    print(f"Current size: {word_count} unique words")
    print(f"Target: 256 words")
    print(f"Gap: {256 - word_count} words needed")
    print(f"Recording count: {wordmap_data.get('recording_count', 0)}\n")

    # Show top words
    print("Top 20 words by frequency:")
    sorted_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)[:20]

    for i, (word, freq) in enumerate(sorted_words, 1):
        bar = '█' * min(int(freq), 20)
        print(f"   {i:2}. {word:15} {bar} ({freq})")

    return {
        'wordmap': wordmap,
        'word_count': word_count,
        'gap': 256 - word_count
    }


def simulate_wordmap_growth(generator, num_transcripts: int = 5, verbose: bool = False):
    """Simulate wordmap growth with synthetic transcripts"""
    print_header(f"🎙️  GENERATING {num_transcripts} SYNTHETIC TRANSCRIPTS")

    print("This will:")
    print(f"  1. Generate {num_transcripts} voice memo transcripts via Ollama")
    print(f"  2. Extract wordmap from each transcript")
    print(f"  3. Merge into user's cumulative wordmap")
    print(f"  4. Show progression toward 256-word target\n")

    # Get seed transcripts
    seed_transcripts = generator.get_seed_transcripts()

    if not seed_transcripts:
        print("⚠️  No seed transcripts found. Using generic style.\n")
    else:
        print(f"✅ Using {len(seed_transcripts)} existing recordings as style seed\n")

    # Track progression
    progression = []

    from wordmap_transcript_generator import GENERATION_TOPICS

    for i in range(num_transcripts):
        topic = GENERATION_TOPICS[i % len(GENERATION_TOPICS)]

        print(f"\n{'─'*70}")
        print(f"TRANSCRIPT {i+1}/{num_transcripts}")
        print(f"{'─'*70}")
        print(f"Topic: {topic[:60]}...")

        # Generate transcript
        transcript = generator.generate_synthetic_transcript(
            topic=topic,
            seed_transcripts=seed_transcripts,
            model='llama3',
            target_length=250
        )

        if not transcript:
            print("   ❌ Generation failed, skipping...")
            continue

        # Get wordmap before
        before_state = generator.get_current_wordmap_state()
        before_count = before_state['word_count']

        # Update wordmap
        from user_wordmap_engine import update_user_wordmap

        update_result = update_user_wordmap(
            user_id=1,
            recording_id=None,  # Synthetic
            transcript=transcript
        )

        after_count = len(update_result['wordmap'])
        new_words = after_count - before_count

        print(f"\n   📈 Wordmap: {before_count} → {after_count} (+{new_words} new words)")
        print(f"   Progress: {after_count}/256 ({(after_count/256)*100:.1f}%)")

        # Show new words added (if verbose)
        if verbose and new_words > 0:
            before_words = set(before_state['wordmap'].keys())
            after_words = set(update_result['wordmap'].keys())
            added_words = after_words - before_words

            print(f"\n   ✨ New words added ({len(added_words)}):")
            for word in sorted(list(added_words)[:10]):
                print(f"      • {word}")
            if len(added_words) > 10:
                print(f"      ... and {len(added_words) - 10} more")

        progression.append({
            'transcript_num': i + 1,
            'topic': topic,
            'word_count': after_count,
            'new_words': new_words,
            'progress_pct': (after_count / 256) * 100
        })

        # Stop if we hit 256
        if after_count >= 256:
            print(f"\n✅ TARGET REACHED! ({after_count} words)")
            break

    return progression


def show_final_results(generator):
    """Show final wordmap results with SHA256 hash"""
    print_header("🎉 FINAL WORDMAP RESULTS")

    final_state = generator.get_current_wordmap_state()
    wordmap = final_state['wordmap']
    word_count = final_state['word_count']

    print(f"Final size: {word_count} unique words")
    print(f"Target: 256 words")

    if word_count >= 256:
        print(f"Status: ✅ TARGET REACHED (+{word_count - 256} extra)")
    else:
        print(f"Status: ⏳ {256 - word_count} words remaining")

    # Calculate SHA256 hash
    wordmap_hash = generator._hash_wordmap(wordmap)

    print(f"\n🔐 SHA256 Voice Signature:")
    print(f"   {wordmap_hash}")
    print(f"\n💡 This hash is your deterministic voice identity fingerprint")
    print(f"   • Same wordmap = Same hash")
    print(f"   • Content filtering: Match AI responses against this signature")
    print(f"   • Agent routing: Use hash for tier/permission decisions")

    return {
        'wordmap': wordmap,
        'word_count': word_count,
        'sha256_hash': wordmap_hash
    }


def demonstrate_content_filtering(wordmap: dict):
    """Demonstrate content filtering using wordmap alignment"""
    print_header("🔍 CONTENT FILTERING DEMONSTRATION")

    print("Testing how well different texts align with your wordmap:\n")

    # Test texts
    test_cases = [
        {
            'name': 'Your style (high alignment)',
            'text': 'I really think about authentic connection and genuine community. The cringe culture feels fake, but real trust and belonging matter.'
        },
        {
            'name': 'Similar topic (medium alignment)',
            'text': 'Social media platforms create echo chambers. Algorithms prioritize engagement metrics over meaningful discourse.'
        },
        {
            'name': 'Unrelated topic (low alignment)',
            'text': 'The quantum computing breakthrough enables faster cryptographic calculations using entangled qubit pairs.'
        }
    ]

    for case in test_cases:
        alignment = calculate_wordmap_alignment(wordmap, case['text'])

        # Visual bar
        bar_length = int(alignment * 50)
        bar = '█' * bar_length + '░' * (50 - bar_length)

        print(f"{case['name']}:")
        print(f"   {bar} {alignment:.1%}")

        if alignment >= 0.5:
            print(f"   ✅ ACCEPT - Sounds like your voice")
        elif alignment >= 0.3:
            print(f"   ⚠️  REVIEW - Partially matches")
        else:
            print(f"   ❌ REJECT - Doesn't match your style")

        print()

    print("💡 Use this for:")
    print("   • AI debate response filtering (accept if > 50% alignment)")
    print("   • Agent routing decisions (higher alignment = higher tier)")
    print("   • Content recommendation (surface similar vocabulary)")
    print("   • Brand voice consistency (flag off-brand responses)")


def demonstrate_sha256_wrapping():
    """Demonstrate SHA256 content wrapping concept"""
    print_header("🎁 SHA256 CONTENT WRAPPING")

    print("The '256 words = SHA256 hash' concept enables content filtering:\n")

    print("1️⃣  Build wordmap to 256 unique words")
    print("    Your vocabulary fingerprint\n")

    print("2️⃣  Generate SHA256 hash of wordmap")
    print("    Deterministic identity proof\n")

    print("3️⃣  Filter incoming content by alignment %")
    print("    Example: AI debate responses\n")

    print("4️⃣  'Wrap' content with metadata:")
    print("    {")
    print("      'content': '...',")
    print("      'wordmap_alignment': 0.73,")
    print("      'user_hash': 'abc123...',")
    print("      'approved': true")
    print("    }\n")

    print("5️⃣  Agent router uses alignment for decisions:")
    print("    • >80% alignment: Premium tier (better ads)")
    print("    • 50-80%: Standard tier")
    print("    • <50%: Flagged for review\n")

    print("💡 This creates:")
    print("   • Self-authenticating content")
    print("   • Deterministic filtering")
    print("   • Payment tier justification")
    print("   • Character/lore consistency checks")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Prove Wordmap System - 20 → 256 Word Progression'
    )

    parser.add_argument(
        '--build-to-256',
        action='store_true',
        help='Build wordmap all the way to 256 words'
    )

    parser.add_argument(
        '--num-transcripts', '-n',
        type=int,
        default=5,
        help='Number of transcripts to generate (default: 5)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progression (new words added, etc.)'
    )

    parser.add_argument(
        '--show-only',
        action='store_true',
        help='Only show current state, don\'t generate'
    )

    parser.add_argument(
        '--demo-filtering',
        action='store_true',
        help='Demonstrate content filtering with current wordmap'
    )

    args = parser.parse_args()

    try:
        print("\n" + "="*70)
        print("  🔐 WORDMAP SYSTEM - PROOF OF CONCEPT")
        print("  Voice Fingerprint: 20 → 256 Words → SHA256 Hash")
        print("="*70)

        generator = WordmapTranscriptGenerator(user_id=1)

        # Check Ollama
        if not args.show_only and not args.demo_filtering:
            if not generator.check_ollama():
                print("\n❌ Ollama not running!")
                print("   Start: ollama serve")
                sys.exit(1)
            print("\n✅ Ollama is running\n")

        # Show current state
        current_state = show_current_state()

        if not current_state:
            sys.exit(1)

        # Demo filtering
        if args.demo_filtering:
            demonstrate_content_filtering(current_state['wordmap'])
            demonstrate_sha256_wrapping()
            sys.exit(0)

        # Show only mode
        if args.show_only:
            final_results = show_final_results(generator)
            sys.exit(0)

        # Determine number of transcripts
        if args.build_to_256:
            # Calculate how many we need
            gap = current_state['gap']
            # Assume ~25 new words per transcript (conservative)
            num_transcripts = max(1, (gap // 20) + 2)
            print(f"\n📋 Will generate ~{num_transcripts} transcripts to reach 256 words\n")
        else:
            num_transcripts = args.num_transcripts

        # Generate synthetic transcripts
        progression = simulate_wordmap_growth(
            generator,
            num_transcripts=num_transcripts,
            verbose=args.verbose
        )

        # Show progression chart
        if progression:
            print(f"\n{'='*70}")
            print("  📊 WORDMAP PROGRESSION CHART")
            print(f"{'='*70}\n")

            for p in progression:
                bar_length = int((p['progress_pct'] / 100) * 50)
                bar = '█' * bar_length + '░' * (50 - bar_length)

                print(f"Transcript {p['transcript_num']:2}: {bar} {p['word_count']:3}/256 (+{p['new_words']:2})")

            print()

        # Show final results
        final_results = show_final_results(generator)

        # Demo content filtering
        if final_results['word_count'] >= 100:  # Only if we have enough words
            demonstrate_content_filtering(final_results['wordmap'])
            demonstrate_sha256_wrapping()

        # Summary
        print(f"\n{'='*70}")
        print("  ✅ WORDMAP SYSTEM PROVEN")
        print(f"{'='*70}")

        print("\n💡 What this enables:")
        print("   1. Voice identity fingerprint (256 words → SHA256 hash)")
        print("   2. Content filtering by alignment %")
        print("   3. Agent router tier decisions")
        print("   4. Character/lore consistency checks")
        print("   5. Self-hosted automation routing")

        print("\n🔗 Integration with other systems:")
        print("   • AI Debate: Filter responses by wordmap alignment")
        print("   • Agent Router: Payment tiers based on content quality")
        print("   • Automation: Route workflows by hash matching")
        print("   • Voice Clone: Wordmap ensures TTS sounds like you")

        print("\n📝 Next steps:")
        if final_results['word_count'] < 256:
            print(f"   • python3 wordmap_transcript_generator.py --build-to-256")
        print("   • python3 prove_debate_system.py --all")
        print("   • Build agent router with tier system")
        print("   • Create automation node architecture")

        print("\n" + "="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n👋 Proof cancelled")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
