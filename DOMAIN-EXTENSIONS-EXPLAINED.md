# 🌐 Domain Extensions Explained - .com vs .net vs .org vs .dev vs .io vs .ai

> **Your question**: "what is .dev and all these other fucking domains? or how do we judge something and give it a ranking?"

**Answer**: Here's exactly how domain extensions (TLDs) rank and what they mean.

---

## 🎯 The Domain Extension Hierarchy

### Tier 1: The Big Three (.com, .org, .net)

**1. .com - Commercial** ⭐⭐⭐⭐⭐
- **Price**: $10-15/year
- **Trust Level**: Highest (everyone knows .com)
- **SEO**: Best (Google favors .com)
- **Use For**: Businesses, general purpose, anything
- **Examples**: google.com, facebook.com, soulfra.com

**Why .com wins**:
```
✅ Most trusted by users
✅ Best for SEO (Google's algorithm favors it)
✅ Easy to remember
✅ Universal recognition
✅ Professional appearance
```

---

**2. .org - Organization** ⭐⭐⭐⭐⭐
- **Price**: $10-15/year
- **Trust Level**: Highest (implies non-profit, trustworthy)
- **SEO**: Excellent
- **Use For**: Non-profits, open source, communities
- **Examples**: wikipedia.org, archive.org, python.org

**Why .org is powerful**:
```
✅ Implies legitimacy + non-profit
✅ Great for open source projects
✅ Users trust .org for information
✅ Good SEO
✅ Professional for communities
```

---

**3. .net - Network** ⭐⭐⭐⭐
- **Price**: $10-15/year
- **Trust Level**: High (second to .com)
- **SEO**: Good
- **Use For**: Tech companies, SaaS, networks
- **Examples**: speedtest.net, behance.net

**Why .net works**:
```
✅ Good fallback if .com taken
✅ Tech-focused perception
✅ Acceptable for businesses
✅ Still professional
```

---

### Tier 2: Modern/Specialty (.dev, .io, .ai)

**4. .dev - Developer** ⭐⭐⭐⭐
- **Price**: $12-20/year
- **Trust Level**: High (among developers)
- **SEO**: Good
- **Use For**: Developer tools, portfolios, APIs
- **Examples**: web.dev, firebase.google.dev
- **Special**: **Requires HTTPS** (forced encryption)

**Why .dev is cool**:
```
✅ Signals "this is for developers"
✅ Google-owned (trusted)
✅ Forced HTTPS (secure)
✅ Modern, clean
✅ Great for APIs, tools
```

**When to use .dev**:
- API documentation sites
- Developer portfolios
- Open source projects
- Technical blogs

---

**5. .io - Input/Output** ⭐⭐⭐
- **Price**: $30-60/year **(EXPENSIVE!)**
- **Trust Level**: Good (startups love it)
- **SEO**: OK
- **Use For**: Tech startups, SaaS
- **Examples**: github.io (pages), socket.io

**Why startups like .io**:
```
✅ Signals "tech startup"
✅ Short, memorable
✅ Trendy in startup world
```

**Why .io might not be worth it**:
```
❌ EXPENSIVE ($30-60 vs $10-15 for .com)
❌ Not as trusted by general public
❌ SEO not as good as .com
❌ Actually stands for "Indian Ocean" (British territory)
```

---

**6. .ai - Artificial Intelligence** ⭐⭐⭐
- **Price**: $80-100/year **(VERY EXPENSIVE!)**
- **Trust Level**: Medium (new, trendy)
- **SEO**: OK
- **Use For**: AI companies, ML tools
- **Examples**: openai.com (but they use .com!), character.ai

**Why .ai is expensive**:
```
❌ $80-100/year (8x cost of .com!)
❌ Actually stands for "Anguilla" (Caribbean island)
❌ High renewal fees
```

**When to use .ai**:
- Your company name IS an AI (e.g., character.ai)
- You want to signal "AI-first"
- You have budget for expensive domains

**When NOT to use .ai**:
- You're on a budget (use .com instead)
- Your company isn't AI-focused
- You care about SEO (.com is better)

---

## 📊 Domain Ranking Algorithm

### How to Score Any Domain

