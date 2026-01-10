# 🏗️ COMPLETE ARCHITECTURE MAP
**Soulfra Magic Publish & Multi-Domain AI System**
**Last Updated:** 2026-01-02

---

## 📊 SYSTEM OVERVIEW

This is a **multi-domain AI-powered blog publishing system** with **multi-tenant chat capabilities**. It combines:
- 22 Ollama models (9 custom, 13 base)
- Flask web application (0.0.0.0:5001)
- SQLite database (36 posts, 8 brands, 16 users)
- Multiple frontends for different use cases
- Network-accessible chat for roommate collaboration

---

## 🎯 YOUR VISION (FROM YOUR DESCRIPTION)

> "i make a super easy 1 window chat with my ollama, and then i get that to work and build out my localhost, which is the admin to the ip or something where my roommates can come. and then also they can create accounts but i have all the ais from other domains that can comment or help on what their asks are"

**Translation into Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                   YOUR LAPTOP (Admin)                       │
│                                                             │
│  http://localhost:5001                                      │
│  ┌──────────────────────────────────────┐                  │
│  │  ADMIN INTERFACE                     │                  │
│  │  - Full control panel                │                  │
│  │  - Model management                  │                  │
│  │  - User management                   │                  │
│  │  - Publishing tools                  │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  Ollama Server: 0.0.0.0:11434                              │
│  Flask Server: 0.0.0.0:5001                                │
└─────────────────────────────────────────────────────────────┘
                        ↓ Network (192.168.1.87)
┌─────────────────────────────────────────────────────────────┐
│              ROOMMATE ACCESS (User Mode)                    │
│                                                             │
│  http://192.168.1.87:5001                                   │
│  ┌──────────────────────────────────────┐                  │
│  │  CHAT INTERFACE                      │                  │
│  │  - Simple 1-window chat              │                  │
│  │  - Model selection                   │                  │
│  │  - Conversation history              │                  │
│  │  - Multi-AI collaboration            │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  Each roommate has:                                         │
│  - Own account/session                                      │
│  - Access to all domain AIs                                 │
│  - Ability to ask questions                                 │
│  - Get responses from multiple experts                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 YOUR 22 AI MODELS

### Custom Domain Experts (9 Models)

| Model | Size | Specialization | When to Use |
|-------|------|----------------|-------------|
| **soulfra-model** | 3.8GB | Identity, security, API keys, encryption | Security questions, auth design |
| **calos-model** | 2.0GB | CalOS sysadmin, server management | System administration, DevOps |
| **publishing-model** | 2.0GB | Content publishing, blog strategy | Writing, editing, content strategy |
| **drseuss-model** | 2.0GB | Creative writing (Dr. Seuss style) | Creative content, poetry, fun writing |
| **deathtodata-model** | 986MB | Privacy advocacy, data protection | Privacy policy, GDPR questions |
| **calos-expert** | 2.0GB | CalRiven system administration | Server config, backup strategies |
| **visual-expert** | 4.7GB | Visual/image analysis | Image processing, visual Q&A |
| **iiif-expert** | 4.4GB | IIIF protocol (image sharing) | Digital libraries, image APIs |
| **jsonld-expert** | 4.4GB | JSON-LD, semantic web, linked data | API design, structured data |

### Base Models (13 Models)
- llama3.2:3b (general purpose)
- qwen2.5-coder:1.5b (coding assistant)
- mistral:7b (general purpose, larger)
- ... and 10 more

---

## 🎨 MULTI-DOMAIN AI COLLABORATION

### How Multiple AIs Can "Comment" on a Question

**Example User Question from Roommate:**
> "How do I build a secure API for sharing photos with friends?"

**System Flow:**
```
1. User sends question to /api/chat/send
2. Flask backend routes to MULTIPLE models:

   ┌─────────────────────┐
   │ jsonld-expert       │ → "Use JSON-LD for metadata structure"
   ├─────────────────────┤
   │ soulfra-model       │ → "Implement OAuth2 + API key rotation"
   ├─────────────────────┤
   │ visual-expert       │ → "Consider EXIF data privacy issues"
   ├─────────────────────┤
   │ iiif-expert         │ → "Use IIIF Image API for delivery"
   ├─────────────────────┤
   │ deathtodata-model   │ → "Strip EXIF GPS data before sharing!"
   └─────────────────────┘

3. Chat UI displays all responses in thread
4. User sees expert commentary from each domain
```

