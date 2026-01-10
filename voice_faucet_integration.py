#!/usr/bin/env python3
"""
Voice Faucet Integration - Unlock Domains by Speaking Keywords

Speak words → Keywords extracted → Domains unlocked → Content accessible

Like a voice-activated treasure hunt where speaking about topics unlocks access.

Features:
- Voice wordmap tracking (words you've spoken)
- Domain unlocking based on keyword frequency
- Faucet "keys" generated from voice
- Progressive domain ownership via speech
- QR faucet + voice integration

Flow:
1. User speaks → transcription saved
2. Keywords extracted from speech
3. User's wordmap updated (word frequency)
4. Check if keywords match domain contexts
5. Unlock domains when threshold met
6. Generate faucet QR codes for access

Usage:
    from voice_faucet_integration import process_voice_for_faucet

    result = process_voice_for_faucet(
        user_id=1,
        transcription="I love privacy and encryption",
        recording_id=42
    )
    # Returns: {
    #   'domains_unlocked': ['privacy.com', 'encryption.org'],
    #   'new_keywords': ['privacy', 'encryption'],
    #   'faucet_keys_generated': [...],
    #   'ownership_percentage': {...}
    # }
"""

import json
from typing import Dict, List, Optional
from database import get_db
from datetime import datetime
import re


