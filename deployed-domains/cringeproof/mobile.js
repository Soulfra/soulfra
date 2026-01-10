/**
 * CringeProof Mobile - Touch-Optimized Voice Recording
 *
 * Features:
 * - Tap-and-hold recording
 * - Haptic feedback
 * - Swipe navigation
 * - Offline queue integration
 * - Shadow account system
 *
 * Gameplay Loop:
 * 1. Tap record button
 * 2. Speak idea
 * 3. Auto-upload (or queue if offline)
 * 4. See in feed
 * 5. Swipe to browse
 */

class MobileRecorder {
  constructor() {
    this.isRecording = false;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.startTime = null;
    this.timerInterval = null;

    // API Base URL - auto-detects localhost vs tunnel
    this.API_BASE_URL = this.detectAPIBaseURL();

    this.btnRecord = document.getElementById('btnRecord');
    this.btnStop = document.getElementById('btnStop');
    this.recordingModal = document.getElementById('recordingModal');
    this.timer = document.getElementById('timer');
    this.feed = document.getElementById('feed');
    this.connectionBadge = document.getElementById('connectionBadge');

    this.init();
  }

  detectAPIBaseURL() {
    // Check if running on localhost
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:5001';
    }

    // Check if running on Tailscale funnel
    if (window.location.hostname.includes('tailscale-funnel.com')) {
      return window.location.origin;
    }

    // Check if running on Cloudflare tunnel
    if (window.location.hostname.includes('trycloudflare.com')) {
      return window.location.origin;
    }

    // Check if running on ngrok
    if (window.location.hostname.includes('ngrok')) {
      return window.location.origin;
    }

