# Google Business Profile Integration - Architecture

## Overview

Integrate Google Business Profile (formerly Google My Business) with StPetePros to automatically sync professional listings, pull real Google reviews, and manage business information.

## User Flow

```
Professional Signs Up → Create/Sync Google Business Profile → Pull Reviews → Display on StPetePros
```

## What You Get

### For Professionals
- **Auto-create Google Business Profile** from StPetePros listing
- **Sync business info** (name, phone, address, hours, photos)
- **QR code** links to both StPetePros profile AND Google Business Profile
- **Real Google reviews** displayed on StPetePros profile
- **Manage from one dashboard** (StPetePros becomes the control panel)

### For Customers
- **Real reviews** - See actual Google reviews, not fake ones
- **Verified listings** - If it's on Google, it's real
- **Consistent info** - Phone/address synced across platforms
- **SEO boost** - StPetePros profiles rank higher with Google integration

## Google Business Profile API

### Authentication
- **OAuth 2.0** - Professionals authorize StPetePros to manage their Google Business Profile
- **Scopes needed:**
  - `https://www.googleapis.com/auth/business.manage` - Full access to manage listings
  - `https://www.googleapis.com/auth/plus.business.manage` - Manage Google+ pages (legacy)

### Key APIs

#### 1. My Business Account Management API
```
GET https://mybusinessaccountmanagement.googleapis.com/v1/accounts
```
Returns all Google Business accounts the user can access.

#### 2. My Business Business Information API
```
GET https://mybusinessbusinessinformation.googleapis.com/v1/locations/{locationId}
POST https://mybusinessbusinessinformation.googleapis.com/v1/accounts/{accountId}/locations
PATCH https://mybusinessbusinessinformation.googleapis.com/v1/locations/{locationId}
```
Create, read, update business info (name, phone, address, categories, hours).

#### 3. My Business Reviews API
```
GET https://mybusiness.googleapis.com/v4/accounts/{accountId}/locations/{locationId}/reviews
```
Pull real Google reviews (rating, text, reviewer name, date).

#### 4. My Business Photos API
```
POST https://mybusinessbusinessinformation.googleapis.com/v1/locations/{locationId}/media
```
Upload business photos (logo, cover, interior, team).

## Database Schema Changes

### New Table: `google_business_profiles`
```sql
CREATE TABLE google_business_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professional_id INTEGER NOT NULL,
    google_account_id TEXT,           -- Google account ID
    google_location_id TEXT UNIQUE,   -- Google Business Profile location ID
    google_place_id TEXT,              -- Google Maps place ID
    sync_enabled BOOLEAN DEFAULT 1,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professional_id) REFERENCES professionals(id)
);
```

### New Table: `google_reviews`
```sql
CREATE TABLE google_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professional_id INTEGER NOT NULL,
    google_review_id TEXT UNIQUE,
    reviewer_name TEXT,
    rating INTEGER,                    -- 1-5 stars
    review_text TEXT,
    review_reply TEXT,                 -- Professional's reply
    created_at TIMESTAMP,              -- When review was posted on Google
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professional_id) REFERENCES professionals(id)
);
```

### Modify: `professionals` table
```sql
ALTER TABLE professionals ADD COLUMN google_connected BOOLEAN DEFAULT 0;
ALTER TABLE professionals ADD COLUMN google_access_token TEXT;
ALTER TABLE professionals ADD COLUMN google_refresh_token TEXT;
ALTER TABLE professionals ADD COLUMN google_token_expires_at TIMESTAMP;
```

## Routes to Add

### 1. `/professional/<id>/connect-google` (GET)
OAuth flow start - redirects to Google authorization page.

```python
@stpetepros_bp.route('/professional/<int:professional_id>/connect-google')
@auth_bridge.require_auth
def connect_google(professional_id):
    """Initiate Google Business Profile OAuth"""
    oauth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        "redirect_uri=https://stpetepros.com/google-callback&"
        "response_type=code&"
        "scope=https://www.googleapis.com/auth/business.manage&"
        f"state={professional_id}"
    )
    return redirect(oauth_url)
```

### 2. `/google-callback` (GET)
OAuth callback - exchanges code for access token.

