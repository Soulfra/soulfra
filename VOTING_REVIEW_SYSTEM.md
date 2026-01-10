# Voting & Review Systems - Polls vs Professional Reviews

**Date:** 2026-01-09
**Purpose:** Clarify difference between community voting (polls) and professional reviews
**Status:** System architecture specification

---

## The Confusion

**User said:** "user polls and shit too" and "or reviews or yea idk thats the confusing part too"

**The problem:** Two separate concepts being conflated:

1. **Polls/Voting** = Community decides platform direction
   - Used on: Soulfra Network (free tier)
   - Purpose: Democratic platform governance
   - Example: "Should we add dark mode?"

2. **Reviews** = Customers rate professionals (and vice versa)
   - Used on: CringeProof (paid tier)
   - Purpose: Trust & reputation for service businesses
   - Example: "Joe fixed my faucet - 5 stars!"

**This document clarifies both systems.**

---

## Part 1: Polls/Voting (Soulfra Network)

### What Are Polls?

**Definition:** Community voting on platform decisions, feature requests, content direction

**Purpose:**
- Give users voice in platform development
- Prioritize features democratically
- Build community engagement
- Reward active contributors with voting power

### Types of Polls

**1. Feature Requests**
```
Poll: Should we add video tutorials?

Options:
├── Yes - video + audio (47 votes)
├── Audio only is fine (12 votes)
└── Video optional, not required (23 votes)

Winner: Yes - video + audio

Result: Feature added to roadmap
```

**2. Content Direction**
```
Poll: What tutorial topic should we prioritize?

Options:
├── Emergency repairs (67 votes)
├── Preventive maintenance (34 votes)
├── DIY vs Call Pro (51 votes)
└── Tool recommendations (19 votes)

Winner: Emergency repairs

Result: Create template for emergency content
```

**3. Platform Governance**
```
Poll: Should we allow unverified professionals?

Options:
├── No - license required (103 votes)
├── Yes - with "unverified" badge (23 votes)
└── Trial period, then verify (45 votes)

Winner: No - license required

Result: Policy updated
```

**4. Domain Unlocking**
```
Poll: Which domain should we unlock next?

Options:
├── legaltech.ai (89 votes)
├── healthcode.dev (67 votes)
├── foodsafe.io (45 votes)
└── autorepair.pro (112 votes)

Winner: autorepair.pro

Result: Domain unlocked for Tier 3 users
```

### Voting Power (Tier-Based)

**Not all votes are equal - reward active contributors**

```python
# voting_power.py

def calculate_voting_power(user: User) -> int:
    """
    Calculate user's voting power based on tier and activity
    """
    base_power = {
        0: 1,   # Entry
        1: 2,   # Commenter
        2: 5,   # Contributor
        3: 10,  # Creator
        4: 20   # Leader
    }

    power = base_power.get(user.tier, 1)

    # Bonuses
    if user.tutorials_published > 10:
        power += 5  # Active creator bonus

    if user.account_age_days > 365:
        power += 3  # Loyalty bonus

    if user.has_verified_license:
        power += 2  # Professional bonus

    return power
```

**Example voting power:**
```
User A (Tier 0, new):
├── Base: 1 vote
└── Total: 1 vote

User B (Tier 2, active):
├── Base: 5 votes
├── +5 (published 12 tutorials)
├── +3 (member for 2 years)
└── Total: 13 votes

User C (Tier 4, leader):
├── Base: 20 votes
├── +5 (published 50+ tutorials)
├── +3 (member for 3 years)
├── +2 (verified license)
└── Total: 30 votes
```

