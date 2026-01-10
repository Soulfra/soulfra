/**
 * Soulfra Studio - Visual Development Environment
 *
 * Zero terminal required. All tools accessible via browser.
 *
 * Features:
 * - Neural network builder (drag-drop)
 * - Schema editor (JSON → Python)
 * - Ollama AI chat
 * - Live concept map
 * - Email builder
 * - Code generator
 * - Visual test runner with auto-loop
 */

// ==============================================================================
// WEBSOCKET CONNECTION
// ==============================================================================

const socket = io();

socket.on('connect', () => {
    console.log('🔌 Connected to Soulfra Studio');
    updateConnectionStatus(true);
});

socket.on('disconnect', () => {
    console.log('🔌 Disconnected from Soulfra Studio');
    updateConnectionStatus(false);
});

function updateConnectionStatus(connected) {
    const indicator = document.querySelector('.status-indicator');
    if (indicator) {
        indicator.className = 'status-indicator ' + (connected ? 'connected' : 'disconnected');
    }
}

// ==============================================================================
// TAB SWITCHING
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Sidebar navigation
    const sidebarIcons = document.querySelectorAll('.sidebar-icon');
    const panels = document.querySelectorAll('.panel');

    sidebarIcons.forEach(icon => {
        icon.addEventListener('click', () => {
            const panelId = icon.dataset.panel;

            // Update active icon
            sidebarIcons.forEach(i => i.classList.remove('active'));
            icon.classList.add('active');

            // Show selected panel
            panels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.id === panelId + '-panel') {
                    panel.classList.add('active');
                }
            });

            console.log(`📋 Switched to: ${panelId}`);
        });
    });

    // Initialize test runner
    initTestRunner();

    // Initialize Ollama chat
    initOllamaChat();

    // Initialize neural network builder
    initNeuralBuilder();

    // Initialize concept map
    initConceptMap();

    // Initialize Debug Lab (if function exists from debug_lab.js)
    if (typeof initDebugLab === 'function') {
        initDebugLab();
    }
});

// ==============================================================================
// TEST RUNNER - "how do we run all the tests"
// ==============================================================================

let autoLoopActive = false;
let testResults = {};

function initTestRunner() {
    const runAllBtn = document.getElementById('run-all-tests-btn');
    const autoLoopBtn = document.getElementById('auto-loop-btn');
    const testOutput = document.getElementById('test-output');

    if (runAllBtn) {
        runAllBtn.addEventListener('click', runAllTests);
    }

    if (autoLoopBtn) {
        autoLoopBtn.addEventListener('click', toggleAutoLoop);
    }

    // Listen for test events from server
    socket.on('test_started', (data) => {
        appendTestOutput(`\n🧪 Starting: ${data.test_name}\n`, 'info');
    });

    socket.on('test_output', (data) => {
        appendTestOutput(data.line, 'output');
    });

    socket.on('test_complete', (data) => {
        testResults[data.test_name] = data.passed;

        const icon = data.passed ? '✅' : '❌';
        const className = data.passed ? 'success' : 'error';

        appendTestOutput(`\n${icon} ${data.test_name}: ${data.passed ? 'PASSED' : 'FAILED'}\n`, className);

        if (data.error) {
            appendTestOutput(`Error: ${data.error}\n`, 'error');
        }

        updateTestList();
    });

    socket.on('all_tests_complete', (data) => {
        const allPassed = data.passed_count === data.total_count;

        appendTestOutput(`\n${'='.repeat(70)}\n`, 'info');
        appendTestOutput(`Results: ${data.passed_count}/${data.total_count} passed\n`, allPassed ? 'success' : 'error');
        appendTestOutput(`${'='.repeat(70)}\n\n`, 'info');

        if (autoLoopActive && !allPassed) {
            // Loop until all tests pass
            appendTestOutput('🔄 Auto-loop active, rerunning failed tests in 3s...\n\n', 'warning');
            setTimeout(runAllTests, 3000);
        } else if (autoLoopActive && allPassed) {
            appendTestOutput('🎉 All tests passed! Auto-loop stopped.\n\n', 'success');
            autoLoopActive = false;
            updateAutoLoopButton();
        }
    });

    // Load test list
    loadTestList();
}

