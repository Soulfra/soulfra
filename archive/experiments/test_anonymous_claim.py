#!/usr/bin/env python3
"""
Test Anonymous Play → Signup → Claim Flow

Tests the complete user journey:
1. Play cringeproof anonymously
2. Get result with user_id=NULL
3. Click "Create Account & Save This Result"
4. Signup with ?claim_result=<id>
5. Verify result claimed (user_id updated)
"""

import requests
import json
from database import get_db

BASE_URL = "http://localhost:5001"

def test_anonymous_claim_flow():
    """Test complete anonymous → signup → claim flow"""

    print("=" * 80)
    print("TEST: Anonymous Play → Signup → Claim Flow")
    print("=" * 80)

    # Step 1: Play cringeproof anonymously
    print("\n[STEP 1] Playing cringeproof anonymously...")

    session = requests.Session()

    # GET /cringeproof to start
    response = session.get(f"{BASE_URL}/cringeproof")
    if response.status_code != 200:
        print(f"❌ Failed to load cringeproof page: {response.status_code}")
        return False

    print("✅ Loaded cringeproof game page")

    # Submit answers (simulate gameplay)
    # All questions use radio buttons with values 1-5
    answers = {
        'q1': '3',  # Question 1 - select option 3
        'q2': '2',  # Question 2 - select option 2
        'q3': '4',  # Question 3 - select option 4
        'q4': '1',  # Question 4 - select option 1
        'q5': '5',  # Question 5 - select option 5
        'q6': '3',  # Question 6 - select option 3
        'q7': '2'   # Question 7 - select option 2
    }

    print(f"Submitting answers: {json.dumps(answers, indent=2)}")

    response = session.post(f"{BASE_URL}/cringeproof/submit", data=answers, allow_redirects=False)

    if response.status_code not in [302, 303]:
        print(f"❌ Failed to submit answers: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return False

    # Get redirect URL (should be /cringeproof/results/<id>)
    redirect_url = response.headers.get('Location', '')
    print(f"✅ Game submitted, redirecting to: {redirect_url}")

    if '/cringeproof/results/' not in redirect_url:
        print(f"❌ Unexpected redirect URL: {redirect_url}")
        return False

    # Extract result_id from redirect URL
    result_id = redirect_url.split('/cringeproof/results/')[-1].split('?')[0]
    print(f"✅ Result ID: {result_id}")

    # Step 2: Verify result is anonymous (user_id=NULL)
    print(f"\n[STEP 2] Verifying result {result_id} is anonymous...")

    db = get_db()
    result_row = db.execute('SELECT * FROM game_results WHERE id = ?', (result_id,)).fetchone()

    if not result_row:
        print(f"❌ Result {result_id} not found in database")
        return False

    if result_row['user_id'] is not None:
        print(f"❌ Result already has user_id: {result_row['user_id']}")
        return False

    print(f"✅ Result {result_id} is anonymous (user_id=NULL)")
    print(f"   Game type: {result_row['game_type']}")
    print(f"   Created at: {result_row['created_at']}")

    # Step 3: View results page and verify "Save Your Results" prompt
    print(f"\n[STEP 3] Viewing results page...")

    response = session.get(f"{BASE_URL}/cringeproof/results/{result_id}")

    if response.status_code != 200:
        print(f"❌ Failed to load results page: {response.status_code}")
        return False

    html = response.text

    if '💾 Save Your Results!' not in html:
        print(f"❌ Results page missing 'Save Your Results!' prompt")
        return False

    if f'/signup?claim_result={result_id}' not in html:
        print(f"❌ Results page missing signup link with claim_result parameter")
        return False

    print(f"✅ Results page shows signup prompt with claim link")

    # Step 4: Create account with claim_result parameter
    print(f"\n[STEP 4] Creating account to claim result...")

    # Generate unique username
    import time
    username = f"testuser_{int(time.time())}"
    email = f"{username}@test.com"
    password = "testpass123"

    signup_data = {
        'username': username,
        'email': email,
        'password': password,
        'claim_result': result_id  # This is the key parameter
    }

    print(f"Signing up as: {username}")

    response = session.post(f"{BASE_URL}/signup", data=signup_data, allow_redirects=False)

    if response.status_code not in [302, 303]:
        print(f"❌ Signup failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return False

    signup_redirect = response.headers.get('Location', '')
    print(f"✅ Signup successful, redirecting to: {signup_redirect}")

    # Should redirect back to results page
    if f'/cringeproof/results/{result_id}' not in signup_redirect:
        print(f"⚠️  Warning: Expected redirect to results page, got: {signup_redirect}")

    # Step 5: Verify result was claimed
    print(f"\n[STEP 5] Verifying result was claimed...")

    # Get user_id for new user
    user_row = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if not user_row:
        print(f"❌ User {username} not found in database")
        return False

    new_user_id = user_row['id']
    print(f"✅ New user created with ID: {new_user_id}")

    # Check if result was updated
    result_row = db.execute('SELECT * FROM game_results WHERE id = ?', (result_id,)).fetchone()

    if result_row['user_id'] != new_user_id:
        print(f"❌ Result not claimed! user_id is: {result_row['user_id']} (expected {new_user_id})")
        return False

    print(f"✅ Result {result_id} successfully claimed by user {new_user_id}")

    # Step 6: Verify results page now shows confirmation
    print(f"\n[STEP 6] Verifying results page shows confirmation...")

    response = session.get(f"{BASE_URL}/cringeproof/results/{result_id}")

    if response.status_code != 200:
        print(f"❌ Failed to load results page: {response.status_code}")
        return False

    html = response.text

    if '✅ Results saved to your profile!' not in html:
        print(f"❌ Results page missing confirmation message")
        # Check what we got instead
        if '💾 Save Your Results!' in html:
            print(f"⚠️  Still showing signup prompt (expected confirmation)")
        return False

    print(f"✅ Results page shows confirmation message")

    # Clean up test user
    print(f"\n[CLEANUP] Deleting test user and result...")
    db.execute('DELETE FROM game_results WHERE id = ?', (result_id,))
    db.execute('DELETE FROM users WHERE id = ?', (new_user_id,))
    db.commit()
    print(f"✅ Cleanup complete")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Anonymous claim flow works!")
    print("=" * 80)

    return True


if __name__ == '__main__':
    try:
        success = test_anonymous_claim_flow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
