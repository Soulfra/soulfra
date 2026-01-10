# Review Page - How It Actually Works

**Created:** 2025-12-27
**Question:** "Why doesn't /learn/review show me any fields or forms to answer questions?"
**Answer:** It DOES! The forms load dynamically via JavaScript. Here's the complete flow.

---

## The Confusion

**What you expect:** Forms with input fields to type answers

**What you actually get:** Interactive flashcard UI with rating buttons (Anki-style)

**Why it seems broken:** JavaScript loads content dynamically, so initial page load looks empty

---

## What the Page Actually Looks Like

### Initial Load (0-1 seconds)

```
┌─────────────────────────────────────────┐
│   📚 Review Session                     │
│                                         │
│   [Progress: 0%]                        │
│                                         │
│   Loading cards...                      │
│                                         │
└─────────────────────────────────────────┘
```

**Behind the scenes:**
- HTML page loaded
- JavaScript file loaded
- Cards array populated from server
- First card about to display

---

### Step 1: Question Displays (1-2 seconds)

```
┌─────────────────────────────────────────┐
│   📚 Review Session                     │
│                                         │
│   Card 1 of 12       0 correct         │
│   [█░░░░░░░░░░░] 8%                     │
│                                         │
│   ╔═════════════════════════════════╗   │
│   ║ Question                        ║   │
│   ║                                 ║   │
│   ║ What type of database does      ║   │
│   ║ SQLite use for its internal     ║   │
│   ║ storage?                        ║   │
│   ║                                 ║   │
│   ╚═════════════════════════════════╝   │
│                                         │
│        [Show Answer →]                  │
│                                         │
└─────────────────────────────────────────┘
```

**THIS is the "form"!** It's not a text input - it's Anki-style: Read question → Recall answer → Reveal → Rate yourself

**Code:**
```javascript
// Line 216 in templates/learn/review.html
document.getElementById('question-text').textContent = card.question;
```

---

### Step 2: User Clicks "Show Answer"

```
┌─────────────────────────────────────────┐
│   📚 Review Session                     │
│                                         │
│   Card 1 of 12       0 correct         │
│   [█░░░░░░░░░░░] 8%                     │
│                                         │
│   ╔═════════════════════════════════╗   │
│   ║ Answer                          ║   │
│   ║                                 ║   │
│   ║ File-based                      ║   │
│   ║                                 ║   │
│   ║ 💡 Explanation:                 ║   │
│   ║ SQLite stores data in a single  ║   │
│   ║ file with .db extension.        ║   │
│   ╚═════════════════════════════════╝   │
│                                         │
│   How well did you know this?           │
│                                         │
│   ┌──────┐  ┌──────┐  ┌──────┐          │
│   │ 0    │  │ 1    │  │ 2    │          │
│   │Forgot│  │Hard  │  │Remem.│          │
│   └──────┘  └──────┘  └──────┘          │
│                                         │
│   ┌──────┐  ┌──────┐  ┌──────┐          │
│   │ 3    │  │ 4    │  │ 5    │          │
│   │Good  │  │Easy  │  │Perfect│         │
│   └──────┘  └──────┘  └──────┘          │
│                                         │
└─────────────────────────────────────────┘
```

**The "fields" you're looking for = These 6 rating buttons!**

**Not a text input** - You rate how well you knew the answer (0-5 scale)

**Code:**
```html
<!-- Lines 76-105 in templates/learn/review.html -->
<button onclick="rateCard(0)">0 - Forgot</button>
<button onclick="rateCard(1)">1 - Hard</button>
<button onclick="rateCard(2)">2 - Remembered</button>
<button onclick="rateCard(3)">3 - Good</button>
<button onclick="rateCard(4)">4 - Easy</button>
<button onclick="rateCard(5)">5 - Perfect</button>
```

---

### Step 3: User Clicks Rating (e.g., "4 - Easy")

```javascript
// JavaScript sends API call
fetch('/api/learn/answer', {
  method: 'POST',
  body: JSON.stringify({
    card_id: 5,
    quality: 4,
    session_id: 8,
    time_to_answer: 12
  })
})
```

**Backend processes:**
1. SM-2 algorithm calculates new interval
2. Updates `learning_progress` table
3. Saves to `review_history`
4. Returns next card

