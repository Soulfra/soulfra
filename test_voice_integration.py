#!/usr/bin/env python3
"""
Voice Integration Test Harness
===============================

Test the full voice pipeline with existing webm files:
1. Load webm from file/folder
2. Transcribe with Whisper
3. Analyze with Ollama
4. Score quality
5. Generate questions
6. Store in database

Usage:
    # Test single file
    python3 test_voice_integration.py --file recording.webm

    # Test all files in folder
    python3 test_voice_integration.py --folder recordings/

    # Test with specific user
    python3 test_voice_integration.py --file test.webm --user-id 5

    # Test question answering flow
    python3 test_voice_integration.py --file answer.webm --question-id 10
"""

import argparse
import os
import glob
from pathlib import Path
from typing import List, Dict
from database import get_db
from datetime import datetime


def test_single_file(file_path: str, user_id: int = 1, question_id: int = None) -> Dict:
    """
    Test voice integration with a single webm file

    Args:
        file_path: Path to webm file
        user_id: User ID for database
        question_id: Optional question ID for answer testing

    Returns:
        Results dict with all pipeline outputs
    """
    print(f"\n{'='*80}")
    print(f"🎙️  Testing Voice Integration")
    print(f"{'='*80}\n")

    if not os.path.exists(file_path):
        return {'error': f'File not found: {file_path}'}

    # Read file
    print(f"📂 Loading: {file_path}")
    with open(file_path, 'rb') as f:
        audio_data = f.read()

    file_size = len(audio_data)
    print(f"   Size: {file_size} bytes ({file_size/1024:.1f} KB)\n")

    # Step 1: Transcribe with Whisper
    print("🎯 Step 1: Whisper Transcription")
    transcription = None
    transcription_method = None

    try:
        from whisper_transcriber import WhisperTranscriber

        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(file_path)

        transcription = result['text']
        transcription_method = result['backend']

        print(f"   ✅ Transcribed with {transcription_method}")
        print(f"   Text: {transcription[:100]}...")
        print()

    except Exception as e:
        print(f"   ❌ Transcription failed: {e}")
        print(f"   (Install: pip install openai-whisper)\n")
        transcription = "[NO TRANSCRIPTION]"
        transcription_method = "none"

    # Save to database
    print("💾 Step 2: Save to Database")
    db = get_db()

    filename = f"test_{Path(file_path).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"

    cursor = db.execute('''
        INSERT INTO simple_voice_recordings (filename, audio_data, file_size, transcription, transcription_method, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, audio_data, file_size, transcription, transcription_method, user_id))

    recording_id = cursor.lastrowid
    db.commit()
    db.close()

    print(f"   ✅ Saved as recording #{recording_id}\n")

    # Step 3: AI Analysis with Ollama
    print("🤖 Step 3: Ollama AI Analysis")
    analysis = {}

    if transcription and transcription != "[NO TRANSCRIPTION]":
        try:
            from voice_ollama_processor import VoiceOllamaProcessor

            processor = VoiceOllamaProcessor()
            analysis = processor.analyze_recording(recording_id)

            if 'error' not in analysis:
                print(f"   ✅ Analysis complete")
                print(f"   Sentiment: {analysis.get('sentiment', 'unknown')}")
                print(f"   Quality Score: {analysis.get('quality_score', 0)}/100")
                print(f"   Key Topics: {', '.join(analysis.get('key_topics', [])[:3])}")
                print()
            else:
                print(f"   ❌ Analysis failed: {analysis['error']}\n")

        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            print(f"   (Make sure Ollama is running: ollama serve)\n")
    else:
        print(f"   ⏭️  Skipped (no transcription)\n")

    # Step 4: Question Integration (if question_id provided)
    if question_id:
        print(f"📝 Step 4: Answer Question #{question_id}")

        try:
            db = get_db()

            # Get question
            question = db.execute('''
                SELECT question_text, theme, xp_reward
                FROM voice_questions
                WHERE id = ?
            ''', (question_id,)).fetchone()

            if question:
                print(f"   Question: {question['question_text']}")
                print(f"   Theme: {question['theme']}")

                # Calculate XP
                base_xp = question['xp_reward'] or 10
                quality_bonus = 0

                if 'quality_score' in analysis:
                    quality_score = analysis['quality_score']
                    if quality_score >= 80:
                        quality_bonus = 15
                    elif quality_score >= 60:
                        quality_bonus = 10
                    elif quality_score >= 40:
                        quality_bonus = 5

                total_xp = base_xp + quality_bonus

                # Store answer
                db.execute('''
                    INSERT INTO voice_answers (user_id, question_id, answer_text, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, question_id, transcription, datetime.now().isoformat()))

                db.commit()

                print(f"   ✅ Answer recorded")
                print(f"   XP: {base_xp} (base) + {quality_bonus} (quality) = {total_xp} total\n")

            else:
                print(f"   ❌ Question {question_id} not found\n")

            db.close()

        except Exception as e:
            print(f"   ❌ Failed: {e}\n")

    # Step 5: Quality Check
    print("🔍 Step 5: Audio Quality Analysis")

    try:
        from audio_quality import AudioQualityAnalyzer

        analyzer = AudioQualityAnalyzer()
        quality_result = analyzer.analyze_file(file_path)

        print(f"   Duration: {quality_result.get('duration', 0)}s")
        print(f"   Bit Rate: {quality_result.get('bit_rate', 0)} bps")
        print(f"   Quality Score: {quality_result.get('quality_score', 0)}/100")
        print(f"   Usable: {'Yes' if quality_result.get('is_usable') else 'No'}")
        print()

    except Exception as e:
        print(f"   ⏭️  Skipped: {e}\n")

    # Summary
    print(f"{'='*80}")
    print("📊 Test Summary")
    print(f"{'='*80}")
    print(f"Recording ID: {recording_id}")
    print(f"Transcription: {'✅ Success' if transcription != '[NO TRANSCRIPTION]' else '❌ Failed'}")
    print(f"AI Analysis: {'✅ Complete' if analysis and 'error' not in analysis else '❌ Failed'}")
    print(f"Question Answered: {'✅ Yes' if question_id else '⏭️  Skipped'}")
    print()

    return {
        'recording_id': recording_id,
        'transcription': transcription,
        'analysis': analysis,
        'file_path': file_path,
        'file_size': file_size
    }


