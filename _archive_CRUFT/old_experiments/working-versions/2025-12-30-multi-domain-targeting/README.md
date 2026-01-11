# Multi-Domain Targeting System - Working Backup
**Date:** December 30, 2025
**Git Tag:** v1.0-multi-domain-targeting
**Git Commit:** 7aeed77

## What's Archived

This directory contains a **WORKING SNAPSHOT** of the multi-domain targeting system that allows you to:

1. ✅ Target unlimited domains (not just 2)
2. ✅ Assign different Ollama models per domain
3. ✅ Compare N domains for cross-promotion opportunities
4. ✅ Generate production code from comparisons
5. ✅ Use WoW-style click/Ctrl+click targeting

## Files Included

```
domain_manager.html         - Main UI with targeting system
web_domain_manager_routes.py - Flask routes (defaults to 'classic' template)
automation_workflows.py     - Made anthropic optional
app.py                      - Disabled conflicting admin/workflow routes
HOW-TO-USE-TARGETING.md     - User guide
MULTI-DOMAIN-TARGETING.md   - Technical documentation
README.md                   - This file
```

## How to Restore

If something breaks in the future, restore from this archive:

```bash
# 1. Navigate to soulfra-simple directory
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# 2. Backup current (broken) files
cp templates/domain_manager.html templates/domain_manager.html.broken
cp web_domain_manager_routes.py web_domain_manager_routes.py.broken
cp automation_workflows.py automation_workflows.py.broken
cp app.py app.py.broken

# 3. Restore from archive
cp archive/working-versions/2025-12-30-multi-domain-targeting/domain_manager.html templates/
cp archive/working-versions/2025-12-30-multi-domain-targeting/web_domain_manager_routes.py .
cp archive/working-versions/2025-12-30-multi-domain-targeting/automation_workflows.py .
cp archive/working-versions/2025-12-30-multi-domain-targeting/app.py .

# 4. Restart Flask server
pkill -f "python.*app.py"
python app.py
```

## OR Use Git Tag

```bash
git checkout v1.0-multi-domain-targeting -- soulfra-simple/templates/domain_manager.html
git checkout v1.0-multi-domain-targeting -- soulfra-simple/web_domain_manager_routes.py
git checkout v1.0-multi-domain-targeting -- soulfra-simple/automation_workflows.py
git checkout v1.0-multi-domain-targeting -- soulfra-simple/app.py
```

## Verification

After restoring, verify it works:

1. Start Flask: `python app.py`
2. Visit: http://localhost:5001/domains
3. Click a domain → Should see green "TARGET 1" badge
4. Ctrl+Click another → Should see blue "TARGET 2" badge
5. Change model dropdown → Should update target info
6. Click "Compare N Domains" → Should send to Ollama
7. Select code type → Click "Generate Code" → Should create prompt

## Features Summary

### 🎯 Targeting System
- **Click** any domain → Sets as Target 1 (green)
- **Ctrl+Click** another → Sets as Target 2 (blue)
- Keep clicking to add up to 8 targets (each with unique color)
- **Tab key** cycles through targets
- Click same domain again to deselect

### 🤖 Model Specialization
Each domain has a dropdown with 6 models:
- `llama3.2` (General)
- `codellama` (Code)
- `mistral` (Fast)
- `phi` (Small)
- `gemma` (Creative)
- `llama2` (Stable)

Selected model is stored with each target and shown in target info.

### 🔄 Comparison
When 2+ targets selected, "Compare N Domains" button appears.
Sends detailed prompt to Ollama with:
- All domain names
- Their selected models
- Request for cross-promotion strategies

### ⚡ Code Generation
When 2+ targets selected, code generation controls appear.
Choose from:
- Shared Component
- Landing Page
- Cross-Promo Widget
- Integration Code
- Affiliate Link System
- Shared Newsletter Template

Click "Generate Code" → Creates detailed prompt for Ollama to generate production-ready vanilla HTML/CSS/JS.

## Technical Notes

### Key JavaScript Variables
```javascript
let targets = [];  // Array of {domain, name, index, model}
let domainModels = {};  // {domain: model} mapping
```

### Key Functions
```javascript
handleDomainClick(event, domain, name)  // Adds/removes targets
handleModelChange(event, domain)        // Updates model selection
compareTargets()                        // Sends comparison to Ollama
generateCode()                          // Sends code gen to Ollama
updateTargetUI()                        // Refreshes visual state
```

### CSS Classes
```css
.target-0 to .target-7  // Color-coded target states
.model-selector         // Model dropdown styling
.code-gen-controls      // Code generation UI
```

## What NOT to Change

🚫 **Do not modify these without extensive testing:**
- `handleDomainClick` function - Core targeting logic
- `refreshTargetClasses` function - Re-indexing system
- `targets` array structure - Must have {domain, name, index, model}
- Target CSS classes (target-0 through target-7)

## Testing Checklist

After any modifications, verify:
- [ ] Click domain → shows Target 1 badge
- [ ] Ctrl+Click another → shows Target 2 badge
- [ ] Click same domain again → removes target
- [ ] Tab key cycles through targets
- [ ] Model dropdown appears on each domain
- [ ] Changing model updates target info
- [ ] Compare button appears with 2+ targets
- [ ] Code gen controls appear with 2+ targets
- [ ] Generated prompts include model info
- [ ] All targets properly color-coded

## Git Information

**Commit Message:**
```
🎯 LOCKED: Multi-Domain Targeting System - WORKING

Features Implemented:
✅ N-domain targeting (unlimited domains, not just 2)
✅ WoW-style click/Ctrl+click selection
✅ 8 color-coded target states with unique icons
✅ Model specialization per domain (6 Ollama models)
✅ Code generation from comparisons (6 code types)
✅ Tab key cycling through targets
✅ Dynamic UI updates
```

**Tag:** v1.0-multi-domain-targeting
**Commit SHA:** 7aeed77

## Support

If you need to understand how this works:
- Read `HOW-TO-USE-TARGETING.md` for user guide
- Read `MULTI-DOMAIN-TARGETING.md` for technical details
- Check git history: `git log --oneline | grep "LOCKED"`
- View this commit: `git show 7aeed77`

---

**Status:** ✅ WORKING
**Last Verified:** 2025-12-30
**Server:** http://localhost:5001/domains
**Do Not Delete This Archive**
