# Perfect Bits Reputation System API

**Version:** 0.1.0
**Status:** Active
**Last Updated:** December 21, 2025

## Overview

The Perfect Bits system tracks contributor reputation through validated contributions. Contributors earn bits for proposals, code reviews, and implementations that pass automated tests.

## Database Schema

### `reputation` Table

Stores aggregate reputation per user.

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique reputation record ID |
| user_id | INTEGER UNIQUE | Foreign key to users table |
| bits_earned | INTEGER | Total bits earned (lifetime) |
| bits_spent | INTEGER | Total bits spent (future feature) |
| contribution_count | INTEGER | Number of contributions made |
| created_at | TIMESTAMP | When reputation tracking started |

**Example:**
```sql
SELECT u.username, r.bits_earned, r.contribution_count
FROM reputation r
JOIN users u ON r.user_id = u.id
ORDER BY r.bits_earned DESC;
```

### `contribution_logs` Table

Tracks individual contributions and bit awards.

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique log entry ID |
| user_id | INTEGER | Who made the contribution |
| post_id | INTEGER | Which post the contribution is on |
| comment_id | INTEGER | Comment with the contribution |
| contribution_type | TEXT | Type: 'proposal', 'implementation', 'documentation' |
| description | TEXT | What was contributed |
| bits_awarded | INTEGER | Bits awarded for this contribution |
| status | TEXT | Status: 'pending', 'approved', 'rejected' |
| created_at | TIMESTAMP | When contribution was made |
| reviewed_by | INTEGER | Who reviewed it (CalRiven or human) |
| reviewed_at | TIMESTAMP | When it was reviewed |

**Example:**
```sql
-- Get all approved contributions by Alice
SELECT * FROM contribution_logs
WHERE user_id = 5 AND status = 'approved'
ORDER BY created_at DESC;
```

## Bit Award Structure

### Standard Bounty (100 bits total)

| Stage | Bits | Criteria |
|-------|------|----------|
| **Proposal** | 10 | Posted clear implementation plan |
| **Code Review** | 20 | Approach approved by reviewer |
| **Implementation** | 70 | All tests pass (87.5%+ success rate) |

### Bonus Bits

| Bonus Type | Amount | Criteria |
|------------|--------|----------|
| **Perfect Score** | +10 | 100% test pass rate |
| **Performance** | +5-20 | Exceptional benchmarks |
| **Documentation** | +5-15 | Clear, comprehensive docs |
| **Usage Royalty** | +0.1 per use | Code used by others |

## API Functions

### Core Functions

#### `get_user_reputation(user_id)`

Get total reputation for a user.

**Parameters:**
- `user_id` (int): User ID

**Returns:**
```python
{
    'bits_earned': 100,
    'bits_spent': 0,
    'contribution_count': 2,
    'created_at': '2025-12-21 13:00:00'
}
```

**Example:**
```python
from database import get_db

conn = get_db()
rep = conn.execute(
    'SELECT * FROM reputation WHERE user_id = ?',
    (user_id,)
).fetchone()
```

#### `award_bits(user_id, amount, reason, post_id=None, comment_id=None)`

Award Perfect Bits to a user.

**Parameters:**
- `user_id` (int): Who to award
- `amount` (int): How many bits
- `reason` (str): Why ('proposal', 'implementation', etc)
- `post_id` (int, optional): Related post
- `comment_id` (int, optional): Related comment

**Example:**
```python
# Award 10 bits for a good proposal
award_bits(
    user_id=5,
    amount=10,
    reason='Pixel avatar proposal approved',
    post_id=5,
    comment_id=12
)
```

**SQL:**
```sql
-- Update reputation
UPDATE reputation
SET bits_earned = bits_earned + 10,
    contribution_count = contribution_count + 1
WHERE user_id = 5;

-- Log the contribution
INSERT INTO contribution_logs
(user_id, post_id, comment_id, contribution_type, bits_awarded, status)
VALUES (5, 5, 12, 'proposal', 10, 'approved');
```

#### `get_contribution_history(user_id, limit=10)`

Get recent contributions for a user.