**Implementation Options:**

#### Option A: Sequential Consultation (Current - Manual)
```python
# User manually selects models in chat UI
# Each model responds one at a time
@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    model = request.json['model']  # Single model
    message = request.json['message']
    response = ollama.chat(model=model, messages=[...])
    return response
```

#### Option B: Parallel Consultation (Future - Automatic)
```python
# System automatically asks RELEVANT models
@app.route('/api/chat/consult', methods=['POST'])
def chat_consult_experts():
    message = request.json['message']

    # Detect relevant domains (keyword matching or meta-model routing)
    relevant_models = detect_expertise_needed(message)
    # Returns: ['soulfra-model', 'jsonld-expert', 'visual-expert']

    # Query all in parallel
    responses = []
    for model in relevant_models:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": message}])
        responses.append({
            "model": model,
            "expert": model.replace("-model", "").replace("-expert", ""),
            "response": response['message']['content']
        })

    return {"consultations": responses}
```

**Chat UI Display:**
```
┌──────────────────────────────────────────────────┐
│ You: How do I build a secure API for photos?    │
├──────────────────────────────────────────────────┤
│ 💼 Soulfra (Security Expert):                    │
│ "Implement OAuth2 with API key rotation..."     │
├──────────────────────────────────────────────────┤
│ 🔗 JSONLD (API Expert):                          │
│ "Use JSON-LD for metadata structure..."         │
├──────────────────────────────────────────────────┤
│ 🖼️ Visual (Image Expert):                       │
│ "Consider EXIF data privacy issues..."          │
├──────────────────────────────────────────────────┤
│ 💀 DeathToData (Privacy Expert):                 │
│ "Strip EXIF GPS data before sharing!"           │
└──────────────────────────────────────────────────┘
```

---

## 🎓 FINE-TUNING: CATEGORY-SPECIFIC VS GENERALIST

### Your Question:
> "can we do fine tunings specific to categories then more generalist as well? or how do these things work for a domain too"

**Answer: YES - You're Already Doing Both!**

### Current Setup (Category-Specific Models)

Each of your 9 custom models is **category-specific**:

```dockerfile
# Example: soulfra-model (SECURITY SPECIALIST)
FROM llama3.2:3b

SYSTEM """
You are Soulfra, an identity and security expert focused on API key management,
encryption, and vault systems. You prioritize security-first solutions.
"""

PARAMETER temperature 0.7  # Focused, less creative

MESSAGE user What's the best way to store API keys?
MESSAGE assistant Never store API keys in plain text...
# 50-100 examples of security Q&A
```

```dockerfile
# Example: drseuss-model (CREATIVE SPECIALIST)
FROM llama3.2:3b

SYSTEM """
You are a creative writer in the style of Dr. Seuss, focused on
whimsical rhymes, imaginative stories, and playful language.
"""

PARAMETER temperature 0.9  # High creativity

MESSAGE user Write a story about a cat
MESSAGE assistant In a house, not too big, not too small...
# 50-100 examples of creative writing
```

**Trade-offs:**

| Aspect | Category-Specific | Generalist |
|--------|------------------|------------|
| **Accuracy** | ✅ Excellent in domain | ⚠️ Good across all |
| **Tone** | ✅ Perfect brand voice | ⚠️ Generic |
| **Storage** | ❌ Multiple models (23GB total) | ✅ One model (3-7GB) |
| **Speed** | ✅ Fast (small models) | ⚠️ Slower (larger model) |
| **Collaboration** | ✅ Multiple experts per question | ❌ Single perspective |

### Strategy: HYBRID APPROACH (Recommended)

**Keep Your Specialists + Add One Generalist Router**

```
User Question
     ↓
┌─────────────────────┐
│ router-model:latest │  ← NEW: Generalist model that routes questions
│ (llama3.2:3b base)  │
└─────────────────────┘
     ↓
"This is a security question about API keys"
     ↓
┌─────────────────────┐
│ soulfra-model       │  ← Specialist handles actual response
└─────────────────────┘
```

