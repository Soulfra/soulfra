# System Map: The "Idea → Docs → Learning" Loop

**Last Updated**: 2025-12-27

This document explains how Soulfra's self-learning documentation platform works - from voice ideas to AI-validated learning materials.

---

## Overview: "Learn The Docs" - Your Ideas Become Your Curriculum

Soulfra is a **self-documenting learning platform** where:
- Your ideas (voice/text) become documentation
- Your docs become interactive tutorials
- Tutorials become spaced-repetition flashcards
- AI personas auto-comment and validate your thinking
- Everything organizes itself using neural networks

**The Core Loop:**
```
Idea Capture → Brand Building → Documentation → Tutorial Generation →
Learning Cards → AI Classification → Auto-Commenting → Back to Ideas
```

---

## Stage 1: Idea Capture (Voice → Text)

**Files**: `voice_input.py`, `qr_voice_integration.py`

### How It Works:
1. **Record idea via voice** (offline-first)
   - Audio stored locally in `voice_inputs` table
   - Queued for transcription (manual or Whisper API)

2. **Transcription** (manual or auto when online)
   - `voice_input.transcribe_audio()` → converts audio to text
   - Text ready for brand builder

### Database Tables:
```sql
voice_inputs (
    id, filename, file_path, duration_seconds,
    transcription, status, created_at
)
```

### Purpose:
- Capture thoughts fast without typing
- Works 100% offline
- Queue-based processing

---

## Stage 2: Brand Building ("Recipe" Creation)

**Files**: `brand_builder.py`

### How It Works:
1. **Conversational wizard** asks 5-6 questions:
   - What problem are you solving?
   - Who's your audience?
   - What tone? (Professional / Fun / Bold / Calm)
   - What makes you unique?
   - 3 personality words?

2. **Brand concept created** (the "recipe"):
   ```python
   brand_config = {
       'name': 'MyBrand',
       'personality': 'thoughtful, analytical, precise',
       'tone': 'professional',
       'unique_value': 'Makes complex topics simple',
       'target_audience': 'Developers learning AI'
   }
   ```

3. **Stored in brands table** with individual columns:
   - `personality_tone`, `personality_traits`, `category`
   - `color_primary`, `color_secondary`, `color_accent` (visual identity)
   - **Brand tiers**: `foundation` / `business` / `creative`

### CamelCase/PascalCase Convention:
Brand names use **PascalCase** for identity:
- `CalRiven` = Technical architecture AI
- `DeathToData` = Privacy/security AI
- `Soulfra` = Philosophical reasoning AI

### Database Tables:
```sql
brands (
    id, name, slug, tagline, category, tier,
    personality_tone, personality_traits,
    color_primary, color_secondary, color_accent
)

conversation_messages (
    id, conversation_id, role, content
)
```

### Purpose:
- Convert raw ideas into structured brand identities
- Create personality "recipes" for consistent voice
- Generate visual design systems automatically

---

## Stage 3: Documentation (Brand → Posts)

**Files**: `app.py` (routes `/admin/post/new`)

### How It Works:
1. **Write documentation/blog posts** about your brand/idea
2. **Auto-tagging** based on brand category and personality
3. **Neural network classification** predicts:
   - Technical difficulty
   - Topic categories
   - Target audience fit

### Database Tables:
```sql
posts (
    id, user_id, title, slug, content,
    published_at, ai_processed
)
```

### Purpose:
- Transform brand concepts into actual documentation
- Create searchable knowledge base
- Prepare content for tutorial generation

---

## Stage 4: Tutorial Generation (Docs → Questions)

**Files**: `tutorial_builder.py`

### How It Works:
1. **Reads blog post content** (up to 2000 chars)
2. **Calls Ollama API** (100% offline, `llama3.2:3b`)
3. **Generates questions** in 2 styles:

   **GeeksForGeeks-style** (technical):
   ```python
   {
       "question": "What does SQLite use for primary keys?",
       "options": ["UUID", "Auto-increment", "Random"],
       "answer": "Auto-increment",
       "explanation": "SQLite automatically generates..."
   }
   ```

   **Cringeproof-style** (aptitude/self-awareness):
   ```python
   {
       "question": "I often think about how my work documents itself",
       "category": "reflection"  # 1-5 scale rating
   }
   ```

4. **7 questions generated per post** by default

### Database Tables:
```sql
tutorials (
    id, post_id, title, description,
    difficulty, category, created_at
)
```

### Purpose:
- Auto-generate learning materials from docs
- No manual quiz creation needed
- Tests understanding of your own concepts

---

## Stage 5: Learning Cards (Questions → Flashcards)

**Files**: `anki_learning_system.py`