**Returns:**
```python
[
    {
        'id': 1,
        'contribution_type': 'proposal',
        'description': 'Pixel avatar generator - implementation plan',
        'bits_awarded': 10,
        'status': 'approved',
        'created_at': '2025-12-21 13:00:00'
    },
    {
        'id': 2,
        'contribution_type': 'implementation',
        'description': 'Pixel art avatar generator - complete code',
        'bits_awarded': 90,
        'status': 'approved',
        'created_at': '2025-12-21 14:00:00'
    }
]
```

### Validation Functions

#### `can_claim_bounty(user_id, post_id)`

Check if user can claim a bounty.

**Rules:**
- Can't claim if already claimed by someone else
- Can't claim multiple bounties simultaneously
- Must be registered user

**Returns:** `True` or `False`

#### `calculate_bits_for_tests(test_results)`

Calculate bits based on test pass rate.

**Formula:**
```python
base_bits = 70  # Implementation base
success_rate = passed / total
if success_rate >= 1.0:
    bits = base_bits + 10  # Perfect score bonus
elif success_rate >= 0.875:
    bits = base_bits
else:
    bits = int(base_bits * success_rate)  # Partial credit
```

**Example:**
```python
# 15/16 tests passed (93.75%)
test_results = {'total': 16, 'passed': 15}
bits = calculate_bits_for_tests(test_results)
# Returns: 70 (base implementation bits)
```

## Usage Tracking (Code Royalties)

### `track_code_usage(module_name, author_id, used_by_id=None)`

Track when contributed code is used.

**Parameters:**
- `module_name` (str): What code was used ('avatar_generator', etc)
- `author_id` (int): Who wrote the code
- `used_by_id` (int, optional): Who used it

**Example:**
```python
# Every time avatar_generator is called:
from avatar_generator import generate_pixel_avatar
from reputation import track_code_usage

avatar = generate_pixel_avatar(username)
track_code_usage('avatar_generator', author_id=5)  # Alice gets 0.1 bits
```

### Future: Usage Royalties Table
```sql
CREATE TABLE code_usage_logs (
    id INTEGER PRIMARY KEY,
    module_name TEXT,
    author_id INTEGER,
    used_by_id INTEGER,
    bits_earned DECIMAL(10,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Leaderboard

### Top Contributors Query
```sql
SELECT
    u.username,
    u.display_name,
    r.bits_earned,
    r.contribution_count,
    ROUND(r.bits_earned * 1.0 / r.contribution_count, 2) as avg_bits_per_contribution
FROM reputation r
JOIN users u ON r.user_id = u.id
WHERE r.contribution_count > 0
ORDER BY r.bits_earned DESC
LIMIT 10;
```

### Recent Contributions Query
```sql
SELECT
    u.username,
    c.contribution_type,
    c.description,
    c.bits_awarded,
    c.created_at
FROM contribution_logs c
JOIN users u ON c.user_id = u.id
WHERE c.status = 'approved'
ORDER BY c.created_at DESC
LIMIT 20;
```

## Integration Examples

### Award bits after test success
```python
# In test_bot.py
if test_results['success_rate'] >= 0.875:
    bits = 70 if test_results['success_rate'] < 1.0 else 80
    award_bits(
        user_id=contributor_id,
        amount=bits,
        reason=f"Implementation (tests: {test_results['success_rate']}%)",
        post_id=post_id
    )
```

### Display reputation in templates
```html
<!-- templates/user.html -->
<div class="reputation">
    <span class="bits">{{ user.bits_earned }} Perfect Bits</span>
    <span class="contributions">{{ user.contribution_count }} contributions</span>
</div>
```

### Check if user can claim bounty
```python
@app.route('/post/<slug>/claim', methods=['POST'])
def claim_bounty(slug):
    if not can_claim_bounty(current_user_id, post_id):
        flash('Bounty already claimed or you have pending work')
        return redirect(url_for('post', slug=slug))

    # Process claim...
```

## Future Features

- **Bit Spending**: Use bits for priority features, custom themes, etc
- **Tiered Badges**: Bronze (100 bits), Silver (500 bits), Gold (1000 bits)
- **Profit Sharing**: Convert bits to actual compensation
- **NFT Certificates**: Mint contribution certificates on-chain
- **Federated Reputation**: Share reputation across Soulfra instances

## See Also

- [CONTRIBUTING.md](../../CONTRIBUTING.md) - How to earn bits
- [TESTING.md](./TESTING.md) - How tests determine bit awards
- [DATABASE.md](./DATABASE.md) - Full schema documentation
