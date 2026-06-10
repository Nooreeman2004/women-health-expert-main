import { useState } from 'react';
import VoiceInput from './VoiceInput';
import './ChatInput.css';

const ChatInput = ({ onSendMessage, isLoading }) => {
    const [input, setInput] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (input.trim() && !isLoading) {
            const messageText = input;
            setInput(''); // Clear immediately for better UX
            try {
                await onSendMessage(messageText);
            } catch (error) {
                // If send fails, restore the message
                setInput(messageText);
            }
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const handleVoiceTranscript = (transcript) => {
        setInput(prev => prev + (prev ? ' ' : '') + transcript);
    };

    return (
        <form className="chat-input-container" onSubmit={handleSubmit}>
            <div className="input-wrapper">
                <VoiceInput
                    onTranscript={handleVoiceTranscript}
                    isDisabled={isLoading}
                />
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about women's health..."
                    className="chat-input"
                    disabled={isLoading}
                    maxLength={500}
                />
                <button
                    type="submit"
                    className="send-button"
                    disabled={!input.trim() || isLoading}
                >
                    <svg
                        width="24"
                        height="24"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path
                            d="M22 2L11 13"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                        <path
                            d="M22 2L15 22L11 13L2 9L22 2Z"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                </button>
            </div>
        </form>
    );
};

export default ChatInput;
