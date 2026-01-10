/**
 * Debug Lab - Interactive Learning Environment
 *
 * Teaches debugging, log searching, and Linux commands through:
 * - Live log viewer
 * - Error explanation (Ollama-powered)
 * - Command teaching
 * - Gamified challenges
 */

// ==============================================================================
// INITIALIZATION
// ==============================================================================

function initDebugLab() {
    console.log('🔍 Initializing Debug Lab...');

    initLogViewer();
    initErrorExplainer();
    initCommandTeacher();
    initChallengeSystem();
}

// ==============================================================================
// LIVE LOG VIEWER
// ==============================================================================

let logAutoScroll = true;

function initLogViewer() {
    const refreshBtn = document.getElementById('debug-refresh-logs');
    const clearBtn = document.getElementById('debug-clear-logs');
    const searchInput = document.getElementById('debug-log-search');
    const filterSelect = document.getElementById('debug-log-filter');

    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadLogs);
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', clearLogView);
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            loadLogs(e.target.value);
        });
    }

    if (filterSelect) {
        filterSelect.addEventListener('change', (e) => {
            loadLogs(null, e.target.value);
        });
    }

    // Load logs on init
    loadLogs();

    // Listen for live log events from WebSocket
    socket.on('log_line', (data) => {
        appendLogLine(data);
    });
}

function loadLogs(searchPattern = null, level = null) {
    const searchInput = document.getElementById('debug-log-search');
    const filterSelect = document.getElementById('debug-log-filter');

    searchPattern = searchPattern || (searchInput ? searchInput.value : '');
    level = level || (filterSelect ? filterSelect.value : '');

    let url = '/api/debug/logs/recent?limit=100';
    if (searchPattern) {
        url += `&pattern=${encodeURIComponent(searchPattern)}`;
    }
    if (level && level !== 'all') {
        url += `&level=${level}`;
    }

    fetch(url)
        .then(res => res.json())
        .then(data => {
            displayLogs(data.logs);
            showEquivalentCommand(data.command, data.tutorial);
        })
        .catch(err => {
            console.error('Failed to load logs:', err);
        });
}

function displayLogs(logs) {
    const container = document.getElementById('debug-log-viewer');
    if (!container) return;

    container.innerHTML = '';

    logs.forEach(log => {
        const line = document.createElement('div');
        line.className = `log-line log-${log.level}`;
        line.innerHTML = `
            <span class="log-timestamp">${formatTimestamp(log.timestamp)}</span>
            <span class="log-content">${escapeHtml(log.line)}</span>
            <button class="log-explain-btn" data-error="${escapeHtml(log.line)}">
                🤖 Explain
            </button>
        `;

        // Add explain button handler
        const explainBtn = line.querySelector('.log-explain-btn');
        explainBtn.addEventListener('click', () => {
            explainError(log.line);
        });

        container.appendChild(line);
    });

    if (logAutoScroll) {
        container.scrollTop = container.scrollHeight;
    }
}

function appendLogLine(log) {
    const container = document.getElementById('debug-log-viewer');
    if (!container) return;

    const line = document.createElement('div');
    line.className = `log-line log-${log.level}`;
    line.innerHTML = `
        <span class="log-timestamp">${formatTimestamp(log.timestamp)}</span>
        <span class="log-content">${escapeHtml(log.line)}</span>
        <button class="log-explain-btn" data-error="${escapeHtml(log.line)}">🤖 Explain</button>
    `;

    container.appendChild(line);

    if (logAutoScroll) {
        container.scrollTop = container.scrollHeight;
    }
}

function clearLogView() {
    const container = document.getElementById('debug-log-viewer');
    if (container) {
        container.innerHTML = '<div class="log-line">Logs cleared. Refresh to reload.</div>';
    }
}

function showEquivalentCommand(command, tutorial) {
    const commandBox = document.getElementById('debug-equivalent-command');
    if (commandBox) {
        commandBox.innerHTML = `
            <strong>💻 Equivalent Linux command:</strong>
            <code>${command}</code>
            <br>
            <small>${tutorial}</small>
        `;
    }
}

// ==============================================================================
// ERROR EXPLAINER (OLLAMA-POWERED)
// ==============================================================================

function initErrorExplainer() {
    const explainBtn = document.getElementById('debug-explain-btn');
    const errorInput = document.getElementById('debug-error-input');

    if (explainBtn && errorInput) {
        explainBtn.addEventListener('click', () => {
            const error = errorInput.value;
            explainError(error);
        });
    }
}

