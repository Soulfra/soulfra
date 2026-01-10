/**
 * Connection Monitor - Detects Flask backend availability
 *
 * Features:
 * - Real-time connection status (online/offline)
 * - Periodic health checks
 * - Visual status indicator
 * - Auto-retry queue when connection restored
 */

class ConnectionMonitor {
  constructor(apiUrl, checkInterval = 10000) {
    this.apiUrl = apiUrl;
    this.checkInterval = checkInterval;
    this.isOnline = false;
    this.checkTimer = null;
    this.listeners = [];

    this.init();
  }

  init() {
    // Initial check
    this.checkConnection();

    // Start periodic checks
    this.startChecking();

    // Listen for browser online/offline events
    window.addEventListener('online', () => {
      console.log('[ConnectionMonitor] Browser online event');
      this.checkConnection();
    });

    window.addEventListener('offline', () => {
      console.log('[ConnectionMonitor] Browser offline event');
      this.setStatus(false);
    });

    // Listen for visibility changes (resume checking when tab becomes visible)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.checkConnection();
      }
    });
  }

  /**
   * Check if Flask backend is reachable
   */
  async checkConnection() {
    try {
      // Ping health endpoint with short timeout
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000); // 3 second timeout

      const response = await fetch(`${this.apiUrl}/api/health`, {
        method: 'GET',
        signal: controller.signal,
        cache: 'no-cache'
      });

      clearTimeout(timeout);

      if (response.ok) {
        const wasOffline = !this.isOnline;
        this.setStatus(true);

        // If we just came back online, process queue
        if (wasOffline && window.queueManager) {
          console.log('[ConnectionMonitor] Connection restored - processing queue');
          window.queueManager.processQueue();
        }
      } else {
        this.setStatus(false);
      }
    } catch (error) {
      // Network error or timeout
      console.log('[ConnectionMonitor] Connection check failed:', error.message);
      this.setStatus(false);
    }
  }

  /**
   * Update connection status
   */
  setStatus(isOnline) {
    const previousStatus = this.isOnline;
    this.isOnline = isOnline;

    if (previousStatus !== isOnline) {
      console.log(`[ConnectionMonitor] Status changed: ${isOnline ? 'ONLINE' : 'OFFLINE'}`);

      // Notify listeners
      this.notifyListeners(isOnline);

      // Update UI
      this.updateUI(isOnline);

      // Dispatch custom event
      window.dispatchEvent(
        new CustomEvent('connectionstatus', {
          detail: { isOnline }
        })
      );
    }
  }

  /**
   * Update UI status indicator
   */
  updateUI(isOnline) {
    // Update status badge if it exists
    const badge = document.getElementById('connection-status');
    if (badge) {
      badge.textContent = isOnline ? 'Backend Online' : 'Backend Offline';
      badge.className = `connection-badge ${isOnline ? 'online' : 'offline'}`;
    }

    // Update any status text elements
    const statusTexts = document.querySelectorAll('[data-connection-status]');
    statusTexts.forEach((el) => {
      el.textContent = isOnline ? 'Connected to Flask backend' : 'Offline - will sync when reconnected';
    });

    // Show/hide queue stats if offline
    if (!isOnline && window.queueManager) {
      this.showQueueStats();
    }
  }

  /**
   * Show queue stats in UI
   */
  async showQueueStats() {
    if (!window.queueManager) return;

    try {
      const stats = await window.queueManager.getStats();

      if (stats.pending > 0) {
        const statusEl = document.getElementById('status');
        if (statusEl && !statusEl.textContent.includes('queued')) {
          statusEl.textContent += ` (${stats.pending} queued)`;
        }
      }
    } catch (error) {
      console.error('[ConnectionMonitor] Failed to get queue stats:', error);
    }
  }

  /**
   * Start periodic connection checks
   */
  startChecking() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
    }

    this.checkTimer = setInterval(() => {
      this.checkConnection();
    }, this.checkInterval);

    console.log(`[ConnectionMonitor] Started checking every ${this.checkInterval}ms`);
  }

  /**
   * Stop periodic checks
   */
  stopChecking() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
      console.log('[ConnectionMonitor] Stopped checking');
    }
  }

  /**
   * Register listener for status changes
   */
  onStatusChange(callback) {
    this.listeners.push(callback);
  }

  /**
   * Notify all listeners
   */
  notifyListeners(isOnline) {
    this.listeners.forEach((callback) => {
      try {
        callback(isOnline);
      } catch (error) {
        console.error('[ConnectionMonitor] Listener error:', error);
      }
    });
  }

  /**
   * Get current status
   */
  getStatus() {
    return this.isOnline;
  }

  /**
   * Manual trigger for connection check
   */
  refresh() {
    this.checkConnection();
  }
}

// Initialize connection monitor when config is loaded
let connectionMonitor = null;

function initConnectionMonitor() {
  if (window.CRINGEPROOF_CONFIG?.API_BACKEND_URL) {
    const apiUrl = window.CRINGEPROOF_CONFIG.API_BACKEND_URL;
    connectionMonitor = new ConnectionMonitor(apiUrl);
    window.connectionMonitor = connectionMonitor;

    console.log('[ConnectionMonitor] Initialized for:', apiUrl);

    // Add status badge to page if it doesn't exist
    addStatusBadge();
  } else {
    console.warn('[ConnectionMonitor] No API URL configured');
  }
}

/**
 * Add connection status badge to page
 */
function addStatusBadge() {
  // Check if badge already exists
  if (document.getElementById('connection-status')) {
    return;
  }

  // Create status badge
  const badge = document.createElement('div');
  badge.id = 'connection-status';
  badge.className = 'connection-badge checking';
  badge.textContent = 'Checking connection...';
  badge.style.cssText = `
    position: fixed;
    top: 1rem;
    right: 1rem;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    font-weight: 700;
    border: 3px solid #000;
    border-radius: 4px;
    z-index: 9999;
    transition: all 0.3s ease;
    cursor: pointer;
  `;

  // Click to manually refresh
  badge.addEventListener('click', () => {
    if (connectionMonitor) {
      badge.textContent = 'Checking...';
      connectionMonitor.refresh();
    }
  });

  document.body.appendChild(badge);

  // Style badge based on status
  window.addEventListener('connectionstatus', (event) => {
    const { isOnline } = event.detail;

    if (isOnline) {
      badge.style.background = '#00C49A';
      badge.style.color = '#000';
    } else {
      badge.style.background = '#ff006e';
      badge.style.color = '#fff';
    }
  });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initConnectionMonitor);
} else {
  // DOM already loaded
  setTimeout(initConnectionMonitor, 100); // Small delay to ensure config.js loads first
}

// Export for manual initialization
window.initConnectionMonitor = initConnectionMonitor;

console.log('[ConnectionMonitor] Script loaded');
