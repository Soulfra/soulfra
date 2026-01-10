/**
 * Pixel Layer Compositor
 * Visual diffusion-style layer blending with CRT color modes
 */

// State
let layers = [];
let activeLayerIndex = 0;
let currentTool = 'pen';
let currentColor = '#00ff00';
let brushSize = 4;
let crtMode = 'rainbow';
let isDrawing = false;
let lastX = 0;
let lastY = 0;

// Canvas elements
const mainCanvas = document.getElementById('mainCanvas');
const mainCtx = mainCanvas.getContext('2d', { willReadFrequently: true });
const pixelGrid = document.getElementById('pixelGrid');
const gridCtx = pixelGrid.getContext('2d');

// Initialize
function init() {
    // Add initial layer
    addLayer();

    // Draw pixel grid
    drawPixelGrid();

    // Set up canvas events
    mainCanvas.addEventListener('mousedown', startDrawing);
    mainCanvas.addEventListener('mousemove', draw);
    mainCanvas.addEventListener('mouseup', stopDrawing);
    mainCanvas.addEventListener('mouseleave', stopDrawing);

    // Touch support
    mainCanvas.addEventListener('touchstart', handleTouch);
    mainCanvas.addEventListener('touchmove', handleTouch);
    mainCanvas.addEventListener('touchend', stopDrawing);

    console.log('🎨 Pixel Compositor initialized');
}

// Layer Management
function addLayer() {
    const canvas = document.createElement('canvas');
    canvas.width = mainCanvas.width;
    canvas.height = mainCanvas.height;
    const ctx = canvas.getContext('2d');

    const layer = {
        id: Date.now(),
        name: `Layer ${layers.length + 1}`,
        canvas: canvas,
        ctx: ctx,
        opacity: 1.0,
        blendMode: 'source-over',
        visible: true
    };

    layers.push(layer);
    activeLayerIndex = layers.length - 1;

    renderLayerStack();
    updateStats();
    compositeAll();
}

function removeLayer(index) {
    if (layers.length <= 1) {
        alert('Cannot remove the last layer');
        return;
    }

    layers.splice(index, 1);
    if (activeLayerIndex >= layers.length) {
        activeLayerIndex = layers.length - 1;
    }

    renderLayerStack();
    updateStats();
    compositeAll();
}

function setActiveLayer(index) {
    activeLayerIndex = index;
    renderLayerStack();
    updateStats();
}

function renderLayerStack() {
    const stackEl = document.getElementById('layerStack');
    stackEl.innerHTML = '';

    // Render in reverse order (top layer first)
    for (let i = layers.length - 1; i >= 0; i--) {
        const layer = layers[i];
        const isActive = i === activeLayerIndex;

        const layerEl = document.createElement('div');
        layerEl.className = `layer${isActive ? ' active' : ''}`;
        layerEl.onclick = () => setActiveLayer(i);

        layerEl.innerHTML = `
            <div class="layer-name">
                ${layer.name}
                ${layer.visible ? '👁️' : '🚫'}
            </div>
            <div class="layer-controls">
                <input type="range"
                       min="0"
                       max="1"
                       step="0.1"
                       value="${layer.opacity}"
                       onchange="updateLayerOpacity(${i}, this.value)"
                       onclick="event.stopPropagation()">
                <select onchange="updateLayerBlend(${i}, this.value)"
                        onclick="event.stopPropagation()">
                    <option value="source-over" ${layer.blendMode === 'source-over' ? 'selected' : ''}>Normal</option>
                    <option value="multiply" ${layer.blendMode === 'multiply' ? 'selected' : ''}>Multiply</option>
                    <option value="screen" ${layer.blendMode === 'screen' ? 'selected' : ''}>Screen</option>
                    <option value="overlay" ${layer.blendMode === 'overlay' ? 'selected' : ''}>Overlay</option>
                    <option value="difference" ${layer.blendMode === 'difference' ? 'selected' : ''}>Difference</option>
                    <option value="lighten" ${layer.blendMode === 'lighten' ? 'selected' : ''}>Lighten</option>
                    <option value="darken" ${layer.blendMode === 'darken' ? 'selected' : ''}>Darken</option>
                </select>
            </div>
            <button onclick="toggleLayerVisibility(${i}); event.stopPropagation();"
                    style="padding: 5px; margin-top: 5px; font-size: 0.8rem;">
                ${layer.visible ? 'Hide' : 'Show'}
            </button>
            ${layers.length > 1 ? `
                <button onclick="removeLayer(${i}); event.stopPropagation();"
                        style="padding: 5px; margin-top: 5px; font-size: 0.8rem; background: #aa0000;">
                    Delete
                </button>
            ` : ''}
        `;

        stackEl.appendChild(layerEl);
    }
}