class VoiceFaucetIntegrator:
    """Integrate voice recordings with domain faucet system"""

    def __init__(self):
        self.db = get_db()

    def process_voice_for_faucet(self, user_id: int, transcription: str,
                                 recording_id: Optional[int] = None) -> Dict:
        """
        Process voice transcription to unlock domains via faucet

        Args:
            user_id: User ID
            transcription: Voice transcription text
            recording_id: Optional recording ID to link

        Returns:
            {
                'keywords_extracted': [words],
                'wordmap_updated': bool,
                'domains_unlocked': [domain names],
                'new_keywords': [new words added],
                'faucet_keys_generated': [QR payloads],
                'ownership_progress': {domain: percentage}
            }
        """
        # Step 1: Extract keywords from transcription
        keywords = self._extract_keywords(transcription)

        # Step 2: Update user's wordmap
        wordmap_result = self._update_user_wordmap(user_id, keywords, recording_id)

        # Step 3: Check domain unlock eligibility
        unlock_result = self._check_domain_unlocks(user_id, keywords)

        # Step 4: Generate faucet keys for unlocked domains
        faucet_keys = self._generate_faucet_keys(user_id, unlock_result['unlocked_domains'])

        # Step 5: Award domain ownership
        ownership_progress = self._award_domain_ownership(user_id, keywords)

        return {
            'keywords_extracted': keywords,
            'wordmap_updated': wordmap_result['success'],
            'new_keywords': wordmap_result.get('new_keywords', []),
            'domains_unlocked': unlock_result['unlocked_domains'],
            'unlock_reasons': unlock_result['reasons'],
            'faucet_keys_generated': faucet_keys,
            'ownership_progress': ownership_progress
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from transcription

        Returns list of meaningful keywords
        """
        # Stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'this', 'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
            'show', 'find', 'search', 'look', 'get', 'give', 'tell'
        }

        # Clean and tokenize
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter: remove stop words, keep words 3+ chars
        keywords = [word for word in words if word not in stop_words and len(word) >= 3]

        return keywords

    def _update_user_wordmap(self, user_id: int, keywords: List[str],
                            recording_id: Optional[int] = None) -> Dict:
        """
        Update user's wordmap with new keywords from voice

        Returns update result
        """
        # Get existing wordmap
        row = self.db.execute('''
            SELECT wordmap_json, recording_count
            FROM user_wordmaps
            WHERE user_id = ?
        ''', (user_id,)).fetchone()

        if row and row['wordmap_json']:
            wordmap = json.loads(row['wordmap_json'])
            recording_count = row['recording_count'] or 0
        else:
            wordmap = {}
            recording_count = 0

        # Track new keywords
        new_keywords = []

        # Update wordmap with new keywords
        for keyword in keywords:
            if keyword in wordmap:
                wordmap[keyword] += 1
            else:
                wordmap[keyword] = 1
                new_keywords.append(keyword)

        # Update or insert wordmap
        if row:
            self.db.execute('''
                UPDATE user_wordmaps
                SET wordmap_json = ?,
                    recording_count = ?,
                    last_updated = ?
                WHERE user_id = ?
            ''', (json.dumps(wordmap), recording_count + 1, datetime.now(), user_id))
        else:
            self.db.execute('''
                INSERT INTO user_wordmaps (user_id, wordmap_json, recording_count, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (user_id, json.dumps(wordmap), 1, datetime.now()))

        self.db.commit()

        return {
            'success': True,
            'new_keywords': new_keywords,
            'total_keywords': len(wordmap),
            'wordmap_size': sum(wordmap.values())
        }

    def _check_domain_unlocks(self, user_id: int, keywords: List[str]) -> Dict:
        """
        Check if keywords unlock any domains

        Returns unlocked domains and reasons
        """
        unlocked = []
        reasons = {}

        # Get domain contexts
        for keyword in set(keywords):  # Unique keywords only
            domains = self.db.execute('''
                SELECT domain, tier, contexts, required_mentions
                FROM domain_contexts
                WHERE contexts LIKE ?
            ''', (f'%{keyword}%',)).fetchall()

            for domain_row in domains:
                domain = domain_row['domain']
                tier = domain_row['tier']
                required = domain_row['required_mentions'] or 5

                # Check user's keyword frequency
                wordmap_row = self.db.execute('''
                    SELECT wordmap_json FROM user_wordmaps WHERE user_id = ?
                ''', (user_id,)).fetchone()

                if wordmap_row and wordmap_row['wordmap_json']:
                    wordmap = json.loads(wordmap_row['wordmap_json'])
                    mentions = wordmap.get(keyword, 0)

                    if mentions >= required:
                        if domain not in unlocked:
                            unlocked.append(domain)
                            reasons[domain] = f"Mentioned '{keyword}' {mentions} times (required: {required})"

        return {
            'unlocked_domains': unlocked,
            'reasons': reasons
        }

    def _generate_faucet_keys(self, user_id: int, domains: List[str]) -> List[Dict]:
        """
        Generate faucet QR payloads for unlocked domains

        Returns list of faucet key data
        """
        from qr_faucet import generate_qr_payload

        keys = []

        for domain in domains:
            # Generate faucet payload
            payload_data = {
                'domain': domain,
                'user_id': user_id,
                'unlock_type': 'voice',
                'unlocked_at': datetime.now().isoformat()
            }

            try:
                encoded = generate_qr_payload('domain_unlock', payload_data, ttl_seconds=86400 * 30)  # 30 days

                keys.append({
                    'domain': domain,
                    'faucet_payload': encoded,
                    'qr_url': f'/qr/faucet/{encoded}',
                    'expires_days': 30
                })
            except Exception as e:
                print(f"Failed to generate faucet key for {domain}: {e}")

        return keys

    def _award_domain_ownership(self, user_id: int, keywords: List[str]) -> Dict:
        """
        Award incremental domain ownership based on keywords

        Returns ownership progress per domain
        """
        ownership_progress = {}

        # Get domains matching keywords
        for keyword in set(keywords):
            domains = self.db.execute('''
                SELECT id, domain, tier
                FROM domain_contexts
                WHERE contexts LIKE ?
            ''', (f'%{keyword}%',)).fetchall()

            for domain_row in domains:
                domain_id = domain_row['id']
                domain = domain_row['domain']

                # Get current ownership
                ownership_row = self.db.execute('''
                    SELECT ownership_percentage, mention_count
                    FROM domain_ownership
                    WHERE user_id = ? AND domain_id = ?
                ''', (user_id, domain_id)).fetchone()

                if ownership_row:
                    current_pct = ownership_row['ownership_percentage']
                    mentions = ownership_row['mention_count'] + 1
                else:
                    current_pct = 0.0
                    mentions = 1

                # Award 0.5% per keyword mention, max 50%
                new_pct = min(current_pct + 0.5, 50.0)

                # Update ownership
                if ownership_row:
                    self.db.execute('''
                        UPDATE domain_ownership
                        SET ownership_percentage = ?,
                            mention_count = ?,
                            last_mention_at = ?
                        WHERE user_id = ? AND domain_id = ?
                    ''', (new_pct, mentions, datetime.now(), user_id, domain_id))
                else:
                    self.db.execute('''
                        INSERT INTO domain_ownership (
                            user_id, domain_id, ownership_percentage, mention_count, last_mention_at
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, domain_id, new_pct, mentions, datetime.now()))

                ownership_progress[domain] = {
                    'percentage': new_pct,
                    'mentions': mentions,
                    'keyword': keyword
                }

        self.db.commit()

        return ownership_progress


# Convenience function
def process_voice_for_faucet(user_id: int, transcription: str,
                            recording_id: Optional[int] = None) -> Dict:
    """
    Process voice recording to unlock domains via faucet

    Args:
        user_id: User ID
        transcription: Voice transcription
        recording_id: Optional recording ID

    Returns:
        Faucet processing results
    """
    integrator = VoiceFaucetIntegrator()
    return integrator.process_voice_for_faucet(user_id, transcription, recording_id)


# CLI for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 2:
        user_id = int(sys.argv[1])
        transcription = ' '.join(sys.argv[2:])

        print(f"\n🎤 Processing voice faucet for user {user_id}")
        print(f"Transcription: '{transcription}'\n")

        result = process_voice_for_faucet(user_id, transcription)

        print(f"✅ Keywords extracted: {', '.join(result['keywords_extracted'])}")

        if result['new_keywords']:
            print(f"🆕 New keywords: {', '.join(result['new_keywords'])}")

        if result['domains_unlocked']:
            print(f"\n🎉 Domains Unlocked:")
            for domain in result['domains_unlocked']:
                reason = result['unlock_reasons'].get(domain, '')
                print(f"  - {domain}")
                print(f"    {reason}")

        if result['ownership_progress']:
            print(f"\n📊 Ownership Progress:")
            for domain, progress in result['ownership_progress'].items():
                print(f"  - {domain}: {progress['percentage']:.1f}% (via '{progress['keyword']}')")

        if result['faucet_keys_generated']:
            print(f"\n🔑 Faucet Keys Generated:")
            for key in result['faucet_keys_generated']:
                print(f"  - {key['domain']}")
                print(f"    QR URL: {key['qr_url']}")
                print(f"    Expires: {key['expires_days']} days")

        print()

    else:
        print("\nVoice Faucet Integration")
        print("\nUsage:")
        print("  python3 voice_faucet_integration.py <user_id> <transcription>")
        print("\nExample:")
        print("  python3 voice_faucet_integration.py 1 'I love privacy and encryption'")
        print()