    // Default to current origin
    return window.location.origin;
  }

  init() {
    // Log API base URL for debugging
    console.log('[MobileRecorder] API Base URL:', this.API_BASE_URL);

    // Check for existing recordings
    this.loadFeed();

    // Record button
    this.btnRecord.addEventListener('click', () => {
      this.hapticFeedback('medium');
      this.startRecording();
    });

    // Stop button
    this.btnStop.addEventListener('click', () => {
      this.hapticFeedback('heavy');
      this.stopRecording();
    });

    // Connection monitor
    window.addEventListener('online', () => this.updateConnectionStatus(true));
    window.addEventListener('offline', () => this.updateConnectionStatus(false));

    // Swipe gestures for navigation
    this.initSwipeGestures();

    // Listen for shadow account ready
    window.addEventListener('shadowaccount', (e) => {
      if (e.detail.type === 'READY') {
        console.log('[MobileRecorder] Shadow account ready:', e.detail.account.shadowId);
      }
    });

    console.log('[MobileRecorder] Initialized');
  }

  async startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        this.handleRecordingComplete();
      };

      this.mediaRecorder.start();
      this.isRecording = true;
      this.startTime = Date.now();

      // Show recording modal
      this.recordingModal.classList.add('active');

      // Start timer
      this.startTimer();

      console.log('[MobileRecorder] Recording started');
    } catch (error) {
      console.error('[MobileRecorder] Failed to start recording:', error);
      alert('Microphone access denied. Please enable in settings.');
    }
  }

  stopRecording() {
    if (!this.isRecording || !this.mediaRecorder) return;

    this.mediaRecorder.stop();
    this.isRecording = false;

    // Stop all tracks
    this.mediaRecorder.stream.getTracks().forEach((track) => track.stop());

    // Stop timer
    this.stopTimer();

    // Hide modal
    setTimeout(() => {
      this.recordingModal.classList.remove('active');
    }, 300);

    console.log('[MobileRecorder] Recording stopped');
  }

  async handleRecordingComplete() {
    const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
    const duration = Math.floor((Date.now() - this.startTime) / 1000);

    console.log('[MobileRecorder] Recording complete:', {
      size: blob.size,
      duration: duration + 's'
    });

    // Get shadow account ID
    const shadowId = window.shadowAccount?.getShadowId() || 'anonymous';

    // Create form data
    const formData = new FormData();
    formData.append('audio', blob, `mobile-recording-${Date.now()}.webm`);
    formData.append('duration', duration);
    formData.append('shadow_id', shadowId);

    // Upload or queue
    await this.uploadRecording(formData);

    // Add to feed immediately (optimistic UI)
    this.addToFeed({
      id: Date.now(),
      text: 'Processing...',
      tier: 'pending',
      score: 0,
      created_at: new Date().toISOString(),
      status: 'uploading'
    });
  }

  async uploadRecording(formData) {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[MobileRecorder] Upload successful:', data);

        // Update feed with real data
        this.updateFeedItem(data);

        this.hapticFeedback('light');
      } else {
        throw new Error(`Upload failed: ${response.status}`);
      }
    } catch (error) {
      console.error('[MobileRecorder] Upload failed:', error);

      // Queue for later
      if (window.queueManager) {
        await window.queueManager.enqueue({
          url: '/api/upload',
          method: 'POST',
          body: formData
        });
        console.log('[MobileRecorder] Queued for retry');
      }

      this.showToast('Offline - queued for upload');
    }
  }

  startTimer() {
    this.timer.textContent = '0:00';

    this.timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      const minutes = Math.floor(elapsed / 60);
      const seconds = elapsed % 60;
      this.timer.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
  }

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  loadFeed() {
    // Load from localStorage or IndexedDB
    const ideas = JSON.parse(localStorage.getItem('mobile_feed') || '[]');

    if (ideas.length === 0) {
      // Show empty state
      return;
    }

    // Clear empty state
    this.feed.innerHTML = '';

    // Render ideas
    ideas.forEach((idea) => this.addToFeed(idea, false));
  }

  addToFeed(idea, prepend = true) {
    const card = document.createElement('div');
    card.className = 'idea-card';
    card.dataset.id = idea.id;

    const tierEmoji = this.getTierEmoji(idea.tier);

    card.innerHTML = `
      <div class="idea-header">
        <div class="idea-tier">${tierEmoji}</div>
        <div class="idea-score">${idea.score}/100</div>
      </div>
      <div class="idea-title">${this.escapeHtml(idea.title || idea.text.substring(0, 50))}</div>
      <div class="idea-text">${this.escapeHtml(idea.text)}</div>
      <div class="idea-meta">
        <span>${new Date(idea.created_at).toLocaleDateString()}</span>
        <span>${idea.status || 'completed'}</span>
      </div>
    `;

    if (prepend) {
      this.feed.insertBefore(card, this.feed.firstChild);
    } else {
      this.feed.appendChild(card);
    }

    // Save to localStorage
    this.saveFeed();
  }

  updateFeedItem(data) {
    const card = this.feed.querySelector(`[data-id="${data.id}"]`);
    if (card) {
      card.outerHTML = '';
      this.addToFeed(data, true);
    }
  }

  saveFeed() {
    const ideas = Array.from(this.feed.querySelectorAll('.idea-card')).map((card) => ({
      id: card.dataset.id,
      // Extract data from card (simplified)
    }));

    localStorage.setItem('mobile_feed', JSON.stringify(ideas));
  }

  updateConnectionStatus(online) {
    this.connectionBadge.textContent = online ? '● Online' : '● Offline';
    this.connectionBadge.className = `connection-badge ${online ? 'online' : 'offline'}`;

    if (online && window.queueManager) {
      // Process queued uploads
      window.queueManager.processQueue();
    }
  }

  initSwipeGestures() {
    let startX = 0;
    let startY = 0;

    this.feed.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    });

    this.feed.addEventListener('touchend', (e) => {
      const endX = e.changedTouches[0].clientX;
      const endY = e.changedTouches[0].clientY;

      const diffX = endX - startX;
      const diffY = endY - startY;

      // Horizontal swipe (left/right)
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
        if (diffX > 0) {
          console.log('[MobileRecorder] Swipe right');
          this.hapticFeedback('light');
          // Navigate to previous
        } else {
          console.log('[MobileRecorder] Swipe left');
          this.hapticFeedback('light');
          // Navigate to next
        }
      }
    });
  }

  hapticFeedback(intensity = 'medium') {
    // Visual haptic feedback
    this.btnRecord.classList.add(`haptic-${intensity}`);
    setTimeout(() => {
      this.btnRecord.classList.remove(`haptic-${intensity}`);
    }, 200);

    // Native haptic (if available)
    if (navigator.vibrate) {
      const patterns = {
        light: 10,
        medium: 20,
        heavy: 30
      };
      navigator.vibrate(patterns[intensity] || 20);
    }
  }

  showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      top: 60px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(255,255,255,0.9);
      color: #000;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      z-index: 9999;
      animation: slideDown 0.3s ease-out;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 3000);
  }

  getTierEmoji(tier) {
    const emojis = {
      trash: '🗑️',
      bronze: '🥉',
      silver: '🥈',
      gold: '🥇',
      platinum: '💎',
      pending: '⏳'
    };
    return emojis[tier] || '📝';
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Auto-initialize
let mobileRecorder;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    mobileRecorder = new MobileRecorder();
  });
} else {
  mobileRecorder = new MobileRecorder();
}

// Export
window.MobileRecorder = MobileRecorder;
window.mobileRecorder = mobileRecorder;

console.log('[Mobile] Loaded');