function updateLayerOpacity(index, opacity) {
    layers[index].opacity = parseFloat(opacity);
    compositeAll();
}

function updateLayerBlend(index, blendMode) {
    layers[index].blendMode = blendMode;
    compositeAll();
}

function toggleLayerVisibility(index) {
    layers[index].visible = !layers[index].visible;
    renderLayerStack();
    compositeAll();
}

// Drawing
function startDrawing(e) {
    isDrawing = true;
    const rect = mainCanvas.getBoundingClientRect();
    lastX = e.clientX - rect.left;
    lastY = e.clientY - rect.top;

    if (currentTool === 'fill') {
        floodFill(lastX, lastY);
    } else if (currentTool === 'eyedropper') {
        pickColor(lastX, lastY);
    }
}

function draw(e) {
    if (!isDrawing) return;

    const rect = mainCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const ctx = layers[activeLayerIndex].ctx;

    if (currentTool === 'pen') {
        drawLine(ctx, lastX, lastY, x, y, currentColor, brushSize);
    } else if (currentTool === 'eraser') {
        drawLine(ctx, lastX, lastY, x, y, 'rgba(0,0,0,0)', brushSize, true);
    }

    lastX = x;
    lastY = y;

    compositeAll();
}

function stopDrawing() {
    isDrawing = false;
}

function handleTouch(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent(e.type === 'touchstart' ? 'mousedown' : 'mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    mainCanvas.dispatchEvent(mouseEvent);
}

function drawLine(ctx, x1, y1, x2, y2, color, size, erase = false) {
    if (erase) {
        ctx.globalCompositeOperation = 'destination-out';
    } else {
        ctx.globalCompositeOperation = 'source-over';
    }

    ctx.strokeStyle = color;
    ctx.lineWidth = size;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();

    ctx.globalCompositeOperation = 'source-over';
}

function floodFill(x, y) {
    const ctx = layers[activeLayerIndex].ctx;
    const imageData = ctx.getImageData(0, 0, mainCanvas.width, mainCanvas.height);
    const targetColor = getPixelColor(imageData, Math.floor(x), Math.floor(y));
    const fillColor = hexToRgb(currentColor);

    if (colorsMatch(targetColor, fillColor)) return;

    const stack = [[Math.floor(x), Math.floor(y)]];

    while (stack.length > 0) {
        const [px, py] = stack.pop();

        if (px < 0 || px >= mainCanvas.width || py < 0 || py >= mainCanvas.height) continue;

        const currentColor = getPixelColor(imageData, px, py);
        if (!colorsMatch(currentColor, targetColor)) continue;

        setPixelColor(imageData, px, py, fillColor);

        stack.push([px + 1, py], [px - 1, py], [px, py + 1], [px, py - 1]);
    }

    ctx.putImageData(imageData, 0, 0);
    compositeAll();
}

function pickColor(x, y) {
    const ctx = layers[activeLayerIndex].ctx;
    const imageData = ctx.getImageData(Math.floor(x), Math.floor(y), 1, 1);
    const [r, g, b] = imageData.data;

    currentColor = rgbToHex(r, g, b);
    document.getElementById('brushColor').value = currentColor;
}

// Color utilities
function getPixelColor(imageData, x, y) {
    const index = (y * imageData.width + x) * 4;
    return [
        imageData.data[index],
        imageData.data[index + 1],
        imageData.data[index + 2],
        imageData.data[index + 3]
    ];
}

function setPixelColor(imageData, x, y, [r, g, b, a = 255]) {
    const index = (y * imageData.width + x) * 4;
    imageData.data[index] = r;
    imageData.data[index + 1] = g;
    imageData.data[index + 2] = b;
    imageData.data[index + 3] = a;
}

function colorsMatch([r1, g1, b1], [r2, g2, b2]) {
    return r1 === r2 && g1 === g2 && b1 === b2;
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16),
        255
    ] : [0, 0, 0, 255];
}

function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

