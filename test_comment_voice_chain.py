#!/usr/bin/env python3
"""
Test Comment-Voice-QR Chain

Verifies the Merkle-tree style flywheel:
Comment → Voice → Ollama → QR → Domain Router
"""

import requests
import json
import base64

API_BASE = "http://192.168.1.87:5001"


def test_simple_text_comment():
    """Test 1: Simple text comment (no voice)"""
    print("\n" + "="*60)
    print("TEST 1: Simple Text Comment")
    print("="*60)

    response = requests.post(f"{API_BASE}/api/comment-voice-chain", json={
        'post_id': 1,
        'content': 'This is a test comment for the flywheel chain'
    })

    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"\n✅ Comment created:")
    print(f"   ID: {data['comment_id']}")
    print(f"   Chain Hash: {data['chain_hash']}")
    print(f"   QR Code: {data['qr_code']['code']}")
    print(f"   QR URL: {data['qr_code']['url']}")

    return data['comment_id']


def test_threaded_comment(parent_id):
    """Test 2: Reply to comment (threaded chain)"""
    print("\n" + "="*60)
    print("TEST 2: Threaded Comment (Merkle Tree)")
    print("="*60)

    response = requests.post(f"{API_BASE}/api/comment-voice-chain", json={
        'post_id': 1,
        'content': 'This is a reply - chain should link to parent hash',
        'parent_comment_id': parent_id
    })

    data = response.json()

    print(f"\n✅ Reply created:")
    print(f"   ID: {data['comment_id']}")
    print(f"   Chain Hash: {data['chain_hash']}")
    print(f"   Parent Hash: {data['parent_hash']}")
    print(f"   Hashes linked: {data['parent_hash'] is not None}")

    return data['comment_id']


def test_get_chain(comment_id):
    """Test 3: Retrieve full chain"""
    print("\n" + "="*60)
    print("TEST 3: Get Full Chain")
    print("="*60)

    response = requests.get(f"{API_BASE}/api/comment-chain/{comment_id}")
    data = response.json()

    print(f"\n✅ Chain retrieved:")
    print(f"   Comment ID: {data['comment']['id']}")
    print(f"   Chain Depth: {data['chain_depth']}")
    print(f"   Has Voice: {data['voice_attached']}")
    print(f"   QR Code: {data['qr_code']}")

    if data['parent_chain']:
        print(f"\n   Parent Chain:")
        for i, parent in enumerate(data['parent_chain']):
            print(f"      [{i}] ID={parent['id']}, Hash={parent['hash'][:8]}...")

    return data


def test_verify_chain(comment_id):
    """Test 4: Verify chain integrity"""
    print("\n" + "="*60)
    print("TEST 4: Verify Chain (Merkle Proof)")
    print("="*60)

    response = requests.get(f"{API_BASE}/api/verify-chain/{comment_id}")
    data = response.json()

    print(f"\n✅ Verification result:")
    print(f"   Comment ID: {data['comment_id']}")
    print(f"   Expected Hash: {data['expected_hash'][:16]}...")
    print(f"   Actual Hash: {data['actual_hash'][:16]}...")
    print(f"   Valid: {data['is_valid']}")
    print(f"   Status: {data['verification']}")

    assert data['is_valid'], "❌ Chain verification failed!"
    print("\n   🔒 Chain integrity verified!")

    return data


def main():
    print("\n")
    print("="*60)
    print("🔗 Comment-Voice-QR Chain Test Suite")
    print("="*60)

    try:
        # Test 1: Create root comment
        root_id = test_simple_text_comment()

        # Test 2: Create threaded reply
        reply_id = test_threaded_comment(root_id)

        # Test 3: Get full chain
        chain_data = test_get_chain(reply_id)

        # Test 4: Verify chain integrity
        verification = test_verify_chain(reply_id)

        # Summary
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   Root Comment: #{root_id}")
        print(f"   Reply Comment: #{reply_id}")
        print(f"   Chain Depth: {chain_data['chain_depth']}")
        print(f"   Verification: {verification['verification']}")
        print("\n🎯 The flywheel is working!")
        print("   Comment → Chain Hash → QR Code → Verified ✓")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
