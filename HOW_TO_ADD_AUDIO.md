# How to Add Audio to CringeProof.com

## Quick Start

1. **Record or get your audio file** (wav, webm, mp3, m4a)

2. **Run the script:**
   ```bash
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   python add_audio_page.py my_recording.wav "My Idea Title" "Transcription text here"
   ```

3. **Push to GitHub:**
   ```bash
   cd voice-archive
   git add audio/8/
   git commit -m "Add audio recording #8"
   git push
   ```

4. **Wait 1-2 minutes** for GitHub Pages to deploy

5. **Visit:** `https://cringeproof.com/audio/8/`

## Examples

### Add a WAV recording:
```bash
python add_audio_page.py my_voice.wav "Testing CringeProof" "This is a test recording to see how it works"
```

### Add a WEBM recording (from browser):
```bash
python add_audio_page.py recording.webm "Browser Recording" "Recorded directly in the browser using record-simple.html"
```

### Add MP3 (converted from other format):
```bash
python add_audio_page.py idea.mp3 "My Startup Idea" "This is my million dollar idea..."
```

## What the Script Does

1. **Finds next number** - Looks at `/voice-archive/audio/` and picks the next available number
2. **Creates directory** - Makes `/voice-archive/audio/N/`
3. **Copies audio** - Saves your audio file as `recording.{ext}`
4. **Generates HTML** - Creates `index.html` with built-in audio player
5. **Shows instructions** - Tells you the git commands to run

## File Structure

After running the script:

```
voice-archive/
└── audio/
    └── 8/
        ├── index.html        # Audio player page
        └── recording.wav     # Your audio file
```

## HTML5 Audio Player

The generated pages use a simple HTML5 `<audio>` tag:

```html
<audio controls preload="metadata">
    <source src="recording.wav" type="audio/wav">
    Your browser does not support the audio element.
</audio>
```

Works on all modern browsers. No JavaScript, no backend needed.

## Supported Audio Formats

- ✅ **WAV** (`.wav`) - Uncompressed, large files
- ✅ **WebM** (`.webm`) - Browser standard, good compression
- ✅ **MP3** (`.mp3`) - Universal support
- ✅ **M4A** (`.m4a`) - Apple/iOS format
- ✅ **OGG** (`.ogg`) - Open source format

## Manual Method (No Script)

If you want to create pages manually:

1. Copy an existing audio page:
   ```bash
   cp -r voice-archive/audio/7/ voice-archive/audio/8/
   ```

2. Replace the audio file:
   ```bash
   cp my_recording.wav voice-archive/audio/8/recording.wav
   ```

3. Edit `index.html`:
   - Change the title
   - Update the transcription
   - Fix the audio `<source src="...">` if needed

4. Push to GitHub

## Sharing Links

Once pushed to GitHub, share these URLs:

- **Direct page**: `https://cringeproof.com/audio/8/`
- **Direct audio**: `https://cringeproof.com/audio/8/recording.wav`
- **Homepage** lists all recordings: `https://cringeproof.com/`

## Tips

- **Keep files under 10MB** for fast loading on GitHub Pages
- **Use descriptive titles** so people know what it's about
- **Add transcriptions** for accessibility (helps SEO too)
- **Test locally first** by opening `voice-archive/audio/8/index.html` in your browser

## Troubleshooting

**"Audio file not found"**
- Check the path to your audio file
- Use absolute or relative paths correctly

**"Unsupported audio format"**
- Convert to wav, webm, or mp3
- Use ffmpeg: `ffmpeg -i input.m4a output.wav`

**"Page shows but audio won't play"**
- Check browser console for errors
- Try a different audio format
- Ensure file isn't corrupted

**"404 on GitHub Pages"**
- Wait 2-3 minutes for deployment
- Check git push was successful
- Verify CNAME file exists: `voice-archive/CNAME`

## Next Steps

Want to automate this further?
- Hook it up to `/record-simple.html` to auto-upload
- Connect to Flask backend for transcription
- Build a web UI to manage recordings

For now, this script lets you manually add audio to cringeproof.com anytime!