def test_folder(folder_path: str, user_id: int = 1) -> List[Dict]:
    """
    Test all webm files in a folder

    Args:
        folder_path: Path to folder with webm files
        user_id: User ID for database

    Returns:
        List of result dicts
    """
    print(f"\n{'='*80}")
    print(f"📁 Batch Testing Voice Integration")
    print(f"{'='*80}\n")

    # Find all webm files
    pattern = os.path.join(folder_path, '*.webm')
    webm_files = glob.glob(pattern)

    if not webm_files:
        print(f"❌ No .webm files found in {folder_path}\n")
        return []

    print(f"Found {len(webm_files)} webm files\n")

    results = []
    for i, file_path in enumerate(webm_files, 1):
        print(f"\n--- File {i}/{len(webm_files)} ---")
        result = test_single_file(file_path, user_id)
        results.append(result)

    # Batch summary
    print(f"\n{'='*80}")
    print("📊 Batch Summary")
    print(f"{'='*80}")
    print(f"Total Files: {len(results)}")
    print(f"Transcribed: {sum(1 for r in results if r.get('transcription') != '[NO TRANSCRIPTION]')}")
    print(f"Analyzed: {sum(1 for r in results if r.get('analysis') and 'error' not in r.get('analysis', {}))}")
    print()

    return results


def export_results(results: List[Dict], output_file: str = 'voice_test_results.json'):
    """Export test results to JSON"""
    import json

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"✅ Results exported to {output_file}\n")


def main():
    parser = argparse.ArgumentParser(description="Test Voice Integration Pipeline")
    parser.add_argument('--file', type=str, help='Test single webm file')
    parser.add_argument('--folder', type=str, help='Test all webm files in folder')
    parser.add_argument('--user-id', type=int, default=1, help='User ID for database')
    parser.add_argument('--question-id', type=int, help='Question ID to answer')
    parser.add_argument('--export', type=str, help='Export results to JSON file')

    args = parser.parse_args()

    if args.file:
        # Test single file
        result = test_single_file(args.file, args.user_id, args.question_id)

        if args.export:
            export_results([result], args.export)

    elif args.folder:
        # Test folder
        results = test_folder(args.folder, args.user_id)

        if args.export:
            export_results(results, args.export)

    else:
        # Show usage
        parser.print_help()
        print("\nExamples:")
        print("  python3 test_voice_integration.py --file recording.webm")
        print("  python3 test_voice_integration.py --folder recordings/")
        print("  python3 test_voice_integration.py --file test.webm --question-id 5")
        print("  python3 test_voice_integration.py --folder recordings/ --export results.json")


if __name__ == '__main__':
    main()
