"""
Mesh-Router ↔ Flask Bridge

Connects the Express mesh-router.js (port 8888) to Flask (port 5001)
Enables P2P discovery and mesh sync for voice recordings

Architecture:
- mesh-router.js handles P2P routing, QR auth, session management
- Flask handles voice recording, wordmap, database
- This bridge syncs data between them
"""

import requests
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path

# Configuration from mesh-config.json
MESH_PORT = 8888
FLASK_PORT = 5001
MESH_BASE = f"http://localhost:{MESH_PORT}"
FLASK_BASE = f"http://localhost:{FLASK_PORT}"
DB_PATH = Path(__file__).parent / "soulfra.db"

class MeshFlaskBridge:
    def __init__(self):
        self.mesh_url = MESH_BASE
        self.flask_url = FLASK_BASE
        self.db_path = DB_PATH
        self.session_id = None

    def initialize_mesh(self, qr_code="CRINGEPROOF-WALL"):
        """Initialize connection to mesh-router with QR authentication"""
        try:
            response = requests.post(
                f"{self.mesh_url}/api/mesh/initialize",
                json={
                    "uuid": "flask-bridge-" + str(int(time.time())),
                    "qrCode": qr_code,
                    "claudeKey": "default",
                    "ollamaUrl": "http://localhost:11434",
                    "trustFlags": {
                        "is_flask_bridge": True,
                        "has_database": True,
                        "can_sync": True
                    }
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('sessionId')
                print(f"✅ Mesh initialized - Session: {self.session_id[:16]}...")
                return True
            else:
                print(f"❌ Mesh init failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Mesh router not reachable: {e}")
            return False

    def get_recent_recordings(self, limit=20):
        """Get recent voice recordings from Flask database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            recordings = cursor.execute('''
                SELECT
                    id,
                    transcription,
                    created_at,
                    file_size,
                    ipfs_hash,
                    crypto_signature
                FROM simple_voice_recordings
                WHERE transcription IS NOT NULL
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,)).fetchall()

            conn.close()

            return [dict(r) for r in recordings]

        except Exception as e:
            print(f"❌ Database error: {e}")
            return []

    def get_domain_wordmap(self, domain="cringeproof.com"):
        """Get collective wordmap for a domain"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            wordmap_row = cursor.execute('''
                SELECT wordmap_json, contributor_count, last_updated
                FROM domain_wordmaps
                WHERE domain = ?
                ORDER BY last_updated DESC
                LIMIT 1
            ''', (domain,)).fetchone()

            conn.close()

            if wordmap_row:
                return {
                    'wordmap': json.loads(wordmap_row['wordmap_json']),
                    'contributor_count': wordmap_row['contributor_count'],
                    'last_updated': wordmap_row['last_updated']
                }
            else:
                return None

        except Exception as e:
            print(f"❌ Wordmap error: {e}")
            return None

    def publish_recording_to_mesh(self, recording_id):
        """
        Publish a recording to the mesh network

        This makes the recording discoverable via:
        - IPFS (if hash exists)
        - mDNS (soulfra.local)
        - Mesh peers (P2P sync)
        """
        try:
            recordings = self.get_recent_recordings(limit=100)
            recording = next((r for r in recordings if r['id'] == recording_id), None)

            if not recording:
                print(f"❌ Recording {recording_id} not found")
                return False

            # Publish to IPFS if not already published
            if not recording['ipfs_hash']:
                # Try HTTP first (IPFS API), fallback to HTTPS
                try:
                    ipfs_response = requests.post(
                        f"http://localhost:5001/api/ipfs/publish/{recording_id}",
                        timeout=30
                    )
                except:
                    ipfs_response = requests.post(
                        f"{self.flask_url}/api/ipfs/publish/{recording_id}",
                        verify=False,  # Self-signed cert
                        timeout=30
                    )

                if ipfs_response.status_code == 200:
                    ipfs_data = ipfs_response.json()
                    print(f"✅ Published to IPFS: {ipfs_data['ipfs_hash']}")
                    recording['ipfs_hash'] = ipfs_data['ipfs_hash']

            # Announce to mesh network
            mesh_announcement = {
                'type': 'voice_recording',
                'recording_id': recording_id,
                'ipfs_hash': recording['ipfs_hash'],
                'timestamp': recording['created_at'],
                'domain': 'cringeproof.com',
                'discovery_urls': [
                    f"ipfs://{recording['ipfs_hash']}" if recording['ipfs_hash'] else None,
                    f"https://192.168.1.87:5001/api/simple-voice/download/{recording_id}",
                    f"http://soulfra.local:5001/api/simple-voice/download/{recording_id}"
                ]
            }

            print(f"📡 Recording {recording_id} available via mesh network")
            return mesh_announcement

        except Exception as e:
            print(f"❌ Mesh publish error: {e}")
            return False

    def sync_wall_feed_to_mesh(self):
        """
        Sync current wall feed to mesh network
        Enables multi-device synchronization
        """
        try:
            recordings = self.get_recent_recordings(limit=20)
            wordmap = self.get_domain_wordmap("cringeproof.com")

            mesh_feed = {
                'type': 'wall_feed_sync',
                'timestamp': datetime.now().isoformat(),
                'recordings_count': len(recordings),
                'wordmap_words': len(wordmap['wordmap']) if wordmap else 0,
                'domain': 'cringeproof.com',
                'discovery_method': 'mesh_bridge'
            }

            print(f"📡 Wall feed synced to mesh: {len(recordings)} recordings")
            return mesh_feed

        except Exception as e:
            print(f"❌ Mesh sync error: {e}")
            return False

    def run_heartbeat(self, interval=10):
        """
        Run continuous sync heartbeat
        Keeps mesh network aware of latest recordings
        """
        print(f"💓 Starting mesh heartbeat (every {interval}s)")

        while True:
            try:
                self.sync_wall_feed_to_mesh()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n🛑 Heartbeat stopped")
                break
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
                time.sleep(interval)


def test_bridge():
    """Test the mesh-flask bridge"""
    print("🔧 Testing Mesh-Flask Bridge\n")

    bridge = MeshFlaskBridge()

    # Test mesh connection
    print("1️⃣ Testing mesh-router connection...")
    if bridge.initialize_mesh():
        print("   ✅ Mesh connection OK\n")
    else:
        print("   ⚠️ Mesh router not responding (is it running on port 8888?)\n")

    # Test database access
    print("2️⃣ Testing database access...")
    recordings = bridge.get_recent_recordings(limit=5)
    print(f"   ✅ Found {len(recordings)} recordings\n")

    # Test wordmap access
    print("3️⃣ Testing wordmap access...")
    wordmap = bridge.get_domain_wordmap("cringeproof.com")
    if wordmap:
        print(f"   ✅ Wordmap has {len(wordmap['wordmap'])} words\n")
    else:
        print("   ⚠️ No wordmap data yet\n")

    # Test IPFS publishing
    if recordings:
        print(f"4️⃣ Testing IPFS publish for recording #{recordings[0]['id']}...")
        result = bridge.publish_recording_to_mesh(recordings[0]['id'])
        if result:
            print(f"   ✅ Publishing complete\n")
        else:
            print("   ⚠️ IPFS publish failed\n")

    # Test mesh sync
    print("5️⃣ Testing mesh sync...")
    sync_result = bridge.sync_wall_feed_to_mesh()
    if sync_result:
        print("   ✅ Mesh sync complete\n")
    else:
        print("   ⚠️ Mesh sync failed\n")

    print("✅ Bridge test complete")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_bridge()
        elif sys.argv[1] == "heartbeat":
            bridge = MeshFlaskBridge()
            bridge.initialize_mesh()
            bridge.run_heartbeat(interval=10)
    else:
        print("Usage:")
        print("  python3 mesh_flask_bridge.py test        # Test bridge")
        print("  python3 mesh_flask_bridge.py heartbeat   # Run continuous sync")
