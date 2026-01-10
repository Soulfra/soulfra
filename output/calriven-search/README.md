# CalRiven Search Page

**Purpose:** Standalone search page for CalRiven content

## What This Is

Static HTML page with:
- Client-side search (works without server)
- QR code linking to AI-powered search
- Links to published CalRiven posts
- Mobile-friendly design

## Local Testing

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/output/calriven-search
python3 -m http.server 8002
```

Visit: http://localhost:8002

## Deploying to GitHub Pages

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/output/calriven-search
git init
git add .
git commit -m "Deploy CalRiven search page"
gh repo create calriven-search --public --source=. --push

# Enable Pages in repo settings
gh browse
# Settings → Pages → Source: main branch
```

Live at: `https://<username>.github.io/calriven-search`

## Generating QR Code

Generate QR code pointing to AI search:

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 -c "
import qrcode
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data('http://192.168.1.87:5001/search?brand=calriven')
qr.make(fit=True)
img = qr.make_image(fill_color='black', back_color='white')
img.save('output/calriven-search/search-qr.png')
print('✅ QR code saved to output/calriven-search/search-qr.png')
"
```

## Features

### Client-Side Search
- Instant search as you type
- Works offline (no server needed)
- Filters CalRiven posts by title/excerpt

### AI Search Integration
- QR code links to full AI search
- Semantic search across all content
- Powered by Ollama

### Mobile-Friendly
- Responsive design
- Touch-friendly inputs
- Works great on iPhone

## Integration with Main System

**Links to:**
- CalRiven blog: https://soulfra.github.io/calriven/
- Unified dashboard: http://192.168.1.87:5001/dashboard
- AI search: http://192.168.1.87:5001/search?brand=calriven

## Cost

- **Hosting:** $0/month (GitHub Pages)
- **No server needed** for basic search
- AI search available via main system (port 5001)
