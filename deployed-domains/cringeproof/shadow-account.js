/**
 * Shadow Account System - Browser Fingerprinting
 *
 * Creates persistent anonymous accounts without traditional OAuth.
 * Uses browser fingerprinting + IndexedDB for cross-session identity.
 *
 * Features:
 * - Canvas fingerprinting
 * - WebGL fingerprinting
 * - Audio context fingerprinting
 * - Screen/timezone/platform detection
 * - Persistent storage with IndexedDB
 * - Automatic shadow account creation
 */

const SHADOW_DB_NAME = 'CringeProofShadow';
const SHADOW_STORE_NAME = 'shadow_account';

class ShadowAccount {
  constructor() {
    this.db = null;
    this.fingerprint = null;
    this.shadowId = null;
    this.initDB();
  }

  async initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(SHADOW_DB_NAME, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        console.log('[ShadowAccount] Database initialized');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        if (!db.objectStoreNames.contains(SHADOW_STORE_NAME)) {
          const objectStore = db.createObjectStore(SHADOW_STORE_NAME, {
            keyPath: 'fingerprint'
          });

          objectStore.createIndex('shadowId', 'shadowId', { unique: true });
          objectStore.createIndex('createdAt', 'createdAt', { unique: false });
          objectStore.createIndex('lastSeen', 'lastSeen', { unique: false });

          console.log('[ShadowAccount] Object store created');
        }
      };
    });
  }

  /**
   * Generate browser fingerprint using multiple techniques
   */
  async generateFingerprint() {
    const components = [];

    // Canvas fingerprinting
    components.push(await this.getCanvasFingerprint());

    // WebGL fingerprinting
    components.push(await this.getWebGLFingerprint());

    // Audio context fingerprinting
    components.push(await this.getAudioFingerprint());

    // Screen & hardware
    components.push(screen.width + 'x' + screen.height);
    components.push(screen.colorDepth);
    components.push(navigator.hardwareConcurrency || 'unknown');
    components.push(navigator.deviceMemory || 'unknown');

    // Timezone & language
    components.push(Intl.DateTimeFormat().resolvedOptions().timeZone);
    components.push(navigator.language);
    components.push(navigator.languages.join(','));

    // Platform & user agent
    components.push(navigator.platform);
    components.push(navigator.userAgent);

    // Plugins (deprecated but still useful)
    if (navigator.plugins) {
      const pluginNames = Array.from(navigator.plugins).map((p) => p.name);
      components.push(pluginNames.join(','));
    }

    // Combine all components and hash
    const combined = components.join('|');
    const fingerprint = await this.hashString(combined);

    console.log('[ShadowAccount] Fingerprint generated:', fingerprint);
    return fingerprint;
  }

  /**
   * Canvas fingerprinting
   */
  async getCanvasFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = 200;
    canvas.height = 50;

    // Draw text with specific styling
    ctx.textBaseline = 'top';
    ctx.font = '14px "Arial"';
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('CringeProof 🚫', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('CringeProof 🚫', 4, 17);

    return canvas.toDataURL();
  }

  /**
   * WebGL fingerprinting
   */
  async getWebGLFingerprint() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');

    if (!gl) {
      return 'no-webgl';
    }

    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    if (debugInfo) {
      const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
      const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
      return `${vendor}|${renderer}`;
    }

    return 'webgl-no-debug';
  }

  /**
   * Audio context fingerprinting
   */
  async getAudioFingerprint() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) {
        return 'no-audio';
      }

      const context = new AudioContext();
      const oscillator = context.createOscillator();
      const analyser = context.createAnalyser();
      const gainNode = context.createGain();
      const scriptProcessor = context.createScriptProcessor(4096, 1, 1);

      gainNode.gain.value = 0; // Mute
      oscillator.type = 'triangle';
      oscillator.connect(analyser);
      analyser.connect(scriptProcessor);
      scriptProcessor.connect(gainNode);
      gainNode.connect(context.destination);

      oscillator.start(0);

      return new Promise((resolve) => {
        scriptProcessor.onaudioprocess = (event) => {
          const output = event.inputBuffer.getChannelData(0);
          const hash = Array.from(output.slice(0, 30))
            .map((val) => val.toFixed(6))
            .join('');

          oscillator.stop();
          scriptProcessor.disconnect();
          gainNode.disconnect();
          analyser.disconnect();
          oscillator.disconnect();
          context.close();

          resolve(hash);
        };
      });
    } catch (e) {
      return 'audio-error';
    }
  }

  /**
   * Hash string using SHA-256
   */
  async hashString(str) {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
    return hashHex.substring(0, 16); // First 16 chars
  }

  /**
   * Get or create shadow account
   */
  async getOrCreateAccount() {
    await this.ensureDB();

    // Generate fingerprint
    this.fingerprint = await this.generateFingerprint();

    // Check if account exists
    const existing = await this.getAccount(this.fingerprint);

    if (existing) {
      console.log('[ShadowAccount] Existing account found:', existing.shadowId);
      this.shadowId = existing.shadowId;

      // Update last seen
      await this.updateLastSeen(this.fingerprint);

      return existing;
    } else {
      // Create new account
      console.log('[ShadowAccount] Creating new account');
      return await this.createAccount(this.fingerprint);
    }
  }

  /**
   * Get account by fingerprint
   */
  async getAccount(fingerprint) {
    await this.ensureDB();

    const transaction = this.db.transaction([SHADOW_STORE_NAME], 'readonly');
    const store = transaction.objectStore(SHADOW_STORE_NAME);

    return new Promise((resolve, reject) => {
      const request = store.get(fingerprint);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Create new shadow account
   */
  async createAccount(fingerprint) {
    await this.ensureDB();

    // Generate shadow ID (shorter, user-friendly)
    const shadowId = await this.hashString(fingerprint + Date.now());

    const account = {
      fingerprint: fingerprint,
      shadowId: shadowId,
      createdAt: Date.now(),
      lastSeen: Date.now(),
      recordingCount: 0,
      metadata: {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      }
    };

    const transaction = this.db.transaction([SHADOW_STORE_NAME], 'readwrite');
    const store = transaction.objectStore(SHADOW_STORE_NAME);

    return new Promise((resolve, reject) => {
      const request = store.add(account);

      request.onsuccess = () => {
        console.log('[ShadowAccount] Account created:', shadowId);
        this.shadowId = shadowId;
        resolve(account);
      };

      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Update last seen timestamp
   */
  async updateLastSeen(fingerprint) {
    await this.ensureDB();

    const transaction = this.db.transaction([SHADOW_STORE_NAME], 'readwrite');
    const store = transaction.objectStore(SHADOW_STORE_NAME);

    return new Promise((resolve, reject) => {
      const getRequest = store.get(fingerprint);

      getRequest.onsuccess = () => {
        const account = getRequest.result;
        if (!account) {
          reject(new Error('Account not found'));
          return;
        }

        account.lastSeen = Date.now();
        const putRequest = store.put(account);

        putRequest.onsuccess = () => resolve(account);
        putRequest.onerror = () => reject(putRequest.error);
      };

      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  /**
   * Increment recording count
   */
  async incrementRecordingCount() {
    if (!this.fingerprint) {
      throw new Error('No fingerprint available');
    }

    await this.ensureDB();

    const transaction = this.db.transaction([SHADOW_STORE_NAME], 'readwrite');
    const store = transaction.objectStore(SHADOW_STORE_NAME);

    return new Promise((resolve, reject) => {
      const getRequest = store.get(this.fingerprint);

      getRequest.onsuccess = () => {
        const account = getRequest.result;
        if (!account) {
          reject(new Error('Account not found'));
          return;
        }

        account.recordingCount = (account.recordingCount || 0) + 1;
        account.lastSeen = Date.now();

        const putRequest = store.put(account);

        putRequest.onsuccess = () => resolve(account);
        putRequest.onerror = () => reject(putRequest.error);
      };

      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  /**
   * Get current shadow ID
   */
  getShadowId() {
    return this.shadowId;
  }

  /**
   * Get current fingerprint
   */
  getFingerprint() {
    return this.fingerprint;
  }

  /**
   * Ensure database is initialized
   */
  async ensureDB() {
    if (!this.db) {
      await this.initDB();
    }
  }
}

// Create global instance
const shadowAccount = new ShadowAccount();

// Auto-initialize on page load
window.addEventListener('load', async () => {
  try {
    const account = await shadowAccount.getOrCreateAccount();
    console.log('[ShadowAccount] Ready:', account.shadowId);

    // Store in localStorage for quick access
    localStorage.setItem('shadow_id', account.shadowId);
    localStorage.setItem('shadow_fingerprint', account.fingerprint);

    // Dispatch custom event for other scripts
    window.dispatchEvent(
      new CustomEvent('shadowaccount', {
        detail: { type: 'READY', account }
      })
    );
  } catch (error) {
    console.error('[ShadowAccount] Initialization failed:', error);
  }
});

// Export for use in other scripts
window.shadowAccount = shadowAccount;

console.log('[ShadowAccount] Initialized');