---

### Step 4: Result Shows

```
┌─────────────────────────────────────────┐
│   📚 Review Session                     │
│                                         │
│   Card 1 of 12       1 correct         │
│   [██░░░░░░░░░░] 16%                    │
│                                         │
│   ╔═════════════════════════════════╗   │
│   ║           ✅                     ║   │
│   ║      Card reviewed!              ║   │
│   ║                                 ║   │
│   ║  ┌──────┐  ┌──────┐  ┌──────┐  ║   │
│   ║  │  1   │  │  0   │  │ 100% │  ║   │
│   ║  │ Days │  │Streak│  │Accur.│  ║   │
│   ║  └──────┘  └──────┘  └──────┘  ║   │
│   ║                                 ║   │
│   ║      [Next Card →]              ║   │
│   ╚═════════════════════════════════╝   │
│                                         │
└─────────────────────────────────────────┘
```

**Stats updated:**
- Progress bar: 8% → 16%
- Correct count: 0 → 1
- Next review: 1 day from now

---

### Step 5: Next Card Loads

Cycle repeats! Question → Show Answer → Rate → Result → Next Card...

---

## Why It Might Look "Broken"

### Reason 1: JavaScript Hasn't Loaded Yet

**Symptom:** Page shows nothing except header/footer

**Fix:** Wait 1-2 seconds for JavaScript to load

**Debug:**
```javascript
// Open browser console (F12)
// Check for errors:
console.log(cards);  // Should show array of 12 cards
```

---

### Reason 2: No Cards Due

**Symptom:** Page shows "All Caught Up!" message

**Cause:** No cards are due for review (all cards scheduled for future dates)

**Fix:**
```bash
# Initialize cards for your user
python3 init_learning_cards_for_user.py

# Now cards will be "due"
```

---

### Reason 3: Expecting Text Input

**Symptom:** "I don't see where to type my answer"

**Explanation:** This is **Anki-style** flashcards, not quiz-style

**How it works:**
1. Read question
2. **Think of answer** (in your head)
3. Click "Show Answer" to reveal
4. Compare your mental answer to actual answer
5. Rate yourself (0-5)

**NOT:**
1. ~~Type answer in text box~~
2. ~~Click submit~~
3. ~~Computer grades you~~

**Why?** Anki-style is proven more effective for long-term retention

---

## Complete JavaScript Flow

### 1. Page Loads

```html
<!-- templates/learn/review.html:191 -->
<script>
const cards = {{ cards|tojson|safe }};  <!-- Server data injected -->
const sessionId = {{ session_id }};
let currentCardIndex = 0;
</script>
```

**What happens:**
- Flask passes `cards` array to template
- Jinja2 converts Python list to JavaScript array
- JavaScript variable `cards` now has all card data

---

### 2. First Card Loads

```javascript
// Line 198
if (cards.length > 0) {
    loadCard(0);  // Load first card
}

function loadCard(index) {
    const card = cards[index];

    // Update UI
    document.getElementById('question-text').textContent = card.question;
    document.getElementById('answer-text').textContent = card.answer;

    // Show question, hide answer
    document.getElementById('question-side').classList.remove('hidden');
    document.getElementById('answer-side').classList.add('hidden');
}
```

**Result:** Question text appears, answer hidden

---

### 3. User Clicks "Show Answer"

```javascript
// Line 228
function showAnswer() {
    document.getElementById('question-side').classList.add('hidden');
    document.getElementById('answer-side').classList.remove('hidden');
}
```

**Result:** Question hides, answer + rating buttons appear

---

### 4. User Clicks Rating

```javascript
// Line 233
function rateCard(quality) {
    const card = cards[currentCardIndex];

    // API call
    fetch('/api/learn/answer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            card_id: card.id,
            quality: quality,
            session_id: sessionId
        })
    })
    .then(res => res.json())
    .then(data => {
        // Show result
        document.getElementById('next-review-days').textContent = data.interval_days;
        document.getElementById('answer-side').classList.add('hidden');
        document.getElementById('result-card').classList.remove('hidden');
    });
}
```

**Result:** API saves rating, shows stats, hides answer

---

### 5. User Clicks "Next Card"

```javascript
// Line 269
function nextCard() {
    currentCardIndex++;
    loadCard(currentCardIndex);  // Load next card
}
```

