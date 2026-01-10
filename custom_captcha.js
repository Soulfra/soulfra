/**
 * Custom CAPTCHA - Ollama-Powered Challenge System
 *
 * Privacy-friendly alternative to Google reCAPTCHA.
 * Uses Ollama to generate and validate challenges.
 *
 * Usage:
 *   1. Include this file in your HTML: <script src="custom_captcha.js"></script>
 *   2. Add CAPTCHA container: <div id="ollama-captcha"></div>
 *   3. Initialize: const captcha = new OllamaCaptcha('ollama-captcha', config);
 *   4. Validate: if (await captcha.validate()) { ... }
 *
 * No tracking, no Google, no external services.
 */

class OllamaCaptcha {
    constructor(containerId, config = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);

        // Configuration
        this.config = {
            ollamaHost: config.ollamaHost || 'http://localhost:11434',
            model: config.model || 'llama2',
            difficulty: config.difficulty || 'easy', // easy, medium, hard
            type: config.type || 'math', // math, text, logic, mixed
            timeoutSeconds: config.timeoutSeconds || 60,
            maxAttempts: config.maxAttempts || 3,
            customPrompts: config.customPrompts || []
        };

        // State
        this.currentChallenge = null;
        this.currentAnswer = null;
        this.attempts = 0;
        this.isValidated = false;
        this.startTime = null;

