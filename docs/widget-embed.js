/**
 * Soulfra Embeddable Widget
 *
 * Usage:
 *   <script src="https://YOUR_USERNAME.github.io/YOUR_REPO/widget-embed.js"></script>
 *   <div id="soulfra-widget" data-brand="deathtodata"></div>
 *
 * Options:
 *   data-brand: "deathtodata" | "soulfra" | "calriven"
 *   data-width: Width in pixels (default: "400px")
 *   data-height: Height in pixels (default: "600px")
 */

(function() {
  'use strict';

  const WIDGET_BASE_URL = 'https://YOUR_USERNAME.github.io/YOUR_REPO';

  function initSoulfraWidget() {
    const containers = document.querySelectorAll('#soulfra-widget');

    containers.forEach(container => {
      const brand = container.getAttribute('data-brand') || 'soulfra';
      const width = container.getAttribute('data-width') || '400px';
      const height = container.getAttribute('data-height') || '600px';

      // Create iframe
      const iframe = document.createElement('iframe');
      iframe.src = `${WIDGET_BASE_URL}/widget.html?brand=${brand}`;
      iframe.style.width = width;
      iframe.style.height = height;
      iframe.style.border = '1px solid #ccc';
      iframe.style.borderRadius = '8px';
      iframe.setAttribute('frameborder', '0');
      iframe.setAttribute('allowtransparency', 'true');

      // Replace container with iframe
      container.appendChild(iframe);

      console.log(`[Soulfra Widget] Loaded ${brand} widget`);
    });
  }

  // Auto-initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSoulfraWidget);
  } else {
    initSoulfraWidget();
  }

  // Expose for manual initialization
  window.SoulfraWidget = {
    init: initSoulfraWidget
  };
})();
