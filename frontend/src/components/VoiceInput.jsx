import { useState, useEffect, useRef } from 'react';
import './VoiceInput.css';

const VoiceInput = ({ onTranscript, isDisabled }) => {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [isSupported, setIsSupported] = useState(true);
    const recognitionRef = useRef(null);

    useEffect(() => {
        // Check for browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            setIsSupported(false);
            console.warn('⚠️ Speech Recognition not supported in this browser');
            return;
        }

        // Initialize speech recognition
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            setIsListening(true);
            console.log('🎤 Listening...');
        };

        recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcriptPiece = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcriptPiece + ' ';
                } else {
                    interimTranscript += transcriptPiece;
                }
            }

            const currentTranscript = finalTranscript || interimTranscript;
            setTranscript(currentTranscript);

            // Send final transcript to parent
            if (finalTranscript) {
                onTranscript(finalTranscript.trim());
            }
        };

        recognition.onerror = (event) => {
            console.error('❌ Speech recognition error:', event.error);
            setIsListening(false);

            if (event.error === 'not-allowed') {
                alert('Microphone access denied. Please allow microphone access to use voice input.');
            }
        };

        recognition.onend = () => {
            setIsListening(false);
            setTranscript('');
            console.log('🎤 Stopped listening');
        };

        recognitionRef.current = recognition;

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
        };
    }, [onTranscript]);

    const toggleListening = () => {
        if (!isSupported) {
            alert('Speech recognition is not supported in your browser. Please use Chrome or Edge.');
            return;
        }

        if (isListening) {
            recognitionRef.current?.stop();
        } else {
            try {
                recognitionRef.current?.start();
            } catch (error) {
                console.error('Error starting recognition:', error);
            }
        }
    };

    if (!isSupported) {
        return null; // Don't render if not supported
    }

    return (
        <div className="voice-input">
            <button
                type="button"
                className={`voice-button ${isListening ? 'listening' : ''}`}
                onClick={toggleListening}
                disabled={isDisabled}
                title={isListening ? 'Stop recording' : 'Start voice input'}
            >
                <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    <path
                        d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z"
                        fill="currentColor"
                    />
                    <path
                        d="M19 10V12C19 15.87 15.87 19 12 19C8.13 19 5 15.87 5 12V10H3V12C3 16.97 7.03 21 12 21C16.97 21 21 16.97 21 12V10H19Z"
                        fill="currentColor"
                    />
                    <path
                        d="M11 22H13V24H11V22Z"
                        fill="currentColor"
                    />
                    {!isListening && (
                        <line
                            x1="4"
                            y1="4"
                            x2="20"
                            y2="20"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                        />
                    )}
                </svg>

                {isListening && (
                    <span className="listening-indicator">
                        <span className="pulse-ring"></span>
                        <span className="pulse-ring"></span>
                        <span className="pulse-ring"></span>
                    </span>
                )}
            </button>

            {transcript && isListening && (
                <div className="transcript-preview">
                    {transcript}
                </div>
            )}
        </div>
    );
};
export default VoiceInput;