// Compositing
function compositeAll() {
    // Clear main canvas
    mainCtx.clearRect(0, 0, mainCanvas.width, mainCanvas.height);

    // Composite layers from bottom to top
    for (let i = 0; i < layers.length; i++) {
        const layer = layers[i];
        if (!layer.visible) continue;

        mainCtx.globalAlpha = layer.opacity;
        mainCtx.globalCompositeOperation = layer.blendMode;
        mainCtx.drawImage(layer.canvas, 0, 0);
    }

    // Reset
    mainCtx.globalAlpha = 1.0;
    mainCtx.globalCompositeOperation = 'source-over';
}

// CRT Effects
function setCRTMode(mode) {
    crtMode = mode;

    // Update active state
    document.querySelectorAll('.color-mode').forEach(el => {
        el.classList.toggle('active', el.dataset.mode === mode);
    });

    // Apply CSS class
    const container = document.getElementById('canvasContainer');
    container.className = 'canvas-container crt-' + mode;

    updateCRTEffects();
}

function updateCRTEffects() {
    const brightness = document.getElementById('brightness').value;
    const contrast = document.getElementById('contrast').value;

    document.getElementById('brightnessValue').textContent = brightness;
    document.getElementById('contrastValue').textContent = contrast;

    const canvas = mainCanvas;
    let filter = `brightness(${brightness}%) contrast(${contrast}%)`;

    switch (crtMode) {
        case 'rainbow':
            filter += ' saturate(150%) hue-rotate(0deg)';
            break;
        case 'bw':
            filter += ' grayscale(100%)';
            break;
        case 'grey':
            filter += ' grayscale(100%)';
            break;
        case 'white':
            filter += ' invert(1) sepia(1) saturate(5) hue-rotate(20deg)';
            break;
    }

    canvas.style.filter = filter;
}

// Tools
function setTool(tool) {
    currentTool = tool;
    document.querySelectorAll('.tool').forEach(el => {
        el.classList.toggle('active', el.dataset.tool === tool);
    });
}

function updateBrushSize() {
    brushSize = parseInt(document.getElementById('brushSize').value);
    document.getElementById('brushSizeValue').textContent = brushSize;
}

// Pixel Grid
function drawPixelGrid() {
    const gridSize = 16; // 16x16 pixel grid
    gridCtx.strokeStyle = 'rgba(0, 255, 0, 0.2)';
    gridCtx.lineWidth = 1;

    for (let x = 0; x <= mainCanvas.width; x += gridSize) {
        gridCtx.beginPath();
        gridCtx.moveTo(x, 0);
        gridCtx.lineTo(x, mainCanvas.height);
        gridCtx.stroke();
    }

    for (let y = 0; y <= mainCanvas.height; y += gridSize) {
        gridCtx.beginPath();
        gridCtx.moveTo(0, y);
        gridCtx.lineTo(mainCanvas.width, y);
        gridCtx.stroke();
    }
}

function toggleGrid() {
    const grid = document.getElementById('pixelGrid');
    const toggle = document.getElementById('gridToggle');
    grid.style.display = toggle.checked ? 'block' : 'none';
}

// Utilities
function clearCanvas() {
    if (!confirm('Clear the active layer?')) return;
    layers[activeLayerIndex].ctx.clearRect(0, 0, mainCanvas.width, mainCanvas.height);
    compositeAll();
}

function updateStats() {
    document.getElementById('layerCount').textContent = layers.length;
    document.getElementById('activeLayer').textContent = layers[activeLayerIndex]?.name || 'None';
}

function composeAll() {
    console.log('🎬 Compositing all layers...');
    console.log(`  Layers: ${layers.length}`);
    console.log(`  CRT Mode: ${crtMode}`);
    console.log(`  Blend Modes: ${layers.map(l => l.blendMode).join(', ')}`);

    // TODO: Send to backend for server-side compositing
    // For now, client-side compositing is sufficient
    compositeAll();

    alert(`✅ Composite rendered!\n\nLayers: ${layers.length}\nCRT Mode: ${crtMode.toUpperCase()}\nCanvas: ${mainCanvas.width}x${mainCanvas.height}`);
}

function exportPNG() {
    mainCanvas.toBlob(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pixel-art-${Date.now()}.png`;
        a.click();
        URL.revokeObjectURL(url);
    });
}

function exportGIF() {
    alert('🎬 GIF export coming soon!\n\nFor now, use PNG export or screenshot the animation timeline.');
    // TODO: Implement GIF encoding with animation frames
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);

// Update brush color on color picker change
document.getElementById('brushColor')?.addEventListener('change', (e) => {
    currentColor = e.target.value;
});
