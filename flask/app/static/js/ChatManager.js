import ChatUI from './ChatUI.js';
import TokenBuffer from './stream/TokenBuffer.js';
import StreamProcessor from './stream/StreamProcessor.js';
import ChatService from './services/ChatService.js';

class ChatManager {
    constructor() {
        this.ui = new ChatUI();
        this.currentPrompt = '';
        this.isProcessing = false;
        this.promptEditor = document.getElementById("prompt-editor");
        this.modelRadioGroup = document.getElementById("model-radio-group");
        this.savePromptButton = document.getElementById('save-prompt');
        
        // Initialize event listeners
        this.setupEventListeners();
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
        const cancelButton = document.getElementById('cancel-prompt');
        const reloadButton = document.getElementById('reload-prompt');
        this.modal = document.getElementById('prompt-modal');

        editPromptButton.addEventListener('click', () => this.showPromptModal(false, false));
        cancelButton.addEventListener('click', () => this.hidePromptModal());
        reloadButton.addEventListener('click', () => this.reloadDefaultPrompt());

        // Regular save button handler
        this.savePromptButton.addEventListener('click', async () => {
            await this.savePromptAndModel();
        });

        // Setup user modal events
        const editUserButton = document.getElementById('edit-user-button');
        const cancelUserButton = document.getElementById('cancel-user');
        this.userModal = document.getElementById('user-modal');

        editUserButton.addEventListener('click', () => this.showUserModal());
        cancelUserButton.addEventListener('click', () => this.hideUserModal());
    }

    async loadCurrentModel() {
        try {
            const response = await ChatService.loadConfig();
            if (response.status === 'success' && response.model) {
                this.updateModelSelection(response.model);
            }
        } catch (error) {
            console.error('Error loading current configuration:', error);
        }
    }

    updateModelSelection(selectedModel) {
        const options = this.modelRadioGroup.querySelectorAll('.radio-option');
        options.forEach(option => {
            if (option.dataset.model === selectedModel) {
                option.classList.add('selected');
            } else {
                option.classList.remove('selected');
            }
        });
    }

    async showPromptModal(hideCloseButtons = false, isNewChat = false) {
        this.modal.classList.add('show');
        
        try {
            // Always load available models
            const modelsResponse = await ChatService.getAvailableModels();

            if (modelsResponse.status === 'success' && Array.isArray(modelsResponse.models)) {
                this.modelRadioGroup.innerHTML = '';
                modelsResponse.models.forEach((model, index) => {
                    const option = document.createElement('div');
                    option.className = 'radio-option';
                    option.dataset.model = model;
                    option.textContent = model;
                    
                    // Add click handler
                    option.addEventListener('click', () => {
                        if (option.classList.contains('selected')) {
                            // If already selected, deselect it
                            option.classList.remove('selected');
                        } else {
                            // Deselect all other options and select this one
                            this.modelRadioGroup.querySelectorAll('.radio-option').forEach(opt => {
                                opt.classList.remove('selected');
                            });
                            option.classList.add('selected');
                        }
                    });
                    
                    this.modelRadioGroup.appendChild(option);

                    // For new chats, select the first model by default
                    if (isNewChat && index === 0) {
                        option.classList.add('selected');
                    }
                });
        }
        
        if (isNewChat) {
                // For new chats, just load the default prompt
                const response = await ChatService.loadDefaultPrompt();
                if (response.status === 'success') {
                    this.promptEditor.value = response.prompt;
                } else {
                    console.error('Failed to load default prompt:', response.error);
                this.promptEditor.value = '';
            }
        } else {
                // For existing chats, load current config
                const configResponse = await ChatService.loadConfig();
                if (configResponse.status === 'success') {
                    this.currentPrompt = configResponse.prompt || '';
                    this.promptEditor.value = this.currentPrompt;
                    if (configResponse.model) {
                        this.updateModelSelection(configResponse.model);
                    }
                }
                    }
                } catch (error) {
            console.error('Error in prompt modal setup:', error);
            // For new chats, we can continue with empty prompt and first model
            if (!isNewChat) {
                this.ui.showErrorModal('**Failed to load configuration**\n\nThere was an issue loading your chat settings. Please check your connection and try again.');
            }
        }
        
        this.promptEditor.focus();

        const cancelButton = this.modal.querySelector('#cancel-prompt');
        cancelButton.style.display = hideCloseButtons ? 'none' : '';
    }

    hidePromptModal() {
        this.modal.classList.remove('show');
    }

    async savePromptAndModel() {
        const newPrompt = this.promptEditor.value.trim();
        const selectedOption = this.modelRadioGroup.querySelector('.radio-option.selected');
        const newModel = selectedOption ? selectedOption.dataset.model : null;
        
        if (!newModel) {
            this.ui.addMessage('Please select a model.', false);
            return false;
        }
        
        try {
            const response = await ChatService.saveConfig({
                prompt: newPrompt,
                model: newModel
            });

            if (response.status === 'success') {
                this.currentPrompt = newPrompt;
                this.hidePromptModal();
                return true;
            } else {
                this.ui.addMessage('Failed to save configuration. Please try again.', false);
                return false;
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.ui.addMessage('Failed to save configuration. Please try again.', false);
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
        return new Promise((resolve) => {
            const saveHandler = async () => {
                const success = await this.savePromptAndModel();
                if (success) {
                    resolve();
                }
            };

            this.savePromptButton.addEventListener('click', saveHandler, { once: true });
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