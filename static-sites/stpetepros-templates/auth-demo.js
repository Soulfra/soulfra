/**
 * StPetePros Auth Demo - Client-Side Simulation
 *
 * Features:
 * - Visual token system with persona colors
 * - Token diffusion animations (spreading across domains)
 * - Token decay (expiration countdown)
 * - Token aging (color fading over time)
 * - Token caching (localStorage persistence)
 *
 * Personas & Colors:
 * - CalRiven (blue #3B82F6) - Work/Technical
 * - CringeProof (purple #A855F7) - Ideas/Creative
 * - Soulfra (cyan #06B6D4) - Spiritual/Balanced
 * - DeathToData (dark grey #1F2937) - Privacy
 * - HowToCookAtHome (orange #F59E0B) - Cooking
 */

// Persona color definitions
const PERSONA_COLORS = {
    calriven: '#3B82F6',
    cringeproof: '#A855F7',
    soulfra: '#06B6D4',
    deathtodata: '#1F2937',
    howtocookathome: '#F59E0B'
};

// Token expiration time (7 days in milliseconds)
const TOKEN_LIFETIME = 7 * 24 * 60 * 60 * 1000;

/**
 * Token class - represents an auth token with visual properties
 */
class AuthToken {
    constructor(persona, email, display_name) {
        this.persona = persona;
        this.email = email;
        this.display_name = display_name;
        this.created_at = Date.now();
        this.expires_at = this.created_at + TOKEN_LIFETIME;
        this.color = PERSONA_COLORS[persona] || '#6B7280'; // Default grey
        this.domains = ['stpetepros', 'cringeproof', 'soulfra']; // Domains this token can diffuse to
    }

    /**
     * Get token age in milliseconds
     */
    getAge() {
        return Date.now() - this.created_at;
    }

    /**
     * Get remaining time until expiration
     */
    getTimeRemaining() {
        return this.expires_at - Date.now();
    }

    /**
     * Check if token is expired
     */
    isExpired() {
        return Date.now() >= this.expires_at;
    }

    /**
     * Get color with opacity based on age (aging effect)
     */
    getAgingColor() {
        const age = this.getAge();
        const lifetime = TOKEN_LIFETIME;
        const opacity = 1 - (age / lifetime * 0.5); // Fade from 1.0 to 0.5 over lifetime
        return this.hexToRgba(this.color, opacity);
    }

    /**
     * Convert hex color to rgba with opacity
     */
    hexToRgba(hex, opacity) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }

    /**
     * Serialize token to JSON
     */
    toJSON() {
        return {
            persona: this.persona,
            email: this.email,
            display_name: this.display_name,
            created_at: this.created_at,
            expires_at: this.expires_at,
            color: this.color,
            domains: this.domains
        };
    }

    /**
     * Deserialize token from JSON
     */
    static fromJSON(json) {
        const token = new AuthToken(json.persona, json.email, json.display_name);
        token.created_at = json.created_at;
        token.expires_at = json.expires_at;
        token.color = json.color;
        token.domains = json.domains;
        return token;
    }
}

/**
 * Save token to localStorage (caching)
 */
function cacheToken(token) {
    localStorage.setItem('stpetepros_auth_token', JSON.stringify(token.toJSON()));
    console.log('🔐 Token cached to localStorage:', token);
}

/**
 * Load token from localStorage (cache retrieval)
 */
function loadCachedToken() {
    const cached = localStorage.getItem('stpetepros_auth_token');
    if (!cached) return null;

    const token = AuthToken.fromJSON(JSON.parse(cached));

    if (token.isExpired()) {
        console.log('⏰ Cached token expired, removing...');
        clearToken();
        return null;
    }

    console.log('✅ Loaded cached token:', token);
    return token;
}

/**
 * Clear token from cache
 */
function clearToken() {
    localStorage.removeItem('stpetepros_auth_token');
    console.log('🗑️ Token cleared from cache');
}

/**
 * Create a demo login with selected persona
 */
function createDemoLogin(persona, display_name, email) {
    const token = new AuthToken(persona, email, display_name);
    cacheToken(token);

    // Show token diffusion animation
    animateTokenDiffusion(token);

    // Start decay countdown
    startDecayCountdown(token);

    return token;
}

/**
 * Show auth demo modal
 */