**Create router-model:**
```dockerfile
FROM llama3.2:3b

SYSTEM """
You are a routing assistant. Your job is to identify the domain expertise needed
for a question and recommend which specialist models should respond.

Available specialists:
- soulfra-model: Security, encryption, API keys, auth
- calos-model: System administration, DevOps, servers
- publishing-model: Content writing, blogging, editing
- jsonld-expert: APIs, structured data, semantic web
- visual-expert: Image processing, visual content
- iiif-expert: Image APIs, digital libraries
- deathtodata-model: Privacy, GDPR, data protection

Respond with JSON: {"models": ["model1", "model2"], "reasoning": "why"}
"""

MESSAGE user How do I build a secure photo sharing API?
MESSAGE assistant {"models": ["soulfra-model", "jsonld-expert", "visual-expert", "deathtodata-model"], "reasoning": "Security (auth), API design (structure), image handling, privacy concerns"}
```

**Benefits:**
- ✅ Keep your brand-specific voices
- ✅ Automatically route to relevant experts
- ✅ Multiple perspectives on complex questions
- ✅ Fallback to generalist if no specialist matches

---

## 🏠 MULTI-TENANT ARCHITECTURE (ROOMMATE SYSTEM)

### Current Database Schema

```sql
-- users table (16 users currently)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT,
    created_at TIMESTAMP
);

-- chat_sessions (track conversations)
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    model_name TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- chat_messages (conversation history)
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    model_name TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);
```

### Roommate Access Flow

```
1. Roommate visits http://192.168.1.87:5001/chat

2. First-time user sees registration:
   ┌──────────────────────────────┐
   │ Welcome! Create Account      │
   │                              │
   │ Username: [________]         │
   │ Email (opt): [________]      │
   │                              │
   │ [ Create Account ]           │
   └──────────────────────────────┘

3. System creates user record + session ID

4. Chat interface loads:
   ┌──────────────────────────────────────┐
   │ 🤖 Soulfra AI Network                │
   │ Logged in as: roommate_mike          │
   ├──────────────────────────────────────┤
   │ Select AI Experts:                   │
   │ [x] Soulfra (Security)               │
   │ [x] JSONLD (APIs)                    │
   │ [ ] Publishing (Writing)             │
   │ [ ] CalOS (Sysadmin)                 │
   │                                      │
   │ Or: [Auto-detect] [All experts]      │
   ├──────────────────────────────────────┤
   │ You: _________________________       │
   │                           [Send]     │
   └──────────────────────────────────────┘

5. Messages stored with user_id for history

6. Each roommate sees only their own conversations
   (or optionally, shared workspace)
```

### Access Control Levels

```python
# Simple role-based access
ROLES = {
    'admin': {  # You on localhost
        'can_manage_users': True,
        'can_manage_models': True,
        'can_publish_blogs': True,
        'can_view_all_chats': True,
        'can_access_studio': True
    },
    'roommate': {  # Network users
        'can_manage_users': False,
        'can_manage_models': False,
        'can_publish_blogs': False,
        'can_view_all_chats': False,  # Only their own
        'can_access_studio': False
    }
}

# Detect access level by IP
@app.before_request
def check_access():
    if request.remote_addr == '127.0.0.1':
        session['role'] = 'admin'
    else:
        session['role'] = 'roommate'
```

---

## 🗺️ FRONTEND MAP

### Available Interfaces

| URL | Purpose | Who Uses | Status |
|-----|---------|----------|--------|
| `/` | Landing page | Everyone | ✅ Working |
| `/chat` | Unified chat interface | Roommates | ✅ Working |
| `/studio` | Magic Publish UI (blog creation) | Admin only | ✅ Working |
| `/master-control` | Master Control Panel | Admin only | ✅ Working |
| `/status` | System dashboard | Admin only | ✅ Working |
| `/post/<slug>` | Individual blog posts | Public | ❌ HTTP 500 |

### Recommended Setup

**Admin (You on localhost:5001):**
- `/master-control` - Main dashboard
- `/studio` - Create blog posts
- `/status` - Monitor system health
- `/chat` - Test models

**Roommates (192.168.1.87:5001):**
- `/chat` - Primary interface (only this)
- Redirect all other URLs to /chat for simplicity

**Implementation:**
```python
@app.before_request
def restrict_roommate_access():
    if session.get('role') == 'roommate':
        allowed_paths = ['/chat', '/api/chat/send', '/api/chat/history']
        if request.path not in allowed_paths:
            return redirect('/chat')
```

---

