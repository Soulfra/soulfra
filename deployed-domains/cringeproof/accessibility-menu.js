/**
 * Accessibility Menu - Universal Input Mode Switcher
 *
 * Like RuneScape's interface modes or WoW's accessibility settings.
 * Let users choose how they want to interact with the site.
 *
 * Input Modes:
 * - Voice: Speak commands
 * - Scan: QR codes for actions
 * - Emoji: React/navigate with emoji
 * - Gesture: Mouse/touch patterns
 * - Menu: Click-only (no keyboard)
 *
 * Features:
 * - Persistent across sessions (localStorage)
 * - Floating menu (always accessible)
 * - Visual feedback for active mode
 * - Mode-specific tutorials
 */

class AccessibilityMenu {
  constructor() {
    this.currentMode = localStorage.getItem('inputMode') || 'menu';
    this.menuOpen = false;

    this.modes = {
      voice: {
        name: 'Voice Control',
        icon: '🎤',
        description: 'Speak commands to navigate and submit',
        color: '#ff006e'
      },
      scan: {
        name: 'QR Scanner',
        icon: '📱',
        description: 'Scan QR codes for quick actions',
        color: '#00C49A'
      },
      emoji: {
        name: 'Emoji Nav',
        icon: '😊',
        description: 'Navigate with emoji reactions',
        color: '#bdb2ff'
      },
      gesture: {
        name: 'Gestures',
        icon: '👆',
        description: 'Swipe and tap to interact',
        color: '#ffc6ff'
      },
      menu: {
        name: 'Menu Only',
        icon: '🖱️',
        description: 'Click-based navigation (default)',
        color: '#333'
      }
    };

    this.init();
  }

  init() {
    // Create menu UI
    this.createMenuUI();

    // Apply current mode
    this.applyMode(this.currentMode);

    // Keyboard shortcut (Alt+A)
    document.addEventListener('keydown', (e) => {
      if (e.altKey && e.key === 'a') {
        e.preventDefault();
        this.toggleMenu();
      }
    });

    console.log('[AccessibilityMenu] Initialized with mode:', this.currentMode);
  }

  createMenuUI() {
    const menu = document.createElement('div');
    menu.id = 'accessibility-menu';
    menu.className = 'accessibility-menu';
    menu.innerHTML = `
      <button class="accessibility-trigger" id="accessibility-trigger" title="Accessibility Menu (Alt+A)">
        <span class="accessibility-icon">${this.modes[this.currentMode].icon}</span>
      </button>

      <div class="accessibility-panel" id="accessibility-panel">
        <div class="accessibility-header">
          <h3>Input Mode</h3>
          <button class="accessibility-close" id="accessibility-close">✕</button>
        </div>

        <div class="accessibility-modes">
          ${Object.entries(this.modes).map(([key, mode]) => `
            <button
              class="accessibility-mode-btn ${key === this.currentMode ? 'active' : ''}"
              data-mode="${key}"
              style="--mode-color: ${mode.color}"
            >
              <span class="mode-icon">${mode.icon}</span>
              <span class="mode-name">${mode.name}</span>
              <span class="mode-desc">${mode.description}</span>
            </button>
          `).join('')}
        </div>

        <div class="accessibility-footer">
          <small>Press <kbd>Alt+A</kbd> to toggle this menu</small>
        </div>
      </div>
    `;

    document.body.appendChild(menu);

    // Event listeners
    document.getElementById('accessibility-trigger').addEventListener('click', () => {
      this.toggleMenu();
    });

    document.getElementById('accessibility-close').addEventListener('click', () => {
      this.closeMenu();
    });

    document.querySelectorAll('.accessibility-mode-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        this.setMode(mode);
      });
    });

    // Click outside to close
    document.addEventListener('click', (e) => {
      const menu = document.getElementById('accessibility-menu');
      if (!menu.contains(e.target) && this.menuOpen) {
        this.closeMenu();
      }
    });
  }

  toggleMenu() {
    if (this.menuOpen) {
      this.closeMenu();
    } else {
      this.openMenu();
    }
  }

  openMenu() {
    document.getElementById('accessibility-panel').classList.add('open');
    this.menuOpen = true;
  }

  closeMenu() {
    document.getElementById('accessibility-panel').classList.remove('open');
    this.menuOpen = false;
  }

  setMode(mode) {
    if (!this.modes[mode]) {
      console.error('[AccessibilityMenu] Invalid mode:', mode);
      return;
    }

    this.currentMode = mode;
    localStorage.setItem('inputMode', mode);

    // Update UI
    document.querySelectorAll('.accessibility-mode-btn').forEach((btn) => {
      if (btn.dataset.mode === mode) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Update trigger icon
    document.querySelector('.accessibility-icon').textContent = this.modes[mode].icon;

    // Apply mode
    this.applyMode(mode);

    // Show notification
    this.showNotification(`Switched to ${this.modes[mode].name}`);

    // Dispatch event for workflow coordinator
    window.dispatchEvent(
      new CustomEvent('inputmodechange', {
        detail: { mode, modeData: this.modes[mode] }
      })
    );

    console.log('[AccessibilityMenu] Mode changed to:', mode);
  }

  applyMode(mode) {
    // Add data attribute to body for CSS targeting
    document.body.dataset.inputMode = mode;

    // Enable/disable features based on mode
    switch (mode) {
      case 'voice':
        this.enableVoiceMode();
        break;
      case 'scan':
        this.enableScanMode();
        break;
      case 'emoji':
        this.enableEmojiMode();
        break;
      case 'gesture':
        this.enableGestureMode();
        break;
      case 'menu':
        this.enableMenuMode();
        break;
    }
  }

  enableVoiceMode() {
    // Check if voice commands are available
    if (!window.voiceCommands) {
      console.warn('[AccessibilityMenu] Voice commands not loaded');
      return;
    }

    // Start listening
    window.voiceCommands.startListening();
  }

  enableScanMode() {
    // Check if QR scanner is available
    if (!window.qrActions) {
      console.warn('[AccessibilityMenu] QR actions not loaded');
      return;
    }

    // Show QR scan hint
    this.showNotification('Tap QR icon to scan codes');
  }

  enableEmojiMode() {
    // Check if emoji controls are available
    if (!window.emojiControls) {
      console.warn('[AccessibilityMenu] Emoji controls not loaded');
      return;
    }

    // Enable emoji overlay
    window.emojiControls.showOverlay();
  }

  enableGestureMode() {
    // Check if gesture detector is available
    if (!window.gestureDetector) {
      console.warn('[AccessibilityMenu] Gesture detector not loaded');
      return;
    }

    // Enable gesture detection
    window.gestureDetector.enable();
  }

  enableMenuMode() {
    // Disable other modes
    if (window.voiceCommands) window.voiceCommands.stopListening();
    if (window.emojiControls) window.emojiControls.hideOverlay();
    if (window.gestureDetector) window.gestureDetector.disable();

    this.showNotification('Menu mode - click to interact');
  }

  showNotification(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'accessibility-toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Remove after 3 seconds
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  getCurrentMode() {
    return this.currentMode;
  }

  getModeData(mode) {
    return this.modes[mode];
  }
}

// Auto-initialize
let accessibilityMenu;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    accessibilityMenu = new AccessibilityMenu();
  });
} else {
  accessibilityMenu = new AccessibilityMenu();
}

// Export
window.AccessibilityMenu = AccessibilityMenu;
window.accessibilityMenu = accessibilityMenu;

console.log('[Accessibility Menu] Loaded');