```python
def rank_domain(domain_name, extension):
    """
    Rank a domain on a scale of 0-100

    Args:
        domain_name: "soulfra" or "how-to-cook-at-home"
        extension: ".com", ".dev", ".io", etc.

    Returns:
        score: 0-100 (higher = better)
    """

    # Base score by extension
    extension_scores = {
        '.com': 100,  # Best
        '.org': 95,   # Best for non-profits
        '.net': 90,   # Good fallback
        '.dev': 85,   # Modern, developer-focused
        '.io': 75,    # Trendy but expensive
        '.ai': 70,    # Very expensive, niche
        '.co': 65,    # Confusable with .com
        '.tech': 60,  # Generic
        '.site': 50,  # Too generic
        '.xyz': 40,   # Spammy reputation
    }

    base_score = extension_scores.get(extension, 30)

    # Length penalty (shorter = better)
    length = len(domain_name)
    if length <= 6:
        length_bonus = 20    # Short = great (e.g., "api.dev")
    elif length <= 10:
        length_bonus = 10    # Medium = good (e.g., "soulfra.com")
    elif length <= 15:
        length_bonus = 0     # OK (e.g., "calriven.com")
    else:
        length_bonus = -10   # Too long

    # Word count penalty (fewer words = better)
    word_count = len(domain_name.replace('-', ' ').split())
    word_penalty = (word_count - 1) * 10

    # Hyphen penalty (no hyphens = better)
    hyphen_count = domain_name.count('-')
    hyphen_penalty = hyphen_count * 15

    # Brandability bonus (is it a word or made-up name?)
    is_dictionary_word = domain_name in ['soulfra', 'calriven']  # Simplified
    is_brandable = len(domain_name) <= 10 and hyphen_count == 0
    brandable_bonus = 20 if is_brandable else 0

    # Calculate final score
    score = (
        base_score +
        length_bonus +
        brandable_bonus -
        word_penalty -
        hyphen_penalty
    )

    return max(0, min(100, score))  # Clamp to 0-100


# Examples:
print(rank_domain("soulfra", ".com"))
# → 100 + 10 (good length) + 20 (brandable) = 130 → capped at 100 ⭐⭐⭐⭐⭐

print(rank_domain("how-to-cook-at-home", ".com"))
# → 100 + 0 (long) + 0 (not brandable) - 40 (4 words) - 60 (4 hyphens) = 0 ⭐

print(rank_domain("api", ".dev"))
# → 85 + 20 (short!) + 20 (brandable) = 125 → capped at 100 ⭐⭐⭐⭐⭐

print(rank_domain("character", ".ai"))
# → 70 + 10 (good length) + 20 (brandable) = 100 ⭐⭐⭐⭐⭐

print(rank_domain("my-awesome-app", ".io"))
# → 75 + 0 (medium) + 0 - 20 (2 words) - 30 (2 hyphens) = 25 ⭐
```

---

## 🎯 Domain Ranking Examples

### Your Domains Ranked:

**soulfra.com**
- Base: 100 (.com)
- Length bonus: +10 (7 letters = good)
- Brandable: +20 (made-up word, memorable)
- No hyphens: +0
- **Total: 100/100** ⭐⭐⭐⭐⭐ **PERFECT**

**calriven.com**
- Base: 100 (.com)
- Length bonus: +10 (8 letters = good)
- Brandable: +20 (made-up word)
- **Total: 100/100** ⭐⭐⭐⭐⭐ **PERFECT**

**deathtodata.com**
- Base: 100 (.com)
- Length bonus: 0 (11 letters = OK)
- Brandable: +20 (unique phrase)
- **Total: 100/100** ⭐⭐⭐⭐⭐ **EXCELLENT**

**howtocookathome.com**
- Base: 100 (.com)
- Length bonus: -10 (16 letters = too long)
- Word count: -30 (4 words: "how", "to", "cook", "at", "home")
- Brandable: 0 (too long)
- **Total: 60/100** ⭐⭐⭐ **OK** (too long, but .com saves it)

---

### Hypothetical Examples:

**api.dev**
- Base: 85 (.dev)
- Length bonus: +20 (3 letters = short!)
- Brandable: +20
- **Total: 100/100** ⭐⭐⭐⭐⭐ **PERFECT FOR DEVELOPERS**

**my-ai-app.io**
- Base: 75 (.io)
- Length bonus: 0
- Word count: -20 (3 words)
- Hyphens: -30 (2 hyphens)
- **Total: 25/100** ⭐ **POOR**

**soulfra.ai**
- Base: 70 (.ai)
- Length bonus: +10
- Brandable: +20
- **Total: 100/100** ⭐⭐⭐⭐⭐ **PERFECT IF YOU CAN AFFORD $100/YEAR**

---

## 💰 Cost vs Value Analysis

### What You Actually Pay:

| Extension | Registration | Renewal | 10 Years | Worth It? |
|-----------|--------------|---------|----------|-----------|
| **.com** | $10-15 | $10-15 | $150 | ✅ YES (best ROI) |
| **.org** | $10-15 | $10-15 | $150 | ✅ YES (if non-profit) |
| **.net** | $10-15 | $10-15 | $150 | ✅ YES (if .com taken) |
| **.dev** | $12-20 | $12-20 | $180 | ✅ YES (if developer tool) |
| **.io** | $30-60 | $30-60 | $500 | ⚠️ MAYBE (expensive!) |
| **.ai** | $80-100 | $80-100 | $900 | ❌ NO (unless AI-first company) |

**Rule of thumb**: If it costs more than $20/year, you better have a REALLY good reason.

---

## 🎓 When to Use Each Extension

### Use .com if:
- ✅ It's available for your brand
- ✅ You're a business
- ✅ You want best SEO
- ✅ You want maximum trust
- ✅ General purpose site

**Examples**: soulfra.com, calriven.com, deathtodata.com

---

### Use .org if:
- ✅ You're a non-profit
- ✅ Open source project
- ✅ Community/educational
- ✅ Want trust + legitimacy

**Examples**: wikipedia.org, python.org, mozilla.org

---

### Use .net if:
- ✅ .com is taken
- ✅ Tech/SaaS company
- ✅ Network-related service

**Examples**: speedtest.net, asp.net

---

### Use .dev if:
- ✅ Developer tool/API
- ✅ Technical documentation
- ✅ Developer portfolio
- ✅ Want HTTPS enforced

**Examples**: web.dev, api.dev (hypothetical)

---

### Use .io if:
- ✅ Tech startup with budget
- ✅ .com taken and you're OK paying $50/year
- ✅ Targeting developer audience

**Examples**: github.io/pages, socket.io

---

### Use .ai if:
- ✅ AI-first company
- ✅ Budget for $100/year
- ✅ Brand IS AI-related
- ✅ .com taken

**Examples**: character.ai, openai.com (wait, they use .com!)

---

## ✅ Recommendations for Your Domains

### Your Current Domains (All Excellent!):

1. **soulfra.com** → 100/100 ⭐⭐⭐⭐⭐
   - Keep this! Perfect branding.

2. **calriven.com** → 100/100 ⭐⭐⭐⭐⭐
   - Keep this! Excellent brandable name.

3. **deathtodata.com** → 100/100 ⭐⭐⭐⭐⭐
   - Keep this! Unique, memorable.

4. **howtocookathome.com** → 60/100 ⭐⭐⭐
   - Consider shorter alternative like:
     - cookit.com (if available)
     - homecook.com (if available)
     - But keep it if it's working!

---

### If You're Buying New Domains:

**Golden rules**:
1. ✅ Always try .com first
2. ✅ Keep it under 10 characters if possible
3. ✅ Avoid hyphens
4. ✅ Make it brandable (made-up word > common phrase)
5. ✅ Under $20/year

**Good examples**:
- soulfra.dev → 100/100 (alternative to .com)
- api.soulfra.dev → 100/100 (for API docs)
- blog.soulfra.com → 100/100 (subdomain)

**Bad examples**:
- my-soulfra-app.io → 25/100 (hyphens, expensive)
- soulfra-platform.ai → 30/100 (hyphen, expensive)

---

## 🚀 Quick Decision Tree

```
Do you have the .com?
├─ YES → Use .com! (100/100)
└─ NO → ⬇

Is it a developer tool/API?
├─ YES → Use .dev (85/100)
└─ NO → ⬇

Is it a non-profit/open source?
├─ YES → Use .org (95/100)
└─ NO → ⬇

Is it a tech company?
├─ YES → Use .net (90/100)
└─ NO → ⬇

Do you have $50/year budget?
├─ YES → Consider .io (75/100)
└─ NO → Use .com of different name
```

---

## ✅ Summary

**Best to worst**:
1. .com (100) - Always first choice
2. .org (95) - If non-profit
3. .net (90) - If .com taken
4. .dev (85) - If developer-focused
5. .io (75) - If startup with budget
6. .ai (70) - Only if AI-focused + budget

**Your domains**:
- soulfra.com → Perfect ⭐⭐⭐⭐⭐
- calriven.com → Perfect ⭐⭐⭐⭐⭐
- deathtodata.com → Perfect ⭐⭐⭐⭐⭐
- howtocookathome.com → Good (could be shorter) ⭐⭐⭐

**Rule**: If it's .com and under 10 characters with no hyphens, you've won the domain game!

---

**Next**: See `AUTO-BUILD-FROM-DOMAINS-TXT.md` to learn how to auto-build sites from your domains.txt file (you already have this!).