        this.init();
    }

    init() {
        if (!this.container) {
            console.error(`CAPTCHA container "${this.containerId}" not found`);
            return;
        }

        this.render();
        this.generateChallenge();
    }

    render() {
        this.container.innerHTML = `
            <div class="ollama-captcha-container">
                <style>
                    .ollama-captcha-container {
                        background: rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(10px);
                        border: 2px solid rgba(255, 255, 255, 0.2);
                        border-radius: 15px;
                        padding: 20px;
                        margin: 20px 0;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    }

                    .ollama-captcha-header {
                        font-size: 1.1em;
                        font-weight: 600;
                        margin-bottom: 15px;
                        opacity: 0.95;
                    }

                    .ollama-captcha-challenge {
                        background: rgba(0, 0, 0, 0.3);
                        padding: 15px;
                        border-radius: 10px;
                        margin-bottom: 15px;
                        font-size: 1.05em;
                        line-height: 1.6;
                    }

                    .ollama-captcha-input {
                        width: 100%;
                        padding: 12px;
                        border: 2px solid rgba(255, 255, 255, 0.3);
                        border-radius: 8px;
                        background: rgba(255, 255, 255, 0.2);
                        color: white;
                        font-size: 1em;
                        margin-bottom: 10px;
                    }

                    .ollama-captcha-input::placeholder {
                        color: rgba(255, 255, 255, 0.6);
                    }

                    .ollama-captcha-buttons {
                        display: flex;
                        gap: 10px;
                    }

                    .ollama-captcha-button {
                        flex: 1;
                        padding: 10px 20px;
                        border: 2px solid rgba(255, 255, 255, 0.3);
                        border-radius: 8px;
                        background: rgba(103, 126, 234, 0.8);
                        color: white;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s;
                    }

                    .ollama-captcha-button:hover {
                        background: rgba(103, 126, 234, 1);
                        transform: translateY(-2px);
                    }

                    .ollama-captcha-button:disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                    }

                    .ollama-captcha-status {
                        margin-top: 10px;
                        padding: 10px;
                        border-radius: 8px;
                        font-size: 0.95em;
                        text-align: center;
                    }

                    .ollama-captcha-status.success {
                        background: rgba(74, 222, 128, 0.3);
                        border: 2px solid rgba(74, 222, 128, 0.5);
                    }

                    .ollama-captcha-status.error {
                        background: rgba(248, 113, 113, 0.3);
                        border: 2px solid rgba(248, 113, 113, 0.5);
                    }

                    .ollama-captcha-status.loading {
                        background: rgba(251, 191, 36, 0.3);
                        border: 2px solid rgba(251, 191, 36, 0.5);
                    }

                    .ollama-captcha-meta {
                        margin-top: 10px;
                        font-size: 0.85em;
                        opacity: 0.7;
                        text-align: center;
                    }
                </style>

                <div class="ollama-captcha-header">
                    🤖 Human Verification (Ollama-Powered)
                </div>

                <div class="ollama-captcha-challenge" id="captcha-challenge">
                    Loading challenge...
                </div>

                <input
                    type="text"
                    class="ollama-captcha-input"
                    id="captcha-input"
                    placeholder="Type your answer here..."
                    disabled
                />

                <div class="ollama-captcha-buttons">
                    <button class="ollama-captcha-button" id="captcha-submit" disabled>
                        Submit
                    </button>
                    <button class="ollama-captcha-button" id="captcha-refresh" disabled>
                        🔄 New Challenge
                    </button>
                </div>

                <div class="ollama-captcha-status" id="captcha-status" style="display: none;"></div>

                <div class="ollama-captcha-meta">
                    Privacy-friendly • No tracking • Powered by ${this.config.model}
                </div>
            </div>
        `;

        // Attach event listeners
        document.getElementById('captcha-submit').addEventListener('click', () => this.handleSubmit());
        document.getElementById('captcha-refresh').addEventListener('click', () => this.generateChallenge());
        document.getElementById('captcha-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.handleSubmit();
            }
        });
    }

    async generateChallenge() {
        this.showStatus('Generating challenge...', 'loading');
        this.disableInput();

        try {
            // Select challenge type
            const challengeType = this.selectChallengeType();

            // Generate challenge using Ollama
            const challenge = await this.createChallenge(challengeType);

            this.currentChallenge = challenge.question;
            this.currentAnswer = challenge.answer;
            this.attempts = 0;
            this.startTime = Date.now();

            // Display challenge
            document.getElementById('captcha-challenge').textContent = this.currentChallenge;
            this.enableInput();
            this.hideStatus();

        } catch (error) {
            this.showStatus('Failed to generate challenge. Check Ollama connection.', 'error');
            console.error('CAPTCHA generation error:', error);
        }
    }

    selectChallengeType() {
        const types = {
            math: ['addition', 'subtraction', 'multiplication', 'division', 'hexadecimal'],
            text: ['color', 'day', 'month', 'direction', 'animal'],
            logic: ['sequence', 'pattern', 'reasoning'],
            mixed: ['addition', 'subtraction', 'color', 'day', 'sequence']
        };

        const typeList = types[this.config.type] || types['math'];
        return typeList[Math.floor(Math.random() * typeList.length)];
    }

    async createChallenge(type) {
        // Use custom prompts if provided
        if (this.config.customPrompts.length > 0) {
            const prompt = this.config.customPrompts[Math.floor(Math.random() * this.config.customPrompts.length)];
            const answer = await this.askOllama(`What is the answer to: "${prompt}"? Respond with ONLY the answer, no explanation.`);
            return { question: prompt, answer: answer.trim().toLowerCase() };
        }

        // Built-in challenge types
        const challenges = {
            addition: async () => {
                const a = Math.floor(Math.random() * 20) + 1;
                const b = Math.floor(Math.random() * 20) + 1;
                return { question: `What is ${a} + ${b}?`, answer: String(a + b) };
            },

            subtraction: async () => {
                const a = Math.floor(Math.random() * 30) + 10;
                const b = Math.floor(Math.random() * 10) + 1;
                return { question: `What is ${a} - ${b}?`, answer: String(a - b) };
            },

            multiplication: async () => {
                const a = Math.floor(Math.random() * 10) + 1;
                const b = Math.floor(Math.random() * 10) + 1;
                return { question: `What is ${a} × ${b}?`, answer: String(a * b) };
            },

            hexadecimal: async () => {
                const num = Math.floor(Math.random() * 16);
                return {
                    question: `What is ${num} in hexadecimal? (lowercase)`,
                    answer: num.toString(16)
                };
            },

            color: async () => {
                const colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange'];
                const color = colors[Math.floor(Math.random() * colors.length)];
                const question = await this.askOllama(`Ask the user to name a primary color. Make it a simple question.`);
                return { question: question, answer: '' }; // Will use Ollama to validate
            },

            day: async () => {
                const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
                const idx = Math.floor(Math.random() * days.length);
                const nextIdx = (idx + 1) % days.length;
                return {
                    question: `What day comes after ${days[idx]}?`,
                    answer: days[nextIdx]
                };
            },

            sequence: async () => {
                const start = Math.floor(Math.random() * 10);
                const step = Math.floor(Math.random() * 5) + 1;
                const seq = [start, start + step, start + step * 2, start + step * 3];
                return {
                    question: `What's the next number in the sequence: ${seq.join(', ')}, ___?`,
                    answer: String(start + step * 4)
                };
            }
        };

        const generator = challenges[type] || challenges['addition'];
        return await generator();
    }

    async handleSubmit() {
        const input = document.getElementById('captcha-input');
        const userAnswer = input.value.trim().toLowerCase();

        if (!userAnswer) {
            this.showStatus('Please enter an answer', 'error');
            return;
        }

        this.attempts++;
        this.disableInput();
        this.showStatus('Validating...', 'loading');

        try {
            const isCorrect = await this.validateAnswer(userAnswer);

            if (isCorrect) {
                this.isValidated = true;
                this.showStatus('✓ Verified! You may proceed.', 'success');
                this.disableInput();

                // Trigger validation event
                this.container.dispatchEvent(new CustomEvent('captcha-validated', {
                    detail: {
                        validated: true,
                        attempts: this.attempts,
                        timeSeconds: (Date.now() - this.startTime) / 1000
                    }
                }));

            } else {
                if (this.attempts >= this.config.maxAttempts) {
                    this.showStatus('❌ Too many incorrect attempts. Generating new challenge...', 'error');
                    setTimeout(() => this.generateChallenge(), 2000);
                } else {
                    this.showStatus(`❌ Incorrect. ${this.config.maxAttempts - this.attempts} attempts remaining.`, 'error');
                    this.enableInput();
                    input.value = '';
                    input.focus();
                }
            }

        } catch (error) {
            this.showStatus('Validation failed. Please try again.', 'error');
            this.enableInput();
            console.error('CAPTCHA validation error:', error);
        }
    }

    async validateAnswer(userAnswer) {
        // If we have a direct answer, compare
        if (this.currentAnswer) {
            return userAnswer === this.currentAnswer.toLowerCase();
        }

        // Otherwise, ask Ollama to validate
        const prompt = `
            Question: ${this.currentChallenge}
            User's answer: ${userAnswer}

            Is the user's answer correct? Respond with ONLY "yes" or "no", nothing else.
        `;

        const response = await this.askOllama(prompt);
        return response.toLowerCase().includes('yes');
    }

    async askOllama(prompt) {
        const response = await fetch(`${this.config.ollamaHost}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: this.config.model,
                prompt: prompt,
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(`Ollama API error: ${response.status}`);
        }

        const data = await response.json();
        return data.response.trim();
    }

    showStatus(message, type) {
        const status = document.getElementById('captcha-status');
        status.textContent = message;
        status.className = `ollama-captcha-status ${type}`;
        status.style.display = 'block';
    }

    hideStatus() {
        document.getElementById('captcha-status').style.display = 'none';
    }

    enableInput() {
        document.getElementById('captcha-input').disabled = false;
        document.getElementById('captcha-submit').disabled = false;
        document.getElementById('captcha-refresh').disabled = false;
        document.getElementById('captcha-input').focus();
    }

    disableInput() {
        document.getElementById('captcha-input').disabled = true;
        document.getElementById('captcha-submit').disabled = true;
        document.getElementById('captcha-refresh').disabled = true;
    }

    // Public API

    async validate() {
        return this.isValidated;
    }

    reset() {
        this.isValidated = false;
        this.attempts = 0;
        this.currentChallenge = null;
        this.currentAnswer = null;
        this.generateChallenge();
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OllamaCaptcha;
}

/**
 * USAGE EXAMPLES
 *
 * === Example 1: Basic Usage ===
 *
 * HTML:
 * <div id="my-captcha"></div>
 * <button id="submit-btn" disabled>Submit Form</button>
 *
 * JavaScript:
 * const captcha = new OllamaCaptcha('my-captcha', {
 *     ollamaHost: 'http://localhost:11434',
 *     model: 'llama2',
 *     difficulty: 'easy'
 * });
 *
 * // Listen for validation
 * document.getElementById('my-captcha').addEventListener('captcha-validated', (e) => {
 *     console.log('CAPTCHA validated!', e.detail);
 *     document.getElementById('submit-btn').disabled = false;
 * });
 *
 *
 * === Example 2: Custom Prompts ===
 *
 * const captcha = new OllamaCaptcha('my-captcha', {
 *     model: 'llama2',
 *     type: 'mixed',
 *     customPrompts: [
 *         "What is the capital of France?",
 *         "How many legs does a spider have?",
 *         "What color is the sky?"
 *     ]
 * });
 *
 *
 * === Example 3: Form Integration ===
 *
 * <form id="signup-form">
 *     <input type="email" name="email" required>
 *     <input type="password" name="password" required>
 *     <div id="signup-captcha"></div>
 *     <button type="submit" id="signup-submit" disabled>Sign Up</button>
 * </form>
 *
 * const captcha = new OllamaCaptcha('signup-captcha');
 *
 * document.getElementById('signup-captcha').addEventListener('captcha-validated', () => {
 *     document.getElementById('signup-submit').disabled = false;
 * });
 *
 * document.getElementById('signup-form').addEventListener('submit', async (e) => {
 *     e.preventDefault();
 *
 *     if (!await captcha.validate()) {
 *         alert('Please complete the CAPTCHA');
 *         return;
 *     }
 *
 *     // Submit form...
 * });
 *
 *
 * === Example 4: Per-Brand Configuration ===
 *
 * // Load brand config
 * const brandConfig = await fetch('brand.json').then(r => r.json());
 *
 * const captcha = new OllamaCaptcha('brand-captcha', {
 *     ollamaHost: brandConfig.ollama.host,
 *     model: brandConfig.ollama.default_model,
 *     customPrompts: brandConfig.captcha.prompts,
 *     maxAttempts: brandConfig.captcha.max_attempts || 3
 * });
 */