**Result:** Cycle repeats with next card

---

## Debugging Checklist

If you visit `/learn/review` and don't see forms:

### ✅ Check 1: Cards Array Populated

```javascript
// Browser console (F12)
console.log(cards);

// Expected output:
[
  {id: 5, question: "What type...", answer: "File-based", ...},
  {id: 4, question: "Can SQLite...", answer: "Yes", ...},
  ...
]

// If empty [] or undefined:
// → No cards due for review
// → Run: python3 init_learning_cards_for_user.py
```

---

### ✅ Check 2: JavaScript Loaded

```javascript
// Browser console
typeof loadCard

// Expected: "function"
// If "undefined":
// → JavaScript file didn't load
// → Check browser console for 404 errors
```

---

### ✅ Check 3: Elements Present

```javascript
// Browser console
document.getElementById('question-text')

// Expected: <div id="question-text">...</div>
// If null:
// → Template didn't render
// → Check server logs for errors
```

---

### ✅ Check 4: API Working

```bash
# Terminal
curl -X POST http://localhost:5001/api/learn/answer \
  -H "Content-Type: application/json" \
  -d '{"card_id":5,"quality":4,"session_id":1}'

# Expected:
{"interval_days":1,"streak":0,"accuracy":100.0}

# If error:
# → Backend route broken
# → Check app.py:11793
```

---

## Comparison: Quiz-Style vs Anki-Style

### Quiz-Style (What You Might Expect)

```
┌─────────────────────────────────────────┐
│ Question: What is 2+2?                  │
│                                         │
│ Your Answer: [______________]           │
│              ↑ Text input box           │
│                                         │
│ [Submit] [Next] [Skip]                  │
└─────────────────────────────────────────┘

User types answer → Computer grades → Right/Wrong
```

---

### Anki-Style (What We Actually Have)

```
┌─────────────────────────────────────────┐
│ Question: What is 2+2?                  │
│                                         │
│ (Think of answer...)                    │
│                                         │
│ [Show Answer]                           │
│                                         │
│ Answer: 4                               │
│                                         │
│ How well did you know?                  │
│ [0-Forgot] [1-Hard] ... [5-Perfect]     │
└─────────────────────────────────────────┘

User recalls mentally → Reveals answer → Rates self
```

**Why Anki-style?**
- Proven by research (spaced repetition)
- Faster than typing
- Better for memorization
- Works for any content type (not just factual)

---

## Mobile Version

On phone, the UI adapts:

```
┌──────────────────┐
│ 📚 Review        │
│                  │
│ Card 1/12        │
│ ▓▓░░░░░░░░ 20%   │
│                  │
│ ┏━━━━━━━━━━━━┓   │
│ ┃ Question   ┃   │
│ ┃            ┃   │
│ ┃ What is... ┃   │
│ ┗━━━━━━━━━━━━┛   │
│                  │
│ [Show Answer]    │
│                  │
│ ┌──────┐         │
│ │  0   │         │
│ │Forgot│         │
│ └──────┘         │
│ ┌──────┐         │
│ │  3   │         │
│ │Good  │         │
│ └──────┘         │
│ ┌──────┐         │
│ │  5   │         │
│ │Perfect│        │
│ └──────┘         │
└──────────────────┘
```

**Responsive design:** Tailwind CSS adapts grid to screen size

---

## Summary

**The "forms" you're looking for:**
1. ❌ NOT text input boxes
2. ✅ ARE rating buttons (0-5)

**Flow:**
1. Question displays
2. Click "Show Answer"
3. Answer reveals
4. Click rating button (0-5)
5. Stats update
6. Next card loads

**If nothing shows:**
- Wait 1-2 seconds for JavaScript
- Check browser console (F12) for errors
- Verify cards array has data (`console.log(cards)`)
- Initialize cards if needed (`python3 init_learning_cards_for_user.py`)

**This is working as designed!** It's Anki-style flashcards, not traditional quiz forms.

---

**Created:** 2025-12-27
**Demo:** Visit http://localhost:5001/learn/review to see it in action
**Next:** Read [TEMPLATE_DATA_FLOW.md](TEMPLATE_DATA_FLOW.md) to understand how data flows from backend to frontend