function explainError(error) {
    if (!error) return;

    const resultDiv = document.getElementById('debug-explanation-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="loading">🤖 Asking Ollama to explain...</div>';
    }

    fetch('/api/debug/explain', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({error: error})
    })
        .then(res => res.json())
        .then(data => {
            displayExplanation(data);
        })
        .catch(err => {
            if (resultDiv) {
                resultDiv.innerHTML = `<div class="error">❌ Error: ${err.message}</div>`;
            }
        });
}

function displayExplanation(data) {
    const resultDiv = document.getElementById('debug-explanation-result');
    if (!resultDiv) return;

    let html = '<div class="explanation">';
    html += `<h3>🤖 Ollama's Explanation</h3>`;
    html += `<div class="explanation-text">${formatMarkdown(data.explanation)}</div>`;

    if (data.debug_steps && data.debug_steps.length > 0) {
        html += '<h4>📋 Debug Steps:</h4><ul>';
        data.debug_steps.forEach(step => {
            html += `<li>${escapeHtml(step)}</li>`;
        });
        html += '</ul>';
    }

    if (data.linux_commands && data.linux_commands.length > 0) {
        html += '<h4>💻 Try These Commands:</h4>';
        data.linux_commands.forEach(cmd => {
            html += `<div class="command-suggestion">
                <code>${escapeHtml(cmd.command)}</code>
                <button class="run-command-btn" data-command="${escapeHtml(cmd.command)}">▶️ Run</button>
            </div>`;
        });
    }

    html += '</div>';

    resultDiv.innerHTML = html;

    // Add run command button handlers
    resultDiv.querySelectorAll('.run-command-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const command = btn.dataset.command;
            runCommand(command);
        });
    });
}

// ==============================================================================
// COMMAND TEACHER
// ==============================================================================

function initCommandTeacher() {
    const grepBtn = document.getElementById('debug-teach-grep');
    const curlBtn = document.getElementById('debug-teach-curl');
    const tailBtn = document.getElementById('debug-teach-tail');

    if (grepBtn) {
        grepBtn.addEventListener('click', () => teachCommand('grep'));
    }

    if (curlBtn) {
        curlBtn.addEventListener('click', () => teachCommand('curl'));
    }

    if (tailBtn) {
        tailBtn.addEventListener('click', () => teachCommand('tail'));
    }
}

function teachCommand(commandType) {
    const teachings = {
        grep: {
            title: '🔍 grep - Search Text Patterns',
            description: 'grep searches for patterns in files. Essential for log analysis!',
            examples: [
                {cmd: 'grep "error" app.log', desc: 'Find all lines with "error"'},
                {cmd: 'grep -i "ERROR" app.log', desc: 'Case-insensitive search'},
                {cmd: 'grep -r "TODO" .', desc: 'Recursively search all files'},
                {cmd: 'grep -n "function" script.py', desc: 'Show line numbers'},
                {cmd: 'grep -A 5 "error" log', desc: 'Show 5 lines after match'}
            ],
            practice: 'Try searching the logs above for "302" to find redirects!'
        },
        curl: {
            title: '🌐 curl - Transfer Data with URLs',
            description: 'curl makes HTTP requests from command line. Perfect for API testing!',
            examples: [
                {cmd: 'curl http://localhost:5001/api/studio/list-tests', desc: 'GET request'},
                {cmd: 'curl -X POST -d "data=value" /api/endpoint', desc: 'POST request'},
                {cmd: 'curl -v http://example.com', desc: 'Verbose output (headers)'},
                {cmd: 'curl -c cookies.txt /login', desc: 'Save cookies'},
                {cmd: 'curl -b cookies.txt /admin', desc: 'Send cookies'}
            ],
            practice: 'Try: curl http://localhost:5001/api/debug/challenges'
        },
        tail: {
            title: '📜 tail - View End of Files',
            description: 'tail shows the last lines of files. Use -f to follow live updates!',
            examples: [
                {cmd: 'tail -100 app.log', desc: 'Last 100 lines'},
                {cmd: 'tail -f app.log', desc: 'Follow file (live updates)'},
                {cmd: 'tail -f log | grep ERROR', desc: 'Follow + filter errors'},
                {cmd: 'tail -n 50 log', desc: 'Last 50 lines'},
                {cmd: 'tail -f log | grep --color "fail"', desc: 'Highlight matches'}
            ],
            practice: 'Tail commands work best in a real terminal - try one!'
        }
    };

    const teaching = teachings[commandType];
    if (!teaching) return;

    const panel = document.getElementById('debug-command-tutorial');
    if (!panel) return;

    let html = `<h3>${teaching.title}</h3>`;
    html += `<p>${teaching.description}</p>`;
    html += '<div class="command-examples">';

    teaching.examples.forEach(ex => {
        html += `<div class="command-example">
            <code>${escapeHtml(ex.cmd)}</code>
            <p>${ex.desc}</p>
        </div>`;
    });

    html += '</div>';
    html += `<div class="practice-box">💪 <strong>Practice:</strong> ${teaching.practice}</div>`;

    panel.innerHTML = html;
}

