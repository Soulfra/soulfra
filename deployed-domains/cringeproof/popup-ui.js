/**
 * Popup UI System - "Clippy Mode"
 *
 * Single-page popup system to replace multiple HTML pages
 * Desktop: Draggable popup (like Clippy)
 * Mobile: Full-screen takeover (like ChatGPT/Siri)
 */

class PopupUI {
    constructor() {
        this.currentState = null;
        this.isOpen = false;
        this.isMobile = this.detectMobile();
        this.voiceFeedback = null;
        this.userId = localStorage.getItem('user_id');
        this.authToken = localStorage.getItem('auth_token');

        this.init();
    }

    detectMobile() {
        return window.innerWidth <= 768 ||
               /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    init() {
        // Create popup container
        this.createPopupElements();

        // Bind events
        this.bindEvents();

        // Check auth state
        if (!this.authToken) {
            this.openPopup('login');
        }
    }

    createPopupElements() {
        // Floating assistant icon (Clippy-style)
        const floatingIcon = document.createElement('div');
        floatingIcon.id = 'clippy-icon';
        floatingIcon.className = 'clippy-icon';
        floatingIcon.innerHTML = '🎤';
        floatingIcon.title = 'Open CringeProof Assistant';
        document.body.appendChild(floatingIcon);

        // Popup overlay
        const overlay = document.createElement('div');
        overlay.id = 'popup-overlay';
        overlay.className = 'popup-overlay';
        document.body.appendChild(overlay);

        // Popup container
        const popup = document.createElement('div');
        popup.id = 'popup-container';
        popup.className = this.isMobile ? 'popup-container mobile' : 'popup-container desktop';

        popup.innerHTML = `
            <div class="popup-header">
                <div class="popup-title">CringeProof Assistant</div>
                <button class="popup-close" id="popup-close-btn">✕</button>
            </div>
            <div class="popup-content" id="popup-content">
                <!-- Dynamic content loaded here -->
            </div>
        `;

        document.body.appendChild(popup);

        // Store references
        this.floatingIcon = floatingIcon;
        this.overlay = overlay;
        this.popup = popup;
        this.content = document.getElementById('popup-content');
    }

    bindEvents() {
        // Open popup on icon click
        this.floatingIcon.addEventListener('click', () => {
            if (this.authToken) {
                this.openPopup('menu');
            } else {
                this.openPopup('login');
            }
        });

        // Close popup
        document.getElementById('popup-close-btn').addEventListener('click', () => {
            this.closePopup();
        });

        // Close on overlay click (desktop only)
        if (!this.isMobile) {
            this.overlay.addEventListener('click', () => {
                this.closePopup();
            });
        }

        // Make draggable on desktop
        if (!this.isMobile) {
            this.makeDraggable();
        }

        // Handle window resize
        window.addEventListener('resize', () => {
            const wasMobile = this.isMobile;
            this.isMobile = this.detectMobile();

            if (wasMobile !== this.isMobile) {
                this.popup.className = this.isMobile ? 'popup-container mobile' : 'popup-container desktop';
            }
        });
    }

    makeDraggable() {
        const header = this.popup.querySelector('.popup-header');
        let isDragging = false;
        let currentX, currentY, initialX, initialY;

        header.style.cursor = 'move';

        header.addEventListener('mousedown', (e) => {
            isDragging = true;
            initialX = e.clientX - this.popup.offsetLeft;
            initialY = e.clientY - this.popup.offsetTop;
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;

            this.popup.style.left = currentX + 'px';
            this.popup.style.top = currentY + 'px';
            this.popup.style.transform = 'none';
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
        });
    }

    openPopup(state) {
        this.currentState = state;
        this.isOpen = true;

        this.overlay.classList.add('active');
        this.popup.classList.add('active');

        // Load content for state
        this.loadState(state);
    }

    closePopup() {
        this.isOpen = false;
        this.overlay.classList.remove('active');
        this.popup.classList.remove('active');
    }

    loadState(state) {
        switch(state) {
            case 'login':
                this.renderLogin();
                break;
            case 'menu':
                this.renderMenu();
                break;
            case 'record':
                this.renderRecord();
                break;
            case 'onboarding':
                this.renderOnboarding();
                break;
            case 'stats':
                this.renderStats();
                break;
            case 'shipping':
                this.renderShipping();
                break;
            default:
                this.renderMenu();
        }
    }

    renderLogin() {
        this.content.innerHTML = `
            <div class="login-container">
                <h2>🚫 Welcome to CringeProof</h2>
                <p>Login to access your encyclopedia</p>

                <form id="login-form">
                    <input type="email" id="login-email" placeholder="Email" required>
                    <input type="password" id="login-password" placeholder="Password" required>
                    <button type="submit" class="btn-primary">Login</button>
                </form>

                <p style="margin-top: 1rem; font-size: 0.9rem;">
                    Don't have an account?
                    <a href="https://soulfra.com" style="color: #ff006e;">Sign up</a>
                </p>

                <div id="login-status"></div>
            </div>
        `;

        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleLogin();
        });
    }

    async handleLogin() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const statusDiv = document.getElementById('login-status');
        const API_URL = window.CRINGEPROOF_CONFIG?.API_BACKEND_URL || 'https://sega-affordable-soviet-weed.trycloudflare.com';

        try {
            const response = await fetch(`${API_URL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('auth_token', data.token);
                localStorage.setItem('user_id', data.user_id);
                localStorage.setItem('email', email);

                this.authToken = data.token;
                this.userId = data.user_id;

                statusDiv.innerHTML = '<div class="status success">✅ Login successful!</div>';

                setTimeout(() => {
                    this.loadState('onboarding');
                }, 1000);
            } else {
                statusDiv.innerHTML = '<div class="status error">❌ ' + data.error + '</div>';
            }
        } catch (error) {
            statusDiv.innerHTML = '<div class="status error">❌ Network error</div>';
        }
    }

    renderMenu() {
        this.content.innerHTML = `
            <div class="menu-container">
                <h2>🎯 Quick Actions</h2>
                <div class="menu-grid">
                    <button class="menu-item" onclick="popupUI.loadState('record')">
                        <div class="menu-icon">🎤</div>
                        <div class="menu-label">Record Voice Memo</div>
                    </button>

                    <button class="menu-item" onclick="popupUI.loadState('stats')">
                        <div class="menu-icon">📊</div>
                        <div class="menu-label">View Stats</div>
                    </button>

                    <button class="menu-item" onclick="popupUI.loadState('shipping')">
                        <div class="menu-icon">📬</div>
                        <div class="menu-label">Shipping Address</div>
                    </button>

                    <button class="menu-item" onclick="window.location.href='/wordmap.html'">
                        <div class="menu-icon">🗺️</div>
                        <div class="menu-label">Wordmap</div>
                    </button>
                </div>
            </div>
        `;
    }

    renderRecord() {
        this.content.innerHTML = `
            <div class="record-container">
                <h2>🎙️ Record Voice Memo</h2>
                <p>Tap the microphone to start recording</p>

                <div class="recording-box">
                    <button class="record-btn" id="record-btn">🎤</button>
                    <p id="record-status">Tap to start recording</p>
                </div>

                <div id="upload-status"></div>
            </div>
        `;

        this.initRecording();
    }

    initRecording() {
        const recordBtn = document.getElementById('record-btn');
        const recordStatus = document.getElementById('record-status');
        let mediaRecorder = null;
        let audioChunks = [];

        recordBtn.addEventListener('click', async () => {
            if (!mediaRecorder || mediaRecorder.state === 'inactive') {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        await this.uploadRecording(audioBlob);
                        stream.getTracks().forEach(track => track.stop());
                    };

                    mediaRecorder.start();
                    recordBtn.classList.add('recording');
                    recordBtn.textContent = '⏹️';
                    recordStatus.textContent = 'Recording... Tap to stop';
                } catch (error) {
                    recordStatus.textContent = 'Microphone access denied';
                }
            } else {
                mediaRecorder.stop();
                recordBtn.classList.remove('recording');
                recordBtn.textContent = '🎤';
                recordStatus.textContent = 'Processing...';
            }
        });
    }

    async uploadRecording(audioBlob) {
        const API_URL = window.CRINGEPROOF_CONFIG?.API_BACKEND_URL || 'https://sega-affordable-soviet-weed.trycloudflare.com';
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('user_id', this.userId);

        try {
            const response = await fetch(`${API_URL}/api/simple-voice/save`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                document.getElementById('upload-status').innerHTML =
                    '<div class="status success">✅ Recording saved! Transcription: "' +
                    (data.transcription || 'Processing...') + '"</div>';

                if (this.voiceFeedback) {
                    this.voiceFeedback.announceRecordingSaved();
                }
            } else {
                document.getElementById('upload-status').innerHTML =
                    '<div class="status error">❌ Upload failed: ' + data.error + '</div>';
            }
        } catch (error) {
            document.getElementById('upload-status').innerHTML =
                '<div class="status error">❌ Network error</div>';
        }
    }

    renderOnboarding() {
        this.content.innerHTML = `
            <div class="onboarding-container">
                <h2>🔍 Finding Your Squad</h2>
                <p>Matching you with similar users...</p>
                <div class="loading">
                    <div class="spinner"></div>
                </div>
                <div id="squad-results"></div>
            </div>
        `;

        this.findSquad();
    }

    async findSquad() {
        const API_URL = window.CRINGEPROOF_CONFIG?.API_BACKEND_URL || 'https://sega-affordable-soviet-weed.trycloudflare.com';

        try {
            const response = await fetch(`${API_URL}/api/squad/match?user_id=${this.userId}`);
            const data = await response.json();

            if (response.ok && data.squad && data.squad.length > 0) {
                const squadHTML = data.squad.map(member => `
                    <div class="squad-card">
                        <div class="similarity-score">${Math.round(member.similarity * 100)}% Match</div>
                        <h3>${member.email || 'Anonymous'}</h3>
                        <div class="shared-words">
                            ${(member.shared_words || []).slice(0, 5).map(word =>
                                `<span class="word-tag">${word}</span>`
                            ).join('')}
                        </div>
                    </div>
                `).join('');

                document.getElementById('squad-results').innerHTML = `
                    <h3 style="margin-top: 2rem; margin-bottom: 1rem;">🏆 Your Squad</h3>
                    <div class="squad-grid">${squadHTML}</div>
                `;

                if (this.voiceFeedback) {
                    const topMatch = data.squad[0];
                    this.voiceFeedback.announceSquadMatch(topMatch.similarity, data.squad.length);
                }
            } else {
                document.getElementById('squad-results').innerHTML = `
                    <div style="text-align: center; padding: 2rem;">
                        <h3>🌟 You're the First!</h3>
                        <p>More squad members will appear as people join</p>
                    </div>
                `;
            }
        } catch (error) {
            document.getElementById('squad-results').innerHTML = `
                <div class="status error">❌ Failed to load squad</div>
            `;
        }
    }

    renderStats() {
        this.content.innerHTML = `
            <div class="stats-container">
                <h2>📊 Your Stats</h2>
                <div class="stats-grid-popup">
                    <div class="stat-card-popup">
                        <div class="stat-value" id="stat-recordings">0</div>
                        <div class="stat-label">Voice Memos</div>
                    </div>
                    <div class="stat-card-popup">
                        <div class="stat-value" id="stat-words">0</div>
                        <div class="stat-label">Unique Words</div>
                    </div>
                    <div class="stat-card-popup">
                        <div class="stat-value" id="stat-level">0</div>
                        <div class="stat-label">Level</div>
                    </div>
                </div>
            </div>
        `;

        this.loadStats();
    }

    async loadStats() {
        const API_URL = window.CRINGEPROOF_CONFIG?.API_BACKEND_URL || 'https://sega-affordable-soviet-weed.trycloudflare.com';

        try {
            const response = await fetch(`${API_URL}/api/encyclopedia/progression?user_id=${this.userId}`);
            const data = await response.json();

            if (response.ok) {
                document.getElementById('stat-recordings').textContent = data.stats.recordings;
                document.getElementById('stat-words').textContent = data.stats.unique_words;
                document.getElementById('stat-level').textContent = data.level;
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    renderShipping() {
        this.content.innerHTML = `
            <div class="shipping-container">
                <h2>📬 Shipping Address</h2>
                <p>Enter your address to receive physical postcards and prizes</p>

                <form id="shipping-form">
                    <input type="text" id="full-name" placeholder="Full Name" required>
                    <input type="text" id="address-line1" placeholder="Address Line 1" required>
                    <input type="text" id="address-line2" placeholder="Address Line 2 (optional)">
                    <input type="text" id="city" placeholder="City" required>
                    <input type="text" id="state" placeholder="State/Province" required>
                    <input type="text" id="postal-code" placeholder="Postal Code" required>
                    <select id="country" required>
                        <option value="US">United States</option>
                        <option value="CA">Canada</option>
                        <option value="GB">United Kingdom</option>
                        <option value="AU">Australia</option>
                    </select>

                    <button type="submit" class="btn-primary">Save Address ($1 verification)</button>
                </form>

                <div id="shipping-status"></div>
            </div>
        `;

        document.getElementById('shipping-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleShipping();
        });
    }

    async handleShipping() {
        const statusDiv = document.getElementById('shipping-status');
        statusDiv.innerHTML = '<div class="status">🚧 Postcard verification coming soon!</div>';

        // TODO: Integrate with postcard_verification.py API endpoints
    }

    // Initialize voice feedback
    async initVoiceFeedback() {
        const API_URL = window.CRINGEPROOF_CONFIG?.API_BACKEND_URL || 'https://sega-affordable-soviet-weed.trycloudflare.com';

        try {
            const response = await fetch(`${API_URL}/api/encyclopedia/progression?user_id=${this.userId}`);
            const data = await response.json();

            if (window.VoiceFeedback) {
                this.voiceFeedback = new VoiceFeedback(data.level || 0);
            }
        } catch (error) {
            // Fallback to level 0
            if (window.VoiceFeedback) {
                this.voiceFeedback = new VoiceFeedback(0);
            }
        }
    }
}

// Initialize popup UI when DOM is ready
let popupUI = null;
document.addEventListener('DOMContentLoaded', () => {
    popupUI = new PopupUI();

    // Initialize voice feedback if available
    if (popupUI.userId) {
        popupUI.initVoiceFeedback();
    }
});

// Export for use in other scripts
window.PopupUI = PopupUI;
window.popupUI = popupUI;