function showAuthDemo() {
    const modal = document.createElement('div');
    modal.id = 'authDemoModal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full mx-4">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-3xl font-bold text-slate-900">Soulfra Auth Demo</h2>
                <button onclick="closeAuthDemo()" class="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
            </div>

            <p class="text-slate-600 mb-6">
                Choose a persona to see the visual token system with color-coded authentication.
                Each persona represents a different aspect of your identity across Soulfra domains.
            </p>

            <div class="space-y-4 mb-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${Object.entries(PERSONA_COLORS).map(([persona, color]) => `
                        <button
                            onclick="selectPersona('${persona}')"
                            class="persona-btn flex items-center gap-3 p-4 border-2 rounded-lg hover:shadow-md transition-all"
                            style="border-color: ${color};"
                        >
                            <div class="w-4 h-4 rounded-full" style="background-color: ${color};"></div>
                            <span class="font-semibold capitalize">${persona.replace(/([A-Z])/g, ' $1')}</span>
                        </button>
                    `).join('')}
                </div>
            </div>

            <div id="tokenPreview" class="hidden bg-slate-50 rounded-lg p-6 border-2 border-dashed">
                <h3 class="text-lg font-bold mb-4">Token Preview</h3>
                <div id="tokenDisplay"></div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

/**
 * Close auth demo modal
 */
function closeAuthDemo() {
    const modal = document.getElementById('authDemoModal');
    if (modal) modal.remove();
}

/**
 * Select persona and create token
 */
function selectPersona(persona) {
    const display_name = prompt('Enter your display name:', 'Demo User');
    if (!display_name) return;

    const email = prompt('Enter email:', `${persona}@demo.soulfra.com`);
    if (!email) return;

    const token = createDemoLogin(persona, display_name, email);

    // Update preview
    const preview = document.getElementById('tokenPreview');
    const display = document.getElementById('tokenDisplay');

    preview.classList.remove('hidden');
    preview.style.borderColor = token.color;

    display.innerHTML = `
        <div class="space-y-3">
            <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full animate-pulse" style="background-color: ${token.color};"></div>
                <div>
                    <div class="font-bold text-slate-900">${token.display_name}</div>
                    <div class="text-sm text-slate-500">${token.email}</div>
                </div>
            </div>
            <div class="text-sm text-slate-600">
                <div><strong>Persona:</strong> ${token.persona}</div>
                <div><strong>Created:</strong> ${new Date(token.created_at).toLocaleString()}</div>
                <div><strong>Expires:</strong> ${new Date(token.expires_at).toLocaleString()}</div>
            </div>
            <div id="decayCounter" class="text-sm font-mono bg-slate-800 text-green-400 p-3 rounded"></div>
        </div>
    `;

    // Close modal after 3 seconds
    setTimeout(() => {
        closeAuthDemo();
        updateAuthUI(token);
    }, 3000);
}

/**
 * Animate token diffusion across domains
 */
function animateTokenDiffusion(token) {
    // Create visual representation of token spreading across domains
    const container = document.createElement('div');
    container.id = 'tokenDiffusion';
    container.className = 'fixed top-20 right-4 bg-white rounded-lg shadow-lg p-4 z-50';
    container.innerHTML = `
        <div class="text-sm font-semibold text-slate-900 mb-2">Token Diffusion</div>
        <div class="space-y-2">
            ${token.domains.map((domain, i) => `
                <div class="diffusion-bar" style="animation-delay: ${i * 0.5}s;">
                    <div class="text-xs text-slate-600">${domain}</div>
                    <div class="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div class="h-full rounded-full transition-all duration-1000"
                             style="background-color: ${token.color}; width: 0%;"
                             id="diffusion-${domain}"></div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    document.body.appendChild(container);

    // Animate bars filling up
    token.domains.forEach((domain, i) => {
        setTimeout(() => {
            const bar = document.getElementById(`diffusion-${domain}`);
            if (bar) bar.style.width = '100%';
        }, i * 500);
    });

    // Remove after animation
    setTimeout(() => {
        container.remove();
    }, 5000);
}

/**
 * Start decay countdown timer
 */
function startDecayCountdown(token) {
    const updateCountdown = () => {
        const counter = document.getElementById('decayCounter');
        if (!counter) return;

        const remaining = token.getTimeRemaining();
        if (remaining <= 0) {
            counter.textContent = '⚠️ TOKEN EXPIRED';
            counter.classList.add('bg-red-600');
            clearToken();
            return;
        }

        const days = Math.floor(remaining / (24 * 60 * 60 * 1000));
        const hours = Math.floor((remaining % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000));
        const minutes = Math.floor((remaining % (60 * 60 * 1000)) / (60 * 1000));
        const seconds = Math.floor((remaining % (60 * 1000)) / 1000);

        counter.textContent = `⏱️ Expires in: ${days}d ${hours}h ${minutes}m ${seconds}s`;

        // Update color based on age (decay effect)
        const age_percent = (token.getAge() / TOKEN_LIFETIME) * 100;
        if (age_percent > 80) {
            counter.classList.remove('bg-slate-800', 'text-green-400');
            counter.classList.add('bg-red-800', 'text-red-200');
        } else if (age_percent > 50) {
            counter.classList.remove('bg-slate-800', 'text-green-400');
            counter.classList.add('bg-yellow-800', 'text-yellow-200');
        }
    };

    // Update every second
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

/**
 * Update UI to show logged-in state
 */
function updateAuthUI(token) {
    // Create persistent token indicator in header
    const indicator = document.createElement('div');
    indicator.id = 'authIndicator';
    indicator.className = 'fixed top-4 right-4 bg-white rounded-lg shadow-lg p-3 z-40';
    indicator.innerHTML = `
        <div class="flex items-center gap-2">
            <div class="w-3 h-3 rounded-full animate-pulse" style="background-color: ${token.color};"></div>
            <span class="text-sm font-semibold">${token.display_name}</span>
            <button onclick="logoutDemo()" class="text-xs text-red-600 hover:text-red-800">Logout</button>
        </div>
    `;

    document.body.appendChild(indicator);
}

/**
 * Logout and clear token
 */
function logoutDemo() {
    clearToken();
    const indicator = document.getElementById('authIndicator');
    if (indicator) indicator.remove();
    const diffusion = document.getElementById('tokenDiffusion');
    if (diffusion) diffusion.remove();
    location.reload();
}

/**
 * Initialize auth on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    const token = loadCachedToken();
    if (token) {
        console.log('🔄 Restoring session from cache...');
        updateAuthUI(token);
        startDecayCountdown(token);
    }
});