// ==============================================================================
// CHALLENGE SYSTEM
// ==============================================================================

let currentChallenges = [];
let currentChallengeIndex = 0;

function initChallengeSystem() {
    loadChallenges();

    const nextBtn = document.getElementById('debug-challenge-next');
    const prevBtn = document.getElementById('debug-challenge-prev');
    const completeBtn = document.getElementById('debug-challenge-complete');

    if (nextBtn) {
        nextBtn.addEventListener('click', () => navigateChallenge(1));
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => navigateChallenge(-1));
    }

    if (completeBtn) {
        completeBtn.addEventListener('click', completeCurrentChallenge);
    }
}

function loadChallenges() {
    fetch('/api/debug/challenges')
        .then(res => res.json())
        .then(data => {
            currentChallenges = data.challenges;
            displayCurrentChallenge();
        })
        .catch(err => {
            console.error('Failed to load challenges:', err);
        });
}

function displayCurrentChallenge() {
    if (currentChallenges.length === 0) return;

    const challenge = currentChallenges[currentChallengeIndex];
    const container = document.getElementById('debug-challenge-view');

    if (!container) return;

    let html = `
        <div class="challenge-header">
            <h2>${challenge.title}</h2>
            <span class="challenge-level ${challenge.level}">${challenge.level}</span>
            <span class="challenge-time">⏱️ ${challenge.estimated_time}</span>
        </div>

        <p class="challenge-description">${challenge.description}</p>

        <h4>📋 Tasks:</h4>
        <ul class="challenge-tasks">
            ${challenge.tasks.map(task => `<li>${task}</li>`).join('')}
        </ul>

        <details class="challenge-hints">
            <summary>💡 Show Hints</summary>
            <ul>
                ${challenge.hints.map(hint => `<li>${hint}</li>`).join('')}
            </ul>
        </details>

        <details class="challenge-solution">
            <summary>💻 Show Solution Commands</summary>
            <div class="solution-commands">
                ${challenge.solution_commands.map(cmd => `<code>${cmd}</code>`).join('<br>')}
            </div>
        </details>

        <div class="challenge-footer">
            <strong>🏆 Reward:</strong> ${challenge.reward}
            <br>
            <strong>📚 Learn:</strong> ${challenge.learn}
        </div>
    `;

    container.innerHTML = html;

    // Update navigation
    const progressDiv = document.getElementById('debug-challenge-progress');
    if (progressDiv) {
        progressDiv.textContent = `Challenge ${currentChallengeIndex + 1} of ${currentChallenges.length}`;
    }
}

function navigateChallenge(direction) {
    currentChallengeIndex += direction;

    if (currentChallengeIndex < 0) {
        currentChallengeIndex = currentChallenges.length - 1;
    } else if (currentChallengeIndex >= currentChallenges.length) {
        currentChallengeIndex = 0;
    }

    displayCurrentChallenge();
}

function completeCurrentChallenge() {
    const challenge = currentChallenges[currentChallengeIndex];

    fetch('/api/debug/challenge/complete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({challenge_id: challenge.id})
    })
        .then(res => res.json())
        .then(data => {
            alert(`${data.message}\n\n${challenge.reward}`);

            if (data.next_challenge) {
                navigateChallenge(1);
            }
        })
        .catch(err => {
            alert('Error completing challenge: ' + err.message);
        });
}

// ==============================================================================
// UTILITY FUNCTIONS
// ==============================================================================

function runCommand(command) {
    // TODO: Implement safe command execution
    alert(`Would run: ${command}\n\nFor now, try this in your terminal!`);
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

function formatMarkdown(text) {
    // Simple markdown formatting
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Note: initDebugLab() is called by studio.js during DOMContentLoaded
// This function is exported globally for studio.js to access
