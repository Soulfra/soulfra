/**
 * Circular Color Wheel Picker
 *
 * Replaces default square <input type="color"> with a circular HSV color wheel
 * that respects border-radius styling and provides a better personality test UX
 */

class CircularColorPicker {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`Canvas with ID "${canvasId}" not found`);
            return;
        }

        this.ctx = this.canvas.getContext('2d');
        this.size = options.size || 200;
        this.selectedColor = options.defaultColor || '#667eea';
        this.onChange = options.onChange || (() => {});

        // Set canvas size
        this.canvas.width = this.size;
        this.canvas.height = this.size;
        this.radius = this.size / 2;

        // State
        this.isDragging = false;

        // Initialize
        this.draw();
        this.attachEvents();
    }

    /**
     * Draw the circular color wheel
     */
    draw() {
        const centerX = this.radius;
        const centerY = this.radius;

        // Clear canvas
        this.ctx.clearRect(0, 0, this.size, this.size);

        // Draw color wheel (HSV space)
        for (let angle = 0; angle < 360; angle += 1) {
            const startAngle = (angle - 90) * Math.PI / 180;
            const endAngle = (angle + 1 - 90) * Math.PI / 180;

            // Create gradient from center (white) to edge (saturated color)
            const gradient = this.ctx.createRadialGradient(
                centerX, centerY, 0,
                centerX, centerY, this.radius
            );

            const color = this.hsvToRgb(angle, 1, 1);
            gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
            gradient.addColorStop(0.7, `rgb(${color.r}, ${color.g}, ${color.b})`);
            gradient.addColorStop(1, `rgb(${color.r}, ${color.g}, ${color.b})`);

            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();
            this.ctx.moveTo(centerX, centerY);
            this.ctx.arc(centerX, centerY, this.radius, startAngle, endAngle);
            this.ctx.closePath();
            this.ctx.fill();
        }

        // Draw selection indicator
        this.drawSelector();
    }

    /**
     * Draw selector at selected color position
     */
    drawSelector() {
        const hsv = this.hexToHsv(this.selectedColor);
        const angle = (hsv.h - 90) * Math.PI / 180;
        const distance = (hsv.s * this.radius * 0.7); // Map saturation to distance from center

        const x = this.radius + Math.cos(angle) * distance;
        const y = this.radius + Math.sin(angle) * distance;

        // Draw white circle with black border
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 3;
        this.ctx.fillStyle = '#fff';
        this.ctx.beginPath();
        this.ctx.arc(x, y, 8, 0, 2 * Math.PI);
        this.ctx.fill();
        this.ctx.stroke();

        // Draw inner dot with selected color
        this.ctx.fillStyle = this.selectedColor;
        this.ctx.beginPath();
        this.ctx.arc(x, y, 5, 0, 2 * Math.PI);
        this.ctx.fill();
    }

    /**
     * Handle mouse/touch events
     */
    attachEvents() {
        const handleMove = (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX || e.touches[0].clientX) - rect.left;
            const y = (e.clientY || e.touches[0].clientY) - rect.top;

            this.updateColor(x, y);
        };

        this.canvas.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            handleMove(e);
        });

        this.canvas.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                handleMove(e);
            }
        });

        this.canvas.addEventListener('mouseup', () => {
            this.isDragging = false;
        });

        this.canvas.addEventListener('mouseleave', () => {
            this.isDragging = false;
        });

        // Touch support
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.isDragging = true;
            handleMove(e);
        });

        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (this.isDragging) {
                handleMove(e);
            }
        });

        this.canvas.addEventListener('touchend', () => {
            this.isDragging = false;
        });
    }

    /**
     * Update selected color based on click/drag position
     */
    updateColor(x, y) {
        const centerX = this.radius;
        const centerY = this.radius;

        // Calculate angle (hue)
        const dx = x - centerX;
        const dy = y - centerY;
        let angle = Math.atan2(dy, dx) * 180 / Math.PI + 90;
        if (angle < 0) angle += 360;

        // Calculate distance (saturation)
        const distance = Math.sqrt(dx * dx + dy * dy);
        const saturation = Math.min(distance / (this.radius * 0.7), 1);

        // Check if click is within circle
        if (distance > this.radius) {
            return; // Outside circle
        }

        // Convert HSV to RGB to Hex
        const rgb = this.hsvToRgb(angle, saturation, 1);
        this.selectedColor = this.rgbToHex(rgb.r, rgb.g, rgb.b);

        // Redraw
        this.draw();

        // Trigger callback
        this.onChange(this.selectedColor);
    }

    /**
     * Get current selected color
     */
    getColor() {
        return this.selectedColor;
    }

    /**
     * Set color programmatically
     */
    setColor(hex) {
        this.selectedColor = hex;
        this.draw();
    }

    /**
     * Convert HSV to RGB
     */
    hsvToRgb(h, s, v) {
        h = h / 60;
        const c = v * s;
        const x = c * (1 - Math.abs((h % 2) - 1));
        const m = v - c;

        let r, g, b;
        if (h < 1) { r = c; g = x; b = 0; }
        else if (h < 2) { r = x; g = c; b = 0; }
        else if (h < 3) { r = 0; g = c; b = x; }
        else if (h < 4) { r = 0; g = x; b = c; }
        else if (h < 5) { r = x; g = 0; b = c; }
        else { r = c; g = 0; b = x; }

        return {
            r: Math.round((r + m) * 255),
            g: Math.round((g + m) * 255),
            b: Math.round((b + m) * 255)
        };
    }

    /**
     * Convert RGB to Hex
     */
    rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }

    /**
     * Convert Hex to HSV
     */
    hexToHsv(hex) {
        // Convert hex to RGB
        const r = parseInt(hex.slice(1, 3), 16) / 255;
        const g = parseInt(hex.slice(3, 5), 16) / 255;
        const b = parseInt(hex.slice(5, 7), 16) / 255;

        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const delta = max - min;

        let h = 0;
        if (delta !== 0) {
            if (max === r) {
                h = 60 * (((g - b) / delta) % 6);
            } else if (max === g) {
                h = 60 * ((b - r) / delta + 2);
            } else {
                h = 60 * ((r - g) / delta + 4);
            }
        }
        if (h < 0) h += 360;

        const s = max === 0 ? 0 : delta / max;
        const v = max;

        return { h, s, v };
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CircularColorPicker;
}
