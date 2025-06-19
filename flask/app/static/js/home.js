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

        // Then check if chat exists
        const chatExists = await ChatService.checkChatExists();
        
        // Initialize chat manager
        const chatManager = new ChatManager();

        if (!chatExists) {
            // For new chats, show prompt modal and wait for user input
            chatManager.showPromptModal(true, true);  // hideCloseButtons=true, isNewChat=true
            await chatManager.waitForPromptSave();

            // Get welcome message
            chatManager.setProcessingState(true);
            try {
                await chatManager.getWelcomeMessage();
            } catch (error) {
                chatManager.ui.addMessage('Failed to get welcome message. Please refresh the page.', false);
            } finally {
                chatManager.setProcessingState(false);
            }
        } else {
            // For existing chats, load history
            const chatData = await fetch('/ui/chat').then(r => r.json());
            chatData.history.forEach(msg => {
                chatManager.ui.addMessage(msg.content, msg.role === 'user');
            });
            chatManager.ui.setInputState(true);
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