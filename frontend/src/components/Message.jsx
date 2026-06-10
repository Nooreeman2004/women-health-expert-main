import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Message.css';
import ttsService from '../services/textToSpeech';

const Message = ({ message, delay = 0 }) => {
    const isUser = message.sender === 'user';
    const [isSpeaking, setIsSpeaking] = useState(false);

    const handleSpeak = () => {
        if (isSpeaking) {
            ttsService.stop();
            setIsSpeaking(false);
        } else {
            setIsSpeaking(true);
            ttsService.speak(message.text).then(() => {
                setIsSpeaking(false);
            }).catch(() => {
                setIsSpeaking(false);
            });
        }
    };

    return (
        <div
            className={`message ${isUser ? 'message-user' : 'message-ai'}`}
            style={{ animationDelay: `${delay}ms` }}
        >
            <div className="message-content">
                {isUser ? (
                    <p className="message-text">{message.text}</p>
                ) : (
                    <div className="message-text markdown-content">
                        <ReactMarkdown>{message.text}</ReactMarkdown>
                    </div>
                )}
                <div className="message-footer">
                    <span className="message-time">
                        {new Date(message.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                        })}
                    </span>
                    {!isUser && (
                        <button
                            className={`message-speaker ${isSpeaking ? 'speaking' : ''}`}
                            onClick={handleSpeak}
                            title={isSpeaking ? 'Stop speaking' : 'Play message'}
                        >
                            {isSpeaking ? (
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <rect x="6" y="4" width="4" height="16" fill="currentColor" />
                                    <rect x="14" y="4" width="4" height="16" fill="currentColor" />
                                </svg>
                            ) : (
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M3 9V15H7L12 20V4L7 9H3Z" fill="currentColor" />
                                    <path d="M16.5 12C16.5 10.23 15.48 8.71 14 7.97V16.02C15.48 15.29 16.5 13.77 16.5 12Z" fill="currentColor" />
                                </svg>
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Message;
