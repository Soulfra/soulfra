// Auto-generated config for CringeProof
const CRINGEPROOF_CONFIG = {
    API_BACKEND_URL: (() => {
        const hostname = window.location.hostname;

        // Local testing
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:5001';
        }

        // Production - your deployed backend
        return 'http://localhost:5001';
    })(),

    DOMAIN: 'cringeproof',
    BRAND_NAME: 'CringeProof',
    TAGLINE: 'Zero Performance Anxiety',
    CATEGORY: 'social',
    THEME: {
        primary: '#ff006e',
        secondary: '#bdb2ff',
        accent: '#000'
    }
};

// Export for compatibility
if (typeof window !== 'undefined') {
    window.CRINGEPROOF_CONFIG = CRINGEPROOF_CONFIG;
}