function runAllTests() {
    const testOutput = document.getElementById('test-output');
    if (testOutput) {
        testOutput.value = ''; // Clear output
    }
    testResults = {};

    appendTestOutput('🚀 Running all tests...\n\n', 'info');

    socket.emit('run_all_tests');
}

function toggleAutoLoop() {
    autoLoopActive = !autoLoopActive;
    updateAutoLoopButton();

    if (autoLoopActive) {
        appendTestOutput('🔄 Auto-loop activated: Will run until all tests pass\n\n', 'warning');
        runAllTests();
    } else {
        appendTestOutput('⏸️ Auto-loop deactivated\n\n', 'info');
    }
}

function updateAutoLoopButton() {
    const btn = document.getElementById('auto-loop-btn');
    if (btn) {
        btn.textContent = autoLoopActive ? '⏸️ Stop Auto-Loop' : '🔄 Auto-Loop Until Pass';
        btn.style.background = autoLoopActive ? '#dc3545' : '#667eea';
    }
}

function appendTestOutput(text, className = '') {
    const testOutput = document.getElementById('test-output');
    if (!testOutput) return;

    testOutput.value += text;
    testOutput.scrollTop = testOutput.scrollHeight; // Auto-scroll to bottom
}

function loadTestList() {
    fetch('/api/studio/list-tests')
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById('test-list');
            if (!list) return;

            list.innerHTML = '';

            data.tests.forEach(test => {
                const item = document.createElement('div');
                item.className = 'test-item';
                item.innerHTML = `
                    <span class="test-name">${test}</span>
                    <button class="run-single-test-btn" data-test="${test}">▶️ Run</button>
                `;
                list.appendChild(item);

                // Add click handler
                const btn = item.querySelector('.run-single-test-btn');
                btn.addEventListener('click', () => runSingleTest(test));
            });
        })
        .catch(err => {
            console.error('Failed to load test list:', err);
        });
}

function runSingleTest(testName) {
    appendTestOutput(`\n🧪 Running: ${testName}\n`, 'info');
    socket.emit('run_single_test', { test_name: testName });
}

function updateTestList() {
    const items = document.querySelectorAll('.test-item');
    items.forEach(item => {
        const testName = item.querySelector('.test-name').textContent;
        const result = testResults[testName];

        if (result === true) {
            item.classList.add('passed');
            item.classList.remove('failed');
        } else if (result === false) {
            item.classList.add('failed');
            item.classList.remove('passed');
        }
    });
}

// ==============================================================================
// OLLAMA CHAT - "we have ollama and can build"
// ==============================================================================

function initOllamaChat() {
    const sendBtn = document.getElementById('ollama-send-btn');
    const input = document.getElementById('ollama-input');
    const messages = document.getElementById('ollama-messages');

    if (sendBtn && input) {
        sendBtn.addEventListener('click', sendOllamaMessage);

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendOllamaMessage();
            }
        });
    }

    // Listen for Ollama responses
    socket.on('ollama_response', (data) => {
        addChatMessage(data.response, 'assistant');
    });

    socket.on('ollama_error', (data) => {
        addChatMessage(`Error: ${data.error}`, 'error');
    });
}

function sendOllamaMessage() {
    const input = document.getElementById('ollama-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');

    // Clear input
    input.value = '';

    // Send to server
    socket.emit('ollama_chat', { message: message });
}

