import ChatManager from './ChatManager.js';
import TokenBuffer from './stream/TokenBuffer.js';
import StreamProcessor from './stream/StreamProcessor.js';
import ChatService from './services/ChatService.js';

// Main initialization flow
async function initializeChat() {
    const chatManager = new ChatManager();

    // 1. Check if chat exists
    const chatData = await ChatService.checkChatExists();

    // 2. Load current prompt
    try {
        const data = await ChatService.loadPrompt();
        chatManager.currentPrompt = data.prompt || '';
    } catch (error) {
        console.error('Error loading prompt:', error);
        chatManager.currentPrompt = '';
    }

    // 3. Initialize based on chat existence
    if (!chatData.exists) {
        // 3a. For new chats, show prompt modal and wait for user input
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
        // 3b. For existing chats, just load history
        chatData.history.forEach(msg => {
            chatManager.ui.addMessage(msg.content, msg.role === 'user');
        });
        chatManager.ui.setInputState(true);
    }
}

// Start the chat initialization
initializeChat().catch(error => {
    console.error('Failed to initialize chat:', error);
    document.body.innerHTML = '<div class="error-message">Failed to initialize chat. Please refresh the page.</div>';
}); 