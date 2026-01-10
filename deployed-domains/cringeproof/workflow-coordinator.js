/**
 * Workflow Coordinator - State Machine for Input Routing
 *
 * Detects page context and routes inputs to appropriate handlers.
 * Like a game controller that maps buttons differently per screen.
 *
 * Context Detection:
 * - Search page → Voice query or visual browse
 * - Idea page → React with emoji or voice comment
 * - Profile → QR share or voice edit
 * - Record page → Voice input
 *
 * Input Modes (from accessibility-menu.js):
 * - voice, scan, emoji, gesture, menu
 *
 * Workflow Examples:
 * 1. User on search page in voice mode:
 *    - Says "search for privacy" → Routes to voice search
 * 2. User on idea card in emoji mode:
 *    - Taps 👍 → Routes to emoji reaction
 * 3. User on profile in scan mode:
 *    - Scans QR → Routes to profile import
 */

class WorkflowCoordinator {
  constructor() {
    this.currentMode = 'menu'; // Default
    this.currentContext = this.detectContext();
    this.workflows = {};

    this.init();
  }

  init() {
    // Listen for mode changes
    window.addEventListener('inputmodechange', (e) => {
      this.currentMode = e.detail.mode;
      console.log('[WorkflowCoordinator] Mode changed to:', this.currentMode);
      this.updateWorkflow();
    });

    // Get initial mode from accessibility menu
    if (window.accessibilityMenu) {
      this.currentMode = window.accessibilityMenu.getCurrentMode();
    }

    // Define workflows for each context
    this.defineWorkflows();

    // Apply current workflow
    this.updateWorkflow();

    console.log('[WorkflowCoordinator] Initialized with context:', this.currentContext);
  }

  detectContext() {
    const path = window.location.pathname;
    const search = window.location.search;

    // Detect page context
    if (path.includes('/record') || path.includes('record-simple')) {
      return 'record';
    }

    if (path.includes('/ideas') || path.includes('/i/')) {
      return 'idea';
    }

    if (path.includes('/profile') || path.includes('/u/')) {
      return 'profile';
    }

    if (search.includes('?q=') || document.getElementById('instant-search')) {
      return 'search';
    }

    if (path === '/' || path.includes('/index')) {
      return 'home';
    }

    return 'generic';
  }

  defineWorkflows() {
    // ========================================
    // RECORD PAGE WORKFLOWS
    // ========================================
    this.workflows.record = {
      voice: {
        description: 'Record voice memo',
        handler: () => {
          console.log('[Workflow] Voice mode on record page - ready to record');
          // Voice is already the default on this page
        }
      },
      scan: {
        description: 'Scan QR to pre-fill title/category',
        handler: () => {
          console.log('[Workflow] Scan mode on record page');
          if (window.qrActions) {
            window.qrActions.enableScanForPrefill();
          }
        }
      },
      emoji: {
        description: 'Choose category with emoji',
        handler: () => {
          console.log('[Workflow] Emoji mode on record page');
          this.showEmojiCategoryPicker();
        }
      },
      gesture: {
        description: 'Swipe to start/stop recording',
        handler: () => {
          console.log('[Workflow] Gesture mode on record page');
          if (window.gestureDetector) {
            window.gestureDetector.bindRecordGestures();
          }
        }
      },
      menu: {
        description: 'Click record button',
        handler: () => {
          console.log('[Workflow] Menu mode on record page - default behavior');
        }
      }
    };

    // ========================================
    // IDEA PAGE WORKFLOWS
    // ========================================
    this.workflows.idea = {
      voice: {
        description: 'Voice comment or share',
        handler: () => {
          console.log('[Workflow] Voice mode on idea page');
          if (window.voiceCommands) {
            window.voiceCommands.enableIdeaCommands();
          }
        }
      },
      scan: {
        description: 'Scan to share or download',
        handler: () => {
          console.log('[Workflow] Scan mode on idea page');
          this.showQRShareOptions();
        }
      },
      emoji: {
        description: 'React with emoji',
        handler: () => {
          console.log('[Workflow] Emoji mode on idea page');
          if (window.emojiControls) {
            window.emojiControls.enableReactions();
          }
        }
      },
      gesture: {
        description: 'Swipe to navigate ideas',
        handler: () => {
          console.log('[Workflow] Gesture mode on idea page');
          if (window.gestureDetector) {
            window.gestureDetector.bindIdeaNavigation();
          }
        }
      },
      menu: {
        description: 'Click to interact',
        handler: () => {
          console.log('[Workflow] Menu mode on idea page - default behavior');
        }
      }
    };

    // ========================================
    // SEARCH PAGE WORKFLOWS
    // ========================================
    this.workflows.search = {
      voice: {
        description: 'Voice search query',
        handler: () => {
          console.log('[Workflow] Voice mode on search page');
          if (window.voiceCommands) {
            window.voiceCommands.enableSearchCommands();
          }
        }
      },
      scan: {
        description: 'Scan to search or filter',
        handler: () => {
          console.log('[Workflow] Scan mode on search page');
          if (window.qrActions) {
            window.qrActions.enableScanForSearch();
          }
        }
      },
      emoji: {
        description: 'Filter by emoji tier',
        handler: () => {
          console.log('[Workflow] Emoji mode on search page');
          this.showEmojiFilters();
        }
      },
      gesture: {
        description: 'Swipe to browse results',
        handler: () => {
          console.log('[Workflow] Gesture mode on search page');
          if (window.gestureDetector) {
            window.gestureDetector.bindSearchNavigation();
          }
        }
      },
      menu: {
        description: 'Type to search',
        handler: () => {
          console.log('[Workflow] Menu mode on search page - default behavior');
        }
      }
    };

    // ========================================
    // PROFILE PAGE WORKFLOWS
    // ========================================
    this.workflows.profile = {
      voice: {
        description: 'Voice edit bio',
        handler: () => {
          console.log('[Workflow] Voice mode on profile page');
          if (window.voiceCommands) {
            window.voiceCommands.enableProfileCommands();
          }
        }
      },
      scan: {
        description: 'Generate QR for sharing',
        handler: () => {
          console.log('[Workflow] Scan mode on profile page');
          this.generateProfileQR();
        }
      },
      emoji: {
        description: 'Change status emoji',
        handler: () => {
          console.log('[Workflow] Emoji mode on profile page');
          this.showEmojiStatusPicker();
        }
      },
      gesture: {
        description: 'Swipe through recordings',
        handler: () => {
          console.log('[Workflow] Gesture mode on profile page');
          if (window.gestureDetector) {
            window.gestureDetector.bindProfileGestures();
          }
        }
      },
      menu: {
        description: 'Click to edit',
        handler: () => {
          console.log('[Workflow] Menu mode on profile page - default behavior');
        }
      }
    };

    // ========================================
    // HOME PAGE WORKFLOWS
    // ========================================
    this.workflows.home = {
      voice: {
        description: 'Voice navigation',
        handler: () => {
          console.log('[Workflow] Voice mode on home page');
          if (window.voiceCommands) {
            window.voiceCommands.enableNavigationCommands();
          }
        }
      },
      scan: {
        description: 'Quick login or action',
        handler: () => {
          console.log('[Workflow] Scan mode on home page');
          if (window.qrActions) {
            window.qrActions.showLoginQR();
          }
        }
      },
      emoji: {
        description: 'Browse by category',
        handler: () => {
          console.log('[Workflow] Emoji mode on home page');
          this.showEmojiCategoryNav();
        }
      },
      gesture: {
        description: 'Swipe through features',
        handler: () => {
          console.log('[Workflow] Gesture mode on home page');
          if (window.gestureDetector) {
            window.gestureDetector.bindHomeGestures();
          }
        }
      },
      menu: {
        description: 'Click to navigate',
        handler: () => {
          console.log('[Workflow] Menu mode on home page - default behavior');
        }
      }
    };

    // ========================================
    // GENERIC FALLBACK
    // ========================================
    this.workflows.generic = {
      voice: {
        description: 'Voice navigation',
        handler: () => {
          console.log('[Workflow] Voice mode - generic');
          if (window.voiceCommands) {
            window.voiceCommands.enableNavigationCommands();
          }
        }
      },
      scan: {
        description: 'Scan for actions',
        handler: () => {
          console.log('[Workflow] Scan mode - generic');
        }
      },
      emoji: {
        description: 'Emoji reactions',
        handler: () => {
          console.log('[Workflow] Emoji mode - generic');
        }
      },
      gesture: {
        description: 'Gesture navigation',
        handler: () => {
          console.log('[Workflow] Gesture mode - generic');
        }
      },
      menu: {
        description: 'Click navigation',
        handler: () => {
          console.log('[Workflow] Menu mode - generic');
        }
      }
    };
  }

