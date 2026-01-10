# Voice Feedback System

**Browser-based text-to-speech tied to user progression**

No external APIs, no tacotron2-DDC bullshit, just simple pitch/speed/tone control.

---

## How It Works

Uses browser's built-in `speechSynthesis` API (works in all modern browsers).

**Tier-based customization:**

| Level | Recordings | Voice Settings | Example Message |
|-------|-----------|----------------|-----------------|
| 0 (Free) | 0-4 | Normal speed, normal pitch | "Squad match found" |
| 1 | 5-9 | 20% faster | "Squad match found with high similarity" |
| 2 | 10-49 | 20% faster, deeper voice | "New squad member detected" |
| 3 | 50-99 | 30% faster, custom voice | "Yo! Found your squad" |
| 4 | 100+ | 50% faster, deepest voice | "Hell yeah! Squad match at 92%" |

---

## Usage

**In HTML:**

```html
<script src="voice-feedback.js"></script>
<script>
const voiceFeedback = new VoiceFeedback(userLevel);

// Announce events
voiceFeedback.announceRecordingSaved();
voiceFeedback.announceSquadMatch(0.87, 3);  // 87% match, 3 members
voiceFeedback.announceLevelUp(2);

// Custom message
voiceFeedback.announce("Custom message here");

// Toggle on/off
voiceFeedback.toggle();

// Stop current speech
voiceFeedback.stop();
</script>
```

---

## Events with Voice

### Onboarding Flow

1. **Recording saved** → "Recording saved" (or variant based on level)
2. **Squad match found** → "Squad match found" (with similarity %)
3. **Level up** → "Level up! New features unlocked"

### Future Integration Ideas

- **Word of the Year unlocked** → "You unlocked Word of the Year. Your top word is 'infrastructure'"
- **Encyclopedia milestone** → "50 recordings! Encyclopedia features unlocked"
- **New feature available** → "Custom wordmap now available"
- **Error messages** → "Microphone not found" (slower, clearer)

---

## Customization

**Adjust voice settings** (in `voice-feedback.js`):

```javascript
getVoiceSettings() {
    const settings = {
        0: { rate: 1.0, pitch: 1.0, volume: 0.8 },  // Free tier
        1: { rate: 1.2, pitch: 1.0, volume: 0.9 },  // Faster
        2: { rate: 1.2, pitch: 0.8, volume: 0.9 },  // Deeper
        3: { rate: 1.3, pitch: 0.9, volume: 1.0 },  // Fast + deep
        4: { rate: 1.5, pitch: 0.7, volume: 1.0 }   // Max custom
    };
    return settings[this.userLevel] || settings[0];
}
```

**Adjust messages** (in `getMessage()` function):

```javascript
'squad_match': {
    0: 'Squad match found',
    1: 'Squad match found with high similarity',
    2: 'New squad member detected',
    3: 'Yo! Found your squad',
    4: 'Hell yeah! Squad match at {similarity}%'
}
```

---

## Browser Support

**Works in:**
- ✅ Chrome/Edge (all versions)
- ✅ Safari (macOS/iOS)
- ✅ Firefox (all versions)

**Doesn't work in:**
- ❌ Old IE (who cares)

**Fallback:** If browser doesn't support, silently fails (no errors)

---

## Why This Instead of External TTS?

**Browser API:**
- ✅ Free
- ✅ Offline
- ✅ Fast (instant)
- ✅ No API keys
- ✅ Works everywhere

**External (Google TTS, Coqui, tacotron2-DDC):**
- ❌ Requires internet
- ❌ Slower (API latency)
- ❌ More dependencies
- ❌ Weird names (tacotron2-DDC lol)

**Simple wins.**

---

## Testing

**Open browser console:**

```javascript
// Test different levels
const v0 = new VoiceFeedback(0);
v0.announceSquadMatch(0.92);

const v4 = new VoiceFeedback(4);
v4.announceSquadMatch(0.92);

// Compare the difference!
```

---

## Next Steps

- [ ] Add to encyclopedia.html
- [ ] Add to wordmap.html
- [ ] Add to record-simple.html
- [ ] Custom voices per user preference
- [ ] Voice speed slider in settings
- [ ] Mute button in UI

**Status:** ✅ Working in onboarding.html
