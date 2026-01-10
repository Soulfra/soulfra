#!/usr/bin/env python3
"""
Hex to Media Transformation - SHA256 → Music & Sound

Like your quote: "we're so close to getting the hex codes into music and other things"

Transforms SHA256 hashes and hex data into:
1. Musical notes (deterministic composition from hash)
2. Sound patterns (wordmap → audio fingerprint)
3. MIDI sequences (hex → melody)
4. Rhythmic patterns (hash bits → beats)

Usage:
    # Convert SHA256 hash to music
    python3 hex_to_media.py --hash <SHA256_HASH> --to-music

    # Convert user's wordmap signature to MIDI
    python3 hex_to_media.py --wordmap-to-music

    # Generate audio fingerprint from voice signature
    python3 hex_to_media.py --audio-fingerprint

    # Create rhythmic pattern from hash
    python3 hex_to_media.py --hash <HASH> --to-rhythm

Like:
- Deterministic: Same hash = Same melody
- Voice signature → Musical signature
- Hex codes as creative medium
- Offline-first audio generation
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ==============================================================================
# CONFIG
# ==============================================================================

MEDIA_OUTPUT_DIR = Path('./media_output')
MEDIA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Musical scale (C Major for simplicity)
NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
CHROMATIC_NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# MIDI note numbers (Middle C = 60)
MIDI_BASE = 60

# Frequencies (Hz) for notes
NOTE_FREQUENCIES = {
    'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
    'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
    'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88
}


# ==============================================================================
# HEX TO MUSIC CONVERTER
# ==============================================================================

class HexToMediaConverter:
    """Convert hex data (SHA256 hashes) to music and sound"""

    def __init__(self):
        pass

    def hash_to_notes(self, hash_str: str, num_notes: int = 16) -> List[Dict]:
        """
        Convert SHA256 hash to musical notes

        Args:
            hash_str: SHA256 hash (64 hex chars)
            num_notes: Number of notes to generate

        Returns:
            List of note dicts: [{'note': 'C', 'octave': 4, 'duration': 0.5}, ...]
        """
        # Take first num_notes * 2 hex chars
        hex_data = hash_str[:num_notes * 2]

        notes = []

        for i in range(num_notes):
            # Get 2 hex chars
            hex_pair = hex_data[i*2:(i*2)+2]
            byte_val = int(hex_pair, 16)

            # Map to note (0-255 → 0-11 chromatic scale)
            note_index = byte_val % 12
            note = CHROMATIC_NOTES[note_index]

            # Map to octave (3-6)
            octave = 3 + (byte_val % 4)

            # Map to duration (0.25, 0.5, 1.0, 2.0 beats)
            duration_map = [0.25, 0.5, 1.0, 2.0]
            duration = duration_map[byte_val % 4]

            notes.append({
                'note': note,
                'octave': octave,
                'duration': duration,
                'midi_note': MIDI_BASE + (octave - 4) * 12 + note_index,
                'frequency': NOTE_FREQUENCIES[note] * (2 ** (octave - 4)),
                'hex_source': hex_pair
            })

        return notes

    def hash_to_rhythm(self, hash_str: str, num_beats: int = 16) -> List[int]:
        """
        Convert hash to rhythmic pattern (1 = beat, 0 = rest)

        Args:
            hash_str: SHA256 hash
            num_beats: Number of beats

        Returns:
            List of 1s and 0s representing beats
        """
        # Convert hash to binary
        hash_int = int(hash_str[:16], 16)  # Use first 16 hex chars
        binary = format(hash_int, '064b')  # 64 bits

        # Take first num_beats bits
        rhythm = []
        for i in range(num_beats):
            bit = int(binary[i % len(binary)])
            rhythm.append(bit)

        return rhythm

    def wordmap_to_melody(self, wordmap: Dict[str, int]) -> List[Dict]:
        """
        Convert wordmap to melody based on word frequencies

        Args:
            wordmap: User's wordmap {word: frequency}

        Returns:
            List of notes
        """
        # Sort words by frequency
        sorted_words = sorted(wordmap.items(), key=lambda x: x[1], reverse=True)

        notes = []

        for i, (word, freq) in enumerate(sorted_words[:16]):  # Top 16 words
            # Map frequency to note intensity/duration
            # Higher frequency = longer note
            duration = min(freq * 0.1, 2.0)  # Max 2 beats

            # Map word to note (hash word to get consistent note)
            word_hash = hashlib.md5(word.encode()).hexdigest()
            byte_val = int(word_hash[:2], 16)

            note_index = byte_val % 12
            note = CHROMATIC_NOTES[note_index]

            octave = 4 + (i % 3)  # Vary octave across melody

            notes.append({
                'note': note,
                'octave': octave,
                'duration': duration,
                'word': word,
                'frequency': freq,
                'midi_note': MIDI_BASE + (octave - 4) * 12 + note_index
            })

        return notes

    def generate_midi_file(self, notes: List[Dict], output_file: Path, tempo: int = 120):
        """
        Generate MIDI file from notes

        Args:
            notes: List of note dicts
            output_file: Output MIDI file path
            tempo: BPM (beats per minute)

        Note: Requires python-midi or mido library
        For simplicity, this creates a simple MIDI-like JSON representation
        """
        midi_data = {
            'tempo': tempo,
            'time_signature': '4/4',
            'tracks': [{
                'name': 'Main',
                'notes': notes
            }],
            'total_duration': sum(n['duration'] for n in notes),
            'generated_at': datetime.now().isoformat()
        }

        # Save as JSON (would need midi library for actual MIDI)
        output_file.write_text(json.dumps(midi_data, indent=2))

        print(f"💾 MIDI data saved to: {output_file}")
        print(f"   Notes: {len(notes)}")
        print(f"   Duration: {midi_data['total_duration']:.1f} beats")
        print(f"   Tempo: {tempo} BPM")

        return midi_data

    def generate_audio_script(self, notes: List[Dict], output_file: Path):
        """
        Generate shell script to create audio using sox/ffmpeg

        Args:
            notes: List of note dicts
            output_file: Output script file

        This generates a bash script that uses `sox` to synthesize audio
        """
        script_lines = [
            '#!/bin/bash',
            '# Generated audio synthesis script',
            '# Requires: sox (brew install sox)',
            '',
            'echo "Generating audio from notes..."',
            ''
        ]

        temp_files = []

        for i, note in enumerate(notes):
            freq = note['frequency']
            duration = note['duration'] * 0.5  # Convert beats to seconds (120 BPM)
            temp_file = f'note_{i}.wav'
            temp_files.append(temp_file)

            # Generate sine wave for note
            script_lines.append(
                f'sox -n -r 44100 {temp_file} synth {duration} sine {freq} fade 0.01 {duration} 0.01'
            )

        # Concatenate all notes
        output_audio = 'output.wav'
        script_lines.append(f'\necho "Concatenating {len(notes)} notes..."')
        script_lines.append(f'sox {" ".join(temp_files)} {output_audio}')

        # Cleanup
        script_lines.append('\necho "Cleaning up temp files..."')
        script_lines.append(f'rm {" ".join(temp_files)}')

        script_lines.append(f'\necho "✅ Audio generated: {output_audio}"')

        # Write script
        output_file.write_text('\n'.join(script_lines))
        output_file.chmod(0o755)  # Make executable

        print(f"📜 Audio script saved to: {output_file}")
        print(f"   Run: ./{output_file.name}")
        print(f"   Requires: sox (brew install sox)")

        return output_file

    def visualize_notes(self, notes: List[Dict]):
        """Print ASCII visualization of notes"""
        print(f"\n{'='*70}")
        print("  🎵 NOTE VISUALIZATION")
        print(f"{'='*70}\n")

        for i, note in enumerate(notes, 1):
            note_str = f"{note['note']}{note['octave']}"
            duration_bar = '█' * int(note['duration'] * 4)

            # Show source data if available
            source = ''
            if 'hex_source' in note:
                source = f" (hex: {note['hex_source']})"
            elif 'word' in note:
                source = f" (word: {note['word']})"

            print(f"{i:2}. {note_str:4} {duration_bar:8} {note['duration']:.2f} beats{source}")

        print()

    def hash_to_audio_fingerprint(self, hash_str: str) -> Dict:
        """
        Create audio fingerprint from SHA256 hash

        Args:
            hash_str: SHA256 hash

        Returns:
            Audio fingerprint data
        """
        # Generate melody from hash
        notes = self.hash_to_notes(hash_str, num_notes=32)

        # Generate rhythm from hash
        rhythm = self.hash_to_rhythm(hash_str, num_beats=32)

        # Combine into structured fingerprint
        fingerprint = {
            'hash': hash_str,
            'melody': notes,
            'rhythm': rhythm,
            'tempo': 120,
            'total_duration': sum(n['duration'] for n in notes),
            'unique_notes': len(set(n['note'] for n in notes)),
            'generated_at': datetime.now().isoformat()
        }

        return fingerprint


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Hex to Media - SHA256 → Music & Sound'
    )

    parser.add_argument(
        '--hash',
        type=str,
        metavar='SHA256',
        help='SHA256 hash to convert'
    )

    parser.add_argument(
        '--wordmap-to-music',
        action='store_true',
        help='Convert user wordmap to music'
    )

    parser.add_argument(
        '--audio-fingerprint',
        action='store_true',
        help='Generate audio fingerprint from voice signature'
    )

    parser.add_argument(
        '--to-music',
        action='store_true',
        help='Convert to musical notes'
    )

    parser.add_argument(
        '--to-rhythm',
        action='store_true',
        help='Convert to rhythmic pattern'
    )

    parser.add_argument(
        '--to-midi',
        action='store_true',
        help='Generate MIDI file'
    )

    parser.add_argument(
        '--to-audio',
        action='store_true',
        help='Generate audio synthesis script'
    )

    parser.add_argument(
        '--num-notes',
        type=int,
        default=16,
        help='Number of notes to generate (default: 16)'
    )

    parser.add_argument(
        '--user-id',
        type=int,
        default=1,
        help='User ID for wordmap (default: 1)'
    )

    args = parser.parse_args()

    converter = HexToMediaConverter()

    try:
        # Wordmap to music
        if args.wordmap_to_music:
            print(f"\n{'='*70}")
            print("  🎵 WORDMAP → MUSIC")
            print(f"{'='*70}\n")

            from user_wordmap_engine import get_user_wordmap

            wordmap_data = get_user_wordmap(args.user_id)

            if not wordmap_data:
                print("❌ No wordmap found. Create by recording voice memos.")
                sys.exit(1)

            wordmap = wordmap_data['wordmap']

            print(f"Wordmap size: {len(wordmap)} words")
            print(f"Converting top {min(16, len(wordmap))} words to melody...\n")

            notes = converter.wordmap_to_melody(wordmap)

            converter.visualize_notes(notes)

            # Generate MIDI
            if args.to_midi or True:  # Always generate
                midi_file = MEDIA_OUTPUT_DIR / f'wordmap_melody_{args.user_id}.json'
                converter.generate_midi_file(notes, midi_file)

            # Generate audio script
            if args.to_audio:
                audio_script = MEDIA_OUTPUT_DIR / f'wordmap_audio_{args.user_id}.sh'
                converter.generate_audio_script(notes, audio_script)

        # Audio fingerprint
        elif args.audio_fingerprint:
            print(f"\n{'='*70}")
            print("  🔊 VOICE SIGNATURE → AUDIO FINGERPRINT")
            print(f"{'='*70}\n")

            from sha256_content_wrapper import SHA256ContentWrapper

            wrapper = SHA256ContentWrapper(user_id=args.user_id)
            hash_str = wrapper.signature_hash

            print(f"Voice signature: {hash_str[:16]}...")
            print(f"Generating audio fingerprint...\n")

            fingerprint = converter.hash_to_audio_fingerprint(hash_str)

            print(f"✅ Fingerprint generated:")
            print(f"   Total duration: {fingerprint['total_duration']:.1f} beats")
            print(f"   Unique notes: {fingerprint['unique_notes']}")
            print(f"   Tempo: {fingerprint['tempo']} BPM\n")

            converter.visualize_notes(fingerprint['melody'][:16])

            # Save fingerprint
            fingerprint_file = MEDIA_OUTPUT_DIR / f'voice_fingerprint_{args.user_id}.json'
            fingerprint_file.write_text(json.dumps(fingerprint, indent=2))
            print(f"💾 Saved to: {fingerprint_file}")

            # Generate audio script
            if args.to_audio:
                audio_script = MEDIA_OUTPUT_DIR / f'voice_fingerprint_{args.user_id}.sh'
                converter.generate_audio_script(fingerprint['melody'], audio_script)

        # Hash to music
        elif args.hash:
            print(f"\n{'='*70}")
            print("  🔐 SHA256 → MUSIC")
            print(f"{'='*70}\n")

            print(f"Hash: {args.hash[:32]}...")
            print(f"Generating {args.num_notes} notes...\n")

            if args.to_music or args.to_midi or args.to_audio:
                notes = converter.hash_to_notes(args.hash, args.num_notes)
                converter.visualize_notes(notes)

                if args.to_midi:
                    midi_file = MEDIA_OUTPUT_DIR / f'hash_melody_{int(datetime.now().timestamp())}.json'
                    converter.generate_midi_file(notes, midi_file)

                if args.to_audio:
                    audio_script = MEDIA_OUTPUT_DIR / f'hash_audio_{int(datetime.now().timestamp())}.sh'
                    converter.generate_audio_script(notes, audio_script)

            if args.to_rhythm:
                rhythm = converter.hash_to_rhythm(args.hash, args.num_notes)

                print(f"🥁 RHYTHM PATTERN\n")
                print(f"Pattern: {' '.join(['X' if b else '.' for b in rhythm])}")
                print(f"Beats: {sum(rhythm)}/{len(rhythm)}\n")

        else:
            parser.print_help()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
