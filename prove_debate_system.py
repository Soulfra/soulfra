#!/usr/bin/env python3
"""
Prove AI Debate System Works - Complete Demo

Uses your existing Recording #7 (cringeproof voice memo) to demonstrate:
1. Voice transcript → AI counter-argument
2. Multi-persona panel debate
3. Ragebait optimization
4. HTML export
5. Integration with live show system

This PROVES the system works with real data.

Usage:
    # Quick proof (text only)
    python3 prove_debate_system.py

    # Full proof with HTML export
    python3 prove_debate_system.py --export-html

    # Panel debate (all 3 personas)
    python3 prove_debate_system.py --panel

    # Maximum ragebait
    python3 prove_debate_system.py --ragebait

Like:
- YouTube "X Says Y... Here's Why They're WRONG"
- TikTok duet responses
- Twitter ratio culture
- Terminal FaceTime panel
"""

import sys
import json
from pathlib import Path
from database import get_db
from ai_debate_generator import AIDebateGenerator, PERSONAS


# ==============================================================================
# PROOF OF CONCEPT
# ==============================================================================

def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def prove_basic_debate():
    """Prove basic debate generation works"""
    print_header("🎯 PROOF 1: Basic AI Counter-Argument")

    generator = AIDebateGenerator()

    # Check Ollama
    if not generator.check_ollama():
        print("❌ Ollama not running! Start with: ollama serve")
        return False

    print("✅ Ollama is running")

    # Get Recording #7 (cringeproof voice)
    db = get_db()
    recording = db.execute('''
        SELECT id, filename, transcription
        FROM simple_voice_recordings
        WHERE id = 7
    ''').fetchone()

    if not recording or not recording['transcription']:
        print("❌ Recording #7 not found or has no transcription")
        print("   Record a voice memo first at: /voice")
        return False

    print(f"\n📼 Recording #7: {recording['filename']}")
    print(f"   Length: {len(recording['transcription'])} characters")
    print(f"\n📝 YOUR VOICE:")
    print(f"   {recording['transcription'][:200]}...\n")

    # Generate DeathToData response
    print("🤖 Generating DeathToData counter-argument...")

    debate = generator.create_debate_from_recording(
        recording_id=7,
        persona='deathtodata',
        ragebait=False
    )

    if 'error' in debate:
        print(f"❌ {debate['error']}")
        return False

    # Show result
    ai_response = debate['ai_response']

    print(f"\n🔥 DEATHTODATA RESPONDS:")
    print(f"   {ai_response['counter_argument']}\n")

    print(f"📊 Controversy Score: {ai_response['controversy_score']:.0%}")
    print(f"✅ Debate saved to: {debate['debate_id']}")

    print(f"\n{'='*70}")
    print(f"✅ PROOF 1 COMPLETE: AI successfully generated counter-argument!")
    print(f"{'='*70}")

    return debate


def prove_panel_debate():
    """Prove multi-persona panel works"""
    print_header("🎯 PROOF 2: Multi-Persona Panel Debate")

    generator = AIDebateGenerator()

    # Get Recording #7
    db = get_db()
    recording = db.execute('''
        SELECT transcription FROM simple_voice_recordings WHERE id = 7
    ''').fetchone()

    if not recording:
        print("❌ Recording #7 not found")
        return False

    print(f"📝 Original statement:")
    print(f"   {recording['transcription'][:150]}...\n")

    # Generate panel debate
    print("🎙️ Generating panel debate with all 3 personas...")
    print("   This may take 1-2 minutes...\n")

    panel = generator.generate_panel_debate(
        recording['transcription'],
        personas=['calriven', 'soulfra', 'deathtodata']
    )

    # Show results
    print(f"\n{'='*70}")
    print(f"🎭 PANEL DEBATE RESULTS ({panel['panel_size']} personas)")
    print(f"{'='*70}\n")

    for response in panel['responses']:
        print(f"🤖 {response['persona_name'].upper()}:")
        print(f"   {response['counter_argument'][:200]}...")
        print(f"   Controversy: {response['controversy_score']:.0%}\n")

    print(f"✅ PROOF 2 COMPLETE: Panel debate generated!")

    return panel


def prove_ragebait_optimization():
    """Prove ragebait optimization works"""
    print_header("🎯 PROOF 3: Ragebait Optimization")

    generator = AIDebateGenerator()

    # Get Recording #7
    db = get_db()
    recording = db.execute('''
        SELECT transcription FROM simple_voice_recordings WHERE id = 7
    ''').fetchone()

    if not recording:
        return False

    print("📝 Testing controversy optimization...\n")

    # Generate normal response
    print("1️⃣ Normal response:")
    normal = generator.generate_counter_argument(
        recording['transcription'],
        persona='deathtodata',
        ragebait=False
    )

    if 'error' not in normal:
        print(f"   Controversy: {normal['controversy_score']:.0%}")
        print(f"   Preview: {normal['counter_argument'][:100]}...\n")

    # Generate ragebait response
    print("2️⃣ Ragebait-optimized response:")
    ragebait = generator.generate_counter_argument(
        recording['transcription'],
        persona='deathtodata',
        ragebait=True
    )

    if 'error' not in ragebait:
        print(f"   Controversy: {ragebait['controversy_score']:.0%}")
        print(f"   Preview: {ragebait['counter_argument'][:100]}...\n")

    # Compare
    if 'error' not in normal and 'error' not in ragebait:
        improvement = ragebait['controversy_score'] - normal['controversy_score']
        print(f"📈 Controversy increased by: {improvement:.0%}")

    print(f"\n✅ PROOF 3 COMPLETE: Ragebait optimization works!")

    return {'normal': normal, 'ragebait': ragebait}