## 🔧 CURRENT BUGS TO FIX

### 1. Post Slug Route (HTTP 500)
**File:** app.py:1433
**Error:** `/post/<slug>` crashes
**Impact:** Blog posts not viewable
**Priority:** HIGH (breaks public-facing feature)

### 2. Domain Manager KeyError
**File:** domain_manager.py:47
**Error:** `KeyError: 'name'`
**Impact:** Studio can't load domain list
**Priority:** MEDIUM (admin feature)

---

## 🚀 NEXT STEPS TO BUILD YOUR VISION

### Phase 1: Fix Existing Bugs (1-2 hours)
1. Fix `/post/<slug>` route
2. Fix domain_manager.py KeyError
3. Test all frontends

### Phase 2: Create Simple Chat UI (2-3 hours)
1. Design clean 1-window chat interface
2. Add model selection (checkboxes for each expert)
3. Implement "Auto-detect" mode (router model)
4. Add conversation history sidebar

### Phase 3: Multi-Tenant System (3-4 hours)
1. Add user registration form
2. Implement session management
3. Add role-based access control (admin vs roommate)
4. Restrict roommates to /chat only

### Phase 4: Multi-AI Collaboration (4-5 hours)
1. Create router-model Modelfile
2. Implement /api/chat/consult endpoint
3. Update chat UI to display multiple expert responses
4. Add "Ask All Experts" button

### Phase 5: Polish & Documentation (2-3 hours)
1. Create user guide for roommates
2. Add onboarding tutorial
3. Test on multiple devices
4. Finalize open-source prep

**Total Estimated Time:** 12-17 hours

---

## 📚 TECHNICAL IMPLEMENTATION DETAILS

### How Ollama Modelfiles Work

**Modelfile = Instructions for Creating a Custom Model**

```dockerfile
# Base model (pre-trained by Meta/Alibaba)
FROM llama3.2:3b

# System prompt (defines personality/expertise)
SYSTEM """
Your core identity and expertise goes here.
This is like hiring a specialist vs a generalist.
"""

# Parameters (control behavior)
PARAMETER temperature 0.7  # 0.0 = deterministic, 1.0 = creative
PARAMETER top_p 0.9        # Nucleus sampling
PARAMETER top_k 40         # Token selection diversity

# Training examples (few-shot learning)
MESSAGE user Example question 1
MESSAGE assistant Example answer 1

MESSAGE user Example question 2
MESSAGE assistant Example answer 2

# Add 50-100 examples for best results
```

**When you run:**
```bash
ollama create soulfra-model -f Modelfile.soulfra
```

**What happens:**
1. Ollama loads base model (llama3.2:3b)
2. Applies system prompt as context
3. Fine-tunes behavior based on examples
4. Saves as new model (soulfra-model:latest)
5. Model size: ~3.8GB (base + customizations)

**Training Data Sources (Your Case):**
- ✅ 100% original content (you wrote it)
- ✅ Brand personality documents
- ✅ Example Q&A pairs
- ✅ Blog posts as style examples
- ✅ No third-party copyrighted data

**Licensing:**
- Base model: Meta Community License (llama3.2) or Apache 2.0 (qwen)
- Your fine-tuned model: Apache 2.0 (recommended)
- Commercial use: ✅ Allowed
- Redistribution: ✅ Allowed

### Category-Specific vs Generalist Trade-offs

**Why You Have 9 Specialists Instead of 1 Generalist:**

**Specialist Approach (Your Current System):**
```
soulfra-model (3.8GB)     → Security questions
calos-model (2.0GB)       → Sysadmin questions
publishing-model (2.0GB)  → Writing questions
jsonld-expert (4.4GB)     → API design questions
...
Total: 23GB, 9 models
```

**Pros:**
- ✅ Perfect brand voice per domain
- ✅ Higher accuracy in specialized areas
- ✅ Parallel consultation (multiple experts on one question)
- ✅ Clear separation of concerns

**Cons:**
- ❌ More storage space
- ❌ Need routing logic to pick right model
- ❌ Can't handle cross-domain questions well alone

**Generalist Approach (Alternative):**
```
mega-model (7GB)  → All questions
Total: 7GB, 1 model
```

**Pros:**
- ✅ Less storage
- ✅ No routing needed
- ✅ Better at cross-domain questions