### How It Works:
1. **Import tutorial questions** → flashcards
   ```python
   import_tutorial_questions(tutorial_id, questions)
   ```

2. **Neural network predicts difficulty**:
   - Uses `calriven_technical_classifier`
   - Analyzes word count, complexity, jargon
   - Assigns difficulty score (0.0 = easy, 1.0 = hard)

3. **SM-2 algorithm** schedules reviews:
   - Spaced repetition like Anki
   - Adaptive intervals based on performance
   - Tracks retention and streaks

### Database Tables:
```sql
learning_cards (
    id, tutorial_id, question, answer, explanation,
    question_type, difficulty_predicted, neural_classifier
)

learning_progress (
    id, user_id, card_id, repetitions, ease_factor,
    interval_days, next_review, last_reviewed
)
```

### Purpose:
- Transform docs into long-term memory
- Personalized learning paths
- Minimize time, maximize retention

---

## Stage 6: AI Classification & Organization

**Files**: `neural_network.py`, `brand_ai_orchestrator.py`

### How It Works:
1. **Neural networks loaded at startup**:
   - `calriven_technical_classifier` → Technical content
   - `theauditor_validation_classifier` → Fact-checking
   - `deathtodata_privacy_classifier` → Privacy concerns
   - `soulfra_judge` → Philosophical reasoning

2. **Auto-classification**:
   - Posts tagged by category
   - Questions tagged by difficulty
   - Comments tagged by sentiment

3. **Orchestration** (which AI should comment?):
   ```python
   orchestrate_brand_comments(post_id)
   # Returns: relevance scores for each AI persona
   # Only top-ranked AIs comment
   ```

### Database Tables:
```sql
neural_networks (
    id, name, model_type, weights, config
)

tags (
    id, name, category
)

post_tags (
    id, post_id, tag_id
)
```

### Purpose:
- Auto-organize knowledge
- Match content to right AI personas
- Maintain quality through classification

---

## Stage 7: AI Auto-Commenting (Validation & Discussion)

**Files**: `ollama_auto_commenter.py`, `brand_ai_persona_generator.py`, `event_hooks.py`

### How It Works:
1. **Post created** → Triggers `on_post_created()` hook in `app.py:7770-7775`

2. **Orchestrator selects AIs**:
   ```python
   selected = orchestrate_brand_comments(post_id)
   # Returns: [
   #   {'brand_slug': 'calriven', 'relevance': 0.85},
   #   {'brand_slug': 'soulfra', 'relevance': 0.72}
   # ]
   ```

3. **AI generates comment** for each selected persona:
   ```python
   generate_ai_comment(brand_slug='calriven', post_id=42)
   ```

   - Loads AI persona config (system prompt, personality)
   - Reads post content
   - Calls Ollama API with context
   - Generates 2-3 paragraph comment
   - Stores in `comments` table

4. **Comment post-processing**:
   - Removes AI preambles ("Here's my comment:")
   - Ensures 150-250 words
   - Checks for quality/relevance

### AI Persona System Prompts:
Each brand has a unique voice:
```python
# CalRiven (Technical Architecture)
"You are CalRiven, a meticulous technical architect AI.
Your responses are precise, analytical, and solution-oriented..."

# DeathToData (Privacy/Security)
"You are DeathToData, a privacy-focused security AI.
You question data collection and promote user sovereignty..."

# Soulfra (Philosophical Reasoning)
"You are Soulfra, a philosophical reasoning AI.
You explore deeper meanings and challenge assumptions..."
```

### Database Tables:
```sql
users (
    id, username, display_name, is_ai_persona
)

comments (
    id, post_id, user_id, content, created_at
)

reasoning_steps (
    id, comment_id, step_number, thought, confidence
)
```

### Purpose:
- Validate your thinking with AI feedback
- Generate discussion automatically
- Multiple perspectives on every post
- **Provable reasoning** (AI explains its logic)

---

## The Full Loop Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  1. IDEA CAPTURE                                            │
│  Voice/Text → Transcription → Raw Idea                     │
│  File: voice_input.py                                       │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  2. BRAND BUILDING                                          │
│  Conversational Wizard → Brand Recipe (personality + tone)  │
│  File: brand_builder.py                                     │
│  Result: PascalCase brand identity (e.g., CalRiven)        │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  3. DOCUMENTATION                                           │
│  Brand → Blog Posts/Docs → Searchable Knowledge Base       │
│  File: app.py (/admin/post/new)                            │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  4. TUTORIAL GENERATION                                     │
│  Docs → Ollama AI → GeeksForGeeks-style Questions          │
│  File: tutorial_builder.py                                  │
│  Result: 7 Q&A pairs per post                              │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  5. LEARNING CARDS                                          │
│  Questions → Neural Network Difficulty → Anki Flashcards   │
│  File: anki_learning_system.py                              │
│  Result: Spaced repetition schedule (SM-2 algorithm)       │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  6. AI CLASSIFICATION                                       │
│  Neural Networks → Auto-Tag → Organize by Category         │
│  File: neural_network.py, brand_ai_orchestrator.py         │
│  Networks: CalRiven, TheAuditor, DeathToData, Soulfra      │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  7. AI AUTO-COMMENTING                                      │
│  Post Created → Orchestrator → AI Personas Generate Comments│
│  File: ollama_auto_commenter.py, event_hooks.py            │
│  Result: 2-3 AI comments with reasoning threads            │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
              [Back to Ideas]
   (AI feedback inspires new thoughts → Voice capture)
