# Contributing to Soulfra Simple

**Welcome!** Soulfra is a self-documenting platform - all development happens through posts and comments. This guide explains how to contribute and earn Perfect Bits.

## How Contributions Work

1. **Browse open bounties** - Check posts tagged `#contribution-needed`
2. **Claim a bounty** - Comment on the post with your proposal
3. **Get reviewed** - Automated tests + CalRiven review
4. **Earn Perfect Bits** - Awarded based on test results

## Perfect Bits Reward Structure

| Stage | Bits | Requirements |
|-------|------|--------------|
| Proposal | 10 | Post implementation plan |
| Code Review Approval | 20 | Code approach approved |
| Implementation | 70 | All tests pass |
| **Total** | **100** | Full bounty |

### Bonus Bits
- **Usage Royalties**: 0.1 bits per use of your code
- **Performance Bonus**: Extra bits for exceptional benchmarks
- **Documentation**: 5-20 bits for writing/improving docs

## Contribution Process

### 1. Claim a Bounty

Find a post with an open bounty (example: Post #5 - Pixel Art Avatar System).

**Comment template:**
```markdown
I'll take this on! Here's my approach:

## Implementation Plan
[Describe your approach - what files you'll change, how it works]

## Code Snippet (for review)
\`\`\`python
# Show key parts of your implementation
def my_function():
    pass
\`\`\`

## Testing Plan
[How will you test this?]

## Time Estimate
X hours

## Claiming
**Perfect Bits:** 100 (proposal: 10, code review: 20, implementation: 70)

CalRiven - does this approach work?
```

### 2. Build & Test

**Requirements:**
- All new code must have tests
- Tests must pass (87.5% minimum)
- Code must follow project structure
- Documentation must be updated

**Create tests:**
```python
# tests/test_your_feature.py
import unittest

class TestYourFeature(unittest.TestCase):
    def test_basic_functionality(self):
        # Your test here
        self.assertTrue(True)
```

**Run tests locally:**
```bash
python test_your_feature.py
```

### 3. Submit Implementation

**Post as comment:**
```markdown
## Implementation Complete ✅

**Changes:**
- Created `feature.py` with [functionality]
- Added `test_feature.py` with 15 tests
- Updated documentation

**Test Results:**
\`\`\`
Total Tests: 15
Passed: 15 ✅
Success Rate: 100%
\`\`\`

**Performance:**
- Generation time: 50ms avg
- Memory usage: < 10MB
- File size: < 1KB

Ready for review!
```

### 4. Automated Review

The test bot will automatically:
1. Run your tests
2. Generate performance report
3. Check code quality
4. Post results as comment

**Example bot response:**
```markdown
## 🤖 Automated Test Results

**Success Rate:** 100% ✅
**Performance:** Excellent
**Recommendation:** APPROVE for merge + award 100 Perfect Bits
```

### 5. Human Review

CalRiven (or community) reviews:
- Code quality
- Design decisions
- Documentation quality
- Overall fit

**If approved:**
- Code merged
- Perfect Bits awarded
- Contribution logged

**If changes needed:**
- Feedback provided
- Revise and resubmit
- Bits awarded upon approval

## Contribution Templates

### Feature Proposal Template
```markdown
## Feature: [Name]

**Problem:** [What needs to be fixed/added]

**Solution:** [Your approach]

**Implementation:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Testing Strategy:**
[How to validate]

**Time Estimate:** X hours
```

### Bug Fix Template
```markdown
## Bug Fix: [Issue]

**Bug:** [Description]

**Root Cause:** [Why it happens]

**Fix:** [What you'll change]

**Test:** [How to verify it's fixed]
```

### Documentation Template
```markdown
## Documentation: [Topic]

**What's Missing:** [Gap in docs]

**What I'll Add:** [New content]

**Format:** [Markdown, API docs, tutorial, etc]
```

## Code Standards

### File Organization
```
soulfra-simple/
├── src/soulfra/          # All Python code here (future)
├── tests/                # All tests here
├── templates/            # HTML templates
├── static/               # CSS, images, generated files
└── docs/                 # Documentation
```

### Python Style
- Use Black formatter (line length: 100)
- Type hints encouraged
- Docstrings for all public functions
- Comments for complex logic

### Testing Requirements
- Unit tests for all functions
- Integration tests for features
- Performance benchmarks
- Visual validation (if applicable)

## What Earns Bits?

✅ **Good contributions:**
- Solves real problem
- Well-tested
- Documented
- Follows standards
- Passes automated tests

❌ **Won't earn bits:**
- No tests
- Breaks existing functionality
- Undocumented
- Copy-paste from external sources without attribution

## FAQ

### Q: Can I work on multiple bounties?
A: Yes, but claim one at a time and finish before claiming another.

### Q: What if someone else claims the same bounty?
A: First to post a valid proposal gets it. Others can propose alternative approaches.

### Q: Can I propose my own bounties?
A: Yes! Post a feature request with `#bounty` tag. Community/CalRiven will review.

### Q: How do I cash out Perfect Bits?
A: Currently, bits are reputation-only. Future: badges, priority features, profit-sharing.

### Q: What if automated tests fail but my code works?
A: Fix the tests or explain why they're wrong. Tests must pass for bits to be awarded.

## Getting Help

- **Questions:** Comment on the relevant post
- **Bugs:** Create issue post with `#bug` tag
- **Ideas:** Post with `#feature-request` tag
- **Stuck:** Ask in comments, community will help

## License

All contributions are licensed under MIT (same as the project).

---

**Ready to contribute?** Find open bounties at http://localhost:5001/ (tagged `#contribution-needed`)

**The platform documents itself - every contribution becomes a tutorial for the next contributor.**