**Cons:**
- ❌ Generic voice (loses brand personalities)
- ❌ Lower accuracy in specialized areas
- ❌ Can't get multiple perspectives

**Hybrid Approach (Recommended for You):**
```
router-model (3.8GB)       → Routes questions
  ↓ delegates to specialists ↓
soulfra-model (3.8GB)      → Security
calos-model (2.0GB)        → Sysadmin
publishing-model (2.0GB)   → Writing
...
Total: 26.8GB, 10 models
```

**Best of both worlds:**
- ✅ Keep specialist accuracy
- ✅ Keep brand voices
- ✅ Automatic routing
- ✅ Multi-expert collaboration
- ⚠️ Slightly more storage (+3.8GB)

---

## 🎯 YOUR USE CASE RECOMMENDATIONS

### For Your Personal Use (Admin)
**Best Models:**
- `router-model` - Automatically picks specialists
- All 9 specialists - Full toolkit
- `llama3.2:3b` - General fallback

**Interface:**
- `/master-control` - Dashboard
- `/studio` - Publishing
- `/chat` - Testing/personal queries

### For Your Roommates (Network Users)
**Best Models:**
- `router-model` - Simplifies model selection
- Top 3-5 specialists based on their interests
- Example: If roommate is a developer → `soulfra-model`, `jsonld-expert`, `calos-model`

**Interface:**
- `/chat` ONLY - Simple, focused
- Auto-detect mode enabled by default
- Optional: Manual model selection for power users

### For Multi-AI Collaboration
**Implementation:**
```javascript
// Frontend: chat.html
function askAllExperts(question) {
    fetch('/api/chat/consult', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message: question,
            mode: 'auto'  // or 'all' for all experts
        })
    })
    .then(response => response.json())
    .then(data => {
        // Display each expert's response
        data.consultations.forEach(consultation => {
            addMessage(consultation.expert, consultation.response);
        });
    });
}
```

```python
# Backend: app.py
@app.route('/api/chat/consult', methods=['POST'])
def chat_consult():
    message = request.json['message']
    mode = request.json.get('mode', 'auto')

    if mode == 'auto':
        # Use router model to detect relevant experts
        routing = ollama.chat(
            model='router-model',
            messages=[{"role": "user", "content": f"What experts should answer: {message}"}]
        )
        models = json.loads(routing['message']['content'])['models']
    elif mode == 'all':
        # Use all 9 custom models
        models = [
            'soulfra-model', 'calos-model', 'publishing-model',
            'jsonld-expert', 'visual-expert', 'iiif-expert',
            'deathtodata-model', 'drseuss-model', 'calos-expert'
        ]

    # Query each model in parallel (use threading for speed)
    responses = []
    for model in models:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": message}]
        )
        responses.append({
            "expert": model.replace('-model', '').replace('-expert', ''),
            "response": response['message']['content']
        })

    return {"consultations": responses}
```

---

## 🔍 DEBUGGING CHECKLIST

Before moving forward, verify these work:

### Network Access
- [x] Ollama accessible at http://192.168.1.87:11434 ✅
- [x] Flask accessible at http://192.168.1.87:5001 ✅
- [x] `/chat` route works ✅
- [x] `/studio` route works ✅
- [ ] `/post/<slug>` route works ❌ (fix needed)

### Database
- [x] 36 posts with slugs ✅
- [x] 8 brands configured ✅
- [x] 16 users exist ✅
- [ ] chat_sessions table exists? (check)
- [ ] chat_messages table exists? (check)

### Models
- [x] 22 models loaded in Ollama ✅
- [x] 9 custom models accessible ✅
- [ ] router-model created? (TODO)

### Multi-Tenant
- [ ] User registration works? (test)
- [ ] Session management works? (test)
- [ ] Role-based access control? (implement)

---

## 📖 RELATED DOCUMENTATION

- **OPEN-SOURCE-PREP.md** - Release checklist
- **MODEL-TRAINING-DOCS.md** - Training methodology
- **SOC2-GDPR-COMPLIANCE.md** - Security/privacy
- **requirements.txt** - Python dependencies
- **ROOMMATE-NETWORK-ACCESS-PLAN.md** - Network setup
- **GITHUB-URL-MAP.md** - GitHub Pages domains

---

**Ready to build? Let's start with fixing the bugs, then move to the multi-AI chat system!** 🚀
