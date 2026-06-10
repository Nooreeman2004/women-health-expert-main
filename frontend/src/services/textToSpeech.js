/**
 * Text-to-Speech Service using Web Speech Synthesis API
 */

class TextToSpeechService {
    constructor() {
        this.synth = window.speechSynthesis;
        this.voice = null;
        this.isSpeaking = false;
        this.isEnabled = true;
        this.rate = 0.9; // Slightly slower for clarity
        this.pitch = 1.0;

        // Initialize voice
        this.initVoice();
    }

    /**
     * Initialize and select a female voice
     */
    initVoice() {
        if (!this.synth) {
            console.warn('⚠️ Speech Synthesis not supported in this browser');
            return;
        }

        const setVoice = () => {
            const voices = this.synth.getVoices();

            // Try to find a female English voice
            this.voice = voices.find(voice =>
                voice.lang.startsWith('en') &&
                (voice.name.toLowerCase().includes('female') ||
                    voice.name.toLowerCase().includes('samantha') ||
                    voice.name.toLowerCase().includes('victoria') ||
                    voice.name.toLowerCase().includes('karen'))
            ) || voices.find(voice => voice.lang.startsWith('en')) || voices[0];

            if (this.voice) {
                console.log('🔊 Voice selected:', this.voice.name);
            }
        };

        // Voices might not be loaded immediately
        if (this.synth.getVoices().length > 0) {
            setVoice();
        } else {
            this.synth.addEventListener('voiceschanged', setVoice);
        }
    }

    /**
     * Speak the given text
     */
    speak(text) {
        if (!this.synth || !this.isEnabled) {
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            // Cancel any ongoing speech
            this.stop();

            const utterance = new SpeechSynthesisUtterance(text);

            if (this.voice) {
                utterance.voice = this.voice;
            }

            utterance.rate = this.rate;
            utterance.pitch = this.pitch;
            utterance.volume = 1.0;

            utterance.onstart = () => {
                this.isSpeaking = true;
                console.log('🔊 Speaking:', text.substring(0, 50) + '...');
            };

            utterance.onend = () => {
                this.isSpeaking = false;
                console.log('✅ Speech completed');
                resolve();
            };

            utterance.onerror = (error) => {
                this.isSpeaking = false;
                console.error('❌ Speech error:', error);
                reject(error);
            };

            this.synth.speak(utterance);
        });
    }

    /**
     * Stop current speech
     */
    stop() {
        if (this.synth && this.synth.speaking) {
            this.synth.cancel();
            this.isSpeaking = false;
        }
    }

    /**
     * Pause speech
     */
    pause() {
        if (this.synth && this.synth.speaking) {
            this.synth.pause();
        }
    }

    /**
     * Resume speech
     */
    resume() {
        if (this.synth && this.synth.paused) {
            this.synth.resume();
        }
    }

    /**
     * Toggle enabled state
     */
    toggleEnabled() {
        this.isEnabled = !this.isEnabled;
        if (!this.isEnabled) {
            this.stop();
        }
        return this.isEnabled;
    }

    /**
     * Set speech rate
     */
    setRate(rate) {
        this.rate = Math.max(0.1, Math.min(2.0, rate));
    }

    /**
     * Set speech pitch
     */
    setPitch(pitch) {
        this.pitch = Math.max(0, Math.min(2, pitch));
    }

    /**
     * Check if speech synthesis is supported
     */
    isSupported() {
        return 'speechSynthesis' in window;
    }
}

// Create singleton instance
const ttsService = new TextToSpeechService();

export default ttsService;