```

---

## Key Concepts Explained

### "Auto-Dictation" = Automated Knowledge Flow
Not literal speech-to-text dictation, but **self-organizing knowledge**:
1. Voice → Text (transcription)
2. Text → Brand (personality "recipe")
3. Brand → Docs (you write, system organizes)
4. Docs → Questions (Ollama generates)
5. Questions → Cards (neural network classifies)
6. Cards → Study Plan (SM-2 schedules)
7. Posts → AI Comments (personas auto-validate)

**It "dictates itself"** by:
- Auto-generating tutorials from your docs
- Auto-scheduling learning reviews
- Auto-commenting with AI reasoning
- Auto-tagging and organizing

### Brand Tiers (Database Column)
In `brands` table, `tier` field:
- **foundation**: Core platform infrastructure (Soulfra, CalRiven)
- **business**: Commercial/enterprise brands
- **creative**: Artistic/experimental brands

### Engagement Tiers (AI Persona Access)
In `brand_ai_persona_generator.py`, tier parameter:
- **free**: Basic AI commenting
- **pro**: Advanced reasoning threads
- **enterprise**: Custom AI training

### Tags & Categories
- **Tags**: User-defined labels (e.g., `#python`, `#ai`, `#security`)
- **Categories**: System-defined buckets (e.g., `technical`, `philosophical`, `privacy`)
- **Neural classification**: Auto-applies both based on content analysis

### CamelCase/PascalCase Convention
Brand identities use **PascalCase** for memorable naming:
- Single word: `Soulfra`, `CalRiven`
- Multi-word: `DeathToData`, `OceanDreams`
- Slug form: `soulfra`, `calriven`, `ocean-dreams`

**Why?** Easier to remember, brand-like, distinguishes from generic terms.

---

## Database Flow Visualization

```
voice_inputs → transcription
    ↓
brands (brand_config)
    ↓
posts → tutorials → learning_cards
    ↓         ↓            ↓
  tags   questions   learning_progress
    ↓         ↓            ↓
neural_networks  →  difficulty prediction
    ↓
users (AI personas) → comments → reasoning_steps
```

---

## CLI Tools & Testing

### Generate AI Personas:
```bash
python3 brand_ai_persona_generator.py generate-all
```

### Create Tutorial from Post:
```bash
python3 tutorial_builder.py --post-id 1
```

### Test AI Auto-Commenting:
```bash
python3 ollama_auto_commenter.py auto 1 --dry-run
```

### Check Learning Stats:
```bash
python3 anki_learning_system.py --stats
```

### Review Due Cards:
```bash
python3 anki_learning_system.py --review
```

---

## File Reference

| Component | Primary Files |
|-----------|---------------|
| **Idea Capture** | `voice_input.py`, `qr_voice_integration.py` |
| **Brand Building** | `brand_builder.py` |
| **Documentation** | `app.py` (routes 7730-7780) |
| **Tutorial Gen** | `tutorial_builder.py` |
| **Learning Cards** | `anki_learning_system.py` |
| **AI Classification** | `neural_network.py`, `brand_ai_orchestrator.py` |
| **Auto-Commenting** | `ollama_auto_commenter.py`, `brand_ai_persona_generator.py` |
| **Event Wiring** | `event_hooks.py` |

---

## Summary: The "Diffusion" Process

Your **idea** becomes a **brand recipe** →
Diffuses into **documentation** →
Transforms into **interactive tutorials** →
Solidifies as **learning flashcards** →
Gets **validated by AI personas** →
Feeds back as **new inspiration**

**Every step is automatic after the initial idea capture.**

This is a **self-learning, self-documenting, self-validating** knowledge platform where your thoughts evolve into structured, learnable, AI-validated content.

---

**Status**: ✅ All systems operational. AI auto-commenting live. Ready for testing.

**Next**: Create a post at http://localhost:5001/admin/post/new and watch AI personas comment automatically.
