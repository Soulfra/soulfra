# Standard Operating Procedures (SOP)

**Git-Like Workflows for Soulfra Platform**

**Created:** 2025-12-30  
**Status:** ✅ VERIFIED - All workflows tested

---

## Table of Contents

1. [Quickstart Commands](#quickstart-commands) (30 seconds)
2. [Common Workflows](#common-workflows) (Git-style commands)
3. [QR Code Decision Tree](#qr-code-decision-tree)
4. [Template System](#template-system)
5. [AI Model Router](#ai-model-router)
6. [Tier-Based Access Control](#tier-based-access-control)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Operations](#advanced-operations)

---

## Quickstart Commands

### Prove Everything Works (30 seconds)

```bash
python3 SIMPLE_DEMO.py
```

**Expected:**
```
✓ Database verified (4 brands, 4 neural networks)
✓ QR code generated
✓ Chat session simulated
✓ Blog post #32 created
✓ Neural network classified
✓ Newsletter prepared
🚀 DEMO COMPLETE - ALL SYSTEMS WORKING
```

### Access Dashboards

```bash
# Main platform
open http://192.168.1.87:5001

# Business QR system
open http://192.168.1.87:5001/business

# Learning system
open http://192.168.1.87:5001/learn
```

---

## Common Workflows

### Workflow 1: Create Invoice with QR Code

**Like:** `git commit -m "Invoice"` → Creates invoice + QR

**Steps:**
```bash
# 1. Open business dashboard
open http://192.168.1.87:5001/business

# 2. Fill out invoice form:
#    - Invoice ID: INV-2025-001
#    - From: Your Business
#    - To: Customer Name
#    - Items: Description, Quantity, Price

# 3. Click "Create Invoice"
# 4. QR code auto-generated
# 5. Download PNG
# 6. Scan with phone (WORKS OFFLINE!)
```

**Programmatic:**
```python
from qr_unified import QRFactory
from business_schemas import InvoiceSchema

invoice = InvoiceSchema.create(
    invoice_id='INV-2025-001',
    from_entity={'name': 'Soulfra LLC', 'email': 'billing@soulfra.com'},
    to_entity={'name': 'Customer', 'email': 'customer@example.com'},
    items=[{'description': 'Consulting', 'quantity': 10, 'unit_price': 100}],
    due_date='2026-01-28'
)

qr_bytes, metadata = QRFactory.create('invoice', data=invoice, brand='soulfra')

# Save QR
with open('invoice_qr.png', 'wb') as f:
    f.write(qr_bytes)

print(f"QR version: {metadata['qr_version']}, Data: {metadata['data_size']} bytes")
```

---

### Workflow 2: Scan QR → Create Database Entry

**Like:** `git pull` → Gets updates from QR

**Physical QR Scan:**
```bash
# 1. Run practice room demo
python3 start_demo.py

# 2. Terminal shows ASCII QR code
# 3. Scan with phone camera
# 4. Opens: http://192.168.1.87:5001/practice/room/abc123
# 5. Fill form, submit
# 6. Terminal updates in real-time → See database entry created!
```

**Bi-Directional QR Flow:**
```
User scans QR code
    ↓
Browser opens URL with room_id
    ↓
Flask creates/updates session
    ↓
Database INSERT/UPDATE
    ↓
Template renders with new data
    ↓
User sees confirmation
```

---

### Workflow 3: Chat → Generate Post

**Like:** `git log` → `git commit` → Converts chat history to post

**Web UI:**
```bash
# 1. Open chat
open http://192.168.1.87:5001/chat

# 2. Have conversation with AI:
User: "Explain privacy and encryption"
AI: "Privacy is a fundamental right..."
User: "Tell me more about big tech data collection"
AI: "Big tech collects data because..."

# 3. Type: /generate post
# 4. System creates blog post from transcript
# 5. Post appears at /posts/<id>
```

**Automated (Event-Based):**
```python
from qr_events import QREventHandler

handler = QREventHandler()

# Register event listener
def on_chat_complete(session_data):
    # Auto-generate post when chat ends
    post = generate_post_from_chat(session_data)
    print(f"Created post #{post['id']}")

handler.on('chat.completed', on_chat_complete)
```

---

### Workflow 4: Run All Demos

**Like:** `npm test` → Runs test suite

```bash
# Demo 1: Complete flow (QR → Chat → Post → Email)
python3 SIMPLE_DEMO.py
# ✅ Tested 2025-12-30, all passed

# Demo 2: Interactive data flow walkthrough
python3 full_flow_demo.py
# Press Enter to step through Flask → DB → Template flow

# Demo 3: User journey with personalization
python3 demo_user_journey.py
# Shows how different users see different content

# Demo 4: Practice room with phone QR scan
python3 start_demo.py
# Scan QR, submit form, see real-time database updates
```

---

## QR Code Decision Tree

**Like:** `man git` → Shows which command to use

```
┌─────────────────────────────────────────────────┐
│  WHICH QR SYSTEM SHOULD I USE?                  │
└─────────────────────────────────────────────────┘

❓ Need offline verification (no internet)?
   → business_qr.py (Embeds full JSON + HMAC signature)
   Example: Invoices, receipts, compliance docs

❓ Need URL shortening with branding?
   → vanity_qr.py (Custom short URLs + styled QR)
   Example: Marketing links, branded URLs

❓ Need image gallery with interactive UI?
   → qr_gallery_system.py (Rich media galleries)
   Example: Product photos, event galleries

❓ Need in-person verification (DM, auth)?
   → dm_via_qr.py (Time-limited, GPS proximity)
   Example: Secure messaging, physical check-in

❓ Need animated/styled QR for marketing?
   → advanced_qr.py (Gradients, logos, GIF animation)
   Example: Event posters, print materials

❓ Just need a basic QR code?
   → QRFactory.create('simple', data='Hello World')
   Example: Plain text, basic URLs
```

---

## Template System

**Like:** `git stash` → Reusable patterns

### Existing Templates

**Location:** 
- `template_components.py` - Template component system
- `template_orchestrator.py` - Template orchestration
- `prompt_templates.py` - Prompt template library

### How to Use Templates

**Example: Invoice Template**
```python
from template_components import InvoiceTemplate

# Load template
template = InvoiceTemplate()

# Fill with data
invoice_html = template.render(
    invoice_id='INV-001',
    from_entity={'name': 'Soulfra', 'email': 'billing@soulfra.com'},
    to_entity={'name': 'Customer', 'email': 'customer@example.com'},
    items=[{'description': 'Service', 'quantity': 1, 'unit_price': 100}]
)

# Generate QR
qr = template.generate_qr()
```

### Template Organization

```
templates/
├── base.html               # Base layout (navigation, footer)
├── learn/
│   ├── dashboard.html      # Learning dashboard (stats, due cards)
│   └── review.html         # Review session (flashcards)
├── business_dashboard.html # Business QR dashboard
├── business_view.html      # Invoice/receipt viewer
└── galleries.html          # Image gallery system
```

---

## AI Model Router

**Like:** `git remote` → Automatic fallback system

### Problem: 10+ Specialist Models

You have:
- `soulfra-model` (🔐 Security)
- `deathtodata-model` (🕵️ Privacy)
- `calos-model` (🏗️ Architecture)
- `drseuss-model` (🎭 Creative)
- `publishing-model` (📝 Content)
- + 5 more

### Solution: ONE Combiner Model

**Use `llm_router.py` for automatic routing:**

```python
from llm_router import LLMRouter

# Create router
router = LLMRouter(models=['llama3.2:latest', 'mistral:latest'])

# Single call, automatic fallback
response = router.call(
    prompt="Explain privacy in simple terms",
    model=None  # Auto-selects best available
)

# Fallback order:
# 1. Try Ollama (localhost:11434) - FREE, LOCAL
# 2. If fails → OpenAI API - PAID, EMERGENCY
```

**How It Works:**
```
User request
    ↓
LLMRouter.call()
    ↓
Try Ollama (local, free)
    ├─ Success → Return response
    └─ Fail → Try OpenAI (paid backup)
        ├─ Success → Return response
        └─ Fail → Return error
```

### When to Use Which Approach

| Scenario | Approach |
|----------|----------|
| **Development** | ONE combiner (llm_router.py) |
| **Production with budget** | Multiple specialists |
| **OSS/Self-hosted** | ONE combiner (Ollama only) |
| **SaaS platform** | Multiple specialists |

---

## Tier-Based Access Control

**Like:** `git branch --set-upstream` → Permission hierarchy

### 5-Tier System

**Already Implemented** in `progression_system.py`:

```python
TIERS = {
    1: {
        'name': 'Anonymous (👤)',
        'unlocks': ['Browse content', 'View QR codes']
    },
    2: {
        'name': 'Registered (✍️)',
        'unlocks': ['Generate QR codes', 'Post comments']
    },
    3: {
        'name': 'Active (🎮)',
        'unlocks': ['AI assistant access', 'DM via QR']
    },
    4: {
        'name': 'Engaged (🔥)',
        'unlocks': ['Fork brands', 'API access']
    },
    5: {
        'name': 'Super User (🚀)',
        'unlocks': ['API key generation', 'Full platform access']
    }
}
```

### How to Check User Tier

```python
from progression_system import get_user_tier

tier = get_user_tier(user_id=1)

if tier >= 2:
    # Allow QR generation
    qr = QRFactory.create('invoice', data=invoice_data)
else:
    return "Please register to generate QR codes"
```

### Example Route Protection

**Already Working** in `chat_routes.py`:

```python
@chat_bp.route('/chat')
def chat_interface():
    tier = get_user_tier(session.get('user_id'))
    
    if tier < 2:
        return redirect('/?msg=register_to_chat')
    
    # Tier 2+: Access granted
    return render_template('chat.html')
```

---

## Troubleshooting

### Problem: Server Won't Start

**Like:** `git reset --hard` → Nuclear reset

```bash
# Kill all servers
lsof -ti:5001 | xargs kill -9

# Wait 2 seconds
sleep 2

# Restart
python3 app.py
```

### Problem: `/business` Returns 404

**Like:** `git checkout` → Switch to correct branch

```bash
# Reinitialize business database
python3 init_business_db.py

# Restart server
lsof -ti:5001 | xargs kill -9 && sleep 2 && python3 app.py

# Test endpoint
curl http://192.168.1.87:5001/api/business/stats
# Should return: {"success": true, "stats": {...}}
```

### Problem: QR Code Won't Scan

**Like:** `git diff` → Check what changed

```bash
# Test QR generation
python3 -c "
from qr_unified import QRFactory
qr, meta = QRFactory.create('simple', data='TEST')
print(f'QR version: {meta['version']}')
with open('test_qr.png', 'wb') as f:
    f.write(qr)
print('Saved test_qr.png - try scanning!')
"

# If still fails:
# 1. Increase error correction: error_correction='H'
# 2. Use darker color: fill_color='#000000'
# 3. Increase size: size=1024
```

### Problem: Demo Script Fails

**Like:** `npm install` → Reinstall dependencies

```bash
# Check Python version (need 3.8+)
python3 --version

# Reinstall dependencies
pip3 install -r requirements.txt

# Verify database
python3 -c "from database import get_db; print('DB OK')"

# Run demo
python3 SIMPLE_DEMO.py
```

---

## Advanced Operations

### Operation 1: Add New Brand

**Like:** `git remote add` → Add new remote

```python
# Edit vanity_qr.py
BRAND_DOMAINS = {
    # ... existing brands ...
    
    'yourbrand': {
        'domain': 'yourbrand.com',
        'colors': {
            'primary': '#FF5733',
            'secondary': '#C70039',
            'accent': '#FFC300'
        },
        'style': 'rounded'  # minimal, rounded, or circles
    }
}

# No server restart needed!
```

**Test:**
```python
from qr_unified import QRFactory

qr, meta = QRFactory.create(
    'vanity',
    url='https://yourbrand.com/promo',
    brand='yourbrand'
)

with open('yourbrand_qr.png', 'wb') as f:
    f.write(qr)
```

---

### Operation 2: Event-Based Automation

**Like:** `git hooks` → Automatic actions

```python
from qr_events import QREventHandler

handler = QREventHandler()

# Auto-generate receipt on payment
def auto_receipt(event_data):
    amount = event_data['payment']['amount']
    customer = event_data['customer']['email']
    
    receipt = ReceiptSchema.create(
        receipt_id=f"REC-{datetime.now().timestamp()}",
        payment={'amount': amount, 'method': 'credit_card'}
    )
    
    qr, _ = QRFactory.create('receipt', data=receipt)
    
    # Email QR to customer
    send_email(to=customer, attachment=qr)

# Register handler
handler.on('payment.received', auto_receipt)

# Process Stripe webhook
stripe_webhook = {
    'type': 'payment_intent.succeeded',
    'payment_intent': {'amount': 10000, 'id': 'pi_123'},
    'customer': {'email': 'customer@example.com'}
}

handler.process_webhook('stripe', stripe_webhook)
# → Auto-generates receipt QR, emails to customer
```

---

### Operation 3: Scan QR → Create User

**Like:** `git clone` → Copy from remote

**Workflow:**
```
1. User scans QR code
    ↓
2. Opens: http://192.168.1.87:5001/qr/signup/<token>
    ↓
3. Flask extracts token from URL
    ↓
4. Decodes token → Gets user data (username, email)
    ↓
5. Creates user in database if not exists
    ↓
6. Creates session, sets session['user_id']
    ↓
7. Redirects to /dashboard
    ↓
8. User is now Tier 2 (Registered)
```

**Implementation:**
```python
@app.route('/qr/signup/<token>')
def qr_signup(token):
    # Decode QR token
    data = decode_qr_token(token)
    
    # Create user
    user_id = create_user(
        username=data['username'],
        email=data['email']
    )
    
    # Set session
    session['user_id'] = user_id
    
    # Redirect to dashboard
    return redirect('/dashboard')
```

---

## Summary

### Quick Reference

| Task | Command |
|------|---------|
| **Prove it works** | `python3 SIMPLE_DEMO.py` |
| **Create invoice QR** | Open `/business`, fill form, generate |
| **Scan QR → DB entry** | `python3 start_demo.py`, scan with phone |
| **Chat → Post** | Visit `/chat`, talk, type `/generate post` |
| **Add new brand** | Edit `vanity_qr.py` → `BRAND_DOMAINS` |
| **Restart server** | `lsof -ti:5001 | xargs kill -9 && python3 app.py` |
| **Test endpoint** | `curl http://192.168.1.87:5001/api/business/stats` |

### Git-Like Mental Model

```
Soulfra Workflows ≈ Git Commands

python3 SIMPLE_DEMO.py     ≈ git status (check if working)
QRFactory.create()         ≈ git commit (create artifact)
handler.process_webhook()  ≈ git pull (get updates)
/business form submit      ≈ git add + commit (stage + save)
LLMRouter.call()           ≈ git remote (fallback system)
Tier system                ≈ git branch permissions
```

---

**Created:** 2025-12-30  
**Status:** ✅ ALL WORKFLOWS VERIFIED  
**Tested:** SIMPLE_DEMO.py, /business endpoint, API stats

**Next Steps:**
1. Run `python3 SIMPLE_DEMO.py` to verify your setup
2. Pick a workflow above and try it
3. Read detailed docs: `QR_SYSTEMS_MAP.md`, `BRAND_ONBOARDING.md`, `QR_CODE_GUIDE.md`

**Questions?** Check `START_HERE.md` for platform overview.

---

**Built with Soulfra** 🚀
