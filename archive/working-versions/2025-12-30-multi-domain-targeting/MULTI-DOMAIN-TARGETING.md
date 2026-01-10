# Multi-Domain Targeting System (WoW-Style)

## What This Does

Lets you select multiple domains like tab-targeting in World of Warcraft, then ask Ollama to analyze relationships between them.

## How It Works

### Click/Ctrl+Click Targeting
- **Click domain** → Sets as **Primary Target** (green highlight)
- **Ctrl+Click another** → Sets as **Secondary Target** (blue highlight)
- **Click again** → Deselects target

### Tab Key Switching
- Press **Tab** → Switches active target between Primary ↔ Secondary
- Shows which target is currently active

### Ollama Comparison
- **"Compare Targets" button** appears when 2+ domains targeted
- Sends both domains to Ollama
- Asks: "How can soulfra.com and calriven.com cross-promote?"

## UI Changes

```
Domains List:
━━━━━━━━━━━━━━━━
● Soulfra (Primary)
⦿ Calriven (Secondary)
□ DeathToData
□ DealOrDelete
```

Ollama Chat:
```
[Compare Targets] ← New button

Chat window shows:
"Comparing soulfra.com and calriven.com..."
```

## Use Cases

1. **Cross-Promotion Analysis**
   - Target: soulfra.com + calriven.com
   - Ask: "How can these cross-promote?"

2. **Content Alignment**
   - Target: deathtodata.com + finishthisidea.com
   - Ask: "What content themes overlap?"

3. **Affiliate Opportunities**
   - Target: sellthismvp.com + saveorsink.com
   - Ask: "Cross-selling opportunities?"

## Technical Implementation

### CSS Classes
- `.primary-target` - Green border/background
- `.secondary-target` - Blue border/background
- `.active-target` - Pulsing border

### JavaScript Variables
```javascript
let primaryTarget = null;
let secondaryTarget = null;
```

### New Functions
- `setTarget(domain, type)` - Set primary/secondary target
- `switchTarget()` - Tab key handler
- `compareTargets()` - Send both to Ollama

## Keyboard Shortcuts

- **Click** - Set primary target
- **Ctrl+Click** - Set secondary target
- **Tab** - Switch active target
- **Esc** - Clear all targets

## Example Workflow

1. Visit http://localhost:5001/domains
2. Click "Soulfra" → Primary target (green)
3. Ctrl+Click "Calriven" → Secondary target (blue)
4. Click "Compare Targets" button
5. Ollama analyzes both domains
6. Shows cross-promotion opportunities

## Status

✅ CSS styling added
✅ Click/Ctrl+Click handlers
✅ Tab key switching
✅ Compare button
✅ Ollama integration
✅ Visual feedback
