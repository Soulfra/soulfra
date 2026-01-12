/**
 * LLM Router - Client-Side AI with Auto-Fallback
 *
 * Automatically tries: Local Ollama → Anthropic API → OpenAI API → Mock
 *
 * Usage:
 *
 * ```javascript
 * // Basic query
 * const response = await askAI("Explain this code");
 *
 * // With options
 * const response = await askAI("Debug this", {
 *     model: "claude-3-5-sonnet-20241022",
 *     preferLocal: true
 * });
 *
 * // Check status
 * const status = await getLLMStatus();
 * console.log(status); // { mode: "ollama", model: "llama3.2", available: true }
 * ```
 *
 * Features:
 * - 🔄 Auto-fallback between providers
 * - 💾 Caches endpoint status (5 min)
 * - 🚀 Works in browser or Node.js
 * - 🔐 API keys from environment or config
 * - 🎯 Intelligent mock responses
 */

const LLMRouter = (() => {
    // Configuration
    const config = {
        ollama: {
            baseURL: 'http://localhost:11434',
            endpoints: [
                'http://localhost:11434',
                'http://192.168.1.87:11434'  // Fallback to local network
            ],
            model: 'llama3.2'
        },
        anthropic: {
            baseURL: 'https://api.anthropic.com/v1',
            model: 'claude-3-5-sonnet-20241022',
            apiKey: null  // Set via setAPIKey() or environment
        },
        openai: {
            baseURL: 'https://api.openai.com/v1',
            model: 'gpt-4',
            apiKey: null
        }
    };

    // Cache
    let activeEndpoint = null;
    let endpointCheckTime = null;
    const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

    /**
     * Test if Ollama is reachable
     */
    async function testOllama(endpoint, timeout = 3000) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);

            const response = await fetch(`${endpoint}/api/tags`, {
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const data = await response.json();
                console.log(`✅ Ollama reachable at ${endpoint} (${data.models?.length || 0} models)`);
                return true;
            }
            return false;
        } catch (error) {
            console.debug(`❌ Ollama not available at ${endpoint}:`, error.message);
            return false;
        }
    }

    /**
     * Get active Ollama endpoint with caching
     */
    async function getOllamaEndpoint() {
        // Check cache
        if (activeEndpoint && endpointCheckTime) {
            const elapsed = Date.now() - endpointCheckTime;
            if (elapsed < CACHE_DURATION) {
                return activeEndpoint;
            }
        }

        // Try each endpoint
        for (const endpoint of config.ollama.endpoints) {
            if (await testOllama(endpoint)) {
                activeEndpoint = endpoint;
                endpointCheckTime = Date.now();
                return endpoint;
            }
        }

        return null;
    }

    /**
     * Ask Ollama (local)
     */
    async function askOllama(prompt, options = {}) {
        const endpoint = await getOllamaEndpoint();

        if (!endpoint) {
            throw new Error('Ollama not available');
        }

        const response = await fetch(`${endpoint}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: options.model || config.ollama.model,
                prompt: prompt,
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(`Ollama error: ${response.statusText}`);
        }

        const data = await response.json();
        return {
            text: data.response,
            model: data.model,
            provider: 'ollama'
        };
    }

    /**
     * Ask Anthropic (Claude API)
     */
    async function askAnthropic(prompt, options = {}) {
        const apiKey = options.apiKey || config.anthropic.apiKey || process.env.ANTHROPIC_API_KEY;

        if (!apiKey) {
            throw new Error('Anthropic API key not set');
        }

        const response = await fetch(`${config.anthropic.baseURL}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': apiKey,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: options.model || config.anthropic.model,
                max_tokens: options.maxTokens || 1024,
                messages: [
                    { role: 'user', content: prompt }
                ]
            })
        });

        if (!response.ok) {
            throw new Error(`Anthropic error: ${response.statusText}`);
        }

        const data = await response.json();
        return {
            text: data.content[0].text,
            model: data.model,
            provider: 'anthropic'
        };
    }

    /**
     * Ask OpenAI (GPT API)
     */
    async function askOpenAI(prompt, options = {}) {
        const apiKey = options.apiKey || config.openai.apiKey || process.env.OPENAI_API_KEY;

        if (!apiKey) {
            throw new Error('OpenAI API key not set');
        }

        const response = await fetch(`${config.openai.baseURL}/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: options.model || config.openai.model,
                messages: [
                    { role: 'user', content: prompt }
                ],
                max_tokens: options.maxTokens || 1024
            })
        });

        if (!response.ok) {
            throw new Error(`OpenAI error: ${response.statusText}`);
        }

        const data = await response.json();
        return {
            text: data.choices[0].message.content,
            model: data.model,
            provider: 'openai'
        };
    }

    /**
     * Mock response (fallback when all services fail)
     */
    function getMockResponse(prompt) {
        // Intelligent mock responses based on prompt patterns
        const responses = {
            debug: "To debug this issue, I'd recommend:\n1. Check console for errors\n2. Verify API connections\n3. Review recent code changes\n4. Test with simplified inputs",
            explain: "Based on the context, this code appears to handle data processing. The key components work together to transform input into the desired output format.",
            help: "I can help you with:\n• Code debugging\n• Architecture decisions\n• Implementation guidance\n• Best practices\n\nWhat would you like to focus on?",
            analyze: "Key observations:\n• The system follows a modular architecture\n• Error handling is in place\n• Performance could be optimized\n• Consider adding more tests",
            default: "I understand you're asking about this topic. While I'm currently in mock mode (no AI service available), I'd recommend checking the documentation or breaking down the problem into smaller steps."
        };

        const promptLower = prompt.toLowerCase();

        if (promptLower.includes('debug') || promptLower.includes('error') || promptLower.includes('fix')) {
            return responses.debug;
        } else if (promptLower.includes('explain') || promptLower.includes('what is') || promptLower.includes('how does')) {
            return responses.explain;
        } else if (promptLower.includes('help') || promptLower.includes('assist')) {
            return responses.help;
        } else if (promptLower.includes('analyze') || promptLower.includes('review')) {
            return responses.analyze;
        }

        return responses.default;
    }

    /**
     * Main AI query function with auto-fallback
     */
    async function askAI(prompt, options = {}) {
        const providers = options.preferLocal ?
            ['ollama', 'anthropic', 'openai', 'mock'] :
            ['anthropic', 'ollama', 'openai', 'mock'];

        const errors = [];

        for (const provider of providers) {
            try {
                let result;

                switch (provider) {
                    case 'ollama':
                        result = await askOllama(prompt, options);
                        break;
                    case 'anthropic':
                        result = await askAnthropic(prompt, options);
                        break;
                    case 'openai':
                        result = await askOpenAI(prompt, options);
                        break;
                    case 'mock':
                        result = {
                            text: getMockResponse(prompt),
                            model: 'mock',
                            provider: 'mock'
                        };
                        break;
                }

                console.log(`✅ Response from ${result.provider} (${result.model})`);
                return result;

            } catch (error) {
                errors.push({ provider, error: error.message });
                console.debug(`⚠️ ${provider} failed:`, error.message);
                continue;
            }
        }

        // If we get here, all providers failed
        return {
            text: getMockResponse(prompt),
            model: 'mock',
            provider: 'mock',
            errors
        };
    }

    /**
     * Get LLM status
     */
    async function getLLMStatus() {
        const status = {
            ollama: { available: false, endpoint: null },
            anthropic: { available: !!config.anthropic.apiKey, model: config.anthropic.model },
            openai: { available: !!config.openai.apiKey, model: config.openai.model }
        };

        // Check Ollama
        const ollamaEndpoint = await getOllamaEndpoint();
        if (ollamaEndpoint) {
            status.ollama.available = true;
            status.ollama.endpoint = ollamaEndpoint;
        }

        return status;
    }

    /**
     * Set API keys
     */
    function setAPIKey(provider, key) {
        if (config[provider]) {
            config[provider].apiKey = key;
            console.log(`✅ ${provider} API key set`);
        }
    }

    /**
     * Configure models
     */
    function setModel(provider, model) {
        if (config[provider]) {
            config[provider].model = model;
            console.log(`✅ ${provider} model set to ${model}`);
        }
    }

    // Public API
    return {
        askAI,
        getLLMStatus,
        setAPIKey,
        setModel,
        config
    };
})();

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LLMRouter;
} else if (typeof window !== 'undefined') {
    window.LLMRouter = LLMRouter;
}
