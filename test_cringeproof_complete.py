#!/usr/bin/env python3
"""
🧪 Complete CringeProof Pipeline Test
Tests entire workflow: Voice → Whisper → Ollama → Classifier → Site Build

This is what you asked for - full test with local Ollama showing how it all works!
"""

import os
import sys
import sqlite3
import json
import time
import tempfile
import wave
import struct
from pathlib import Path

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PINK = '\033[95m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def print_header(msg):
    print(f"\n{PINK}{'='*70}")
    print(f"  {msg}")
    print(f"{'='*70}{RESET}\n")


class CringeProofTester:
    def __init__(self):
        self.db_path = Path('soulfra.db')
        self.results = []
        self.test_recording_id = None
        self.test_idea_id = None

    def test_1_database(self):
        """Test 1: Database connection and schema"""
        print_header("TEST 1: Database & Brands")

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check brands
            brands = cursor.execute('''
                SELECT id, name, domain, emoji
                FROM brands
                WHERE domain IN ('cringeproof.com', 'soulfra.com', 'deathtodata.com')
            ''').fetchall()

            if len(brands) >= 3:
                print_success(f"Found {len(brands)} brands:")
                for brand in brands:
                    emoji = brand['emoji'] or '�'
                    print_info(f"  {emoji} {brand['name']} ({brand['domain']}) - ID: {brand['id']}")
                self.results.append(('Brands', True, f'{len(brands)} domains'))
            else:
                print_error(f"Only {len(brands)}/3 brands found")
                self.results.append(('Brands', False, 'Missing domains'))
                return False

            # Check domain_wordmaps
            wordmaps = cursor.execute('SELECT domain FROM domain_wordmaps').fetchall()
            print_success(f"Found {len(wordmaps)} domain wordmaps")
            for wm in wordmaps:
                print_info(f"  • {wm['domain']}")

            conn.close()
            return True

        except Exception as e:
            print_error(f"Database error: {e}")
            self.results.append(('Database', False, str(e)))
            return False

    def test_2_classifier(self):
        """Test 2: Domain classifier with test sentences"""
        print_header("TEST 2: Domain Classifier (The Core!)")

        try:
            from classify_idea import classify_idea

            test_cases = [
                ("I hate cringe on social media, be authentic", "cringeproof.com"),
                ("Building infrastructure for human flourishing", "soulfra.com"),
                ("Privacy surveillance capitalism data freedom", "deathtodata.com"),
            ]

            for text, expected_domain in test_cases:
                results = classify_idea(text)

                if results and results[0]['domain'] == expected_domain:
                    score = results[0]['score']
                    matches = ', '.join(results[0]['matches'][:5])
                    print_success(f"'{text[:40]}...' → {expected_domain} ({score:.0%})")
                    print_info(f"  Matches: {matches}")
                    self.results.append((f'Classify: {expected_domain}', True, f'{score:.0%}'))
                else:
                    actual = results[0]['domain'] if results else 'None'
                    print_error(f"Expected {expected_domain}, got {actual}")
                    self.results.append((f'Classify: {expected_domain}', False, f'Got {actual}'))

            return True

        except ImportError as e:
            print_error(f"Classifier not available: {e}")
            self.results.append(('Classifier', False, 'Import error'))
            return False

    def test_3_whisper(self):
        """Test 3: Whisper transcription"""
        print_header("TEST 3: Whisper Transcription")

        try:
            from whisper_transcriber import WhisperTranscriber

            # Create test WAV file (1 second of silence)
            test_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            with wave.open(test_wav.name, 'w') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                # Generate silence
                frames = [0] * 16000
                wav.writeframes(struct.pack(f'{len(frames)}h', *frames))

            transcriber = WhisperTranscriber()
            transcription = transcriber.transcribe(test_wav.name)

            os.unlink(test_wav.name)

            if transcription is not None and len(transcription) > 0:
                print_success(f"Whisper working! Got: '{transcription}'")
                self.results.append(('Whisper', True, 'Transcribed'))
                return True
            else:
                print_warning("Whisper returned empty transcription (expected for silence)")
                self.results.append(('Whisper', True, 'No speech detected'))
                return True

        except ImportError:
            print_warning("Whisper not available (skip)")
            self.results.append(('Whisper', 'SKIP', 'Not installed'))
            return True
        except Exception as e:
            print_error(f"Whisper error: {e}")
            self.results.append(('Whisper', False, str(e)))
            return False

    def test_4_ollama(self):
        """Test 4: Ollama idea extraction"""
        print_header("TEST 4: Ollama Idea Extraction")

        try:
            from ollama_client import OllamaClient
            from voice_idea_board_routes import extract_ideas_from_transcript

            test_transcript = """
            I hate cringe on social media. Everyone's trying to be authentic but it feels fake.
            We need genuine connection, real community where people can be vulnerable and honest.
            """

            # Create test recording
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('''
                INSERT INTO simple_voice_recordings (filename, transcription, file_size, audio_data)
                VALUES (?, ?, ?, ?)
            ''', ('test_pipeline.wav', test_transcript, 1000, b''))

            recording_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.test_recording_id = recording_id

            # Extract ideas
            ideas = extract_ideas_from_transcript(test_transcript, recording_id, user_id=1)

            if ideas and len(ideas) > 0:
                idea = ideas[0]
                self.test_idea_id = idea['id']
                print_success(f"Ollama extracted idea: '{idea['title']}'")
                print_info(f"  Score: {idea.get('score', 'N/A')}")
                print_info(f"  ID: {idea['id']}")
                self.results.append(('Ollama', True, f"Extracted {len(ideas)} ideas"))
                return True
            else:
                print_warning("Ollama didn't extract ideas")
                self.results.append(('Ollama', False, 'No ideas'))
                return False

        except ImportError:
            print_warning("Ollama not available (skip)")
            self.results.append(('Ollama', 'SKIP', 'Not installed'))
            return True
        except Exception as e:
            print_error(f"Ollama error: {e}")
            self.results.append(('Ollama', False, str(e)))
            return False

    def test_5_domain_assignment(self):
        """Test 5: Automatic domain classification"""
        print_header("TEST 5: Automatic Domain Assignment")

        if not self.test_idea_id:
            print_warning("Skipping - no test idea created")
            return True

        try:
            from classify_idea import classify_and_store

            test_transcript = "I hate cringe on social media, we need authentic community"

            # Classify and store
            assigned_domains = classify_and_store(self.test_idea_id, test_transcript)

            # Check database
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            result = conn.execute('''
                SELECT vi.id, vi.title, vi.domain_id, b.name as brand_name, b.domain
                FROM voice_ideas vi
                LEFT JOIN brands b ON vi.domain_id = b.id
                WHERE vi.id = ?
            ''', (self.test_idea_id,)).fetchone()
            conn.close()

            if result and result['domain_id']:
                print_success(f"Idea assigned to: {result['brand_name']} ({result['domain']})")
                print_info(f"  Idea ID: {result['id']}")
                print_info(f"  Domain ID: {result['domain_id']}")
                self.results.append(('Domain Assignment', True, result['domain']))
                return True
            else:
                print_error("Domain not assigned")
                self.results.append(('Domain Assignment', False, 'No domain_id'))
                return False

        except Exception as e:
            print_error(f"Assignment error: {e}")
            self.results.append(('Domain Assignment', False, str(e)))
            return False

    def test_6_site_build(self):
        """Test 6: Static site generation"""
        print_header("TEST 6: Site Build (GitHub Pages)")

        try:
            from build_site import SiteBuilder

            builder = SiteBuilder()

            # Check if voice-archive exists
            if not builder.voice_archive.exists():
                print_warning(f"voice-archive not found at {builder.voice_archive}")
                self.results.append(('Site Build', 'SKIP', 'No voice-archive dir'))
                return True

            # Build ideas page
            builder.build_ideas_hub()

            # Check if file was created
            ideas_page = builder.voice_archive / 'ideas' / 'index.html'
            if ideas_page.exists():
                print_success(f"Ideas page built: {ideas_page}")

                # Check if our test idea is in the page
                content = ideas_page.read_text()
                if self.test_idea_id and f"#{self.test_idea_id}" in content:
                    print_success(f"Test idea #{self.test_idea_id} appears in ideas page!")

                self.results.append(('Site Build', True, 'Pages generated'))
                return True
            else:
                print_error("Ideas page not created")
                self.results.append(('Site Build', False, 'No output'))
                return False

        except Exception as e:
            print_error(f"Site build error: {e}")
            self.results.append(('Site Build', False, str(e)))
            return False

    def test_7_rss_feed(self):
        """Test 7: RSS feed generation"""
        print_header("TEST 7: RSS Feed")

        try:
            from generate_rss import generate_rss

            generate_rss()

            feed_path = Path('voice-archive/feed.xml')
            if feed_path.exists():
                print_success(f"RSS feed generated: {feed_path}")

                # Check if our test recording is in feed
                content = feed_path.read_text()
                if self.test_recording_id and f"<guid>https://cringeproof.com/ideas/{self.test_recording_id}/</guid>" in content:
                    print_success(f"Test recording #{self.test_recording_id} in RSS feed!")

                self.results.append(('RSS Feed', True, 'Generated'))
                return True
            else:
                print_error("RSS feed not created")
                self.results.append(('RSS Feed', False, 'No feed.xml'))
                return False

        except Exception as e:
            print_error(f"RSS generation error: {e}")
            self.results.append(('RSS Feed', False, str(e)))
            return False

    def cleanup(self):
        """Clean up test data"""
        print_header("Cleanup Test Data")

        try:
            conn = sqlite3.connect(self.db_path)

            if self.test_idea_id:
                conn.execute('DELETE FROM voice_ideas WHERE id = ?', (self.test_idea_id,))
                print_info(f"Deleted test idea #{self.test_idea_id}")

            if self.test_recording_id:
                conn.execute('DELETE FROM simple_voice_recordings WHERE id = ?', (self.test_recording_id,))
                print_info(f"Deleted test recording #{self.test_recording_id}")

            conn.commit()
            conn.close()

            print_success("Test data cleaned up")

        except Exception as e:
            print_warning(f"Cleanup error: {e}")

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")

        total = len(self.results)
        passed = len([r for r in self.results if r[1] == True])
        failed = len([r for r in self.results if r[1] == False])
        skipped = len([r for r in self.results if r[1] == 'SKIP'])

        for name, status, details in self.results:
            if status == True:
                print(f"{GREEN}✅ {name:30s} {details}{RESET}")
            elif status == False:
                print(f"{RED}❌ {name:30s} {details}{RESET}")
            else:
                print(f"{YELLOW}⏭️  {name:30s} {details}{RESET}")

        print()
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"Total: {total}  |  {GREEN}Passed: {passed}{RESET}  |  {RED}Failed: {failed}{RESET}  |  {YELLOW}Skipped: {skipped}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}")

        if failed == 0:
            print(f"\n{GREEN}🎉 ALL TESTS PASSED! CringeProof pipeline is working!{RESET}\n")
            return 0
        else:
            print(f"\n{RED}⚠️  {failed} test(s) failed. Check output above.{RESET}\n")
            return 1


def main():
    print(f"\n{PINK}{'='*70}")
    print("  🧪 CRINGEPROOF COMPLETE PIPELINE TEST")
    print("  Tests: Voice → Whisper → Ollama → Classifier → Site Build")
    print(f"{'='*70}{RESET}\n")

    tester = CringeProofTester()

    # Run tests
    tester.test_1_database()
    tester.test_2_classifier()
    tester.test_3_whisper()
    tester.test_4_ollama()
    tester.test_5_domain_assignment()
    tester.test_6_site_build()
    tester.test_7_rss_feed()

    # Summary
    exit_code = tester.print_summary()

    # Cleanup
    print()
    response = input("Clean up test data? (y/n): ")
    if response.lower() == 'y':
        tester.cleanup()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
