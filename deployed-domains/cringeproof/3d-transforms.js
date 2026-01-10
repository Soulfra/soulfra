/**
 * 3D Card Transforms - GPU-Accelerated
 *
 * Features:
 * - Mouse tracking for 3D tilt effect
 * - GPU-accelerated transforms (translateZ, rotateX, rotateY)
 * - Parallax layers (card, text, background)
 * - Smooth transitions with requestAnimationFrame
 * - Touch device support
 * - Performance monitoring
 */

class Card3D {
  constructor(element, options = {}) {
    this.element = element;
    this.options = {
      maxTilt: options.maxTilt || 15, // degrees
      perspective: options.perspective || 1000, // px
      scale: options.scale || 1.05,
      speed: options.speed || 400, // ms
      glare: options.glare !== false, // enable by default
      gyroscope: options.gyroscope || false, // mobile gyroscope
      ...options
    };

    this.width = 0;
    this.height = 0;
    this.left = 0;
    this.top = 0;

    this.transitionTimeout = null;
    this.updateCall = null;

    this.init();
  }

  init() {
    // Add GPU acceleration classes
    this.element.style.transformStyle = 'preserve-3d';
    this.element.style.willChange = 'transform';
    this.element.style.transition = `transform ${this.options.speed}ms cubic-bezier(0.23, 1, 0.32, 1)`;

    // Create glare effect
    if (this.options.glare) {
      this.createGlare();
    }

    // Bind events
    this.bindEvents();

    // Update dimensions
    this.updateElementPosition();

    console.log('[Card3D] Initialized:', this.element);
  }

  createGlare() {
    const glare = document.createElement('div');
    glare.classList.add('card-3d-glare');
    glare.style.position = 'absolute';
    glare.style.top = '0';
    glare.style.left = '0';
    glare.style.width = '100%';
    glare.style.height = '100%';
    glare.style.borderRadius = 'inherit';
    glare.style.pointerEvents = 'none';
    glare.style.background = 'linear-gradient(45deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0) 100%)';
    glare.style.opacity = '0';
    glare.style.transition = `opacity ${this.options.speed}ms ease`;

    this.element.appendChild(glare);
    this.glareElement = glare;
  }

  bindEvents() {
    this.onMouseEnter = this.handleMouseEnter.bind(this);
    this.onMouseMove = this.handleMouseMove.bind(this);
    this.onMouseLeave = this.handleMouseLeave.bind(this);

    this.element.addEventListener('mouseenter', this.onMouseEnter);
    this.element.addEventListener('mousemove', this.onMouseMove);
    this.element.addEventListener('mouseleave', this.onMouseLeave);

    // Touch events for mobile
    this.element.addEventListener('touchstart', this.onMouseEnter);
    this.element.addEventListener('touchmove', this.handleTouchMove.bind(this));
    this.element.addEventListener('touchend', this.onMouseLeave);

    // Gyroscope for mobile (if enabled)
    if (this.options.gyroscope && window.DeviceOrientationEvent) {
      window.addEventListener('deviceorientation', this.handleDeviceOrientation.bind(this));
    }

    // Update on resize
    window.addEventListener('resize', this.updateElementPosition.bind(this));
  }

  handleMouseEnter(event) {
    this.updateElementPosition();
    this.element.style.willChange = 'transform';

    if (this.glareElement) {
      this.glareElement.style.opacity = '1';
    }
  }

  handleMouseMove(event) {
    // Cancel any pending update
    if (this.updateCall !== null) {
      cancelAnimationFrame(this.updateCall);
    }

    // Schedule update on next frame
    this.updateCall = requestAnimationFrame(() => {
      this.update(event.clientX, event.clientY);
    });
  }

  handleTouchMove(event) {
    event.preventDefault();
    const touch = event.touches[0];
    this.update(touch.clientX, touch.clientY);
  }

  handleMouseLeave(event) {
    if (this.updateCall !== null) {
      cancelAnimationFrame(this.updateCall);
      this.updateCall = null;
    }

    this.reset();
  }

  handleDeviceOrientation(event) {
    // Use device orientation for mobile tilt
    const { beta, gamma } = event; // beta: front-to-back, gamma: left-to-right

    // Map orientation to tilt values
    const tiltX = (gamma / 90) * this.options.maxTilt; // -maxTilt to +maxTilt
    const tiltY = (beta / 90) * this.options.maxTilt;

    this.setTransform(tiltX, tiltY);
  }

