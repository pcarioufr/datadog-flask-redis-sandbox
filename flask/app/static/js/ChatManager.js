import ChatUI from './ChatUI.js';
import TokenBuffer from './stream/TokenBuffer.js';
import StreamProcessor from './stream/StreamProcessor.js';
import ChatService from './services/ChatService.js';

class ChatManager {
    constructor() {
        this.ui = new ChatUI();
        this.setupEventListeners();
        this.currentPrompt = '';
        this.savePromptResolve = null;  // For handling initial prompt save
        this.isProcessing = false;
    }

    setupEventListeners() {
        this.ui.sendButton.addEventListener('click', () => this.sendMessage());
        this.ui.clearButton.addEventListener('click', () => this.clearHistory());
        this.ui.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !this.isProcessing) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Setup prompt modal events
        const editPromptButton = document.getElementById('edit-prompt-button');
        const saveButton = document.getElementById('save-prompt');
        const cancelButton = document.getElementById('cancel-prompt');
        const reloadButton = document.getElementById('reload-prompt');
        this.modal = document.getElementById('prompt-modal');
        this.promptEditor = document.getElementById('prompt-editor');

        editPromptButton.addEventListener('click', () => this.showPromptModal(false, false));
        cancelButton.addEventListener('click', () => this.hidePromptModal());
        reloadButton.addEventListener('click', () => this.reloadDefaultPrompt());
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.hidePromptModal();
        });

        // Setup user modal events
        const editUserButton = document.getElementById('edit-user-button');
        const cancelUserButton = document.getElementById('cancel-user');
        this.userModal = document.getElementById('user-modal');

        editUserButton.addEventListener('click', () => this.showUserModal());
        cancelUserButton.addEventListener('click', () => this.hideUserModal());
        this.userModal.addEventListener('click', (e) => {
            if (e.target === this.userModal) this.hideUserModal();
        });

        // Global escape key handler for both modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (this.modal.classList.contains('show')) {
                    this.hidePromptModal();
                }
                if (this.userModal.classList.contains('show')) {
                    this.hideUserModal();
                }
            }
        });

        saveButton.addEventListener('click', async () => {
            const success = await this.savePrompt();
            if (success && this.savePromptResolve) {
                this.savePromptResolve();
                this.savePromptResolve = null;
            }
        });
    }

    async showPromptModal(hideCloseButtons = false, isNewChat = false) {
        this.modal.classList.add('show');
        
        if (isNewChat) {
            // For new chats, load the default prompt automatically
            try {
                const response = await ChatService.loadDefaultPrompt();
                if (response.status === 'success') {
                    this.promptEditor.value = response.prompt;
                } else {
                    console.error('Failed to load default prompt:', response.error);
                    this.promptEditor.value = '';
                }
            } catch (error) {
                console.error('Error loading default prompt:', error);
                this.promptEditor.value = '';
            }
        } else {
            // For editing, just show current prompt
            this.promptEditor.value = this.currentPrompt;
        }
        
        this.promptEditor.focus();

        const cancelButton = this.modal.querySelector('#cancel-prompt');
        cancelButton.style.display = hideCloseButtons ? 'none' : '';
    }

    hidePromptModal() {
        this.modal.classList.remove('show');
    }

    async savePrompt() {
        const newPrompt = this.promptEditor.value.trim();
        try {
            await ChatService.savePrompt(newPrompt);
            this.currentPrompt = newPrompt;
            this.hidePromptModal();
            return true;
        } catch (error) {
            console.error('Error saving prompt:', error);
            this.ui.addMessage('Failed to save prompt. Please try again.', false);
            return false;
        }
    }

    showUserModal() {
        this.userModal.classList.add('show');
    }

    hideUserModal() {
        this.userModal.classList.remove('show');
    }

    setProcessingState(isProcessing) {
        this.isProcessing = isProcessing;
        this.ui.setInputState(!isProcessing);
    }

    async getWelcomeMessage() {
        const container = this.ui.showLoading();
        const tokenBuffer = new TokenBuffer(20, 50, container, this.ui);
        const streamProcessor = new StreamProcessor(tokenBuffer);

        try {
            const response = await ChatService.getWelcomeMessage();
            await streamProcessor.processStream(response);
        } catch (error) {
            console.error('Error getting welcome message:', error);
            container.loadingDots.remove();
            this.ui.addMessage('Failed to get welcome message. Please try again.', false);
            throw error; // Re-throw to let caller handle it
        }
    }

    async clearHistory() {
        this.setProcessingState(true);
        this.ui.clearMessages();

        try {
            // 1. Delete existing chat
            await ChatService.clearChat();
            
            // 2. Get new welcome message
            await this.getWelcomeMessage();
        } catch (error) {
            console.error('Error clearing chat:', error);
            this.ui.addMessage('Failed to clear chat history. Please try again.', false);
        } finally {
            this.setProcessingState(false);
        }
    }

    async sendMessage() {
        // Get and validate message content
        const message = this.ui.input.value.trim();
        if (!message || this.isProcessing) return;

        // Set processing state and show message
        this.setProcessingState(true);
        this.ui.addMessage(message, true);
        this.ui.input.value = '';

        // Create loading state and initialize token buffer for streaming
        const container = this.ui.showLoading();
        const tokenBuffer = new TokenBuffer(20, 50, container, this.ui);
        const streamProcessor = new StreamProcessor(tokenBuffer);

        try {
            // Make streaming request to chat API
            const response = await ChatService.sendMessage(message);
            await streamProcessor.processStream(response);
        } catch (error) {
            // Handle any errors during the streaming process
            console.error('Error:', error);
            container.loadingDots.remove();
            this.ui.addMessage('Sorry, there was an error processing your request.', false);
        } finally {
            this.setProcessingState(false);
        }
    }

    // Method to wait for prompt save
    waitForPromptSave() {
        return new Promise(resolve => {
            this.savePromptResolve = resolve;
        });
    }

    async reloadDefaultPrompt() {
        try {
            const response = await ChatService.loadDefaultPrompt();
            if (response.status === 'success') {
                this.promptEditor.value = response.prompt;
            } else {
                console.error('Failed to load default prompt:', response.error);
            }
        } catch (error) {
            console.error('Error loading default prompt:', error);
        }
    }
}

export default ChatManager; 