```python
@stpetepros_bp.route('/google-callback')
def google_callback():
    """Handle Google OAuth callback"""
    code = request.args.get('code')
    professional_id = request.args.get('state')

    # Exchange code for access token
    token_response = requests.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': 'https://stpetepros.com/google-callback',
        'grant_type': 'authorization_code'
    })

    tokens = token_response.json()

    # Store tokens in database
    db.execute('''
        UPDATE professionals
        SET google_access_token = ?,
            google_refresh_token = ?,
            google_token_expires_at = ?,
            google_connected = 1
        WHERE id = ?
    ''', (
        tokens['access_token'],
        tokens['refresh_token'],
        datetime.now() + timedelta(seconds=tokens['expires_in']),
        professional_id
    ))
    db.commit()

    flash('Google Business Profile connected!', 'success')
    return redirect(url_for('stpetepros.professional_profile', professional_id=professional_id))
```

### 3. `/professional/<id>/sync-google` (POST)
Sync business info from StPetePros → Google.

```python
@stpetepros_bp.route('/professional/<int:professional_id>/sync-google', methods=['POST'])
@auth_bridge.require_auth
def sync_google(professional_id):
    """Sync professional info to Google Business Profile"""
    db = get_db()

    # Get professional info
    pro = db.execute('SELECT * FROM professionals WHERE id = ?', (professional_id,)).fetchone()

    # Get Google access token
    access_token = pro['google_access_token']

    # Refresh token if expired
    if datetime.now() >= pro['google_token_expires_at']:
        access_token = refresh_google_token(pro['google_refresh_token'])

    # Get Google account and location
    accounts = requests.get(
        'https://mybusinessaccountmanagement.googleapis.com/v1/accounts',
        headers={'Authorization': f'Bearer {access_token}'}
    ).json()

    account_id = accounts['accounts'][0]['name']

    # Create or update location
    location_data = {
        'title': pro['business_name'],
        'languageCode': 'en-US',
        'storeCode': f"stpetepros-{professional_id}",
        'phoneNumbers': {
            'primaryPhone': pro['phone']
        },
        'categories': {
            'primaryCategory': {
                'displayName': pro['category']
            }
        },
        'storefrontAddress': {
            'addressLines': [pro['address']],
            'locality': pro['city'],
            'administrativeArea': pro['state'],
            'postalCode': pro['zip_code'],
            'regionCode': 'US'
        },
        'websiteUri': f"https://stpetepros.com/professional/{professional_id}",
        'profile': {
            'description': pro['bio']
        }
    }

    # Check if location exists
    google_profile = db.execute(
        'SELECT * FROM google_business_profiles WHERE professional_id = ?',
        (professional_id,)
    ).fetchone()

    if google_profile:
        # Update existing location
        location_id = google_profile['google_location_id']
        response = requests.patch(
            f'https://mybusinessbusinessinformation.googleapis.com/v1/{location_id}',
            headers={'Authorization': f'Bearer {access_token}'},
            json=location_data
        )
    else:
        # Create new location
        response = requests.post(
            f'https://mybusinessbusinessinformation.googleapis.com/v1/{account_id}/locations',
            headers={'Authorization': f'Bearer {access_token}'},
            json=location_data
        )

        location_id = response.json()['name']

        # Store in database
        db.execute('''
            INSERT INTO google_business_profiles
            (professional_id, google_account_id, google_location_id, last_sync_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (professional_id, account_id, location_id))
        db.commit()

    return jsonify({'success': True, 'location_id': location_id})
```

### 4. `/professional/<id>/pull-google-reviews` (POST)
Pull reviews from Google → StPetePros.

```python
@stpetepros_bp.route('/professional/<int:professional_id>/pull-google-reviews', methods=['POST'])
@auth_bridge.require_auth
def pull_google_reviews(professional_id):
    """Pull Google reviews and display on StPetePros"""
    db = get_db()

    # Get Google profile
    google_profile = db.execute(
        'SELECT * FROM google_business_profiles WHERE professional_id = ?',
        (professional_id,)
    ).fetchone()

    if not google_profile:
        return jsonify({'error': 'Google Business Profile not connected'}), 400

    # Get professional
    pro = db.execute('SELECT * FROM professionals WHERE id = ?', (professional_id,)).fetchone()
    access_token = pro['google_access_token']

    # Pull reviews from Google
    account_id = google_profile['google_account_id']
    location_id = google_profile['google_location_id']

    reviews_response = requests.get(
        f'https://mybusiness.googleapis.com/v4/{location_id}/reviews',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    reviews = reviews_response.json().get('reviews', [])

    # Store in database
    for review in reviews:
        db.execute('''
            INSERT OR REPLACE INTO google_reviews
            (professional_id, google_review_id, reviewer_name, rating, review_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            professional_id,
            review['reviewId'],
            review.get('reviewer', {}).get('displayName', 'Anonymous'),
            review.get('starRating', 5),
            review.get('comment', ''),
            review.get('createTime')
        ))

    db.commit()

    # Update average rating on professionals table
    avg_rating = sum(r['starRating'] for r in reviews) / len(reviews) if reviews else 0
    db.execute(
        'UPDATE professionals SET rating_avg = ?, rating_count = ? WHERE id = ?',
        (avg_rating, len(reviews), professional_id)
    )
    db.commit()

    return jsonify({'success': True, 'count': len(reviews)})
```

