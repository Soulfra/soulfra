/**
 * Soulfra API Configuration
 *
 * Change API_BACKEND_URL to switch between local testing and production
 */

const CONFIG = {
    // ============================================
    // SET YOUR BACKEND HERE:
    // ============================================
    API_BACKEND_URL: 'https://192.168.1.87:5002',  // <-- CHANGE THIS

    // Auto-detection (optional - uncomment to use)
    // API_BACKEND_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    //     ? 'https://192.168.1.87:5002'  // Local testing
    //     : 'https://api.cringeproof.com',  // Production
};

// Export for use in HTML files
window.SOULFRA_CONFIG = CONFIG;