  update(clientX, clientY) {
    // Calculate mouse position relative to element
    const percentageX = (clientX - this.left) / this.width;
    const percentageY = (clientY - this.top) / this.height;

    // Calculate tilt angles
    const tiltY = (percentageX - 0.5) * 2 * this.options.maxTilt; // -maxTilt to +maxTilt
    const tiltX = (0.5 - percentageY) * 2 * this.options.maxTilt;

    this.setTransform(tiltX, tiltY);

    // Update glare position
    if (this.glareElement) {
      const glareX = percentageX * 100;
      const glareY = percentageY * 100;
      this.glareElement.style.background = `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 50%)`;
    }
  }

  setTransform(tiltX, tiltY) {
    // Apply 3D transform with GPU acceleration
    const transform = `
      perspective(${this.options.perspective}px)
      rotateX(${tiltX}deg)
      rotateY(${tiltY}deg)
      scale3d(${this.options.scale}, ${this.options.scale}, ${this.options.scale})
      translateZ(0)
    `;

    this.element.style.transform = transform.replace(/\s+/g, ' ').trim();
  }

  reset() {
    // Reset to default position
    this.element.style.transform = `
      perspective(${this.options.perspective}px)
      rotateX(0deg)
      rotateY(0deg)
      scale3d(1, 1, 1)
      translateZ(0)
    `;

    if (this.glareElement) {
      this.glareElement.style.opacity = '0';
    }

    // Clear will-change after transition
    clearTimeout(this.transitionTimeout);
    this.transitionTimeout = setTimeout(() => {
      this.element.style.willChange = 'auto';
    }, this.options.speed);
  }

  updateElementPosition() {
    const rect = this.element.getBoundingClientRect();
    this.width = rect.width;
    this.height = rect.height;
    this.left = rect.left;
    this.top = rect.top;
  }

  destroy() {
    // Remove event listeners
    this.element.removeEventListener('mouseenter', this.onMouseEnter);
    this.element.removeEventListener('mousemove', this.onMouseMove);
    this.element.removeEventListener('mouseleave', this.onMouseLeave);

    // Remove glare
    if (this.glareElement) {
      this.glareElement.remove();
    }

    // Reset styles
    this.element.style.transform = '';
    this.element.style.transformStyle = '';
    this.element.style.willChange = '';
    this.element.style.transition = '';

    console.log('[Card3D] Destroyed:', this.element);
  }
}

/**
 * Auto-initialize all cards with data-card-3d attribute
 */
class Card3DManager {
  constructor() {
    this.cards = [];
    this.init();
  }

  init() {
    // Find all elements with data-card-3d
    const elements = document.querySelectorAll('[data-card-3d]');

    elements.forEach((element) => {
      // Parse options from data attributes
      const options = {
        maxTilt: parseFloat(element.dataset.maxTilt) || 15,
        perspective: parseFloat(element.dataset.perspective) || 1000,
        scale: parseFloat(element.dataset.scale) || 1.05,
        speed: parseFloat(element.dataset.speed) || 400,
        glare: element.dataset.glare !== 'false',
        gyroscope: element.dataset.gyroscope === 'true'
      };

      const card = new Card3D(element, options);
      this.cards.push(card);
    });

    console.log(`[Card3DManager] Initialized ${this.cards.length} cards`);
  }

  refresh() {
    // Destroy existing cards
    this.cards.forEach((card) => card.destroy());
    this.cards = [];

    // Re-initialize
    this.init();
  }

  destroy() {
    this.cards.forEach((card) => card.destroy());
    this.cards = [];
  }
}

// Auto-initialize on DOM ready
let card3DManager;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    card3DManager = new Card3DManager();
  });
} else {
  card3DManager = new Card3DManager();
}

// Refresh on dynamic content changes
const observer = new MutationObserver((mutations) => {
  let shouldRefresh = false;

  mutations.forEach((mutation) => {
    mutation.addedNodes.forEach((node) => {
      if (node.nodeType === 1 && (node.hasAttribute('data-card-3d') || node.querySelector('[data-card-3d]'))) {
        shouldRefresh = true;
      }
    });
  });

  if (shouldRefresh && card3DManager) {
    card3DManager.refresh();
  }
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});

// Export for manual usage
window.Card3D = Card3D;
window.Card3DManager = Card3DManager;
window.card3DManager = card3DManager;

console.log('[3D Transforms] Loaded');