function addChatMessage(text, role) {
    const messages = document.getElementById('ollama-messages');
    if (!messages) return;

    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    div.textContent = text;

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

// ==============================================================================
// NEURAL NETWORK BUILDER - "build a neural network"
// ==============================================================================

let layers = [];
let nextLayerId = 1;

function initNeuralBuilder() {
    const addLayerBtn = document.getElementById('add-layer-btn');
    const trainBtn = document.getElementById('train-network-btn');
    const exportBtn = document.getElementById('export-network-btn');

    if (addLayerBtn) {
        addLayerBtn.addEventListener('click', addLayer);
    }

    if (trainBtn) {
        trainBtn.addEventListener('click', trainNetwork);
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', exportNetwork);
    }
}

function addLayer() {
    const type = document.getElementById('layer-type').value;
    const neurons = parseInt(document.getElementById('layer-neurons').value) || 64;
    const activation = document.getElementById('layer-activation').value;

    const layer = {
        id: nextLayerId++,
        type: type,
        neurons: neurons,
        activation: activation
    };

    layers.push(layer);
    renderLayers();
}

function renderLayers() {
    const canvas = document.getElementById('neural-canvas');
    if (!canvas) return;

    canvas.innerHTML = '';

    layers.forEach((layer, index) => {
        const div = document.createElement('div');
        div.className = 'neural-layer';
        div.innerHTML = `
            <div class="layer-info">
                <strong>${layer.type}</strong>
                <br>${layer.neurons} neurons
                <br>Activation: ${layer.activation}
            </div>
            <button class="remove-layer-btn" data-id="${layer.id}">🗑️</button>
        `;

        canvas.appendChild(div);

        // Add arrow if not last layer
        if (index < layers.length - 1) {
            const arrow = document.createElement('div');
            arrow.className = 'layer-arrow';
            arrow.textContent = '→';
            canvas.appendChild(arrow);
        }

        // Add remove handler
        const removeBtn = div.querySelector('.remove-layer-btn');
        removeBtn.addEventListener('click', () => removeLayer(layer.id));
    });
}

function removeLayer(layerId) {
    layers = layers.filter(l => l.id !== layerId);
    renderLayers();
}

function trainNetwork() {
    if (layers.length === 0) {
        alert('Add layers first!');
        return;
    }

    const config = {
        layers: layers,
        epochs: parseInt(document.getElementById('epochs').value) || 10,
        batch_size: parseInt(document.getElementById('batch-size').value) || 32
    };

    socket.emit('train_network', config);

    const output = document.getElementById('training-output');
    if (output) {
        output.value = '🚀 Training started...\n';
    }
}

function exportNetwork() {
    if (layers.length === 0) {
        alert('No network to export!');
        return;
    }

    const code = generatePythonCode(layers);

    // Download as .py file
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'neural_network.py';
    a.click();
}

function generatePythonCode(layers) {
    let code = '# Generated by Soulfra Studio\n';
    code += 'import torch\n';
    code += 'import torch.nn as nn\n\n';
    code += 'class GeneratedNetwork(nn.Module):\n';
    code += '    def __init__(self):\n';
    code += '        super().__init__()\n';

    layers.forEach((layer, i) => {
        if (layer.type === 'Dense') {
            const prevNeurons = i > 0 ? layers[i-1].neurons : 'input_size';
            code += `        self.layer${i} = nn.Linear(${prevNeurons}, ${layer.neurons})\n`;
        } else if (layer.type === 'Conv2D') {
            code += `        self.layer${i} = nn.Conv2d(in_channels, ${layer.neurons}, kernel_size=3)\n`;
        }
    });

    code += '\n    def forward(self, x):\n';
    layers.forEach((layer, i) => {
        code += `        x = self.layer${i}(x)\n`;
        if (layer.activation === 'relu') {
            code += `        x = torch.relu(x)\n`;
        } else if (layer.activation === 'sigmoid') {
            code += `        x = torch.sigmoid(x)\n`;
        }
    });
    code += '        return x\n';

    return code;
}

// ==============================================================================
// CONCEPT MAP - "interactive visualization"
// ==============================================================================

function initConceptMap() {
    const renderBtn = document.getElementById('render-map-btn');

    if (renderBtn) {
        renderBtn.addEventListener('click', renderConceptMap);
    }
}

function renderConceptMap() {
    // This would use D3.js to render the concept map
    // For now, just show a placeholder
    const mapDiv = document.getElementById('concept-map-canvas');
    if (!mapDiv) return;

    mapDiv.innerHTML = '<p style="text-align: center; padding: 50px;">🗺️ Concept map rendering with D3.js...</p>';

    // TODO: Implement D3.js visualization
    // See INFRASTRUCTURE_MAP.md for full example
}

// ==============================================================================
// UTILITY FUNCTIONS
// ==============================================================================

// Log all events for debugging
socket.onAny((eventName, ...args) => {
    console.log(`📡 ${eventName}:`, args);
});
