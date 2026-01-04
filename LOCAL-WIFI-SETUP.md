# Local WiFi Setup - No OAuth, No Bullshit

**Dead simple: iPhone + MacBook on same WiFi → Scan QR → Record → Auto-updates README**

---

## Why This Is Better

❌ **OAuth version:**
- Create GitHub app
- Configure callback URLs
- Manage client secrets
- Handle sessions
- Deal with authorization flows
- **Requires internet access**

✅ **Local WiFi version:**
- Generate Personal Access Token (1 minute)
- Start Flask server
- Scan QR code
- Record
- **Works offline, just needs same WiFi**

---

## Step 1: Get Your Personal Access Token

### 1.1 Go to GitHub Settings

https://github.com/settings/tokens

Click: **"Generate new token (classic)"**

### 1.2 Configure Token

```
Note: Soulfra Voice Memos
Expiration: No expiration (or 90 days if you want to rotate)

Scopes (check these):
☑ repo (Full control of private repositories)
  ☑ repo:status
  ☑ repo_deployment
  ☑ public_repo
  ☑ repo:invite
  ☑ security_events
☑ gist (Create gists)
```

### 1.3 Generate & Copy Token

Click "Generate token"

Copy the token (starts with `ghp_`):
```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Save it!** You won't see it again.

---

## Step 2: Configure Environment

```bash
cd ~/Desktop/soulfra-profile

# Add token to .env
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env
echo "GITHUB_USERNAME=Soulfra" >> .env
```

That's it. No OAuth app needed.

---

## Step 3: Generate Local WiFi QR Code

Your MacBook IP: `192.168.1.87`

Generate QR code pointing to local Flask app:

```bash
cd scripts
python3 generate-qr-widget.py --url "http://192.168.1.87:5001/record" --output "../assets/qr-local.svg"
```

This creates a QR code that points directly to your MacBook.

---

## Step 4: Start Flask Server

```bash
cd ~/Desktop/soulfra-profile

# Start Flask on all interfaces (so iPhone can reach it)
python3 -m flask run --host=0.0.0.0 --port=5001
```

Or if you have a custom Flask app:

```python
# app.py
from flask import Flask, request, jsonify
from scripts.create_gist import create_story_from_voice_memo
import os

app = Flask(__name__)

