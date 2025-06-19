import ChatManager from './ChatManager.js';
import ChatService from './services/ChatService.js';

// Main initialization flow
async function initializeChat() {
    try {
        // First, check Ollama status
        const pingResponse = await fetch('/ui/ping');
        const pingData = await pingResponse.json();
        
        if (pingResponse.status !== 200) {
            throw new Error(pingData.error || 'Failed to connect to Ollama');
        }

        // Initialize chat manager
        const chatManager = new ChatManager();

        // Check if chat exists and handle accordingly
        const chatExists = await ChatService.checkChatExists();
        
        if (!chatExists) {
            // Use unified fresh chat initialization
            await chatManager.initializeFreshChat();
        } else {
            // Load existing chat
            await chatManager.loadExistingChat();
        }
        
    } catch (error) {
        console.error('Error initializing chat:', error);
        const chatManager = new ChatManager();
        
        // Use the error message from the backend directly
        const errorMessage = error.message || 'Failed to initialize chat. Please try again.';
        chatManager.ui.showErrorModal(errorMessage);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeChat); 