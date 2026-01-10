#!/usr/bin/env python3
"""
Voice Clone Trainer - Train TTS model on your voice

Uses your existing voice recordings to create a personalized TTS model
that sounds like YOU. Offline-first, privacy-focused.

Features:
- Export voice samples from database
- Train Piper TTS on your voice
- A/B test model versions
- Iterative improvement

Usage:
    # Export samples from database
    python3 voice_clone_trainer.py --export --min-samples 10

    # Train voice model
    python3 voice_clone_trainer.py --train

    # Generate speech with your voice
    python3 voice_clone_trainer.py --synthesize "Hello, this is my voice"

    # A/B test model versions
    python3 voice_clone_trainer.py --ab-test "Test phrase"
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import subprocess


class VoiceCloneTrainer:
    """Train TTS model on your voice recordings"""

    def __init__(self, db_path: str = "soulfra.db"):
        self.db_path = db_path
        self.samples_dir = Path("voice_samples")
        self.models_dir = Path("voice_models")
        self.samples_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)

    def export_samples_from_db(self, min_duration: float = 2.0,
                               max_samples: int = 50) -> List[Path]:
        """
        Export voice recordings from database as training samples

        Args:
            min_duration: Minimum duration in seconds
            max_samples: Maximum number of samples to export

        Returns:
            List of exported file paths
        """
        print(f"\n📤 Exporting voice samples from database...")
        print(f"   Min duration: {min_duration}s")
        print(f"   Max samples: {max_samples}")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Get recordings with transcriptions
        cursor = conn.execute('''
            SELECT id, filename, audio_data, transcription, created_at
            FROM simple_voice_recordings
            WHERE transcription IS NOT NULL
            ORDER BY id DESC
            LIMIT ?
        ''', (max_samples,))

        recordings = cursor.fetchall()
        conn.close()

        if not recordings:
            print("   ❌ No recordings found with transcriptions")
            return []

        print(f"   Found {len(recordings)} recordings")

        exported = []

        for rec in recordings:
            # Save audio file
            audio_path = self.samples_dir / f"sample_{rec['id']}.wav"

            with open(audio_path, 'wb') as f:
                f.write(rec['audio_data'])

            # Save transcription (for training)
            transcript_path = self.samples_dir / f"sample_{rec['id']}.txt"

            with open(transcript_path, 'w') as f:
                f.write(rec['transcription'])

            exported.append(audio_path)

            print(f"   ✅ Exported: {audio_path.name}")
            print(f"      Transcript: {rec['transcription'][:50]}...")

        print(f"\n✅ Exported {len(exported)} samples to {self.samples_dir}")

        return exported

    def analyze_voice_characteristics(self, sample_paths: List[Path]) -> Dict:
        """
        Analyze voice characteristics from samples

        Args:
            sample_paths: List of audio file paths

        Returns:
            Voice profile dict
        """
        print(f"\n🔍 Analyzing voice characteristics...")

        # This is a simplified version
        # In production, use librosa or similar for real analysis

        profile = {
            'sample_count': len(sample_paths),
            'analyzed_at': datetime.now().isoformat(),
            'characteristics': {
                'pitch': 'medium',  # Would be calculated
                'speed': 'normal',  # Would be calculated
                'tone': 'neutral'   # Would be calculated
            }
        }

        # Save profile
        profile_path = self.models_dir / "voice_profile.json"

        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)

        print(f"   Samples analyzed: {profile['sample_count']}")
        print(f"   Profile saved: {profile_path}")

        return profile

    def train_piper_model(self, force: bool = False) -> Dict:
        """
        Train Piper TTS model on voice samples

        Args:
            force: Force retrain even if model exists

        Returns:
            Training result dict
        """
        print(f"\n🎓 Training Piper TTS model on your voice...")

        model_path = self.models_dir / "matthew_voice.ckpt"

        if model_path.exists() and not force:
            print(f"   ⚠️  Model already exists: {model_path}")
            print(f"   Use --force to retrain")
            return {'error': 'Model exists', 'path': str(model_path)}

        # Check for samples
        samples = list(self.samples_dir.glob("*.wav"))

        if len(samples) < 10:
            print(f"   ❌ Need at least 10 samples (have {len(samples)})")
            return {'error': 'Not enough samples', 'count': len(samples)}

        print(f"   Training on {len(samples)} samples...")

        # NOTE: This is a simplified training process
        # Real Piper training requires:
        # 1. Audio preprocessing
        # 2. Feature extraction
        # 3. Model training (takes hours/days)
        # 4. Model export

        # For now, we'll create a placeholder and document the full process

        result = {
            'status': 'placeholder',
            'message': 'Training requires full Piper setup',
            'samples': len(samples),
            'model_path': str(model_path),
            'next_steps': [
                '1. Install Piper training tools',
                '2. Preprocess audio samples',
                '3. Train model (8-24 hours on GPU)',
                '4. Export ONNX model for inference'
            ]
        }

        # Create placeholder
        model_path.touch()

        print(f"\n   ⚠️  Placeholder model created")
        print(f"   📝 Full training requires Piper setup")
        print(f"   See: VOICE_CLONE_SETUP.md")

        return result

    def synthesize_speech(self, text: str, model_name: str = "matthew_voice") -> Optional[Path]:
        """
        Generate speech using trained voice model

        Args:
            text: Text to synthesize
            model_name: Voice model to use

        Returns:
            Path to generated audio file
        """
        print(f"\n🗣️  Synthesizing speech...")
        print(f"   Text: {text}")
        print(f"   Model: {model_name}")

        output_path = Path(f"output_{int(datetime.now().timestamp())}.wav")

        # Check if Piper is available
        try:
            # Try using Piper TTS
            cmd = [
                'piper',
                '--model', f'{model_name}.onnx',
                '--output_file', str(output_path)
            ]

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(input=text)

            if process.returncode == 0:
                print(f"   ✅ Speech generated: {output_path}")
                return output_path
            else:
                print(f"   ❌ Piper error: {stderr}")
                return None

        except FileNotFoundError:
            print(f"   ❌ Piper not found. Install: pip install piper-tts")
            return None

    def ab_test_models(self, text: str, model_a: str, model_b: str) -> Dict:
        """
        Generate speech with two models for A/B comparison

        Args:
            text: Test phrase
            model_a: First model name
            model_b: Second model name

        Returns:
            Test result dict with file paths
        """
        print(f"\n🔬 A/B Testing Models...")
        print(f"   Model A: {model_a}")
        print(f"   Model B: {model_b}")
        print(f"   Phrase: {text}")

        audio_a = self.synthesize_speech(text, model_a)
        audio_b = self.synthesize_speech(text, model_b)

        result = {
            'text': text,
            'model_a': model_a,
            'model_b': model_b,
            'audio_a': str(audio_a) if audio_a else None,
            'audio_b': str(audio_b) if audio_b else None
        }

        if audio_a and audio_b:
            print(f"\n   ✅ Both models generated audio")
            print(f"   🎧 Listen and compare:")
            print(f"      A: {audio_a}")
            print(f"      B: {audio_b}")
            print(f"\n   Which sounds closer to your voice?")
        else:
            print(f"   ❌ Generation failed")

        return result

    def export_training_dataset(self) -> Path:
        """Export complete training dataset with metadata"""
        print(f"\n📦 Exporting training dataset...")

        dataset_dir = Path("voice_dataset")
        dataset_dir.mkdir(exist_ok=True)

        # Copy samples
        for sample in self.samples_dir.glob("*.wav"):
            dest = dataset_dir / sample.name
            dest.write_bytes(sample.read_bytes())

        for transcript in self.samples_dir.glob("*.txt"):
            dest = dataset_dir / transcript.name
            dest.write_bytes(transcript.read_bytes())

        # Create metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'sample_count': len(list(self.samples_dir.glob("*.wav"))),
            'format': 'wav',
            'transcriptions_included': True
        }

        with open(dataset_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"   ✅ Dataset exported to: {dataset_dir}")

        return dataset_dir


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Voice Clone Trainer')
    parser.add_argument('--export', action='store_true', help='Export samples from database')
    parser.add_argument('--min-samples', type=int, default=10, help='Minimum samples needed')
    parser.add_argument('--train', action='store_true', help='Train voice model')
    parser.add_argument('--force', action='store_true', help='Force retrain')
    parser.add_argument('--synthesize', type=str, help='Generate speech from text')
    parser.add_argument('--model', default='matthew_voice', help='Model name to use')
    parser.add_argument('--ab-test', type=str, help='A/B test phrase')
    parser.add_argument('--model-a', default='matthew_voice_v1', help='Model A for A/B test')
    parser.add_argument('--model-b', default='matthew_voice_v2', help='Model B for A/B test')

    args = parser.parse_args()

    trainer = VoiceCloneTrainer()

    if args.export:
        samples = trainer.export_samples_from_db(max_samples=args.min_samples)

        if samples:
            trainer.analyze_voice_characteristics(samples)

    elif args.train:
        # Export samples first if needed
        if not list(trainer.samples_dir.glob("*.wav")):
            print("No samples found. Exporting from database...")
            samples = trainer.export_samples_from_db()

        result = trainer.train_piper_model(force=args.force)
        print(json.dumps(result, indent=2))

    elif args.synthesize:
        audio_path = trainer.synthesize_speech(args.synthesize, args.model)

        if audio_path:
            print(f"\n🎧 Play it: afplay {audio_path}")

    elif args.ab_test:
        result = trainer.ab_test_models(args.ab_test, args.model_a, args.model_b)
        print(json.dumps(result, indent=2))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
