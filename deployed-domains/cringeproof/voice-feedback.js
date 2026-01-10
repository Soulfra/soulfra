/**
 * Voice Feedback System - Tier-based Text-to-Speech
 * 
 * Simple browser-based TTS tied to user progression level
 */

class VoiceFeedback {
    constructor(userLevel = 0) {
        this.userLevel = userLevel;
        this.enabled = true;
        
        // Check browser support
        if (!('speechSynthesis' in window)) {
            console.warn('Speech synthesis not supported');
            this.enabled = false;
        }
    }

    /**
     * Get voice settings based on user level
     */
    getVoiceSettings() {
        const settings = {
            0: { rate: 1.0, pitch: 1.0, volume: 0.8 },      // Free tier
            1: { rate: 1.2, pitch: 1.0, volume: 0.9 },      // Level 1: Faster
            2: { rate: 1.2, pitch: 0.8, volume: 0.9 },      // Level 2: Deeper voice
            3: { rate: 1.3, pitch: 0.9, volume: 1.0 },      // Level 3: Fast + slightly deep
            4: { rate: 1.5, pitch: 0.7, volume: 1.0 }       // Level 4: Maximum customization
        };

        return settings[this.userLevel] || settings[0];
    }

    /**
     * Get message variant based on user level
     */
    getMessage(baseMessage, level) {
        const variants = {
            'squad_match': {
                0: 'Squad match found',
                1: 'Squad match found with high similarity',
                2: 'New squad member detected',
                3: 'Yo! Found your squad',
                4: 'Hell yeah! Squad match at {similarity}%'
            },
            'recording_saved': {
                0: 'Recording saved',
                1: 'Recording saved successfully',
                2: 'Voice memo captured',
                3: 'Recording complete',
                4: 'Saved! Wordmap updated'
            },
            'level_up': {
                0: 'Level up',
                1: 'You leveled up',
                2: 'New level achieved',
                3: 'Level up! New features unlocked',
                4: 'Congrats! You hit level {level}'
            }
        };

        return variants[baseMessage]?.[level] || variants[baseMessage]?.[0] || baseMessage;
    }

    /**
     * Speak text with tier-based customization
     */
    speak(message, context = {}) {
        if (!this.enabled) return;

        const settings = this.getVoiceSettings();
        const utterance = new SpeechSynthesisUtterance(message);

        // Apply voice settings
        utterance.rate = settings.rate;
        utterance.pitch = settings.pitch;
        utterance.volume = settings.volume;

        // Level 3+: Choose voice
        if (this.userLevel >= 3) {
            const voices = window.speechSynthesis.getVoices();
            if (voices.length > 0) {
                // Prefer English voices
                const preferredVoice = voices.find(v => v.lang.startsWith('en')) || voices[0];
                utterance.voice = preferredVoice;
            }
        }

        // Speak
        window.speechSynthesis.speak(utterance);
    }

    /**
     * Announce squad match with similarity
     */
    announceSquadMatch(similarity, count = 1) {
        let message = this.getMessage('squad_match', this.userLevel);
        message = message.replace('{similarity}', Math.round(similarity * 100));
        message = message.replace('{count}', count);
        this.speak(message);
    }

    /**
     * Announce recording saved
     */
    announceRecordingSaved() {
        const message = this.getMessage('recording_saved', this.userLevel);
        this.speak(message);
    }

    /**
     * Announce level up
     */
    announceLevelUp(newLevel) {
        let message = this.getMessage('level_up', this.userLevel);
        message = message.replace('{level}', newLevel);
        this.speak(message);
    }

    /**
     * Custom message (advanced)
     */
    announce(text) {
        this.speak(text);
    }

    /**
     * Toggle voice on/off
     */
    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    }

    /**
     * Stop current speech
     */
    stop() {
        window.speechSynthesis.cancel();
    }
}

// Export for use in HTML
window.VoiceFeedback = VoiceFeedback;