  updateWorkflow() {
    const workflow = this.workflows[this.currentContext];

    if (!workflow) {
      console.warn('[WorkflowCoordinator] No workflow for context:', this.currentContext);
      return;
    }

    const modeWorkflow = workflow[this.currentMode];

    if (!modeWorkflow) {
      console.warn('[WorkflowCoordinator] No workflow for mode:', this.currentMode);
      return;
    }

    // Execute handler
    modeWorkflow.handler();

    // Dispatch event
    window.dispatchEvent(
      new CustomEvent('workflowchange', {
        detail: {
          context: this.currentContext,
          mode: this.currentMode,
          description: modeWorkflow.description
        }
      })
    );
  }

  // ========================================
  // HELPER METHODS
  // ========================================

  showEmojiCategoryPicker() {
    // Show emoji picker for categories
    console.log('[WorkflowCoordinator] Showing emoji category picker');
    // TODO: Implement emoji picker UI
  }

  showQRShareOptions() {
    // Show QR options for sharing
    console.log('[WorkflowCoordinator] Showing QR share options');
    // TODO: Implement QR share UI
  }

  showEmojiFilters() {
    // Show emoji filters for search
    console.log('[WorkflowCoordinator] Showing emoji filters');
    // TODO: Implement emoji filter UI
  }

  generateProfileQR() {
    // Generate QR code for profile
    console.log('[WorkflowCoordinator] Generating profile QR');
    // TODO: Implement profile QR generation
  }

  showEmojiStatusPicker() {
    // Show emoji picker for status
    console.log('[WorkflowCoordinator] Showing emoji status picker');
    // TODO: Implement emoji status picker
  }

  showEmojiCategoryNav() {
    // Show emoji category navigation
    console.log('[WorkflowCoordinator] Showing emoji category nav');
    // TODO: Implement emoji category nav
  }

  // ========================================
  // PUBLIC API
  // ========================================

  getCurrentContext() {
    return this.currentContext;
  }

  getCurrentMode() {
    return this.currentMode;
  }

  refreshContext() {
    this.currentContext = this.detectContext();
    this.updateWorkflow();
  }
}

// Auto-initialize
let workflowCoordinator;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    workflowCoordinator = new WorkflowCoordinator();
  });
} else {
  workflowCoordinator = new WorkflowCoordinator();
}

// Export
window.WorkflowCoordinator = WorkflowCoordinator;
window.workflowCoordinator = workflowCoordinator;

console.log('[Workflow Coordinator] Loaded');
