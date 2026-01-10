#!/usr/bin/env python3
"""
Export CringeProof Carousel Homepage to Static HTML

Generates voice-archive/index.html with:
- Embedded carousel widget (can run from static hosting)
- Placeholder stats (will update via API when backend is available)
- QR code for mobile
- Links to all game modes
"""

import os
import shutil

def export_carousel_homepage(output_dir='voice-archive'):
    """Export carousel homepage to static HTML"""

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Static HTML with embedded carousel
    # Note: iframe src points to localhost for now - update with ngrok URL when available
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CringeProof - Live Questions & Top Plays</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #FF1B6B 0%, #45CAFF 100%);
            min-height: 100vh;
        }

        /* Hero Section with Carousel */
        .hero {
            height: 80vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            padding: 20px;
        }

        .hero-title {
            font-size: 48px;
            font-weight: 900;
            color: white;
            text-align: center;
            margin-bottom: 10px;
            text-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .hero-subtitle {
            font-size: 20px;
            color: rgba(255, 255, 255, 0.9);
            text-align: center;
            margin-bottom: 40px;
        }

        .carousel-container {
            width: 100%;
            max-width: 800px;
            height: 500px;
            border-radius: 30px;
            overflow: hidden;
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
            background: rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .carousel-container iframe {
            width: 100%;
            height: 100%;
            border: none;
        }

        .offline-message {
            color: white;
            text-align: center;
            padding: 40px;
        }

        .offline-message h3 {
            font-size: 24px;
            margin-bottom: 15px;
        }

        .offline-message p {
            font-size: 16px;
            opacity: 0.9;
        }

        /* QR Code Quickstart */
        .qr-quickstart {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: white;
            padding: 20px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            text-align: center;
            max-width: 200px;
        }

        .qr-quickstart h3 {
            font-size: 14px;
            margin-bottom: 10px;
            color: #2d3748;
        }

        .qr-quickstart img {
            width: 150px;
            height: 150px;
            border-radius: 10px;
        }

        .qr-quickstart p {
            font-size: 12px;
            color: #718096;
            margin-top: 10px;
        }

        /* Stats Bar */
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 40px 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }

        .stat {
            text-align: center;
            color: white;
        }

        .stat-value {
            font-size: 36px;
            font-weight: 900;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 14px;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* CTA Section */
        .cta-section {
            padding: 60px 20px;
            text-align: center;
            background: white;
        }

        .cta-section h2 {
            font-size: 36px;
            color: #2d3748;
            margin-bottom: 20px;
        }

        .cta-section p {
            font-size: 18px;
            color: #4a5568;
            margin-bottom: 30px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }

        .cta-buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .cta-button {
            padding: 15px 40px;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            transition: transform 0.2s, box-shadow 0.2s;
            display: inline-block;
        }

        .cta-button.primary {
            background: linear-gradient(135deg, #FF1B6B 0%, #45CAFF 100%);
            color: white;
        }

        .cta-button.secondary {
            background: white;
            color: #2d3748;
            border: 2px solid #e2e8f0;
        }

        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        /* Mobile Responsive */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 32px;
            }

            .hero-subtitle {
                font-size: 16px;
            }

            .carousel-container {
                height: 400px;
            }

            .qr-quickstart {
                display: none;
            }

            .stats-bar {
                flex-direction: column;
                gap: 20px;
            }

            .stat-value {
                font-size: 28px;
            }
        }
    </style>
</head>
<body>
    <!-- Hero Section with Widget Carousel -->
    <div class="hero">
        <h1 class="hero-title">🎮 CringeProof Live</h1>
        <p class="hero-subtitle">Top plays, questions, and ideas updating in real-time</p>

        <div class="carousel-container" id="carouselContainer">
            <!-- Will be populated by JavaScript -->
            <div class="offline-message">
                <h3>🌐 Loading Experience...</h3>
                <p>Connecting to interactive widgets</p>
            </div>
        </div>
    </div>

    <!-- Live Stats -->
    <div class="stats-bar">
        <div class="stat">
            <div class="stat-value" id="questionsToday">0</div>
            <div class="stat-label">Questions Today</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="playersOnline">0</div>
            <div class="stat-label">Players Online</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="ideasShared">0</div>
            <div class="stat-label">Ideas Shared</div>
        </div>
    </div>

    <!-- CTA Section -->
    <div class="cta-section">
        <h2>Jump Into the Action</h2>
        <p>
            Choose your district and start playing. No downloads, no apps, just pure interaction.
            Every choice you make trains the AI and earns you rewards.
        </p>

        <div class="cta-buttons">
            <a href="record-simple.html" class="cta-button primary">
                🎤 Record Voice
            </a>
            <a href="#" class="cta-button secondary" onclick="alert('Backend server needed for full experience'); return false;">
                🌌 Start Quiz
            </a>
            <a href="#" class="cta-button secondary" onclick="alert('Backend server needed for full experience'); return false;">
                🏪 Browse Feed
            </a>
        </div>
    </div>

    <!-- QR Code Quickstart (Desktop Only) -->
    <div class="qr-quickstart">
        <h3>📱 Mobile Quickstart</h3>
        <img id="qrCode" src="" alt="QR Code">
        <p>Scan to jump in from your phone</p>
    </div>

    <script>
        // Configuration - UPDATE THIS when you have ngrok or production URL
        const BACKEND_URL = 'http://localhost:5001';  // Change to https://YOUR-NGROK-URL.ngrok.io

        // Generate QR code for current page
        const currentUrl = window.location.href;
        const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(currentUrl)}`;
        document.getElementById('qrCode').src = qrApiUrl;

        // Try to load carousel widget
        function loadCarousel() {
            const container = document.getElementById('carouselContainer');

            // Check if backend is available
            fetch(`${BACKEND_URL}/widget/carousel?auto_rotate=true&rotation_interval=30000&live=true`, {
                method: 'GET',
                mode: 'cors'
            })
            .then(response => {
                if (response.ok) {
                    // Backend is available, load iframe
                    container.innerHTML = `<iframe src="${BACKEND_URL}/widget/carousel?auto_rotate=true&rotation_interval=30000&live=true"></iframe>`;
                    loadStats();
                } else {
                    showOfflineMode();
                }
            })
            .catch(err => {
                console.log('Backend not available, showing offline mode');
                showOfflineMode();
            });
        }

        function showOfflineMode() {
            const container = document.getElementById('carouselContainer');
            container.innerHTML = `
                <div class="offline-message">
                    <h3>🎮 CringeProof Universe</h3>
                    <p>Interactive widgets load when backend is available</p>
                    <p style="margin-top: 20px; font-size: 14px;">
                        Districts: Exploration 🌌 | Combat ⚔️ | Commerce 🏪 | Creativity 🎨
                    </p>
                </div>
            `;
        }

        // Load live stats if backend is available
        function loadStats() {
            fetch(`${BACKEND_URL}/api/cringeproof/live-stats`)
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('questionsToday').textContent = data.questions_today;
                        document.getElementById('playersOnline').textContent = data.players_online;
                        document.getElementById('ideasShared').textContent = data.ideas_shared;
                    }
                })
                .catch(err => {
                    console.log('Stats not available:', err);
                });
        }

        // Listen for widget launch messages from carousel
        window.addEventListener('message', function(event) {
            if (event.data.type === 'widget_launch') {
                const widget = event.data.widget_id;
                const actionUrls = {
                    'universe': '#quiz',
                    'arena': '#multiplayer',
                    'marketplace': '#feed',
                    'immersion': 'record-simple.html'
                };

                if (actionUrls[widget]) {
                    if (actionUrls[widget].startsWith('#')) {
                        alert('Backend server needed for ' + widget + ' experience');
                    } else {
                        window.location.href = actionUrls[widget];
                    }
                }
            }
        });

        // Update stats every 30 seconds if backend is available
        setInterval(() => {
            loadStats();
        }, 30000);

        // Initial load
        loadCarousel();
    </script>
</body>
</html>
'''

    # Write to output file
    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✅ Exported carousel homepage to {output_path}")
    print(f"")
    print(f"📝 Next steps:")
    print(f"   1. Set up ngrok authtoken: ngrok config add-authtoken YOUR_TOKEN")
    print(f"   2. Start ngrok: ngrok http 5001")
    print(f"   3. Update BACKEND_URL in {output_path} to your ngrok URL")
    print(f"   4. Commit and push to voice-archive repo")
    print(f"")
    print(f"💡 Or use without backend - voice recorder will still work!")

    return output_path


if __name__ == '__main__':
    export_carousel_homepage()
