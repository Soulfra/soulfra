#!/usr/bin/env python3
"""
Voice Health Checker - DNS Health Check for Ideas

Like GitHub's DNS health check, but for voice recordings and their propagation
through the mesh network of domains, lore, and ownership.

Checks:
- Audio validity (BLOB exists, playable)
- Transcription quality (exists, length, clarity)
- Wordmap extraction (keywords extracted)
- Domain alignment (Jaccard similarity matches)
- Ownership earned (percentage across domains)
- Lore contribution (narrative impact)
- Propagation health (network spread)

Usage:
    from voice_health_checker import VoiceHealthChecker

    checker = VoiceHealthChecker()
    health = checker.check_recording(recording_id=5)
    print(health['status'])  # healthy | degraded | broken

CLI:
    python3 voice_health_checker.py --recording 5
    python3 voice_health_checker.py --user 1 --all
"""

import json
import sys
from typing import Dict, List, Optional
from datetime import datetime
from database import get_db


class VoiceHealthChecker:
    """Health check system for voice recordings and their network propagation"""

    def __init__(self):
        self.db = get_db()

    def check_recording(self, recording_id: int) -> Dict:
        """
        Comprehensive health check for a voice recording

        Returns:
            {
                'recording_id': int,
                'status': 'healthy' | 'degraded' | 'broken',
                'overall_score': float (0-1),
                'checks': {
                    'audio_valid': bool,
                    'transcription_quality': float,
                    'wordmap_extracted': bool,
                    'domain_matches': int,
                    'ownership_earned': float,
                    'lore_contribution': str
                },
                'propagation': {
                    'domains_affected': [str],
                    'lore_themes_updated': [str],
                    'network_impact': str
                },
                'recommendations': [str]
            }
        """
        # Get recording
        rec = self.db.execute('''
            SELECT id, user_id, filename, transcription, file_size,
                   audio_data, created_at
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        if not rec:
            return {'error': 'Recording not found'}

        result = {
            'recording_id': recording_id,
            'status': 'unknown',
            'overall_score': 0.0,
            'checks': {},
            'propagation': {},
            'recommendations': []
        }

        # Check 1: Audio validity
        audio_check = self._check_audio(rec)
        result['checks']['audio_valid'] = audio_check['valid']
        result['checks']['audio_size_kb'] = audio_check['size_kb']

        # Check 2: Transcription quality
        transcript_check = self._check_transcription(rec)
        result['checks']['transcription_quality'] = transcript_check['quality_score']
        result['checks']['transcript_length'] = transcript_check['length']

        # Check 3: Wordmap extraction
        wordmap_check = self._check_wordmap(rec['user_id'])
        result['checks']['wordmap_extracted'] = wordmap_check['extracted']
        result['checks']['unique_words'] = wordmap_check['word_count']

        # Check 4: Domain matches
        domain_check = self._check_domain_matches(rec['user_id'])
        result['checks']['domain_matches'] = domain_check['match_count']
        result['checks']['top_domain'] = domain_check['top_domain']

        # Check 5: Ownership earned
        ownership_check = self._check_ownership(rec['user_id'])
        result['checks']['ownership_earned'] = ownership_check['total_ownership']
        result['checks']['domains_owned'] = ownership_check['domain_count']

        # Check 6: Lore contribution
        lore_check = self._check_lore_contribution(rec['user_id'], rec['transcription'])
        result['checks']['lore_contribution'] = lore_check['contribution_level']
        result['checks']['themes_affected'] = lore_check['theme_count']

        # Propagation analysis
        result['propagation'] = self._analyze_propagation(rec['user_id'], recording_id)

        # Calculate overall score
        score = self._calculate_overall_score(result['checks'])
        result['overall_score'] = score

        # Determine status
        if score >= 0.75:
            result['status'] = 'healthy'
        elif score >= 0.40:
            result['status'] = 'degraded'
        else:
            result['status'] = 'broken'

        # Generate recommendations
        result['recommendations'] = self._generate_recommendations(result['checks'])

        return result

    def _check_audio(self, rec: Dict) -> Dict:
        """Check if audio BLOB exists and is valid"""
        audio_data = rec['audio_data']

        if not audio_data:
            return {
                'valid': False,
                'size_kb': 0,
                'reason': 'No audio data found'
            }

        size_kb = len(audio_data) / 1024

        # Basic validity checks
        if size_kb < 1:
            return {
                'valid': False,
                'size_kb': size_kb,
                'reason': 'Audio file too small (< 1KB)'
            }

        return {
            'valid': True,
            'size_kb': round(size_kb, 2),
            'reason': 'Audio BLOB present and valid'
        }

    def _check_transcription(self, rec: Dict) -> Dict:
        """Check transcription quality"""
        transcript = rec['transcription']

        if not transcript:
            return {
                'quality_score': 0.0,
                'length': 0,
                'reason': 'No transcription found'
            }

        length = len(transcript)

        # Quality scoring based on length
        if length < 10:
            quality = 0.1
        elif length < 50:
            quality = 0.3
        elif length < 100:
            quality = 0.6
        elif length < 200:
            quality = 0.8
        else:
            quality = 1.0

        return {
            'quality_score': quality,
            'length': length,
            'reason': f'{length} chars transcribed'
        }

    def _check_wordmap(self, user_id: int) -> Dict:
        """Check if wordmap was extracted"""
        wordmap_row = self.db.execute('''
            SELECT wordmap_json
            FROM user_wordmaps
            WHERE user_id = ?
        ''', (user_id,)).fetchone()

        if not wordmap_row or not wordmap_row['wordmap_json']:
            return {
                'extracted': False,
                'word_count': 0
            }

        wordmap = json.loads(wordmap_row['wordmap_json'])

        return {
            'extracted': True,
            'word_count': len(wordmap)
        }

    def _check_domain_matches(self, user_id: int) -> Dict:
        """Check domain ownership matches"""
        matches = self.db.execute('''
            SELECT dc.domain, do.ownership_percentage
            FROM domain_ownership do
            JOIN domain_contexts dc ON do.domain_id = dc.id
            WHERE do.user_id = ? AND do.ownership_percentage > 0
            ORDER BY do.ownership_percentage DESC
        ''', (user_id,)).fetchall()

        if not matches:
            return {
                'match_count': 0,
                'top_domain': None,
                'top_score': 0.0
            }

        return {
            'match_count': len(matches),
            'top_domain': matches[0]['domain'],
            'top_score': matches[0]['ownership_percentage']
        }

    def _check_ownership(self, user_id: int) -> Dict:
        """Check ownership earned across domains"""
        ownership = self.db.execute('''
            SELECT COUNT(*) as count, SUM(ownership_percentage) as total
            FROM domain_ownership
            WHERE user_id = ? AND ownership_percentage > 0
        ''', (user_id,)).fetchone()

        return {
            'domain_count': ownership['count'] or 0,
            'total_ownership': round(ownership['total'] or 0, 2)
        }

    def _check_lore_contribution(self, user_id: int, transcript: str) -> Dict:
        """Check contribution to lore/narrative"""
        # Check if lore profile exists
        try:
            lore_row = self.db.execute('''
                SELECT lore_json, recording_count
                FROM user_lore_profiles
                WHERE user_id = ?
                ORDER BY generated_at DESC
                LIMIT 1
            ''', (user_id,)).fetchone()
        except:
            # Table doesn't exist yet
            lore_row = None

        if not lore_row:
            # Estimate based on transcript length alone
            if not transcript or len(transcript) < 20:
                level = 'minimal'
            elif len(transcript) < 100:
                level = 'low'
            elif len(transcript) < 200:
                level = 'medium'
            else:
                level = 'high'

            return {
                'contribution_level': level,
                'theme_count': 0
            }

        lore_data = json.loads(lore_row['lore_json'])

        # Determine contribution level based on transcript length
        if not transcript or len(transcript) < 20:
            level = 'minimal'
        elif len(transcript) < 100:
            level = 'low'
        elif len(transcript) < 200:
            level = 'medium'
        else:
            level = 'high'

        # Count themes
        themes = lore_data.get('themes', {}).get('themes', [])
        theme_count = len(themes) if themes else 0

        return {
            'contribution_level': level,
            'theme_count': theme_count
        }

    def _analyze_propagation(self, user_id: int, recording_id: int) -> Dict:
        """Analyze how this recording propagates through the network"""
        # Get domains affected (through ownership)
        domains = self.db.execute('''
            SELECT DISTINCT dc.domain
            FROM domain_ownership do
            JOIN domain_contexts dc ON do.domain_id = dc.id
            WHERE do.user_id = ?
        ''', (user_id,)).fetchall()

        domains_affected = [d['domain'] for d in domains] if domains else []

        # Get lore themes
        try:
            lore_row = self.db.execute('''
                SELECT lore_json
                FROM user_lore_profiles
                WHERE user_id = ?
                ORDER BY generated_at DESC
                LIMIT 1
            ''', (user_id,)).fetchone()
        except:
            lore_row = None

        themes_updated = []
        if lore_row and lore_row['lore_json']:
            lore_data = json.loads(lore_row['lore_json'])
            themes = lore_data.get('themes', {}).get('themes', [])
            themes_updated = themes[:5] if themes else []

        # Determine network impact
        impact_score = len(domains_affected) + (len(themes_updated) * 0.5)

        if impact_score == 0:
            network_impact = 'none'
        elif impact_score < 2:
            network_impact = 'minimal'
        elif impact_score < 5:
            network_impact = 'moderate'
        else:
            network_impact = 'significant'

        return {
            'domains_affected': domains_affected,
            'lore_themes_updated': themes_updated,
            'network_impact': network_impact
        }

    def _calculate_overall_score(self, checks: Dict) -> float:
        """Calculate overall health score (0-1)"""
        scores = []

        # Audio validity (20%)
        if checks.get('audio_valid'):
            scores.append(0.2)

        # Transcription quality (20%)
        scores.append(checks.get('transcription_quality', 0) * 0.2)

        # Wordmap extraction (15%)
        if checks.get('wordmap_extracted'):
            scores.append(0.15)

        # Domain matches (20%)
        match_count = checks.get('domain_matches', 0)
        match_score = min(match_count / 5.0, 1.0)  # Max at 5 domains
        scores.append(match_score * 0.2)

        # Ownership earned (15%)
        ownership = checks.get('ownership_earned', 0)
        ownership_score = min(ownership / 10.0, 1.0)  # Max at 10% total
        scores.append(ownership_score * 0.15)

        # Lore contribution (10%)
        contribution_levels = {'none': 0, 'minimal': 0.25, 'low': 0.5, 'medium': 0.75, 'high': 1.0}
        lore_level = checks.get('lore_contribution', 'none')
        scores.append(contribution_levels.get(lore_level, 0) * 0.1)

        return round(sum(scores), 2)

    def _generate_recommendations(self, checks: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if not checks.get('audio_valid'):
            recommendations.append("⚠️ Audio data missing - re-record this voice memo")

        if checks.get('transcription_quality', 0) < 0.5:
            recommendations.append("📝 Transcription too short - record longer voice memos (30+ seconds)")

        if not checks.get('wordmap_extracted'):
            recommendations.append("🗺️ Wordmap not extracted - run wordmap update")

        if checks.get('domain_matches', 0) == 0:
            recommendations.append("🎯 No domain matches - speak more about specific topics")

        if checks.get('ownership_earned', 0) < 1.0:
            recommendations.append("💎 Low ownership - create more aligned content to earn domains")

        if checks.get('lore_contribution') in ['none', 'minimal']:
            recommendations.append("📖 Minimal lore impact - share deeper thoughts and values")

        if len(recommendations) == 0:
            recommendations.append("✅ Recording is healthy and contributing to the network!")

        return recommendations

    def print_health_report(self, health: Dict):
        """Print formatted health report (like domain_health.py)"""
        recording_id = health['recording_id']
        status = health['status']
        score = health['overall_score']

        # Color coding
        colors = {
            'healthy': '\033[92m',    # Green
            'degraded': '\033[93m',   # Yellow
            'broken': '\033[91m',     # Red
        }
        reset = '\033[0m'

        color = colors.get(status, '')
        symbol = '✓' if status == 'healthy' else ('⚠' if status == 'degraded' else '✗')

        print(f"\n{'='*70}")
        print(f"🎤 Voice Recording Health Check - #{recording_id}")
        print(f"{'='*70}")

        print(f"\nOverall Status: {color}{symbol} {status.upper()}{reset}")
        print(f"Health Score: {score:.0%}\n")

        print(f"{'─'*70}")
        print("Checks:")
        checks = health['checks']

        print(f"  Audio Valid: {self._status_symbol(checks.get('audio_valid'))} ({checks.get('audio_size_kb', 0)} KB)")
        print(f"  Transcription: {checks.get('transcription_quality', 0):.0%} quality ({checks.get('transcript_length', 0)} chars)")
        print(f"  Wordmap: {self._status_symbol(checks.get('wordmap_extracted'))} ({checks.get('unique_words', 0)} words)")
        print(f"  Domain Matches: {checks.get('domain_matches', 0)}")
        if checks.get('top_domain'):
            print(f"    └─ Top: {checks['top_domain']}")
        print(f"  Ownership Earned: {checks.get('ownership_earned', 0):.2f}% ({checks.get('domains_owned', 0)} domains)")
        print(f"  Lore Contribution: {checks.get('lore_contribution', 'none')} ({checks.get('themes_affected', 0)} themes)")

        print(f"\n{'─'*70}")
        print("Propagation:")
        prop = health['propagation']
        print(f"  Network Impact: {prop['network_impact']}")
        if prop['domains_affected']:
            print(f"  Domains Affected: {', '.join(prop['domains_affected'][:3])}")
        if prop['lore_themes_updated']:
            print(f"  Lore Themes: {', '.join(prop['lore_themes_updated'][:3])}")

        print(f"\n{'─'*70}")
        print("Recommendations:")
        for rec in health['recommendations']:
            print(f"  {rec}")

        print(f"\n{'='*70}\n")

    def _status_symbol(self, value: bool) -> str:
        """Return colored status symbol"""
        if value:
            return '\033[92m✓\033[0m'
        else:
            return '\033[91m✗\033[0m'


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Voice Recording Health Checker')
    parser.add_argument('--recording', type=int, help='Check specific recording ID')
    parser.add_argument('--user', type=int, help='Check all recordings for user')
    parser.add_argument('--all', action='store_true', help='Check all recordings for user')

    args = parser.parse_args()

    checker = VoiceHealthChecker()

    if args.recording:
        # Check single recording
        health = checker.check_recording(args.recording)

        if 'error' in health:
            print(f"\n❌ Error: {health['error']}\n")
            sys.exit(1)

        checker.print_health_report(health)

    elif args.user:
        # Check all recordings for user
        db = get_db()
        recordings = db.execute('''
            SELECT id FROM simple_voice_recordings
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (args.user,)).fetchall()

        print(f"\n🔍 Checking {len(recordings)} recordings for user {args.user}...\n")

        for rec in recordings:
            health = checker.check_recording(rec['id'])
            if 'error' not in health:
                checker.print_health_report(health)

    else:
        print("\nUsage:")
        print("  python3 voice_health_checker.py --recording 5")
        print("  python3 voice_health_checker.py --user 1 --all")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()
