#!/usr/bin/env python3
"""
Voice Ollama Processor - AI Analysis of Voice Transcripts

Sends voice transcripts to Ollama for:
- Sentiment detection (happy/sad/angry/neutral/excited)
- Topic extraction
- Brand voice formatting (soulfra style)
- Follow-up question generation
- Quality scoring
"""

from typing import Dict, Optional, List
import json
from ollama_client import OllamaClient
from database import get_db


class VoiceOllamaProcessor:
    """Process voice transcripts with Ollama AI"""

    def __init__(self, model: str = 'llama3.2'):
        self.client = OllamaClient()
        self.model = model

    def analyze_transcript(self, transcript: str, recording_id: Optional[int] = None) -> Dict:
        """
        Analyze voice transcript with Ollama

        Args:
            transcript: The text to analyze
            recording_id: Optional recording ID for metadata

        Returns:
            {
                'sentiment': str (happy/sad/angry/neutral/excited),
                'sentiment_score': float (0-1),
                'key_topics': list of strings,
                'brand_voice': str (reformatted transcript),
                'follow_up_questions': list of strings,
                'quality_score': int (0-100),
                'word_count': int,
                'analysis_model': str
            }
        """
        if not transcript or not transcript.strip():
            return {
                'error': 'Empty transcript',
                'quality_score': 0,
                'sentiment': 'unknown'
            }

        # Build analysis prompt
        system_prompt = """You are an AI analyst for Soulfra, a creative tech platform.
Analyze voice transcripts with a focus on authenticity and user intent.

When analyzing, always return valid JSON with these fields:
- sentiment: one of [happy, sad, angry, neutral, excited, confused, thoughtful]
- sentiment_score: 0.0 to 1.0 (confidence in sentiment)
- key_topics: array of 2-5 main topics mentioned
- brand_voice: the transcript rewritten in soulfra's casual, authentic style
- follow_up_questions: 2-4 relevant questions to ask the user
- quality_score: 0-100 (content quality/clarity)
- insights: brief analysis of what user might need

Soulfra brand voice: casual, real, no corporate speak, fuck yeah energy, helpful but not fake."""

        analysis_prompt = f"""Analyze this voice transcript:

"{transcript}"

Return valid JSON with sentiment, topics, brand voice rewrite, follow-up questions, quality score, and insights."""

        # Send to Ollama
        try:
            result = self.client.generate(
                prompt=analysis_prompt,
                model=self.model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=800,
                timeout=30
            )

            if not result['success']:
                return {
                    'error': result.get('error', 'Ollama request failed'),
                    'quality_score': 0,
                    'sentiment': 'unknown'
                }

            # Parse Ollama response as JSON
            response_text = result['response'].strip()

            # Try to extract JSON from response
            analysis = self._extract_json(response_text)

            if not analysis:
                # Fallback: basic analysis without Ollama JSON
                return {
                    'sentiment': 'neutral',
                    'sentiment_score': 0.5,
                    'key_topics': self._extract_basic_topics(transcript),
                    'brand_voice': transcript,
                    'follow_up_questions': [],
                    'quality_score': 50,
                    'word_count': len(transcript.split()),
                    'analysis_model': self.model,
                    'raw_response': response_text[:200]
                }

            # Add metadata
            analysis['word_count'] = len(transcript.split())
            analysis['analysis_model'] = self.model
            analysis['recording_id'] = recording_id

            # Ensure quality_score is int 0-100
            if 'quality_score' in analysis:
                analysis['quality_score'] = max(0, min(100, int(analysis['quality_score'])))
            else:
                analysis['quality_score'] = 50

            return analysis

        except Exception as e:
            return {
                'error': str(e),
                'quality_score': 0,
                'sentiment': 'unknown',
                'word_count': len(transcript.split())
            }

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from Ollama response"""
        try:
            # Try direct JSON parse
            return json.loads(text)
        except:
            pass

        # Try to find JSON in text (might be wrapped in markdown)
        import re

        # Look for JSON between ```json and ``` or just {}
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*\{[^{}]*\}[^{}]*\})',  # Nested braces
            r'(\{[^{}]+\})'  # Simple braces
        ]

        for pattern in json_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    continue

        return None

    def _extract_basic_topics(self, transcript: str) -> List[str]:
        """Extract basic topics from transcript (fallback)"""
        # Simple keyword extraction
        words = transcript.lower().split()
        # Filter out common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'was', 'are', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}

        meaningful_words = [w for w in words if w not in stopwords and len(w) > 3]

        # Get top 5 by frequency
        from collections import Counter
        word_counts = Counter(meaningful_words)
        topics = [word for word, count in word_counts.most_common(5)]

        return topics[:3]  # Return top 3

    def analyze_recording(self, recording_id: int) -> Dict:
        """
        Analyze a voice recording from the database

        Args:
            recording_id: Database ID of recording

        Returns:
            Analysis dict with recording metadata
        """
        db = get_db()

        recording = db.execute('''
            SELECT id, filename, transcription, created_at, user_id
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        db.close()

        if not recording:
            return {
                'error': f'Recording {recording_id} not found',
                'quality_score': 0
            }

        if not recording['transcription']:
            return {
                'error': 'Recording has no transcription',
                'quality_score': 0,
                'recording_id': recording_id,
                'filename': recording['filename']
            }

        # Analyze the transcript
        analysis = self.analyze_transcript(
            transcript=recording['transcription'],
            recording_id=recording_id
        )

        # Add recording metadata
        analysis['filename'] = recording['filename']
        analysis['created_at'] = recording['created_at']
        analysis['user_id'] = recording['user_id']

        return analysis

    def batch_analyze(self, recording_ids: List[int]) -> List[Dict]:
        """
        Analyze multiple recordings

        Args:
            recording_ids: List of recording IDs

        Returns:
            List of analysis dicts
        """
        results = []
        for recording_id in recording_ids:
            analysis = self.analyze_recording(recording_id)
            results.append(analysis)

        return results

    def get_sentiment_summary(self, user_id: int, limit: int = 10) -> Dict:
        """
        Get sentiment summary for a user's recent recordings

        Args:
            user_id: User ID
            limit: Number of recent recordings to analyze

        Returns:
            {
                'total_recordings': int,
                'sentiment_breakdown': {'happy': 3, 'neutral': 2, ...},
                'average_quality': float,
                'common_topics': list of strings,
                'recent_analyses': list of dicts
            }
        """
        db = get_db()

        recordings = db.execute('''
            SELECT id, transcription
            FROM simple_voice_recordings
            WHERE user_id = ?
            AND transcription IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()

        db.close()

        if not recordings:
            return {
                'total_recordings': 0,
                'sentiment_breakdown': {},
                'average_quality': 0,
                'common_topics': []
            }

        # Analyze each recording
        analyses = []
        for rec in recordings:
            analysis = self.analyze_transcript(rec['transcription'], rec['id'])
            analyses.append(analysis)

        # Calculate summary
        sentiment_counts = {}
        total_quality = 0
        all_topics = []

        for analysis in analyses:
            if 'error' not in analysis:
                sentiment = analysis.get('sentiment', 'unknown')
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                total_quality += analysis.get('quality_score', 0)
                all_topics.extend(analysis.get('key_topics', []))

        avg_quality = total_quality / len(analyses) if analyses else 0

        # Get most common topics
        from collections import Counter
        topic_counts = Counter(all_topics)
        common_topics = [topic for topic, count in topic_counts.most_common(5)]

        return {
            'total_recordings': len(recordings),
            'sentiment_breakdown': sentiment_counts,
            'average_quality': round(avg_quality, 1),
            'common_topics': common_topics,
            'recent_analyses': analyses[:3]  # Return top 3 recent
        }


if __name__ == '__main__':
    # CLI test
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 voice_ollama_processor.py <recording_id>")
        print("  python3 voice_ollama_processor.py --text 'some text to analyze'")
        sys.exit(1)

    processor = VoiceOllamaProcessor()

    if sys.argv[1] == '--text':
        # Analyze text directly
        text = ' '.join(sys.argv[2:])
        result = processor.analyze_transcript(text)
        print(json.dumps(result, indent=2))
    else:
        # Analyze recording from database
        recording_id = int(sys.argv[1])
        result = processor.analyze_recording(recording_id)
        print(json.dumps(result, indent=2))