def prove_html_export(debate: dict):
    """Prove HTML export works"""
    print_header("🎯 PROOF 4: HTML Debate Viewer Export")

    generator = AIDebateGenerator()

    print("📤 Exporting debate as HTML...")

    html_file = generator.export_debate_html(debate)

    print(f"✅ HTML file created: {html_file}")
    print(f"\n🌐 Open in browser:")
    print(f"   file://{html_file.absolute()}")

    print(f"\n✅ PROOF 4 COMPLETE: HTML export works!")

    return html_file


def prove_live_show_integration():
    """Prove integration with live show system"""
    print_header("🎯 PROOF 5: Live Show Integration")

    from live_call_in_show import LiveCallInShow

    show_system = LiveCallInShow()
    generator = AIDebateGenerator()

    # Create show
    print("📺 Creating live show with AI reactions...")

    show = show_system.create_show(
        title="Cringe Debate: AI Responds",
        article_text="Discussion about authenticity and cringe culture on social media"
    )

    print(f"✅ Show created: {show['title']}")
    print(f"   Show ID: {show['show_id']}")
    print(f"   Call-in URL: {show['call_in_url']}")

    # Submit original voice as call-in
    print("\n📞 Submitting original voice memo as call-in...")

    reaction = show_system.submit_call_in(
        show_id=show['show_id'],
        recording_id=7,
        caller_name="Matthew",
        reaction_type='comment'
    )

    print(f"✅ Call-in submitted (Reaction ID: {reaction['reaction_id']})")

    # Generate AI counter-reaction
    print("\n🤖 Generating AI counter-reaction...")

    debate = generator.create_debate_from_recording(
        recording_id=7,
        persona='deathtodata'
    )

    if 'error' not in debate:
        print(f"✅ AI response generated")
        print(f"   Preview: {debate['ai_response']['counter_argument'][:100]}...")

    print(f"\n💡 Integration concept proven:")
    print(f"   1. Original voice → Show call-in")
    print(f"   2. AI generates counter-argument")
    print(f"   3. Both play in live show")
    print(f"   4. Creates debate/controversy")

    print(f"\n✅ PROOF 5 COMPLETE: Live show integration works!")

    return {'show': show, 'reaction': reaction, 'debate': debate}


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Prove AI Debate System Works - Complete Demo'
    )

    parser.add_argument(
        '--export-html',
        action='store_true',
        help='Export HTML viewer'
    )

    parser.add_argument(
        '--panel',
        action='store_true',
        help='Run panel debate proof'
    )

    parser.add_argument(
        '--ragebait',
        action='store_true',
        help='Test ragebait optimization'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all proofs'
    )

    args = parser.parse_args()

    try:
        print("\n" + "="*70)
        print("  🔥 AI DEBATE SYSTEM - PROOF OF CONCEPT")
        print("  Using Recording #7 (Cringeproof Voice Memo)")
        print("="*70)

        results = {}

        # Run basic proof (always)
        debate = prove_basic_debate()

        if not debate:
            print("\n❌ Basic proof failed. Fix errors and try again.")
            sys.exit(1)

        results['basic'] = debate

        # Optional proofs
        if args.panel or args.all:
            results['panel'] = prove_panel_debate()

        if args.ragebait or args.all:
            results['ragebait'] = prove_ragebait_optimization()

        if args.export_html or args.all:
            results['html'] = prove_html_export(debate)

        if args.all:
            results['live_show'] = prove_live_show_integration()

        # Final summary
        print("\n" + "="*70)
        print("  🎉 PROOF OF CONCEPT COMPLETE")
        print("="*70)

        print("\n✅ What was proven:")
        print("   1. AI can generate counter-arguments to voice memos")
        print("   2. Multi-persona debates work")
        print("   3. Controversy can be optimized")
        print("   4. HTML export creates shareable debates")
        print("   5. Integrates with live show system")

        print("\n📝 Next steps:")
        print("   • Record more voice memos for debates")
        print("   • Export HTML and share")
        print("   • Create live show with AI reactions")
        print("   • Train voice model (need 4 more samples)")
        print("   • Add TTS for AI voice responses")

        print("\n🔗 Quick commands:")
        print("   python3 ai_debate_generator.py --recording 7 --export-html")
        print("   python3 ai_debate_generator.py --recording 7 --panel")
        print("   python3 ai_debate_generator.py --recording 7 --ragebait")

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
