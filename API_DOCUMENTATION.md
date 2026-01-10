# Soulfra API Documentation - "The Faucet"

**Base URL:** `http://192.168.1.87:5001` (development) or `https://soulfraapi.com` (production)

## Overview

The Soulfra API distributes content from one backend (soulfra-simple) to multiple domains. Think of it as a "faucet" - content created in one place flows to many destinations based on tags.

---

## Endpoints

### Health Check

```
GET /api/health
```

Check if API is running.

**Response:**
```json
{
  "status": "ok",
  "service": "soulfra-api",
  "version": "1.0"
}
```

---

### List Posts

```
GET /api/posts
```

Get all published posts with optional filtering.

**Query Parameters:**
- `tag` (optional) - Filter by tag (privacy, security, cooking, tech)
- `brand` (optional) - Filter by brand (deathtodata, calriven, soulfra)
- `limit` (optional) - Max posts to return (default 50)
- `offset` (optional) - Pagination offset (default 0)

**Examples:**
```bash
# Get all posts
curl http://localhost:5001/api/posts

# Get privacy posts for DeathToData
curl http://localhost:5001/api/posts?tag=privacy&limit=10

# Get tech posts for CalRiven
curl http://localhost:5001/api/posts?tag=tech&limit=10

# Get cooking posts
curl http://localhost:5001/api/posts?tag=cooking
```

**Response:**
```json
{
  "success": true,
  "posts": [
    {
      "id": 34,
      "title": "Understanding Privacy",
      "slug": "understanding-privacy",
      "content": "Full markdown content...",
      "excerpt": "Short summary...",
      "published_at": "2025-12-31T15:10:15",
      "brand": "deathtodata",
      "author": "admin",
      "url": "/posts/understanding-privacy"
    }
  ],
  "total": 35,
  "limit": 50,
  "offset": 0,
  "tag": null,
  "brand": null
}
```

---

### Get Single Post

```
GET /api/posts/{id}
```

Get one post by ID.

**Example:**
```bash
curl http://localhost:5001/api/posts/34
```

**Response:**
```json
{
  "success": true,
  "post": {
    "id": 34,
    "title": "Understanding Privacy",
    "slug": "understanding-privacy",
    "content": "Full markdown content...",
    "excerpt": "Short summary...",
    "published_at": "2025-12-31T15:10:15",
    "brand": "deathtodata",
    "author": "admin",
    "author_id": 1,
    "tags": ["privacy", "security", "encryption"],
    "url": "/posts/understanding-privacy"
  }
}
```

---

### Get Post by Slug

```
GET /api/posts/slug/{slug}
```

Get one post by URL slug.

**Example:**
```bash
curl http://localhost:5001/api/posts/slug/understanding-privacy
```

**Response:** Same as `/api/posts/{id}`

---

### List Tags

```
GET /api/tags
```

Get all available tags with post counts.

**Response:**
```json
{
  "success": true,
  "tags": [
    {
      "tag": "privacy",
      "post_count": 12
    },
    {
      "tag": "tech",
      "post_count": 8
    }
  ]
}
```

---

### List Brands

```
GET /api/brands
```

Get all available brands with post counts.

**Response:**
```json
{
  "success": true,
  "brands": [
    {
      "brand": "deathtodata",
      "post_count": 15
    },
    {
      "brand": "calriven",
      "post_count": 10
    }
  ]
}
```

---

## How Domains Use the API

### DeathToData (deathtodata.org)

**Purpose:** Privacy & security blog

**Content:** Posts tagged with `privacy`, `security`, `encryption`

**Implementation:**
```javascript
// Fetch privacy posts
fetch('http://soulfraapi.com/api/posts?tag=privacy&limit=10')
  .then(response => response.json())
  .then(data => {
    // Render posts in deathtodata theme
    data.posts.forEach(post => {
      renderPrivacyPost(post);
    });
  });
```

---

### CalRiven (calriven.com)

**Purpose:** Technical blog

**Content:** Posts tagged with `tech`, `programming`, `code`

**Implementation:**
```javascript
// Fetch tech posts
fetch('http://soulfraapi.com/api/posts?tag=tech&limit=10')
  .then(response => response.json())
  .then(data => {
    // Render posts in calriven theme
    data.posts.forEach(post => {
      renderTechPost(post);
    });
  });
```

---

### HowToCookAtHome (howtocookathome.com)