@app.route('/record')
def record_page():
    """Simple recording page - no OAuth needed!"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Record Voice Memo</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .card {
            background: white;
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            max-width: 400px;
        }
        button {
            background: #e74c3c;
            color: white;
            border: none;
            padding: 1rem 2rem;
            font-size: 1.2rem;
            border-radius: 12px;
            cursor: pointer;
            width: 100%;
            margin: 0.5rem 0;
        }
        button:active {
            background: #c0392b;
        }
        #status {
            margin-top: 1rem;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎤 Voice Memo</h1>
        <p>Record directly to your GitHub profile</p>

        <button id="recordBtn" onclick="toggleRecording()">Start Recording</button>
        <button onclick="location.reload()">Cancel</button>

        <div id="status">Ready to record</div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        async function toggleRecording() {
            if (!isRecording) {
                // Start recording
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    await uploadAudio(audioBlob);
                    audioChunks = [];
                };

                mediaRecorder.start();
                isRecording = true;
                document.getElementById('recordBtn').textContent = 'Stop Recording';
                document.getElementById('recordBtn').style.background = '#2ecc71';
                document.getElementById('status').textContent = 'Recording...';
            } else {
                // Stop recording
                mediaRecorder.stop();
                isRecording = false;
                document.getElementById('recordBtn').textContent = 'Start Recording';
                document.getElementById('recordBtn').style.background = '#e74c3c';
                document.getElementById('status').textContent = 'Processing...';
            }
        }

        async function uploadAudio(audioBlob) {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice-memo.webm');
            formData.append('privacy', 'public'); // or 'private'

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.gist) {
                    document.getElementById('status').innerHTML =
                        `✅ Posted to <a href="${result.gist.html_url}">GitHub</a>!`;
                } else {
                    document.getElementById('status').textContent = '✗ Upload failed';
                }
            } catch (error) {
                document.getElementById('status').textContent = '✗ Error: ' + error.message;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/api/upload', methods=['POST'])
def upload():
    """Handle voice memo upload - creates gist & updates README"""
    audio_file = request.files['audio']
    privacy = request.form.get('privacy', 'public')

    # Save audio
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'voice-memo-{timestamp}.webm'
    filepath = f'/tmp/{filename}'
    audio_file.save(filepath)

    # Create voice memo metadata
    voice_memo_data = {
        'title': f'Voice Memo {timestamp}',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'audio_file': filepath,
        'duration': 'unknown' # Could use ffprobe to get duration
    }

    # Create gist and add to story wall
    result = create_story_from_voice_memo(voice_memo_data, privacy_level=privacy)

    # Commit README changes
    os.system('cd ~/Desktop/soulfra-profile && git add README.md && git commit -m "Add voice memo to story wall" && git push')

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
```

---

## Step 5: Test on Same WiFi

### 5.1 Make Sure You're on Same WiFi

**MacBook:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# Should show: inet 192.168.1.87
```

**iPhone:**
- Settings → WiFi → Check network name matches MacBook

### 5.2 Test Direct Access

On iPhone Safari, visit:
```
http://192.168.1.87:5001/record
```

Should see recording page.

### 5.3 Scan QR Code

Put QR code in README or just display `assets/qr-local.svg` on your screen:

```bash
open assets/qr-local.svg
```

Scan with iPhone camera → Should open recording page.

---

## Step 6: Record & Auto-Update

1. **Scan QR code** (or visit `http://192.168.1.87:5001/record`)
2. **Click "Start Recording"**
3. **Speak your memo**
4. **Click "Stop Recording"**
5. **Wait 2-3 seconds**
6. **Success!** → Gist created, README updated, auto-committed

Check your profile: https://github.com/Soulfra

Voice memo should be in the Story Wall section!

---

## Troubleshooting

### Issue: Can't reach 192.168.1.87 from iPhone

**Fix:**
```bash
# Check firewall
sudo pfctl -d  # Disable firewall temporarily

# Or allow Flask port
sudo pfctl -a com.apple.application-firewall -t add -p 5001 -s allow
```

### Issue: "Failed to create gist: 401"

**Fix:**
- Check `.env` has correct `GITHUB_TOKEN`
- Token must have `gist` and `repo` scopes
- Regenerate token if expired

### Issue: Recording works but doesn't update README

**Fix:**
```bash
# Check Flask logs
# Look for git commit output
# Make sure README.md has story wall section
```

### Issue: HTTPS required for microphone

**Solution:** iOS requires HTTPS for microphone access.

**Quick fix:**
```bash
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run Flask with HTTPS
python3 -c "
from flask import Flask
app = Flask(__name__)
# ... your routes ...
app.run(host='0.0.0.0', port=5001, ssl_context=('cert.pem', 'key.pem'))
"
```

Then visit: `https://192.168.1.87:5001/record`

iPhone will warn about self-signed cert → Tap "Continue Anyway"

---

## Comparison: OAuth vs Local WiFi

| Feature | OAuth Version | Local WiFi Version |
|---------|--------------|-------------------|
| Setup time | 30 minutes | 2 minutes |
| Requires internet | ✅ Yes | ❌ No (just WiFi) |
| GitHub OAuth app | ✅ Required | ❌ Not needed |
| Callback URLs | ✅ Required | ❌ Not needed |
| Session management | ✅ Complex | ❌ Simple |
| Works offline | ❌ No | ✅ Yes (with WiFi) |
| Token type | OAuth access token | Personal access token |
| Complexity | 🔥🔥🔥 High | ⚡ Simple |

---

## Which One to Use?

### Use Local WiFi (This Guide) If:
- MacBook + iPhone usually on same WiFi
- You want simple setup
- You're okay with manually starting Flask
- Privacy is important (no cloud)

### Use OAuth (Previous Guide) If:
- Recording from anywhere (not same WiFi)
- Multiple users will contribute
- Production deployment (cringeproof.com)
- Want persistent sessions

**For testing and personal use: Use Local WiFi (way simpler!)**

---

## Next Steps

1. Generate Personal Access Token (Step 1)
2. Add to `.env` file (Step 2)
3. Generate local QR code (Step 3)
4. Start Flask server (Step 4)
5. Test from iPhone (Step 5)
6. Record first voice memo! (Step 6)

No OAuth app, no callback URLs, no bullshit. Just works.
