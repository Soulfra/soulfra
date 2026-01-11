#!/usr/bin/env python3
"""
Voice Content Generator - Generate pitch decks, blogs, templates from voice memos

Uses Ollama to transform voice transcripts into structured content:
- Pitch decks (slides with talking points)
- Blog posts (intro, body, conclusion)
- Social media posts (Twitter, LinkedIn)
- Product descriptions
- Email templates

Integrates with domain ownership system - generates content for user's domains.
"""

from typing import Dict, List, Optional
from database import get_db
from ollama_client import OllamaClient
import json


class VoiceContentGenerator:
    """Generate structured content from voice transcripts using Ollama"""

    def __init__(self, model: str = 'llama3.2'):
        self.client = OllamaClient()
        self.model = model

    def generate_pitch_deck(self, transcript: str, domain: str, recording_id: Optional[int] = None) -> Dict:
        """
        Generate pitch deck slides from voice transcript

        Args:
            transcript: Voice memo transcript
            domain: Domain this pitch is for (e.g., soulfra.com)
            recording_id: Optional recording ID

        Returns:
            {
                'title': str,
                'domain': str,
                'slides': [
                    {'title': str, 'bullets': [str, str, ...]},
                    ...
                ],
                'total_slides': int
            }
        """
        system_prompt = f"""You are a pitch deck expert helping {domain} create compelling presentations.
Transform voice transcripts into professional pitch deck slides.

Each slide should have:
- A clear title (5-10 words)
- 3-5 bullet points (short, punchy)

Focus on: problem, solution, market, traction, team, ask.

Return valid JSON with this structure:
{{
    "title": "Overall deck title",
    "slides": [
        {{"title": "Slide Title", "bullets": ["Point 1", "Point 2", "Point 3"]}},
        ...
    ]
}}"""

        prompt = f"""Based on this voice memo, create a pitch deck:

"{transcript}"

Generate 5-7 slides that tell a compelling story about {domain}.
Return valid JSON only."""

        try:
            result = self.client.generate(
                prompt=prompt,
                model=self.model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1000,
                timeout=60
            )

            if not result['success']:
                return {
                    'error': result.get('error', 'Ollama generation failed'),
                    'domain': domain
                }

            # Parse Ollama JSON response
            response_text = result['response'].strip()
            pitch_data = self._extract_json(response_text)

            if not pitch_data:
                return {
                    'error': 'Failed to parse pitch deck JSON',
                    'raw_response': response_text[:500],
                    'domain': domain
                }

            # Add metadata
            pitch_data['domain'] = domain
            pitch_data['total_slides'] = len(pitch_data.get('slides', []))
            pitch_data['recording_id'] = recording_id
            pitch_data['model'] = self.model

            return pitch_data

        except Exception as e:
            return {
                'error': str(e),
                'domain': domain
            }

    def generate_blog_post(self, transcript: str, domain: str, recording_id: Optional[int] = None) -> Dict:
        """
        Generate blog post from voice transcript

        Returns:
            {
                'title': str,
                'domain': str,
                'intro': str (2-3 sentences),
                'sections': [
                    {'heading': str, 'content': str},
                    ...
                ],
                'conclusion': str,
                'tags': [str, str, ...]
            }
        """
        system_prompt = f"""You are a content writer for {domain}, creating authentic blog posts.

Transform voice transcripts into engaging blog posts with:
- Catchy title
- Strong intro (hook the reader)
- 3-5 sections with headings
- Conclusion with CTA
- Relevant tags

Keep the casual, authentic voice from the transcript. No corporate bullshit.

Return valid JSON with this structure:
{{
    "title": "Blog post title",
    "intro": "Opening paragraph...",
    "sections": [
        {{"heading": "Section Title", "content": "Section content..."}},
        ...
    ],
    "conclusion": "Closing paragraph...",
    "tags": ["tag1", "tag2", "tag3"]
}}"""

        prompt = f"""Transform this voice memo into a blog post for {domain}:

"{transcript}"

Keep the authentic voice. Make it engaging. Return valid JSON only."""

        try:
            result = self.client.generate(
                prompt=prompt,
                model=self.model,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=1500,
                timeout=90
            )

            if not result['success']:
                return {
                    'error': result.get('error', 'Ollama generation failed'),
                    'domain': domain
                }

            response_text = result['response'].strip()
            blog_data = self._extract_json(response_text)

            if not blog_data:
                return {
                    'error': 'Failed to parse blog post JSON',
                    'raw_response': response_text[:500],
                    'domain': domain
                }

            blog_data['domain'] = domain
            blog_data['recording_id'] = recording_id
            blog_data['model'] = self.model
            blog_data['word_count'] = len(' '.join([
                blog_data.get('intro', ''),
                ' '.join([s.get('content', '') for s in blog_data.get('sections', [])]),
                blog_data.get('conclusion', '')
            ]).split())

            return blog_data

        except Exception as e:
            return {
                'error': str(e),
                'domain': domain
            }

    def generate_social_posts(self, transcript: str, domain: str, recording_id: Optional[int] = None) -> Dict:
        """
        Generate social media posts from voice transcript

        Returns:
            {
                'domain': str,
                'twitter': str (280 chars),
                'linkedin': str (longer form),
                'instagram': str (with hashtags)
            }
        """
        system_prompt = f"""You are a social media manager for {domain}.

Create engaging social posts from voice transcripts:
- Twitter: 280 chars max, punchy, with 1-2 hashtags
- LinkedIn: Professional but authentic, 2-3 paragraphs
- Instagram: Visual description + 5-10 relevant hashtags

Keep the authentic voice. No corporate speak.

Return valid JSON:
{{
    "twitter": "Tweet text...",
    "linkedin": "LinkedIn post...",
    "instagram": "Instagram caption..."
}}"""

        prompt = f"""Create social media posts for {domain} based on this voice memo:

"{transcript}"

Generate Twitter, LinkedIn, and Instagram versions. Return valid JSON only."""

        try:
            result = self.client.generate(
                prompt=prompt,
                model=self.model,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=800,
                timeout=60
            )

            if not result['success']:
                return {
                    'error': result.get('error', 'Ollama generation failed'),
                    'domain': domain
                }

            response_text = result['response'].strip()
            social_data = self._extract_json(response_text)

            if not social_data:
                return {
                    'error': 'Failed to parse social posts JSON',
                    'raw_response': response_text[:500],
                    'domain': domain
                }

            social_data['domain'] = domain
            social_data['recording_id'] = recording_id
            social_data['model'] = self.model

            return social_data

        except Exception as e:
            return {
                'error': str(e),
                'domain': domain
            }

    def generate_all_content(self, recording_id: int) -> Dict:
        """
        Generate all content types from a voice recording

        Args:
            recording_id: Database ID of voice recording

        Returns:
            {
                'recording_id': int,
                'transcript': str,
                'domain': str,
                'pitch_deck': {...},
                'blog_post': {...},
                'social_posts': {...}
            }
        """
        db = get_db()

        # Get recording
        recording = db.execute('''
            SELECT id, filename, transcription, user_id, created_at
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        if not recording:
            return {
                'error': f'Recording {recording_id} not found'
            }

        if not recording['transcription']:
            return {
                'error': 'Recording has no transcription',
                'recording_id': recording_id
            }

        # Get user's primary domain
        from domain_unlock_engine import get_primary_domain
        primary_domain = get_primary_domain(recording['user_id'])

        if not primary_domain:
            domain = 'your-domain.com'  # Fallback
        else:
            domain = primary_domain['domain']

        transcript = recording['transcription']

        # Generate all content types
        pitch_deck = self.generate_pitch_deck(transcript, domain, recording_id)
        blog_post = self.generate_blog_post(transcript, domain, recording_id)
        social_posts = self.generate_social_posts(transcript, domain, recording_id)

        return {
            'recording_id': recording_id,
            'filename': recording['filename'],
            'transcript': transcript,
            'domain': domain,
            'user_id': recording['user_id'],
            'created_at': recording['created_at'],
            'pitch_deck': pitch_deck,
            'blog_post': blog_post,
            'social_posts': social_posts,
            'model': self.model
        }

    def batch_generate(self, user_id: int, content_type: str = 'all', limit: int = 5) -> List[Dict]:
        """
        Generate content for multiple voice recordings

        Args:
            user_id: User ID
            content_type: 'pitch_deck', 'blog_post', 'social_posts', or 'all'
            limit: Number of recordings to process

        Returns:
            List of generated content dicts
        """
        db = get_db()

        recordings = db.execute('''
            SELECT id
            FROM simple_voice_recordings
            WHERE user_id = ?
            AND transcription IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()

        results = []
        for rec in recordings:
            content = None

            if content_type == 'all':
                content = self.generate_all_content(rec['id'])
            elif content_type == 'pitch_deck':
                from domain_unlock_engine import get_primary_domain
                primary_domain = get_primary_domain(user_id)
                domain = primary_domain['domain'] if primary_domain else 'your-domain.com'

                transcript = db.execute('SELECT transcription FROM simple_voice_recordings WHERE id = ?', (rec['id'],)).fetchone()['transcription']
                content = self.generate_pitch_deck(transcript, domain, rec['id'])
            elif content_type == 'blog_post':
                from domain_unlock_engine import get_primary_domain
                primary_domain = get_primary_domain(user_id)
                domain = primary_domain['domain'] if primary_domain else 'your-domain.com'

                transcript = db.execute('SELECT transcription FROM simple_voice_recordings WHERE id = ?', (rec['id'],)).fetchone()['transcription']
                content = self.generate_blog_post(transcript, domain, rec['id'])
            elif content_type == 'social_posts':
                from domain_unlock_engine import get_primary_domain
                primary_domain = get_primary_domain(user_id)
                domain = primary_domain['domain'] if primary_domain else 'your-domain.com'

                transcript = db.execute('SELECT transcription FROM simple_voice_recordings WHERE id = ?', (rec['id'],)).fetchone()['transcription']
                content = self.generate_social_posts(transcript, domain, rec['id'])
            else:
                # Unknown content type - return error
                content = {
                    'error': f'Unknown content_type: {content_type}',
                    'recording_id': rec['id'],
                    'valid_types': ['all', 'pitch_deck', 'blog_post', 'social_posts']
                }

            if content:
                results.append(content)

        return results

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from Ollama response (handles markdown code blocks)"""
        try:
            return json.loads(text)
        except:
            pass

        import re

        # Look for JSON in markdown code blocks or raw braces
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*\{[^{}]*\}[^{}]*\})',  # Nested
            r'(\{[^{}]+\})'  # Simple
        ]

        for pattern in json_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    continue

        return None


if __name__ == '__main__':
    # CLI test
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 voice_content_generator.py <recording_id>")
        print("  python3 voice_content_generator.py <recording_id> pitch_deck")
        print("  python3 voice_content_generator.py <recording_id> blog_post")
        print("  python3 voice_content_generator.py <recording_id> social_posts")
        sys.exit(1)

    generator = VoiceContentGenerator()

    recording_id = int(sys.argv[1])
    content_type = sys.argv[2] if len(sys.argv) > 2 else 'all'

    if content_type == 'all':
        result = generator.generate_all_content(recording_id)
    elif content_type == 'pitch_deck':
        db = get_db()
        rec = db.execute('SELECT transcription, user_id FROM simple_voice_recordings WHERE id = ?', (recording_id,)).fetchone()
        from domain_unlock_engine import get_primary_domain
        domain = get_primary_domain(rec['user_id'])['domain'] if get_primary_domain(rec['user_id']) else 'test.com'
        result = generator.generate_pitch_deck(rec['transcription'], domain, recording_id)
    elif content_type == 'blog_post':
        db = get_db()
        rec = db.execute('SELECT transcription, user_id FROM simple_voice_recordings WHERE id = ?', (recording_id,)).fetchone()
        from domain_unlock_engine import get_primary_domain
        domain = get_primary_domain(rec['user_id'])['domain'] if get_primary_domain(rec['user_id']) else 'test.com'
        result = generator.generate_blog_post(rec['transcription'], domain, recording_id)
    elif content_type == 'social_posts':
        db = get_db()
        rec = db.execute('SELECT transcription, user_id FROM simple_voice_recordings WHERE id = ?', (recording_id,)).fetchone()
        from domain_unlock_engine import get_primary_domain
        domain = get_primary_domain(rec['user_id'])['domain'] if get_primary_domain(rec['user_id']) else 'test.com'
        result = generator.generate_social_posts(rec['transcription'], domain, recording_id)

    print(json.dumps(result, indent=2))