## Frontend Integration

### Professional Profile Page (templates/stpetepros/profile.html)

Replace the "Google Reviews (coming soon)" section with:

```html
{% if professional['google_connected'] %}
  <!-- Real Google Reviews -->
  <div class="bg-white p-8 rounded-xl border border-slate-200 mb-8">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-2xl font-bold text-slate-900">Google Reviews ({{ google_reviews|length }})</h2>
      <form action="/professional/{{ professional['id'] }}/pull-google-reviews" method="POST">
        <button type="submit" class="text-sm bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600">
          Sync Reviews
        </button>
      </form>
    </div>

    {% for review in google_reviews %}
      <div class="bg-slate-50 p-6 rounded-lg mb-4">
        <div class="flex justify-between mb-3">
          <span class="font-semibold text-slate-900">{{ review['reviewer_name'] }}</span>
          <span class="text-amber-500">
            {% for i in range(review['rating']) %}<span class="font-bold">★</span>{% endfor %}
          </span>
        </div>
        <div class="text-slate-600 leading-relaxed">{{ review['review_text'] }}</div>
        <div class="text-slate-500 text-sm mt-2">{{ review['created_at']|date }}</div>
      </div>
    {% endfor %}
  </div>
{% else %}
  <!-- Connect Google Business Profile -->
  <div class="bg-white p-8 rounded-xl border border-slate-200 mb-8">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">Connect Google Business Profile</h2>
    <p class="text-slate-600 mb-6">
      Connect your Google Business Profile to pull real reviews and manage your listing.
    </p>
    <a href="/professional/{{ professional['id'] }}/connect-google"
       class="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
      Connect with Google
    </a>
  </div>
{% endif %}
```

## Environment Variables

Add to `.env`:

```bash
# Google Business Profile API
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=https://stpetepros.com/google-callback
```

## Setup Steps

### 1. Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Create new project: "StPetePros Integration"
3. Enable APIs:
   - My Business Account Management API
   - My Business Business Information API
   - My Business Reviews API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `https://stpetepros.com/google-callback`
5. Copy Client ID and Client Secret to `.env`

### 2. Request API Access
Google Business Profile API requires verification:
1. Fill out verification form: https://developers.google.com/my-business/content/prereqs
2. Explain use case: "Professional directory syncing business listings"
3. Wait for approval (2-4 weeks)

### 3. Database Migration
```bash
sqlite3 soulfra.db < migrations/add_google_business_profile.sql
```

### 4. Test OAuth Flow
1. Go to `/professional/1/connect-google`
2. Authorize with Google account
3. Should redirect back with tokens
4. Click "Sync to Google" - creates Google Business Profile
5. Click "Pull Reviews" - displays Google reviews

## Benefits

### For StPetePros
- **Real reviews** - Not fake, verified by Google
- **Higher trust** - If it's on Google, it's real
- **SEO boost** - Google prioritizes businesses with profiles
- **Competitive advantage** - Yelp/Angi don't have this level of integration

### For Professionals
- **One dashboard** - Manage StPetePros + Google from one place
- **Free Google listing** - StPetePros creates it for you
- **More visibility** - Listed on both platforms
- **Centralized reviews** - All reviews in one place

### For Customers
- **Verified reviews** - Can't fake Google reviews
- **Consistent info** - Phone/address always up to date
- **Trust signals** - Real businesses with real Google presence

## Cost

- **Google API:** FREE (no quota limits for My Business API)
- **OAuth:** FREE
- **Development time:** ~8 hours
  - 2 hours: OAuth setup
  - 3 hours: Sync business info
  - 2 hours: Pull reviews
  - 1 hour: Frontend integration

## Next Steps

1. ✅ Architecture documented (this file)
2. ⏳ Create Google Cloud project
3. ⏳ Request API access (2-4 week wait)
4. ⏳ Database migration
5. ⏳ Implement OAuth routes
6. ⏳ Implement sync routes
7. ⏳ Frontend integration
8. ⏳ Test with real professionals

## References

- [Google My Business API Docs](https://developers.google.com/my-business)
- [OAuth 2.0 Setup](https://developers.google.com/identity/protocols/oauth2)
- [Business Information API](https://developers.google.com/my-business/reference/businessinformation/rest)
- [Reviews API](https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews)
