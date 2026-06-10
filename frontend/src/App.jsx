import { useState, useEffect } from 'react';
import './App.css';
import ParticleBackground from './components/ParticleBackground';
import ChatInterface from './components/ChatInterface';
import {
  createSession,
  saveMessage,
  loadSession,
  getCurrentSessionId,
  setCurrentSessionId
} from './services/sessionService';
import ttsService from './services/textToSpeech';

// Initial welcome message
const INITIAL_MESSAGE = {
  id: 1,
  text: "Hello! I'm your Women's Health Expert. How can I help you today?",
  sender: 'ai',
  timestamp: new Date().toISOString()
};

function App() {
  const [messages, setMessages] = useState([{
    ...INITIAL_MESSAGE,
    timestamp: new Date(INITIAL_MESSAGE.timestamp)
  }]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // Initialize or load session
  useEffect(() => {
    const initSession = async () => {
      console.log('🔄 Starting session initialization...');

      // Get or create session ID immediately (synchronously)
      let currentSessionId = getCurrentSessionId();

      if (!currentSessionId) {
        // Create new session ID immediately
        currentSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        setCurrentSessionId(currentSessionId);
        console.log('🆕 Created new session ID:', currentSessionId);
      } else {
        console.log('📂 Using existing session ID:', currentSessionId);
      }

      // Set session ID immediately so app can work
      setSessionId(currentSessionId);
      console.log('✅ Session ID set:', currentSessionId);

      // Now handle Firebase/localStorage async (non-blocking)
      try {
        if (getCurrentSessionId() === currentSessionId) {
          // Try to load existing session data
          const sessionData = await loadSession(currentSessionId);
          if (sessionData && sessionData.messages && sessionData.messages.length > 0) {
            setMessages(sessionData.messages.map((msg, idx) => ({
              id: idx + 1,
              text: msg.text,
              sender: msg.sender,
              timestamp: new Date(msg.timestamp)
            })));
            console.log('✅ Loaded', sessionData.messages.length, 'messages from storage');
            return;
          }
        }

        // Save initial AI message
        await saveMessage(currentSessionId, {
          text: INITIAL_MESSAGE.text,
          sender: INITIAL_MESSAGE.sender,
          timestamp: INITIAL_MESSAGE.timestamp
        });
        console.log('✅ Initial message saved');
      } catch (error) {
        console.error('⚠️ Error with session storage (non-critical):', error);
      }
    };

    initSession();
  }, []);

  const sendMessage = async (messageText) => {
    console.log('🔍 sendMessage called with:', messageText);
    console.log('🔍 sessionId:', sessionId);

    if (!messageText.trim()) {
      console.log('❌ Message is empty');
      return;
    }

    if (!sessionId) {
      console.log('❌ No session ID - waiting for initialization');
      return;
    }

    console.log('✅ Sending message...');

    // Add user message
    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Save user message to Firebase (non-blocking)
    saveMessage(sessionId, {
      text: userMessage.text,
      sender: 'user',
      timestamp: userMessage.timestamp.toISOString()
    }).catch(err => console.warn('Failed to save user message:', err));


    try {
      // Call backend API with timeout
      console.log('📡 Calling backend API...');
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API error:', response.status, errorText);
        throw new Error(`API returned ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ API response:', data);
      const aiResponseText = data.response || 'I apologize, but I could not process your request.';

      // Add AI response
      const aiMessage = {
        id: Date.now() + 1,
        text: aiResponseText,
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);

      // Save AI message to Firebase (non-blocking)
      saveMessage(sessionId, {
        text: aiMessage.text,
        sender: 'ai',
        timestamp: aiMessage.timestamp.toISOString()
      }).catch(err => console.warn('Failed to save AI message:', err));


    } catch (error) {
      console.error('❌ Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: error.name === 'AbortError'
          ? 'Request timed out. Please try again.'
          : 'Sorry, I encountered an error. Please try again.',
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <ParticleBackground />
      <div className="content-wrapper">
        <ChatInterface
          messages={messages}
          onSendMessage={sendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

export default App;
