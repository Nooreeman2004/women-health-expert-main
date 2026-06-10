import { useEffect, useRef } from 'react';
import Message from './Message';
import ChatInput from './ChatInput';
import './ChatInterface.css';

const ChatInterface = ({ messages, onSendMessage, isLoading }) => {
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <div className="header-content">
                    <div className="header-text">
                        <h1 className="chat-title">
                            <span className="text-gradient">Women's Health Expert</span>
                        </h1>
                        <p className="chat-subtitle">Your trusted AI health companion</p>
                    </div>
                </div>
            </div>

            <div className="messages-container">
                {messages.map((message, index) => (
                    <Message
                        key={message.id}
                        message={message}
                        delay={index * 50}
                    />
                ))}
                {isLoading && (
                    <div className="typing-indicator">
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <ChatInput
                onSendMessage={onSendMessage}
                isLoading={isLoading}
            />
        </div>
    );
};

export default ChatInterface;
