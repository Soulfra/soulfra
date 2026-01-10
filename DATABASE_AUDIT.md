# Database Audit - soulfra.db

**File:** `soulfra.db` (2.9MB)
**Total Tables:** 2,252
**Status:** BLOATED - needs cleanup

## Essential Tables (Keep These)

### Core User System
- `users` - User accounts
- `sessions` - Login sessions
- `api_keys` - API authentication

### Chat/Discussion System
- `discussion_sessions` - Chat conversation threads
- `discussion_messages` - Individual chat messages
- Related indexes: `idx_discussion_*`

### Voice/Audio
- `simple_voice_recordings` - Voice uploads (NEW - we just added)
- `voice_memos` - Legacy voice system (MAYBE keep)
- `voice_inputs` / `voice_responses` - Legacy (EVALUATE)

### Content/Posts
- `posts` - Blog posts / content
- `post_tags` - Post tagging
- `post_categories` - Post categorization

### Kangaroo Court (NEW)
- `kangaroo_submissions` - Voice memo submissions
- `kangaroo_users` - User stats/credits
- `kangaroo_votes` - Voting system
- Related indexes: `idx_kangaroo_*`

### Knowledge Graph (NEW - experimental)
- `knowledge_entities` - Extracted concepts
- `knowledge_topics` - Topic tracking
- `knowledge_relationships` - Concept connections
- `knowledge_domain_mapping` - Domain associations
- `knowledge_user_profile` - User learning profiles
- `knowledge_extraction_log` - Extraction history
- Related indexes: `idx_knowledge_*`

## Probably Unused (Investigate)

### Brands/Business
- `brands` - Brand management
- `brand_posts` - Brand content
- `brand_assets` - Brand media
- `brand_licenses` - Licensing
- `brand_sops` - Standard operating procedures

### Narrative/Game System
- `narrative_sessions` - Game sessions
- `plots` - Story plots
- `plot_activities` - Plot events
- `plot_reactions` - User reactions
- `chapter_completions` - Progress tracking
- `path_cards` - Game cards
- `catchphrases` - Game catchphrases
- `catchphrase_reactions` - Reactions

### Practice Rooms
- `practice_room_participants` - Room members
- `practice_room_recordings` - Room recordings
- (More practice room tables...)

### ML/Neural Networks
- `neural_networks` - Stored models
- `ml_models` - ML configs
- `neural_ratings` - Model ratings
- `neural_rating_summary` - Rating aggregates

### Galleries/QR
- `qr_galleries` - QR code galleries
- `vanity_qr_codes` - Custom QR codes
- `qr_chat_transcripts` - QR chat logs

### Analytics/Tracking
- `admin_activity_log` - Admin actions
- `api_usage` - API call tracking
- `active_connections_summary` - Connection stats
- `package_pings` - Package tracking

### Misc
- `aging_milestones` - Time-based events
- `challenge_attempts` - Challenge system
- `challenge_submissions` - Challenge entries
- `affiliate_clicks` / `affiliate_codes` - Affiliate system
- `oauth_states` - OAuth flow
- `notifications` - User notifications
- `anonymous_sessions` - Guest sessions
- `canvas_pairing` - Canvas system

## Cleanup Strategy

### Phase 1: Document Usage
For each table group, check:
```sql
SELECT COUNT(*) FROM table_name;
```

If count = 0, table is unused.

### Phase 2: Archive
Create backup:
```bash
sqlite3 soulfra.db ".dump" > soulfra_backup_$(date +%Y%m%d).sql
```

### Phase 3: Drop Unused
Drop tables with 0 rows that aren't part of active features.

### Phase 4: Optimize
```sql
VACUUM;
ANALYZE;
```

## Questions to Answer

1. **Do we use the brand system?** (brands, brand_posts, etc.)
2. **Do we use the narrative/game system?** (plots, chapters, etc.)
3. **Do we use practice rooms?** (practice_room_*)
4. **Do we use ML models storage?** (neural_networks, ml_models)
5. **Do we use QR galleries?** (qr_galleries, vanity_qr_codes)

## Recommended Minimal Setup

For a SIMPLE system (chat + voice + posts):

**Keep:**
- users
- sessions
- discussion_sessions / discussion_messages
- simple_voice_recordings
- posts
- api_keys

**Total:** ~10 tables instead of 2,252

**Size reduction:** Probably 80%+ smaller database