**Purpose:** Cooking blog

**Content:** Posts tagged with `cooking`, `recipes`, `food`

**Implementation:**
```javascript
// Fetch cooking posts
fetch('http://soulfraapi.com/api/posts?tag=cooking&limit=10')
  .then(response => response.json())
  .then(data => {
    // Render posts in cooking theme
    data.posts.forEach(post => {
      renderRecipe(post);
    });
  });
```

---

### Soulfra (soulfra.com)

**Purpose:** Main site - all content

**Content:** All published posts (no tag filter)

**Implementation:**
```javascript
// Fetch all posts
fetch('http://soulfraapi.com/api/posts?limit=20')
  .then(response => response.json())
  .then(data => {
    // Render all posts
    data.posts.forEach(post => {
      renderPost(post);
    });
  });
```

---

## Content Creation Workflow

### 1. Create Content
- Go to `/admin/studio` in soulfra-simple
- Write post in markdown
- Add title and excerpt
- **Add tags:** privacy, security, cooking, tech, etc.
- Click "Publish"

### 2. Content Saves to Database
- Saves to `posts` table in soulfra.db
- Status: `published_at` is set
- Available immediately via API

### 3. Domains Pull Content
Each domain makes API call on page load:
- deathtodata.org → `GET /api/posts?tag=privacy`
- calriven.com → `GET /api/posts?tag=tech`
- howtocookathome.com → `GET /api/posts?tag=cooking`
- soulfra.com → `GET /api/posts` (all)

### 4. Content Renders
Each domain applies its own:
- CSS theme
- Layout template
- Brand styling

**Result:** One post, many destinations!

---

## CORS Support

All API endpoints support CORS (Cross-Origin Resource Sharing).

**Headers:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Methods: GET, OPTIONS
```

This allows static sites hosted on different domains (GitHub Pages, Netlify, etc.) to call the API.

---

## Testing the API

### Terminal (curl)
```bash
# Health check
curl http://localhost:5001/api/health

# Get all posts
curl http://localhost:5001/api/posts

# Get privacy posts
curl http://localhost:5001/api/posts?tag=privacy

# Get single post
curl http://localhost:5001/api/posts/34
```

### Browser
Visit in your browser:
- http://192.168.1.87:5001/api/health
- http://192.168.1.87:5001/api/posts
- http://192.168.1.87:5001/api/posts?tag=privacy
- http://192.168.1.87:5001/api/tags

### JavaScript (fetch)
```javascript
fetch('http://192.168.1.87:5001/api/posts?tag=privacy')
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## Next Steps

1. **Add tags to existing posts** in /admin/studio
2. **Update domain static sites** to pull from API
3. **Test content flow:** Create post → Tag → Verify it appears on domain
4. **Deploy API** to production (Railway, Render, DigitalOcean)
5. **Point domains** to production API URL

---

## Production Deployment

### Option 1: Railway
```bash
# Deploy soulfra-simple to Railway
railway init
railway up
# Get URL: https://your-app.railway.app
```

### Option 2: Render
```bash
# Deploy soulfra-simple to Render
# Connect GitHub repo
# Deploy → Get URL: https://your-app.onrender.com
```

### Option 3: DigitalOcean App Platform
```bash
# Deploy soulfra-simple to DO
doctl apps create --spec app.yaml
# Get URL: https://your-app.ondigitalocean.app
```

### Update Domain Static Sites
Change API URL from:
```javascript
fetch('http://localhost:5001/api/posts')
```

To:
```javascript
fetch('https://soulfraapi.com/api/posts')
```

---

## Database Schema

### posts table
- `id` - Post ID
- `user_id` - Author ID
- `title` - Post title
- `slug` - URL slug
- `content` - Full markdown content
- `excerpt` - Short summary
- `published_at` - Publication timestamp (NULL = draft)
- `brand` - Brand name (deathtodata, calriven, etc.)

### post_tags table (if exists)
- `post_id` - Foreign key to posts
- `tag` - Tag name (privacy, tech, cooking, etc.)

---

## Error Handling

### Post Not Found
```json
{
  "success": false,
  "error": "Post not found or not published"
}
```

### Invalid Parameters
API will ignore invalid parameters and return results with defaults.

---

**Bottom Line:** The API is live and working. Content flows from soulfra-simple to all your domains via simple HTTP calls. This is "The Faucet" in action! 🚰
