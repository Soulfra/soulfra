// Global Keyboard Shortcuts for Soulfra Development
// Usage: Include this script in any HTML page for consistent shortcuts

(function() {
    'use strict';

    // Shortcuts configuration
    const shortcuts = {
        // Voice control
        'Ctrl+Space': {
            description: 'Toggle voice input',
            handler: () => {
                const voiceBtn = document.getElementById('voiceBtn');
                if (voiceBtn) voiceBtn.click();
            }
        },

        // Text manipulation
        'Ctrl+K': {
            description: 'Clear text/input',
            handler: () => {
                const textarea = document.querySelector('textarea');
                const input = document.querySelector('input[type="text"]');
                if (textarea) {
                    textarea.value = '';
                    textarea.focus();
                } else if (input) {
                    input.value = '';
                    input.focus();
                }
            }
        },

        // Navigation
        'Ctrl+H': {
            description: 'Go to home/dashboard',
            handler: () => {
                window.location.href = '/';
            }
        },

        'Ctrl+D': {
            description: 'Go to domains page',
            handler: () => {
                window.location.href = '/domains.html';
            }
        },

        // Development
        'Ctrl+Shift+R': {
            description: 'Hard reload page',
            handler: () => {
                location.reload(true);
            }
        },

        'Ctrl+Shift+I': {
            description: 'Open browser dev tools',
            // Native browser shortcut - no handler needed
            handler: null
        },

        // Clipboard
        'Ctrl+Shift+C': {
            description: 'Copy all text',
            handler: () => {
                const textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.select();
                    document.execCommand('copy');
                    showNotification('📋 Copied to clipboard');
                }
            }
        },

        // Help
        'Ctrl+/': {
            description: 'Show keyboard shortcuts',
            handler: showShortcutsHelp
        }
    };

    // Parse key combination
    function parseKey(e) {
        const parts = [];
        if (e.ctrlKey) parts.push('Ctrl');
        if (e.shiftKey) parts.push('Shift');
        if (e.altKey) parts.push('Alt');
        if (e.metaKey) parts.push('Meta');

        // Get key name
        let key = e.key;
        if (key === ' ') key = 'Space';
        if (key.length === 1) key = key.toUpperCase();

        parts.push(key);
        return parts.join('+');
    }

    // Global keydown listener
    document.addEventListener('keydown', (e) => {
        const combo = parseKey(e);
        const shortcut = shortcuts[combo];

        if (shortcut && shortcut.handler) {
            e.preventDefault();
            shortcut.handler();
        }
    });

    // Show notification helper
    function showNotification(message, duration = 2000) {
        // Check if notification element exists
        let notification = document.getElementById('global-notification');

        if (!notification) {
            // Create notification element
            notification = document.createElement('div');
            notification.id = 'global-notification';
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(16, 185, 129, 0.95);
                color: white;
                padding: 15px 25px;
                border-radius: 10px;
                font-size: 1.1em;
                font-weight: bold;
                z-index: 10000;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(notification);
        }

        notification.textContent = message;
        notification.style.opacity = '1';

        setTimeout(() => {
            notification.style.opacity = '0';
        }, duration);
    }

    // Show shortcuts help modal
    function showShortcutsHelp() {
        // Remove existing modal if present
        const existing = document.getElementById('shortcuts-modal');
        if (existing) {
            existing.remove();
            return;
        }

        // Create modal
        const modal = document.createElement('div');
        modal.id = 'shortcuts-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 20000;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            padding: 30px;
            border-radius: 15px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            color: #1f2937;
        `;

        let html = '<h2 style="margin-bottom: 20px;">⌨️ Keyboard Shortcuts</h2>';
        html += '<table style="width: 100%; border-collapse: collapse;">';

        for (const [combo, info] of Object.entries(shortcuts)) {
            html += `
                <tr style="border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 10px; font-family: monospace; background: #f3f4f6;">
                        ${combo.replace(/\+/g, ' + ')}
                    </td>
                    <td style="padding: 10px;">
                        ${info.description}
                    </td>
                </tr>
            `;
        }

        html += '</table>';
        html += '<p style="margin-top: 20px; text-align: center; color: #6b7280;">Press <kbd style="background: #e5e7eb; padding: 2px 6px; border-radius: 3px;">Ctrl+/</kbd> again to close</p>';

        content.innerHTML = html;
        modal.appendChild(content);
        document.body.appendChild(modal);

        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    // Expose global API
    window.Soulfra = window.Soulfra || {};
    window.Soulfra.shortcuts = {
        show: showShortcutsHelp,
        notify: showNotification,
        add: (combo, description, handler) => {
            shortcuts[combo] = { description, handler };
        }
    };

    console.log('⌨️ Soulfra keyboard shortcuts loaded. Press Ctrl+/ for help.');
})();