**Why weighted voting:**
- Prevent spam/manipulation (can't create 100 fake accounts)
- Reward active contributors (those who build platform have more say)
- Align incentives (people invested in platform make better decisions)

### Poll Creation

**Who can create polls:**
```
Tier 0-1: Cannot create polls
Tier 2:   Can create polls (requires approval)
Tier 3-4: Can create polls (auto-published)
Admins:   Can create official polls
```

**Poll creation UI:**
```python
@app.route('/polls/create', methods=['GET', 'POST'])
@login_required
@tier_required(2)
def create_poll():
    """Create community poll"""

    if request.method == 'POST':
        poll = Poll(
            title=request.form.get('title'),
            description=request.form.get('description'),
            creator_id=g.current_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            status='pending' if g.current_user.tier < 3 else 'active'
        )
        db.session.add(poll)
        db.session.commit()

        # Add options
        for option_text in request.form.getlist('options'):
            option = PollOption(
                poll_id=poll.id,
                text=option_text,
                votes=0
            )
            db.session.add(option)

        db.session.commit()

        return redirect(url_for('view_poll', poll_id=poll.id))

    return render_template('polls/create.html')
```

### Poll Display

```
┌─────────────────────────────────────┐
│  Poll #47                           │
│  Created by: JoePlumber (Tier 3)    │
│  Expires: 3 days remaining          │
├─────────────────────────────────────┤
│                                     │
│  Should we add Spanish tutorials?   │
│                                     │
│  Many professionals serve Spanish-  │
│  speaking customers. Should we add  │
│  automatic translation?             │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ○ Yes - auto-translate      │   │
│  │   all content               │   │
│  │   ████████████░░░░ 347 votes│   │
│  │   (65%)                     │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ○ Yes - manual translation  │   │
│  │   by professionals          │   │
│  │   ███████░░░░░░░░░ 123 votes│   │
│  │   (23%)                     │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ○ No - English only         │   │
│  │   for now                   │   │
│  │   ██░░░░░░░░░░░░░ 67 votes  │   │
│  │   (12%)                     │   │
│  └─────────────────────────────┘   │
│                                     │
│  Your voting power: 13 votes        │
│  [Cast Vote]                        │
│                                     │
│  537 total votes from 89 users      │
└─────────────────────────────────────┘
```

### Poll Results & Action

```python
def close_poll(poll_id: int):
    """
    Close poll and take action on results
    """
    poll = Poll.query.get(poll_id)

    if poll.expires_at > datetime.utcnow():
        raise ValueError("Poll not expired yet")

    # Calculate winner (weighted by voting power)
    winner = PollOption.query.filter_by(poll_id=poll_id).order_by(
        PollOption.weighted_votes.desc()
    ).first()

    poll.status = 'closed'
    poll.winner_id = winner.id
    db.session.commit()

    # Take action based on poll type
    if poll.category == 'feature_request':
        create_feature_request_ticket(winner.text)

    if poll.category == 'domain_unlock':
        unlock_domain_for_tier(winner.text, tier=3)

    # Notify community
    send_poll_results_notification(poll)
```

---

## Part 2: Reviews (CringeProof Professional)

### What Are Reviews?

**Definition:** Bidirectional ratings between professionals and customers

**Purpose:**
- Build trust (like Yelp/Google reviews)
- Verify authenticity (geofenced check-ins prove job was real)
- Reputation system (5-star pros rank higher)
- Mutual accountability (professionals can review customers too)

### Bidirectional Reviews (Like Airbnb)

**Traditional reviews (Yelp, Google):**
```
Customer → Reviews → Professional
Professional cannot review customer
Result: One-sided, can be abused
```

**Bidirectional reviews (Airbnb, Uber):**
```
Customer ↔ Reviews ↔ Professional
Both parties review each other
Result: Mutual accountability, less abuse
```

**Why bidirectional:**
1. **Protects professionals** - Can flag bad customers (no-shows, rude, didn't pay)
2. **Incentivizes good behavior** - Customers want good reviews for future services
3. **Reduces fake reviews** - Requires actual job to happen (geofenced)
4. **More authentic** - Both sides have skin in the game

### Review Flow

**Step 1: Job Completion**
```
Professional marks job complete in Crampal:
├── "Completed: Fixed leaky faucet for Sarah M."
├── GPS coordinates recorded
└── Timestamp: 2026-01-09 2:34 PM
```

**Step 2: Review Request (24 hours later)**
```
SMS to customer:
"Hi Sarah! Thanks for choosing Joe's Plumbing. Mind leaving a review?
⭐⭐⭐⭐⭐ [link]"

SMS to professional:
"Review your recent customer Sarah M.
⭐⭐⭐⭐⭐ [link]"
```

**Step 3: Customer Reviews Professional**
```
┌─────────────────────────────────────┐
│  Rate Your Experience               │
│  Joe's Plumbing                     │
│  ───────────────────────────────    │
│                                     │
│  Overall:                           │
│  ⭐ ⭐ ⭐ ⭐ ⭐                      │
│                                     │
│  Quality of Work:                   │
│  ⭐ ⭐ ⭐ ⭐ ⭐                      │
│                                     │
│  Professionalism:                   │
│  ⭐ ⭐ ⭐ ⭐ ⭐                      │
│                                     │
│  Value:                             │
│  ⭐ ⭐ ⭐ ⭐ ☆                       │
│                                     │
│  Comments (optional):               │
│  Joe was great! Fixed my faucet     │
│  in 30 minutes, explained what      │
│  was wrong, fair price.             │
│                                     │
│  Photos (optional):                 │
│  [📷 Upload before/after]           │
│                                     │
│  [Submit Review]                    │
└─────────────────────────────────────┘
```

**Step 4: Professional Reviews Customer**
```
┌─────────────────────────────────────┐
│  Rate Your Customer                 │
│  Sarah M.                           │
│  ───────────────────────────────    │
│                                     │
│  Overall:                           │
│  ⭐ ⭐ ⭐ ⭐ ⭐                      │
│                                     │
│  Communication:                     │
│  ⭐ ⭐ ⭐ ⭐ ⭐                      │
│  (Clear about problem, responsive)  │
│                                     │
│  Payment:                           │
│  ⭐ ⭐ ⭐ ⭐ ⭐                      │
│  (Paid promptly, no issues)         │
│                                     │
│  Access:                            │
│  ⭐ ⭐ ⭐ ⭐ ⭐                      │
│  (Easy access, job site ready)      │
│                                     │
│  Comments (private):                │
│  Great customer, would work with    │
│  again. House was clean, dog was    │
│  friendly.                          │
│                                     │
│  [Submit Review]                    │
└─────────────────────────────────────┘
```

**Step 5: Both Reviews Published Simultaneously**
```
After BOTH submit reviews:
├── Customer's review → visible on Joe's profile
└── Professional's review → visible on Sarah's profile (for next pro)

If one doesn't submit:
├── Reminder sent after 7 days
└── If still no response after 14 days, other review published solo
```

### Geofenced Review Authenticity

**Problem:** Fake reviews are epidemic (Yelp, Google, Amazon all struggle)

**Solution:** Require GPS proof that professional was at job site

```python
# reviews/geofence.py

def verify_job_geofence(job_id: int) -> bool:
    """
    Verify professional was physically at customer's location
    """
    job = Job.query.get(job_id)

    # Professional's GPS when marking job complete
    pro_lat = job.completion_gps_lat
    pro_lon = job.completion_gps_lon

    # Customer's address
    customer_lat = job.customer_address_lat
    customer_lon = job.customer_address_lon

    # Calculate distance
    distance_meters = haversine_distance(
        pro_lat, pro_lon,
        customer_lat, customer_lon
    )

    # Must be within 100 meters (330 feet)
    if distance_meters <= 100:
        job.geofence_verified = True
        db.session.commit()
        return True
    else:
        job.geofence_verified = False
        job.geofence_error = f'Professional was {distance_meters}m away'
        db.session.commit()
        return False


def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """
    Calculate distance between two GPS coordinates in meters
    """
    from math import radians, sin, cos, sqrt, atan2

    R = 6371000  # Earth radius in meters

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c
```

**Review authenticity badge:**
```
Customer review:
├── ⭐⭐⭐⭐⭐ 5 stars
├── ✓ Geofence verified (professional was on-site)
├── ✓ Job completed 2026-01-09
└── "Joe was great! Fixed my faucet..."

vs

Fake review (would be rejected):
├── ❌ Geofence failed (professional never at location)
└── Review not published
```

### Review Display

**On professional's profile:**
```
┌─────────────────────────────────────┐
│  Joe's Plumbing                     │
│  ⭐ 4.8 stars (127 reviews)         │
│  100% geofence verified             │
├─────────────────────────────────────┤
│                                     │
│  Rating Breakdown:                  │
│  ─────────────────────────────      │
│  5 stars: ████████████░ 89 (70%)   │
│  4 stars: ████░░░░░░░░ 28 (22%)    │
│  3 stars: █░░░░░░░░░░░  7 (6%)     │
│  2 stars: ░░░░░░░░░░░░  2 (1%)     │
│  1 star:  ░░░░░░░░░░░░  1 (1%)     │
│                                     │
│  Most Recent Reviews:               │
│  ─────────────────────────────      │
│                                     │
│  ⭐⭐⭐⭐⭐ Sarah M. - Jan 9, 2026  │
│  ✓ Geofence verified                │
│  "Joe was great! Fixed my faucet    │
│  in 30 minutes, explained what      │
│  was wrong, fair price."            │
│  [📷 Before/After photos]           │
│                                     │
│  ⭐⭐⭐⭐⭐ Mike T. - Jan 7, 2026   │
│  ✓ Geofence verified                │
│  "Emergency call at 10pm, Joe came  │
│  within an hour. Professional and   │
│  honest - highly recommend!"        │
│                                     │
│  ⭐⭐⭐⭐☆ Lisa K. - Jan 5, 2026   │
│  ✓ Geofence verified                │
│  "Good work but a bit pricey.       │
│  Faucet works perfectly now."       │
│                                     │
│  [View All 127 Reviews]             │
└─────────────────────────────────────┘
```

### Customer Reputation (For Professionals)

**Professionals can see customer ratings before accepting job:**
```
┌─────────────────────────────────────┐
│  New Lead                           │
│  Sarah M.                           │
│  ───────────────────────────────    │
│                                     │
│  Problem: Leaky faucet              │
│  Location: Tampa (2.3 mi)           │
│  Urgency: Soon (not emergency)      │
│                                     │
│  Customer Rating: ⭐ 4.9 (7 jobs)   │
│  ✓ Always paid on time              │
│  ✓ Clear communication              │
│  ✓ Easy access to job site          │
│                                     │
│  Recent reviews from other pros:    │
│  "Great customer, friendly dog"     │
│  "Paid cash, no issues"             │
│  "Job site was clean and ready"     │
│                                     │
│  [Accept Job]  [Decline]            │
└─────────────────────────────────────┘

vs

┌─────────────────────────────────────┐
│  New Lead                           │
│  Karen S.                           │
│  ───────────────────────────────    │
│                                     │
│  Problem: Toilet running            │
│  Location: Brandon (8.1 mi)         │
│  Urgency: EMERGENCY                 │
│                                     │
│  Customer Rating: ⭐ 2.1 (4 jobs)   │
│  ⚠️ Payment issues (1 dispute)      │
│  ⚠️ Cancelled last-minute (2x)      │
│  ⚠️ Rude to professionals           │
│                                     │
│  Recent reviews from other pros:    │
│  "Argued about price after job"     │
│  "Cancelled 10 min before arrival"  │
│  "Unrealistic expectations"         │
│                                     │
│  [Accept Job]  [Decline]            │
└─────────────────────────────────────┘
```

**Why this matters:**
- Professionals can avoid problem customers
- Customers incentivized to be respectful (bad rating = hard to get service)
- Creates marketplace equilibrium (good customers get better service)

### Review Disputes

**What if customer/professional disagrees with review?**

```python
@app.route('/reviews/<int:review_id>/dispute', methods=['POST'])
@login_required
def dispute_review(review_id):
    """
    Dispute a review (requires evidence)
    """
    review = Review.query.get(review_id)

    dispute = ReviewDispute(
        review_id=review_id,
        disputer_id=g.current_user.id,
        reason=request.form.get('reason'),
        evidence=request.form.get('evidence'),
        status='pending'
    )
    db.session.add(dispute)
    db.session.commit()

    # Human review required
    notify_support_team(dispute)

    return jsonify({'status': 'dispute_submitted'})
```

**Dispute reasons:**
```
Valid disputes:
├── "Review is fake (I never worked with this customer)"
│   → Requires geofence proof
├── "Customer threatening to change review if I don't do free work"
│   → Requires screenshot evidence
└── "Review contains false information (says I charged $500, actually $200)"
    → Requires invoice proof

Invalid disputes:
├── "Customer gave me 4 stars instead of 5" (subjective)
├── "I don't like what they said" (opinion)
└── "Bad review is hurting my business" (not grounds for removal)
```

---

## Database Schema

### Polls (Community Voting)

```sql
-- Polls
CREATE TABLE poll (
    id INTEGER PRIMARY KEY,
    creator_id INTEGER REFERENCES users(id),

    -- Content
    title VARCHAR(500),
    description TEXT,
    category VARCHAR(50),  -- 'feature_request', 'content', 'governance', 'domain'

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'active', 'closed'
    expires_at TIMESTAMP,

    -- Results
    winner_id INTEGER REFERENCES poll_option(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Poll options
CREATE TABLE poll_option (
    id INTEGER PRIMARY KEY,
    poll_id INTEGER REFERENCES poll(id),

    text VARCHAR(500),

    -- Votes (unweighted count)
    votes INTEGER DEFAULT 0,

    -- Weighted votes (actual voting power)
    weighted_votes INTEGER DEFAULT 0
);

-- Poll votes (track who voted for what)
CREATE TABLE poll_vote (
    id INTEGER PRIMARY KEY,
    poll_id INTEGER REFERENCES poll(id),
    option_id INTEGER REFERENCES poll_option(id),
    user_id INTEGER REFERENCES users(id),

    voting_power INTEGER,  -- User's voting power at time of vote

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(poll_id, user_id)  -- One vote per poll per user
);
```

### Reviews (Professional ↔ Customer)

```sql
-- Jobs (required for reviews)
CREATE TABLE job (
    id INTEGER PRIMARY KEY,
    professional_id INTEGER REFERENCES professional_profile(id),
    customer_id INTEGER REFERENCES users(id),

    -- Job details
    description TEXT,
    address VARCHAR(500),
    address_lat DECIMAL(10, 8),
    address_lon DECIMAL(11, 8),

    -- Completion
    status VARCHAR(20),  -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    completed_at TIMESTAMP,

    -- Geofence verification
    completion_gps_lat DECIMAL(10, 8),
    completion_gps_lon DECIMAL(11, 8),
    geofence_verified BOOLEAN DEFAULT FALSE,
    geofence_distance_meters DECIMAL(10, 2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews
CREATE TABLE review (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES job(id),

    -- Reviewer
    reviewer_id INTEGER REFERENCES users(id),
    reviewer_type VARCHAR(20),  -- 'customer' or 'professional'

    -- Reviewee
    reviewee_id INTEGER REFERENCES users(id),
    reviewee_type VARCHAR(20),

    -- Ratings
    overall_rating INTEGER,  -- 1-5 stars
    quality_rating INTEGER,  -- 1-5
    professionalism_rating INTEGER,  -- 1-5
    value_rating INTEGER,  -- 1-5 (customer → pro only)
    communication_rating INTEGER,  -- 1-5 (pro → customer only)
    payment_rating INTEGER,  -- 1-5 (pro → customer only)

    -- Content
    comment TEXT,
    photos JSON,  -- Array of photo URLs

    -- Authenticity
    geofence_verified BOOLEAN,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'published', 'disputed', 'removed'
    published_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Review disputes
CREATE TABLE review_dispute (
    id INTEGER PRIMARY KEY,
    review_id INTEGER REFERENCES review(id),
    disputer_id INTEGER REFERENCES users(id),

    reason VARCHAR(500),
    evidence TEXT,

    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'resolved_kept', 'resolved_removed'
    resolution_notes TEXT,
    resolved_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Endpoints

### Polls API

```python
# routes/polls.py

@app.route('/api/polls', methods=['GET'])
def list_polls():
    """List active polls"""
    polls = Poll.query.filter_by(status='active').all()

    return jsonify({
        'polls': [
            {
                'id': p.id,
                'title': p.title,
                'description': p.description,
                'options': [
                    {
                        'id': o.id,
                        'text': o.text,
                        'votes': o.votes,
                        'weighted_votes': o.weighted_votes
                    }
                    for o in p.options
                ],
                'expires_at': p.expires_at.isoformat(),
                'total_votes': sum(o.votes for o in p.options),
                'user_has_voted': has_user_voted(p.id, g.current_user.id)
            }
            for p in polls
        ]
    })


@app.route('/api/polls/<int:poll_id>/vote', methods=['POST'])
@login_required
def vote_on_poll(poll_id):
    """Cast vote on poll"""
    poll = Poll.query.get_or_404(poll_id)

    if poll.status != 'active':
        return jsonify({'error': 'Poll is closed'}), 400

    # Check if already voted
    if has_user_voted(poll_id, g.current_user.id):
        return jsonify({'error': 'Already voted'}), 400

    option_id = request.json.get('option_id')
    option = PollOption.query.get(option_id)

    # Calculate voting power
    voting_power = calculate_voting_power(g.current_user)

    # Record vote
    vote = PollVote(
        poll_id=poll_id,
        option_id=option_id,
        user_id=g.current_user.id,
        voting_power=voting_power
    )
    db.session.add(vote)

    # Update option counts
    option.votes += 1
    option.weighted_votes += voting_power

    db.session.commit()

    return jsonify({'status': 'vote_recorded', 'voting_power': voting_power})
```

### Reviews API

```python
# routes/reviews.py

@app.route('/api/jobs/<int:job_id>/review', methods=['POST'])
@login_required
def create_review(job_id):
    """Create review for completed job"""
    job = Job.query.get_or_404(job_id)

    # Verify job is completed
    if job.status != 'completed':
        return jsonify({'error': 'Job not completed'}), 400

    # Verify geofence
    if not job.geofence_verified:
        return jsonify({'error': 'Geofence verification failed'}), 400

    # Determine reviewer type
    if g.current_user.id == job.customer_id:
        reviewer_type = 'customer'
        reviewee_id = job.professional_id
        reviewee_type = 'professional'
    elif g.current_user.professional_profile and g.current_user.professional_profile.id == job.professional_id:
        reviewer_type = 'professional'
        reviewee_id = job.customer_id
        reviewee_type = 'customer'
    else:
        return jsonify({'error': 'Not authorized'}), 403

    # Create review
    review = Review(
        job_id=job_id,
        reviewer_id=g.current_user.id,
        reviewer_type=reviewer_type,
        reviewee_id=reviewee_id,
        reviewee_type=reviewee_type,
        overall_rating=request.json.get('overall_rating'),
        quality_rating=request.json.get('quality_rating'),
        professionalism_rating=request.json.get('professionalism_rating'),
        comment=request.json.get('comment'),
        geofence_verified=True,
        status='pending'  # Wait for other party to review
    )
    db.session.add(review)
    db.session.commit()

    # Check if other party has reviewed
    check_and_publish_reviews(job_id)

    return jsonify({'status': 'review_submitted'})


def check_and_publish_reviews(job_id: int):
    """
    If both parties have submitted reviews, publish them
    """
    reviews = Review.query.filter_by(job_id=job_id).all()

    if len(reviews) == 2:  # Both submitted
        for review in reviews:
            review.status = 'published'
            review.published_at = datetime.utcnow()
        db.session.commit()

        # Notify both parties
        send_review_published_notification(reviews)
```

---

## Gamification & Incentives

### Poll Participation Rewards

**Reward users for voting:**
```python
def reward_poll_participation(user_id: int):
    """
    Give rewards for participating in polls
    """
    user = User.query.get(user_id)

    # Track participation
    user.polls_voted += 1

    # Milestones
    if user.polls_voted == 10:
        unlock_achievement(user_id, 'CIVIC_PARTICIPANT')

    if user.polls_voted == 100:
        unlock_achievement(user_id, 'DEMOCRACY_CHAMPION')
        # Bonus: +5 voting power permanently

    db.session.commit()
```

### Review Rewards

**Incentivize reviews:**
```python
def reward_review_submission(user_id: int):
    """
    Give rewards for leaving reviews
    """
    user = User.query.get(user_id)

    user.reviews_written += 1

    # Professional rewards
    if user.professional_profile:
        # 10% discount on next month if you review all customers
        if user.reviews_written >= user.jobs_completed:
            apply_discount(user_id, 0.10)

    # Customer rewards
    else:
        # Priority booking if you have good review history
        if user.reviews_written >= 5 and user.avg_rating_received >= 4.5:
            user.priority_customer = True

    db.session.commit()
```

---

## Moderation & Quality Control

### Review Moderation

**Automated filters:**
```python
def moderate_review(review_id: int) -> bool:
    """
    Check review for violations
    """
    review = Review.query.get(review_id)

    # Check for profanity
    if contains_profanity(review.comment):
        flag_review(review_id, 'profanity')
        return False

    # Check for personal info (phone numbers, emails)
    if contains_personal_info(review.comment):
        flag_review(review_id, 'personal_info')
        return False

    # Check for competitor mentions
    if contains_competitor_mention(review.comment):
        flag_review(review_id, 'competitor_mention')
        return False

    # Check for fake/spam patterns
    if is_likely_fake(review):
        flag_review(review_id, 'suspected_fake')
        return False

    return True
```

### Poll Moderation

**Prevent poll spam:**
```python
def moderate_poll(poll_id: int) -> bool:
    """
    Check poll for violations
    """
    poll = Poll.query.get(poll_id)

    # Check for duplicate polls
    similar_polls = Poll.query.filter(
        Poll.title.ilike(f'%{poll.title}%'),
        Poll.id != poll_id,
        Poll.status == 'active'
    ).count()

    if similar_polls > 0:
        reject_poll(poll_id, 'duplicate')
        return False

    # Check for spam keywords
    if is_spam(poll.title) or is_spam(poll.description):
        reject_poll(poll_id, 'spam')
        return False

    return True
```

---

## Comparison Summary

| Feature | Polls (Soulfra) | Reviews (CringeProof) |
|---------|----------------|----------------------|
| **Purpose** | Community governance | Professional reputation |
| **Who uses** | All users (Tier 0-4) | Professionals + Customers |
| **Voting power** | Tier-weighted | One person = one review |
| **Authenticity** | Account-based | Geofence-verified |
| **Bidirectional** | No | Yes (mutual reviews) |
| **Public/Private** | Public (visible to all) | Public (pro reviews) + Private (customer reviews) |
| **Frequency** | Unlimited voting | One review per job |
| **Impact** | Platform decisions | Individual reputation |

---

## Conclusion

**Two separate systems, two different purposes:**

1. **Polls/Voting (Soulfra Network)**
   - Community decides platform direction
   - Tier-weighted voting power
   - Used for: Features, domains, governance
   - Public, democratic, ongoing

2. **Reviews (CringeProof Professional)**
   - Customers rate professionals (and vice versa)
   - Geofence-verified authenticity
   - Used for: Trust, reputation, lead quality
   - Bidirectional, private (customer ratings), job-specific

**Both systems work together:**
- Polls guide platform development
- Reviews build trust in marketplace
- Combined = community-driven, trust-based platform

---

**Created:** 2026-01-09
**By:** Claude Code
**See also:**
- `PLATFORM_INTEGRATION_STRATEGY.md` - How Soulfra + CringeProof connect
- `CRAMPAL_MODERN_CPANEL.md` - Where reviews are displayed
- `tier_progression_engine.py` - Existing tier system for voting power
