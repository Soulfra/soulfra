# How to Use Multi-Domain Targeting

## Quick Start

Visit: **http://localhost:5001/domains**

## WoW-Style Targeting

### 1. Select Primary Target
**Click any domain** → It becomes your **Primary Target** (green highlight)

```
● PRIMARY
━━━━━━━━━━
Soulfra
soulfra.com
```

### 2. Add Secondary Target
**Ctrl+Click another domain** → It becomes your **Secondary Target** (blue highlight)

```
● PRIMARY          ⦿ SECONDARY
━━━━━━━━━━         ━━━━━━━━━━━
Soulfra            Calriven
soulfra.com        calriven.com
```

### 3. Compare Them
The **"🔄 Compare Targets"** button appears automatically.

Click it → Ollama gets asked:
> "Compare soulfra.com and calriven.com. How can they cross-promote? What are the cross-selling opportunities? What content themes overlap?"

### 4. Switch Targets (Tab Key)
Press **Tab** → Swaps Primary ↔ Secondary

Useful for focusing on different target while keeping both selected.

## Use Cases

### Cross-Promotion Analysis
1. Click `soulfra.com` (Primary)
2. Ctrl+Click `calriven.com` (Secondary)
3. Click "Compare Targets"
4. Ollama suggests cross-promotion strategies

### Content Alignment
1. Click `deathtodata.com` (Primary)
2. Ctrl+Click `finishthisidea.com` (Secondary)
3. Click "Compare Targets"
4. Ollama finds overlapping themes

### Affiliate Opportunities
1. Click `sellthismvp.com` (Primary)
2. Ctrl+Click `saveorsink.com` (Secondary)
3. Click "Compare Targets"
4. Ollama suggests cross-selling products

## Visual Indicators

- **Green border + "● PRIMARY"** badge = Primary Target
- **Blue border + "⦿ SECONDARY"** badge = Secondary Target
- **Compare button** appears when 2+ targets selected
- **Target info** shows at top of Ollama chat

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Click | Set primary target |
| Ctrl+Click | Set secondary target |
| Tab | Switch active target |
| Esc | Clear all targets (coming soon) |

## Deselecting Targets

Click the same domain again to deselect it:
- Click primary again → removes primary
- Ctrl+Click secondary again → removes secondary

## Tips

1. **Start with 2 domains** - Compare button only shows with 2+ targets
2. **Use specific questions** - After clicking Compare, you can edit the Ollama prompt
3. **Tab between them** - Use Tab key to switch focus without reselecting
4. **Check the taglines** - Helps identify which domains might work well together

## Example Workflow

```
1. Visit http://localhost:5001/domains
2. Click "Soulfra" → Green "PRIMARY" badge appears
3. Ctrl+Click "Calriven" → Blue "SECONDARY" badge appears
4. See target info at top: "● Primary: soulfra.com / ⦿ Secondary: calriven.com"
5. "Compare Targets" button appears
6. Click it
7. Ollama analyzes both and suggests cross-promotion ideas
8. Press Tab to swap them if you want
9. Click either again to deselect
```

## What's Different from Before

### Old Way (Broken)
- Only see one domain at a time
- No comparison features
- Preview was broken
- Confusing UI with 3 different versions

### New Way (Working)
- Target multiple domains like WoW
- Compare them with Ollama
- Original template with working preview
- Simple, focused interface

## Next Steps

After Ollama gives suggestions, you can:
- Edit content on both domains
- Add cross-links between them
- Create shared content
- Set up affiliate relationships
- Plan joint promotions

---

**Status**: ✅ Working
**Server**: http://localhost:5001/domains
**Template**: Classic (original with working preview)
