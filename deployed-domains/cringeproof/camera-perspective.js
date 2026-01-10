/**
 * Camera Perspective Switcher
 *
 * Provides multiple viewing angles like a video game or Zoom:
 * - First-Person (FPS): Direct, close-up view
 * - Third-Person: Pulled back, angled view
 * - Isometric: Top-down, architectural view
 * - Cinematic: Wide-angle, dramatic view
 *
 * Uses CSS 3D transforms with GPU acceleration
 */

class CameraPerspective {
  constructor(options = {}) {
    this.container = options.container || document.getElementById('camera-container');
    this.currentPerspective = options.defaultPerspective || 'third-person';

    this.perspectives = {
      'first-person': {
        name: 'First Person (FPS)',
        icon: '👁️',
        transform: {
          translateZ: 0,
          rotateX: 0,
          rotateY: 0,
          scale: 1.2
        },
        description: 'Direct close-up view'
      },
      'third-person': {
        name: 'Third Person',
        icon: '🎮',
        transform: {
          translateZ: -200,
          rotateX: 10,
          rotateY: 5,
          scale: 1
        },
        description: 'Pulled back angled view'
      },
      'isometric': {
        name: 'Isometric',
        icon: '📐',
        transform: {
          translateZ: -300,
          rotateX: 45,
          rotateY: 45,
          scale: 0.9
        },
        description: 'Top-down architectural view'
      },
      'cinematic': {
        name: 'Cinematic',
        icon: '🎬',
        transform: {
          translateZ: -400,
          rotateX: 5,
          rotateY: -10,
          scale: 0.8
        },
        description: 'Wide-angle dramatic view'
      },
      'birds-eye': {
        name: "Bird's Eye",
        icon: '🦅',
        transform: {
          translateZ: -500,
          rotateX: 60,
          rotateY: 0,
          scale: 0.7
        },
        description: 'Overhead view'
      }
    };

    this.init();
  }

  init() {
    if (!this.container) {
      console.error('[CameraPerspective] Container not found');
      return;
    }

    // Setup container for 3D transforms
    this.container.style.transformStyle = 'preserve-3d';
    this.container.style.perspective = '1500px';
    this.container.style.transition = 'transform 800ms cubic-bezier(0.23, 1, 0.32, 1)';

    // Create perspective switcher UI
    this.createSwitcherUI();

    // Apply default perspective
    this.setPerspective(this.currentPerspective);

    // Keyboard shortcuts
    this.bindKeyboardShortcuts();

    console.log('[CameraPerspective] Initialized');
  }

  createSwitcherUI() {
    const switcher = document.createElement('div');
    switcher.className = 'camera-perspective-switcher';
    switcher.innerHTML = `
      <div class="camera-perspective-header">
        <strong>📷 Camera Angle</strong>
        <button class="camera-perspective-close" onclick="cameraPerspective.toggleSwitcher()">−</button>
      </div>
      <div class="camera-perspective-buttons">
        ${Object.entries(this.perspectives)
          .map(
            ([key, data]) => `
          <button
            class="camera-perspective-btn"
            data-perspective="${key}"
            onclick="cameraPerspective.setPerspective('${key}')"
            title="${data.description}"
          >
            <span class="camera-perspective-icon">${data.icon}</span>
            <span class="camera-perspective-name">${data.name}</span>
          </button>
        `
          )
          .join('')}
      </div>
      <div class="camera-perspective-footer">
        <small>Keyboard: 1-5 to switch</small>
      </div>
    `;

    document.body.appendChild(switcher);
    this.switcherElement = switcher;
  }

  setPerspective(perspectiveName) {
    if (!this.perspectives[perspectiveName]) {
      console.error('[CameraPerspective] Invalid perspective:', perspectiveName);
      return;
    }

    this.currentPerspective = perspectiveName;
    const perspective = this.perspectives[perspectiveName];

    // Apply transform to container
    const { translateZ, rotateX, rotateY, scale } = perspective.transform;

    const transform = `
      translateZ(${translateZ}px)
      rotateX(${rotateX}deg)
      rotateY(${rotateY}deg)
      scale(${scale})
    `;

    this.container.style.transform = transform.replace(/\s+/g, ' ').trim();

    // Update active button
    this.switcherElement.querySelectorAll('.camera-perspective-btn').forEach((btn) => {
      if (btn.dataset.perspective === perspectiveName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Dispatch event
    window.dispatchEvent(
      new CustomEvent('cameraperspective', {
        detail: { type: 'PERSPECTIVE_CHANGED', perspective: perspectiveName }
      })
    );

    console.log('[CameraPerspective] Switched to:', perspective.name);
  }

  toggleSwitcher() {
    this.switcherElement.classList.toggle('camera-perspective-collapsed');
  }

  bindKeyboardShortcuts() {
    const perspectiveKeys = Object.keys(this.perspectives);

    document.addEventListener('keydown', (e) => {
      // Ignore if typing in input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      // Check for number keys 1-5
      const keyNum = parseInt(e.key);
      if (keyNum >= 1 && keyNum <= perspectiveKeys.length) {
        const perspectiveName = perspectiveKeys[keyNum - 1];
        this.setPerspective(perspectiveName);
      }

      // Toggle switcher with 'C' key
      if (e.key.toLowerCase() === 'c') {
        this.toggleSwitcher();
      }
    });
  }

  reset() {
    this.setPerspective('third-person');
  }
}

/**
 * Auto-apply camera perspective to elements with data-camera-container
 */
let cameraPerspective;

window.addEventListener('DOMContentLoaded', () => {
  const container = document.querySelector('[data-camera-container]');

  if (container) {
    cameraPerspective = new CameraPerspective({
      container,
      defaultPerspective: container.dataset.defaultPerspective || 'third-person'
    });

    console.log('[CameraPerspective] Ready');
  }
});

// Export for manual usage
window.CameraPerspective = CameraPerspective;
window.cameraPerspective = cameraPerspective;

console.log('[Camera Perspective] Loaded');
