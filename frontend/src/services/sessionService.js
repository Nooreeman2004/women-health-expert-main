import { db } from './firebase';
import {
    collection,
    doc,
    setDoc,
    getDoc,
    updateDoc,
    arrayUnion,
    serverTimestamp
} from 'firebase/firestore';

/**
 * Session Service for managing chat sessions with Firebase Firestore
 * Falls back to localStorage if Firebase is not configured
 */

const SESSIONS_COLLECTION = 'chat_sessions';
const STORAGE_KEY = 'women_health_sessions';

// Check if Firebase is available
const isFirebaseAvailable = () => {
    return db !== undefined && db !== null;
};

/**
 * Create a new session
 */
export const createSession = async () => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const sessionData = {
        sessionId,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        messages: []
    };

    if (isFirebaseAvailable()) {
        try {
            await setDoc(doc(db, SESSIONS_COLLECTION, sessionId), {
                ...sessionData,
                createdAt: serverTimestamp(),
                updatedAt: serverTimestamp()
            });
            console.log('✅ Session created in Firebase:', sessionId);
        } catch (error) {
            console.error('❌ Error creating session in Firebase:', error);
            saveToLocalStorage(sessionId, sessionData);
        }
    } else {
        saveToLocalStorage(sessionId, sessionData);
    }

    return sessionId;
};

/**
 * Save a message to a session
 */
export const saveMessage = async (sessionId, message) => {
    const messageData = {
        text: message.text,
        sender: message.sender,
        timestamp: message.timestamp || new Date().toISOString()
    };

    if (isFirebaseAvailable()) {
        try {
            const sessionRef = doc(db, SESSIONS_COLLECTION, sessionId);
            await updateDoc(sessionRef, {
                messages: arrayUnion(messageData),
                updatedAt: serverTimestamp()
            });
            console.log('✅ Message saved to Firebase');
        } catch (error) {
            console.error('❌ Error saving message to Firebase:', error);
            saveMessageToLocalStorage(sessionId, messageData);
        }
    } else {
        saveMessageToLocalStorage(sessionId, messageData);
    }
};

/**
 * Load a session from Firebase or localStorage
 */
export const loadSession = async (sessionId) => {
    if (isFirebaseAvailable()) {
        try {
            const sessionRef = doc(db, SESSIONS_COLLECTION, sessionId);
            const sessionSnap = await getDoc(sessionRef);

            if (sessionSnap.exists()) {
                console.log('✅ Session loaded from Firebase');
                return sessionSnap.data();
            }
        } catch (error) {
            console.error('❌ Error loading session from Firebase:', error);
        }
    }

    // Fallback to localStorage
    return loadFromLocalStorage(sessionId);
};

/**
 * Get current session ID from localStorage
 */
export const getCurrentSessionId = () => {
    return localStorage.getItem('current_session_id');
};

/**
 * Set current session ID in localStorage
 */
export const setCurrentSessionId = (sessionId) => {
    localStorage.setItem('current_session_id', sessionId);
};

// ===== LocalStorage Fallback Functions =====

const saveToLocalStorage = (sessionId, sessionData) => {
    try {
        const sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        sessions[sessionId] = sessionData;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
        console.log('💾 Session saved to localStorage');
    } catch (error) {
        console.error('❌ Error saving to localStorage:', error);
    }
};

const saveMessageToLocalStorage = (sessionId, messageData) => {
    try {
        const sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        if (!sessions[sessionId]) {
            sessions[sessionId] = {
                sessionId,
                createdAt: new Date().toISOString(),
                messages: []
            };
        }
        sessions[sessionId].messages.push(messageData);
        sessions[sessionId].updatedAt = new Date().toISOString();
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
        console.log('💾 Message saved to localStorage');
    } catch (error) {
        console.error('❌ Error saving message to localStorage:', error);
    }
};

const loadFromLocalStorage = (sessionId) => {
    try {
        const sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        return sessions[sessionId] || null;
    } catch (error) {
        console.error('❌ Error loading from localStorage:', error);
        return null;
    }
};
