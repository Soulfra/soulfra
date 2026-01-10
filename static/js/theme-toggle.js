/**
 * Theme Toggle System
 *
 * Handles dark/light mode switching with localStorage persistence
 *
 * Usage:
 * 1. Include this script at the bottom of your HTML
 * 2. Add theme-toggle button to your page (or use auto-inject)
 * 3. Theme preference is saved to localStorage
 */

(function() {
  'use strict';

  // ==================== THEME DETECTION & INITIALIZATION ====================

  /**
   * Get initial theme from localStorage or system preference
   */
  function getInitialTheme() {
    // Check localStorage first
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme;
    }

    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }

    return 'light';
  }

  /**
   * Apply theme to document
   */
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    // Dispatch custom event for other scripts to listen to
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  /**
   * Toggle between light and dark themes
   */
  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
  }

  // ==================== INITIALIZE ON PAGE LOAD ====================

  // Apply theme ASAP to avoid flash of wrong theme
  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);

  // Remove preload class after a short delay to enable transitions
  window.addEventListener('load', function() {
    setTimeout(function() {
      document.body.classList.remove('preload');
    }, 100);
  });

  // ==================== CREATE TOGGLE BUTTON ====================

  /**
   * Create and inject theme toggle button if it doesn't exist
   */
  function createToggleButton() {
    // Check if toggle already exists
    if (document.querySelector('.theme-toggle')) {
      return;
    }

    const button = document.createElement('button');
    button.className = 'theme-toggle';
    button.setAttribute('aria-label', 'Toggle theme');
    button.setAttribute('title', 'Toggle dark/light mode');

    button.innerHTML = `
      <span class="theme-toggle-icon-light">☀️</span>
      <span class="theme-toggle-icon-dark">🌙</span>
    `;

    button.addEventListener('click', toggleTheme);

    document.body.appendChild(button);
  }

  // Create button when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createToggleButton);
  } else {
    createToggleButton();
  }

  // ==================== SYSTEM PREFERENCE LISTENER ====================

  /**
   * Listen for system theme changes
   */
  if (window.matchMedia) {
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

    darkModeQuery.addEventListener('change', function(e) {
      // Only auto-switch if user hasn't explicitly set a preference
      if (!localStorage.getItem('theme')) {
        applyTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  // ==================== PUBLIC API ====================

  // Expose theme functions globally
  window.themeSystem = {
    toggle: toggleTheme,
    setTheme: applyTheme,
    getTheme: function() {
      return document.documentElement.getAttribute('data-theme') || 'light';
    },
    isDark: function() {
      return this.getTheme() === 'dark';
    }
  };

  // ==================== BRAND COLOR INTEGRATION ====================

  /**
   * Auto-generate dark mode variants of brand colors
   * Desaturates and lightens colors for better dark mode appearance
   */
  function generateDarkModeColors() {
    const root = document.documentElement;
    const brandPrimary = getComputedStyle(root).getPropertyValue('--brand-primary').trim();

    if (brandPrimary && brandPrimary.startsWith('#')) {
      // Convert hex to HSL
      const hsl = hexToHSL(brandPrimary);

      // Lighten and desaturate for dark mode
      const darkPrimary = hslToHex(
        hsl.h,
        Math.min(hsl.s * 0.8, 80), // Reduce saturation
        Math.min(hsl.l + 15, 75)    // Increase lightness
      );

      root.style.setProperty('--brand-primary-dark', darkPrimary);
    }
  }

  /**
   * Convert hex color to HSL
   */
  function hexToHSL(hex) {
    // Convert hex to RGB
    let r = parseInt(hex.slice(1, 3), 16) / 255;
    let g = parseInt(hex.slice(3, 5), 16) / 255;
    let b = parseInt(hex.slice(5, 7), 16) / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;

    if (max === min) {
      h = s = 0;
    } else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

      switch (max) {
        case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
        case g: h = ((b - r) / d + 2) / 6; break;
        case b: h = ((r - g) / d + 4) / 6; break;
      }
    }

    return {
      h: Math.round(h * 360),
      s: Math.round(s * 100),
      l: Math.round(l * 100)
    };
  }

  /**
   * Convert HSL to hex
   */
  function hslToHex(h, s, l) {
    h = h / 360;
    s = s / 100;
    l = l / 100;

    let r, g, b;

    if (s === 0) {
      r = g = b = l;
    } else {
      const hue2rgb = (p, q, t) => {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1/6) return p + (q - p) * 6 * t;
        if (t < 1/2) return q;
        if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
        return p;
      };

      const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p = 2 * l - q;
      r = hue2rgb(p, q, h + 1/3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1/3);
    }

    const toHex = x => {
      const hex = Math.round(x * 255).toString(16);
      return hex.length === 1 ? '0' + hex : hex;
    };

    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  }

  // Generate dark mode colors on load
  window.addEventListener('load', generateDarkModeColors);

})();
