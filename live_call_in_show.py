#!/usr/bin/env python3
"""
Live Call-In Show System - NPR-style radio show on localhost

Host reads news articles → Listeners call in with voice reactions → Pair with sponsors

Like NPR's "Talk of the Nation" but self-hosted with voice reactions and ad integration.

Usage:
    # Create new show
    python3 live_call_in_show.py create "AI Regulation News" --article-url https://...

    # Submit call-in reaction
    python3 live_call_in_show.py call-in 1 --recording-id 42 --name "John from Tampa"

    # Approve reaction
    python3 live_call_in_show.py approve 5

    # Pair with sponsor
    python3 live_call_in_show.py pair-sponsor 5 --sponsor-id 2

    # Generate bookend
    python3 live_call_in_show.py bookend 1 --type intro

    # Export show
    python3 live_call_in_show.py export 1
"""

import json
import sys
from typing import Dict, List, Optional
from datetime import datetime
from database import get_db


class LiveCallInShow:
    """Manage live call-in radio shows with voice reactions and sponsors"""

    def __init__(self):
        self.db = get_db()

    def create_show(self, title: str, article_text: str, host_user_id: int = 1,
                   article_url: Optional[str] = None,
                   article_source: Optional[str] = None) -> Dict:
        """
        Create new live call-in show episode

        Args:
            title: Show episode title
            article_text: News article content to discuss
            host_user_id: User ID of host
            article_url: Source URL
            article_source: Publication name

        Returns:
            Show info dict
        """
        cursor = self.db.execute('''
            INSERT INTO live_shows
            (title, article_text, article_url, article_source, host_user_id, status)
            VALUES (?, ?, ?, ?, ?, 'accepting_calls')
        ''', (title, article_text, article_url, article_source, host_user_id))

        self.db.commit()
        show_id = cursor.lastrowid

        return {
            'show_id': show_id,
            'title': title,
            'status': 'accepting_calls',
            'call_in_url': f'http://192.168.1.87:5001/call-in/{show_id}',
            'host_dashboard': f'http://192.168.1.87:5001/live-show-host/{show_id}'
        }

    def submit_call_in(self, show_id: int, recording_id: int,
                      caller_name: Optional[str] = None,
                      user_id: Optional[int] = None,
                      reaction_type: str = 'comment') -> Dict:
        """
        Submit voice reaction to show

        Args:
            show_id: Show to call into
            recording_id: Voice recording ID
            caller_name: "John from Tampa"
            user_id: User ID if logged in
            reaction_type: comment, question, story, counterpoint

        Returns:
            Reaction info dict
        """
        # Get transcription from recording
        rec = self.db.execute('''
            SELECT transcription FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        transcription = rec['transcription'] if rec else None

        # Insert reaction
        cursor = self.db.execute('''
            INSERT INTO show_reactions
            (show_id, recording_id, user_id, caller_name, reaction_type,
             transcription, approval_status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (show_id, recording_id, user_id, caller_name, reaction_type, transcription))

        reaction_id = cursor.lastrowid

        # Update show total
        self.db.execute('''
            UPDATE live_shows
            SET total_reactions = total_reactions + 1
            WHERE id = ?
        ''', (show_id,))

        self.db.commit()

        return {
            'reaction_id': reaction_id,
            'status': 'pending',
            'show_id': show_id,
            'transcription': transcription
        }

    def approve_reaction(self, reaction_id: int, approved_by: int = 1,
                        timestamp_in_show: Optional[int] = None) -> Dict:
        """
        Approve call-in reaction for airing

        Args:
            reaction_id: Reaction to approve
            approved_by: User ID of approver
            timestamp_in_show: When in show this appears (seconds)

        Returns:
            Updated reaction info
        """
        self.db.execute('''
            UPDATE show_reactions
            SET approval_status = 'approved',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP,
                timestamp_in_show = ?
            WHERE id = ?
        ''', (approved_by, timestamp_in_show, reaction_id))

        # Update show approved count
        reaction = self.db.execute('''
            SELECT show_id FROM show_reactions WHERE id = ?
        ''', (reaction_id,)).fetchone()

        if reaction:
            self.db.execute('''
                UPDATE live_shows
                SET approved_reactions = approved_reactions + 1
                WHERE id = ?
            ''', (reaction['show_id'],))

        self.db.commit()

        return {'reaction_id': reaction_id, 'status': 'approved'}

    def add_sponsor(self, show_id: int, sponsor_name: str,
                   sponsor_type: str = 'product',
                   sponsor_url: Optional[str] = None,
                   ad_script: Optional[str] = None,
                   keywords: Optional[List[str]] = None) -> Dict:
        """
        Add sponsor to show

        Args:
            show_id: Show to sponsor
            sponsor_name: Sponsor company name
            sponsor_type: product, service, affiliate, brand
            sponsor_url: Sponsor website
            ad_script: Pre-written ad copy
            keywords: Matching keywords for pairing

        Returns:
            Sponsor info dict
        """
        keywords_json = json.dumps(keywords) if keywords else None

        cursor = self.db.execute('''
            INSERT INTO show_sponsors
            (show_id, sponsor_name, sponsor_type, sponsor_url, ad_script, keywords_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (show_id, sponsor_name, sponsor_type, sponsor_url, ad_script, keywords_json))

        sponsor_id = cursor.lastrowid

        # Update show sponsor count
        self.db.execute('''
            UPDATE live_shows
            SET total_sponsors = total_sponsors + 1
            WHERE id = ?
        ''', (show_id,))

        self.db.commit()

        return {
            'sponsor_id': sponsor_id,
            'sponsor_name': sponsor_name,
            'keywords': keywords
        }

    def pair_reaction_with_sponsor(self, reaction_id: int, sponsor_id: int,
                                   placement_style: str = 'before') -> Dict:
        """
        Pair reaction with sponsor ad

        Args:
            reaction_id: Reaction to pair
            sponsor_id: Sponsor to pair with
            placement_style: before, after, split

        Returns:
            Pairing info dict
        """
        # Get reaction transcription
        reaction = self.db.execute('''
            SELECT transcription, show_id FROM show_reactions WHERE id = ?
        ''', (reaction_id,)).fetchone()

        # Get sponsor keywords
        sponsor = self.db.execute('''
            SELECT keywords_json FROM show_sponsors WHERE id = ?
        ''', (sponsor_id,)).fetchone()

        # Calculate pairing score (simple keyword matching)
        pairing_score = 50.0  # Default
        pairing_reason = "Manual pairing"

        if reaction and sponsor and reaction['transcription']:
            keywords = json.loads(sponsor['keywords_json']) if sponsor['keywords_json'] else []
            transcript_lower = reaction['transcription'].lower()

            matches = sum(1 for kw in keywords if kw.lower() in transcript_lower)
            if matches > 0:
                pairing_score = min(100, 50 + (matches * 15))
                pairing_reason = f"Matched {matches} keywords"

        # Insert pairing
        cursor = self.db.execute('''
            INSERT INTO reaction_ad_pairings
            (reaction_id, sponsor_id, pairing_score, pairing_reason, placement_style)
            VALUES (?, ?, ?, ?, ?)
        ''', (reaction_id, sponsor_id, pairing_score, pairing_reason, placement_style))

        # Update reaction with pairing
        self.db.execute('''
            UPDATE show_reactions
            SET ad_pairing_id = ?
            WHERE id = ?
        ''', (sponsor_id, reaction_id))

        # Update sponsor mention count
        self.db.execute('''
            UPDATE show_sponsors
            SET total_mentions = total_mentions + 1
            WHERE id = ?
        ''', (sponsor_id,))

        self.db.commit()

        return {
            'pairing_id': cursor.lastrowid,
            'pairing_score': pairing_score,
            'pairing_reason': pairing_reason,
            'placement_style': placement_style
        }

    def auto_pair_sponsors(self, show_id: int) -> List[Dict]:
        """
        Automatically pair approved reactions with sponsors using keyword matching

        Args:
            show_id: Show to process

        Returns:
            List of pairings created
        """
        # Get approved reactions without pairings
        reactions = self.db.execute('''
            SELECT id, transcription FROM show_reactions
            WHERE show_id = ?
              AND approval_status = 'approved'
              AND ad_pairing_id IS NULL
        ''', (show_id,)).fetchall()

        # Get show sponsors
        sponsors = self.db.execute('''
            SELECT id, keywords_json FROM show_sponsors
            WHERE show_id = ?
        ''', (show_id,)).fetchall()

        pairings = []

        for reaction in reactions:
            best_sponsor = None
            best_score = 0

            for sponsor in sponsors:
                if not sponsor['keywords_json']:
                    continue

                keywords = json.loads(sponsor['keywords_json'])
                transcript_lower = reaction['transcription'].lower() if reaction['transcription'] else ''

                matches = sum(1 for kw in keywords if kw.lower() in transcript_lower)
                score = matches * 15

                if score > best_score:
                    best_score = score
                    best_sponsor = sponsor['id']

            if best_sponsor and best_score >= 15:  # At least 1 keyword match
                pairing = self.pair_reaction_with_sponsor(
                    reaction['id'],
                    best_sponsor,
                    placement_style='before'
                )
                pairings.append(pairing)

        return pairings

    def generate_bookend(self, show_id: int, bookend_type: str) -> Dict:
        """
        Generate intro or outro bookend with sponsor mentions

        Args:
            show_id: Show to generate bookend for
            bookend_type: 'intro' or 'outro'

        Returns:
            Bookend info with generated script
        """
        # Get show info
        show = self.db.execute('''
            SELECT title FROM live_shows WHERE id = ?
        ''', (show_id,)).fetchone()

        # Get sponsors
        sponsors = self.db.execute('''
            SELECT sponsor_name, ad_script FROM show_sponsors
            WHERE show_id = ?
        ''', (show_id,)).fetchall()

        sponsor_names = [s['sponsor_name'] for s in sponsors]

        # Generate script
        if bookend_type == 'intro':
            script = self._generate_intro_script(show['title'], sponsor_names)
        else:
            script = self._generate_outro_script(show['title'], sponsor_names)

        # Save bookend
        cursor = self.db.execute('''
            INSERT INTO show_bookends
            (show_id, bookend_type, generated_script, sponsor_ids_json)
            VALUES (?, ?, ?, ?)
        ''', (show_id, bookend_type, script, json.dumps([s['sponsor_name'] for s in sponsors])))

        bookend_id = cursor.lastrowid

        # Update show with bookend
        if bookend_type == 'intro':
            self.db.execute('UPDATE live_shows SET intro_bookend_id = ? WHERE id = ?',
                          (bookend_id, show_id))
        else:
            self.db.execute('UPDATE live_shows SET outro_bookend_id = ? WHERE id = ?',
                          (bookend_id, show_id))

        self.db.commit()

        return {
            'bookend_id': bookend_id,
            'type': bookend_type,
            'script': script,
            'sponsors': sponsor_names
        }

    def _generate_intro_script(self, show_title: str, sponsors: List[str]) -> str:
        """Generate intro script with sponsor mentions"""
        if not sponsors:
            return f"Welcome to {show_title}. Let's hear from our callers."

        sponsor_text = ", ".join(sponsors[:-1]) + f" and {sponsors[-1]}" if len(sponsors) > 1 else sponsors[0]

        return f"""Welcome to {show_title}.

This show is brought to you by {sponsor_text}.

Today we're discussing the article you just read. Let's hear what our callers have to say."""

    def _generate_outro_script(self, show_title: str, sponsors: List[str]) -> str:
        """Generate outro script with sponsor mentions"""
        if not sponsors:
            return f"Thanks for listening to {show_title}. Join us next time."

        sponsor_text = ", ".join(sponsors[:-1]) + f" and {sponsors[-1]}" if len(sponsors) > 1 else sponsors[0]

        return f"""Thanks to our callers for their thoughtful reactions.

This has been {show_title}, brought to you by {sponsor_text}.

Join us next time for more discussions."""

    def get_show_queue(self, show_id: int, status: Optional[str] = None) -> List[Dict]:
        """
        Get call-in queue for show

        Args:
            show_id: Show ID
            status: Filter by status (pending, approved, rejected)

        Returns:
            List of reactions
        """
        query = '''
            SELECT r.*, s.sponsor_name
            FROM show_reactions r
            LEFT JOIN show_sponsors s ON r.ad_pairing_id = s.id
            WHERE r.show_id = ?
        '''
        params = [show_id]

        if status:
            query += ' AND r.approval_status = ?'
            params.append(status)

        query += ' ORDER BY r.created_at DESC'

        reactions = self.db.execute(query, params).fetchall()

        return [dict(r) for r in reactions]

    def export_show(self, show_id: int) -> Dict:
        """
        Export complete show with all components

        Args:
            show_id: Show to export

        Returns:
            Complete show data for playback/publishing
        """
        # Get show info
        show = self.db.execute('''
            SELECT * FROM live_shows WHERE id = ?
        ''', (show_id,)).fetchone()

        # Get intro bookend
        intro = None
        if show['intro_bookend_id']:
            intro = self.db.execute('''
                SELECT * FROM show_bookends WHERE id = ?
            ''', (show['intro_bookend_id'],)).fetchone()

        # Get approved reactions with sponsors
        reactions = self.db.execute('''
            SELECT r.*, s.sponsor_name, s.ad_script, s.sponsor_url,
                   p.placement_style, p.pairing_score
            FROM show_reactions r
            LEFT JOIN show_sponsors s ON r.ad_pairing_id = s.id
            LEFT JOIN reaction_ad_pairings p ON r.id = p.reaction_id
            WHERE r.show_id = ? AND r.approval_status = 'approved'
            ORDER BY r.timestamp_in_show, r.created_at
        ''', (show_id,)).fetchall()

        # Get outro bookend
        outro = None
        if show['outro_bookend_id']:
            outro = self.db.execute('''
                SELECT * FROM show_bookends WHERE id = ?
            ''', (show['outro_bookend_id'],)).fetchone()

        # Build show structure
        show_export = {
            'show_id': show_id,
            'title': show['title'],
            'article': {
                'text': show['article_text'],
                'url': show['article_url'],
                'source': show['article_source']
            },
            'intro': dict(intro) if intro else None,
            'reactions': [dict(r) for r in reactions],
            'outro': dict(outro) if outro else None,
            'stats': {
                'total_reactions': show['total_reactions'],
                'approved_reactions': show['approved_reactions'],
                'total_sponsors': show['total_sponsors']
            }
        }

        return show_export

    def close_show(self, show_id: int) -> Dict:
        """Close show to new call-ins"""
        self.db.execute('''
            UPDATE live_shows
            SET status = 'closed'
            WHERE id = ?
        ''', (show_id,))
        self.db.commit()

        return {'show_id': show_id, 'status': 'closed'}

    def publish_show(self, show_id: int) -> Dict:
        """Mark show as published"""
        self.db.execute('''
            UPDATE live_shows
            SET status = 'published',
                published_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (show_id,))

        # Mark all approved reactions as aired
        self.db.execute('''
            UPDATE show_reactions
            SET approval_status = 'aired'
            WHERE show_id = ? AND approval_status = 'approved'
        ''', (show_id,))

        self.db.commit()

        return {'show_id': show_id, 'status': 'published'}


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Live Call-In Show System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create show
    create_parser = subparsers.add_parser('create', help='Create new show')
    create_parser.add_argument('title', help='Show title')
    create_parser.add_argument('--article-text', help='Article text')
    create_parser.add_argument('--article-url', help='Article URL')
    create_parser.add_argument('--article-source', help='Publication name')

    # Submit call-in
    callin_parser = subparsers.add_parser('call-in', help='Submit call-in')
    callin_parser.add_argument('show_id', type=int, help='Show ID')
    callin_parser.add_argument('--recording-id', type=int, required=True)
    callin_parser.add_argument('--name', help='Caller name (John from Tampa)')
    callin_parser.add_argument('--type', default='comment', help='Reaction type')

    # Approve reaction
    approve_parser = subparsers.add_parser('approve', help='Approve reaction')
    approve_parser.add_argument('reaction_id', type=int, help='Reaction ID')

    # Add sponsor
    sponsor_parser = subparsers.add_parser('add-sponsor', help='Add sponsor')
    sponsor_parser.add_argument('show_id', type=int, help='Show ID')
    sponsor_parser.add_argument('name', help='Sponsor name')
    sponsor_parser.add_argument('--keywords', nargs='+', help='Keywords')

    # Pair sponsor
    pair_parser = subparsers.add_parser('pair-sponsor', help='Pair reaction with sponsor')
    pair_parser.add_argument('reaction_id', type=int, help='Reaction ID')
    pair_parser.add_argument('--sponsor-id', type=int, required=True)

    # Auto-pair
    autopair_parser = subparsers.add_parser('auto-pair', help='Auto-pair sponsors')
    autopair_parser.add_argument('show_id', type=int, help='Show ID')

    # Generate bookend
    bookend_parser = subparsers.add_parser('bookend', help='Generate bookend')
    bookend_parser.add_argument('show_id', type=int, help='Show ID')
    bookend_parser.add_argument('--type', required=True, choices=['intro', 'outro'])

    # Get queue
    queue_parser = subparsers.add_parser('queue', help='View call-in queue')
    queue_parser.add_argument('show_id', type=int, help='Show ID')
    queue_parser.add_argument('--status', help='Filter by status')

    # Export show
    export_parser = subparsers.add_parser('export', help='Export show')
    export_parser.add_argument('show_id', type=int, help='Show ID')

    args = parser.parse_args()

    show_system = LiveCallInShow()

    if args.command == 'create':
        result = show_system.create_show(
            title=args.title,
            article_text=args.article_text or "Article content here",
            article_url=args.article_url,
            article_source=args.article_source
        )
        print(f"\n✅ Show created: #{result['show_id']}")
        print(f"   Title: {result['title']}")
        print(f"   Call-in URL: {result['call_in_url']}")
        print(f"   Host dashboard: {result['host_dashboard']}\n")

    elif args.command == 'call-in':
        result = show_system.submit_call_in(
            show_id=args.show_id,
            recording_id=args.recording_id,
            caller_name=args.name,
            reaction_type=args.type
        )
        print(f"\n📞 Call-in submitted: #{result['reaction_id']}")
        print(f"   Status: {result['status']}")
        if result['transcription']:
            print(f"   Transcription: {result['transcription'][:100]}...\n")

    elif args.command == 'approve':
        result = show_system.approve_reaction(args.reaction_id)
        print(f"\n✅ Reaction #{result['reaction_id']} approved\n")

    elif args.command == 'add-sponsor':
        result = show_system.add_sponsor(
            show_id=args.show_id,
            sponsor_name=args.name,
            keywords=args.keywords
        )
        print(f"\n💰 Sponsor added: #{result['sponsor_id']}")
        print(f"   Name: {result['sponsor_name']}")
        print(f"   Keywords: {result['keywords']}\n")

    elif args.command == 'pair-sponsor':
        result = show_system.pair_reaction_with_sponsor(
            reaction_id=args.reaction_id,
            sponsor_id=args.sponsor_id
        )
        print(f"\n🤝 Pairing created:")
        print(f"   Score: {result['pairing_score']:.1f}")
        print(f"   Reason: {result['pairing_reason']}\n")

    elif args.command == 'auto-pair':
        pairings = show_system.auto_pair_sponsors(args.show_id)
        print(f"\n🤖 Auto-paired {len(pairings)} reactions with sponsors\n")

    elif args.command == 'bookend':
        result = show_system.generate_bookend(args.show_id, args.type)
        print(f"\n🎙️ {result['type'].title()} bookend generated:")
        print(f"\n{result['script']}\n")
        print(f"Sponsors mentioned: {', '.join(result['sponsors'])}\n")

    elif args.command == 'queue':
        reactions = show_system.get_show_queue(args.show_id, args.status)
        print(f"\n📋 Call-in queue ({len(reactions)} reactions):\n")
        for r in reactions:
            print(f"#{r['id']} - {r['caller_name'] or 'Anonymous'} ({r['approval_status']})")
            if r['transcription']:
                print(f"   {r['transcription'][:80]}...")
            if r['sponsor_name']:
                print(f"   💰 Paired with: {r['sponsor_name']}")
            print()

    elif args.command == 'export':
        show = show_system.export_show(args.show_id)
        print(f"\n📦 Exported show: {show['title']}\n")
        print(f"Stats:")
        print(f"  - Total reactions: {show['stats']['total_reactions']}")
        print(f"  - Approved: {show['stats']['approved_reactions']}")
        print(f"  - Sponsors: {show['stats']['total_sponsors']}\n")

        if show['intro']:
            print("Intro bookend: ✅")
        if show['outro']:
            print("Outro bookend: ✅")

        print(f"\nShow JSON saved to: show_{args.show_id}_export.json")

        with open(f'show_{args.show_id}_export.json', 'w') as f:
            json.dump(show, f, indent=2, default=str)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
