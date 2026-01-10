#!/usr/bin/env python3
"""
Soul Compiler for Soulfra
Like Go compiler, but for souls

Compiles user data → soul packs:
- Reads raw user data (posts, comments, interactions)
- Extracts essence (interests, values, expertise)
- Generates soul fingerprint for similarity matching
- Exports as JSON/YAML for marketing, products, portability

Usage:
    python soul_compiler.py --user alice
    python soul_compiler.py --all
    python soul_compiler.py --export alice.json
    python soul_compiler.py --compare alice bob
"""

import argparse
import json
import sys
from soul_model import Soul
from database import get_db


class SoulCompiler:
    """Compiles souls from user data"""

    def __init__(self):
        self.compiled = {}

    def compile_user(self, user_id):
        """Compile a single user's soul"""
        try:
            soul = Soul(user_id)
            pack = soul.compile_pack()
            self.compiled[user_id] = pack
            return pack
        except Exception as e:
            print(f"❌ Error compiling soul for user {user_id}: {e}")
            return None

    def compile_all(self):
        """Compile all users"""
        conn = get_db()
        users = conn.execute('SELECT id, username FROM users').fetchall()
        conn.close()

        print(f"🔄 Compiling {len(users)} souls...\n")

        results = []
        for user in users:
            print(f"   Compiling {user['username']}...")
            pack = self.compile_user(user['id'])

            if pack:
                results.append({
                    'username': user['username'],
                    'user_id': user['id'],
                    'pack': pack
                })

        self.compiled = results
        print(f"\n✅ Compiled {len(results)} souls")
        return results

    def export_json(self, filepath):
        """Export compiled souls to JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.compiled, f, indent=2)

        print(f"✅ Exported to {filepath}")

    def compare_souls(self, user_id1, user_id2):
        """Compare two souls"""
        soul1 = Soul(user_id1)
        soul2 = Soul(user_id2)

        similarity = soul1.similarity_to(soul2)

        print(f"\n🔍 Soul Comparison\n")
        print(f"User 1: {soul1.user['username']}")
        print(f"  Interests: {soul1.extract_interests()[:5]}")
        print(f"  Activity: {len(soul1.posts)} posts, {len(soul1.comments)} comments")
        print()
        print(f"User 2: {soul2.user['username']}")
        print(f"  Interests: {soul2.extract_interests()[:5]}")
        print(f"  Activity: {len(soul2.posts)} posts, {len(soul2.comments)} comments")
        print()
        print(f"**Similarity:** {similarity:.0%}")

        return similarity

    def find_similar_souls(self, user_id, top_n=5):
        """Find most similar souls to a user"""
        soul = Soul(user_id)

        conn = get_db()
        all_users = conn.execute('SELECT id FROM users WHERE id != ?', (user_id,)).fetchall()
        conn.close()

        similarities = []
        for user in all_users:
            other_soul = Soul(user['id'])
            sim = soul.similarity_to(other_soul)

            if sim > 0:
                similarities.append({
                    'user_id': user['id'],
                    'username': other_soul.user['username'],
                    'similarity': sim
                })

        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        return similarities[:top_n]


def main():
    parser = argparse.ArgumentParser(
        description='Soul Compiler - Compile user data into soul packs'
    )

    parser.add_argument('--user', help='Compile specific user by username')
    parser.add_argument('--user-id', type=int, help='Compile specific user by ID')
    parser.add_argument('--all', action='store_true', help='Compile all users')
    parser.add_argument('--export', help='Export to JSON file')
    parser.add_argument('--compare', nargs=2, help='Compare two users by username')
    parser.add_argument('--find-similar', help='Find similar souls to user')

    args = parser.parse_args()

    compiler = SoulCompiler()

    if args.all:
        results = compiler.compile_all()

        if args.export:
            compiler.export_json(args.export)
        else:
            # Print summary
            print("\n" + "="*70)
            print("Soul Compilation Summary")
            print("="*70)
            for r in results:
                username = r['username']
                interests = r['pack']['essence']['interests'][:3]
                activity = r['pack']['fingerprint']['activity_level']
                print(f"{username:15} | Interests: {', '.join(interests):30} | Activity: {activity}")

    elif args.user:
        # Get user by username
        conn = get_db()
        user = conn.execute('SELECT id FROM users WHERE username = ?', (args.user,)).fetchone()
        conn.close()

        if not user:
            print(f"❌ User '{args.user}' not found")
            sys.exit(1)

        pack = compiler.compile_user(user['id'])

        print("\n" + "="*70)
        print(f"Soul Pack: {args.user}")
        print("="*70)
        print(json.dumps(pack, indent=2))

        if args.export:
            with open(args.export, 'w') as f:
                json.dump(pack, f, indent=2)
            print(f"\n✅ Exported to {args.export}")

    elif args.user_id:
        pack = compiler.compile_user(args.user_id)

        print("\n" + "="*70)
        print(f"Soul Pack: User #{args.user_id}")
        print("="*70)
        print(json.dumps(pack, indent=2))

    elif args.compare:
        # Get users by username
        conn = get_db()
        user1 = conn.execute('SELECT id FROM users WHERE username = ?', (args.compare[0],)).fetchone()
        user2 = conn.execute('SELECT id FROM users WHERE username = ?', (args.compare[1],)).fetchone()
        conn.close()

        if not user1 or not user2:
            print("❌ One or both users not found")
            sys.exit(1)

        compiler.compare_souls(user1['id'], user2['id'])

    elif args.find_similar:
        # Get user by username
        conn = get_db()
        user = conn.execute('SELECT id FROM users WHERE username = ?', (args.find_similar,)).fetchone()
        conn.close()

        if not user:
            print(f"❌ User '{args.find_similar}' not found")
            sys.exit(1)

        print(f"\n🔍 Finding similar souls to {args.find_similar}...\n")
        similar = compiler.find_similar_souls(user['id'])

        for s in similar:
            print(f"{s['username']:15} | Similarity: {s['similarity']:.0%}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
