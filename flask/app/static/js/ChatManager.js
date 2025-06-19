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
        this.modal = document.getElementById('prompt-modal');
        this.userModal = document.getElementById('user-modal');
        
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

        editPromptButton.addEventListener('click', () => this.showConfigModal());
        cancelButton.addEventListener('click', () => this.hidePromptModal());
        reloadButton.addEventListener('click', () => this.reloadDefaultPrompt());
        this.savePromptButton.addEventListener('click', async () => {
            await this.savePromptAndModel();
        });

        // Setup user modal events
        const editUserButton = document.getElementById('edit-user-button');
        const cancelUserButton = document.getElementById('cancel-user');

        editUserButton.addEventListener('click', () => this.showUserModal());
        cancelUserButton.addEventListener('click', () => this.hideUserModal());
    }

    /**
     * Initialize a fresh chat (either new or after clearing)
     */
    async initializeFreshChat() {
        this.ui.clearMessages();
        await this.showConfigModalForNewChat();
        await this.getWelcomeMessage();
    }

    /**
     * Load existing chat history and configuration
     */
    async loadExistingChat() {
        try {
            const chatData = await fetch('/ui/chat').then(r => r.json());
            chatData.history.forEach(msg => {
                this.ui.addMessage(msg.content, msg.role === 'user');
            });
            this.ui.setInputState(true);
        } catch (error) {
            console.error('Error loading existing chat:', error);
            this.ui.showErrorModal('**Failed to load chat history**\n\nPlease refresh the page and try again.');
        }
    }

    /**
     * Show configuration modal for new chats (blocks until saved)
     */
    async showConfigModalForNewChat() {
        return new Promise(async (resolve, reject) => {
            try {
                // Load models and default prompt
                await this.loadModelsAndDefaultPrompt();
                
                // Show modal with no close button
                this.modal.classList.add('show');
                this.modal.querySelector('#cancel-prompt').style.display = 'none';
                this.promptEditor.focus();

                // Wait for save
                const saveHandler = async () => {
                    const success = await this.savePromptAndModel();
                    if (success) {
                        resolve();
                    }
                };

                this.savePromptButton.addEventListener('click', saveHandler, { once: true });
                
            } catch (error) {
                console.error('Error setting up new chat modal:', error);
                reject(error);
            }
        });
    }

    /**
     * Show configuration modal for editing existing settings
     */
    async showConfigModal() {
        try {
            // Load current config and models
            await this.loadModelsAndCurrentConfig();
            
            // Show modal with close button
            this.modal.classList.add('show');
            this.modal.querySelector('#cancel-prompt').style.display = '';
            this.promptEditor.focus();
            
        } catch (error) {
            console.error('Error showing config modal:', error);
            this.ui.showErrorModal('**Failed to load configuration**\n\nThere was an issue loading your chat settings. Please check your connection and try again.');
        }
    }

    /**
     * Load available models and default prompt (for new chats)
     */
    async loadModelsAndDefaultPrompt() {
        // Load models
        const modelsResponse = await ChatService.getAvailableModels();
        if (modelsResponse.status === 'success' && Array.isArray(modelsResponse.models)) {
            this.populateModelOptions(modelsResponse.models);
            // Select first model by default
            if (modelsResponse.models.length > 0) {
                this.modelRadioGroup.querySelector('.radio-option').classList.add('selected');
            }
        }

        // Load default prompt
        const promptResponse = await ChatService.loadDefaultPrompt();
        if (promptResponse.status === 'success') {
            this.promptEditor.value = promptResponse.prompt;
        } else {
            console.error('Failed to load default prompt:', promptResponse.error);
            this.promptEditor.value = '';
        }
    }

    /**
     * Load current configuration and available models (for existing chats)
     */
    async loadModelsAndCurrentConfig() {
        // Load models
        const modelsResponse = await ChatService.getAvailableModels();
        if (modelsResponse.status === 'success' && Array.isArray(modelsResponse.models)) {
            this.populateModelOptions(modelsResponse.models);
        }

        // Load current config
        const configResponse = await ChatService.loadConfig();
        if (configResponse.status === 'success') {
            this.currentPrompt = configResponse.prompt || '';
            this.promptEditor.value = this.currentPrompt;
            if (configResponse.model) {
                this.updateModelSelection(configResponse.model);
            }
        }
    }

    /**
     * Populate model radio options
     */
    populateModelOptions(models) {
        this.modelRadioGroup.innerHTML = '';
        models.forEach((model) => {
            const option = document.createElement('div');
            option.className = 'radio-option';
            option.dataset.model = model;
            option.textContent = model;
            
            // Add click handler
            option.addEventListener('click', () => {
                this.modelRadioGroup.querySelectorAll('.radio-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                option.classList.add('selected');
            });
            
            this.modelRadioGroup.appendChild(option);
        });
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

        this.setProcessingState(true);
        try {
            const response = await ChatService.getWelcomeMessage();
            await streamProcessor.processStream(response);
        } catch (error) {
            console.error('Error getting welcome message:', error);
            container.loadingDots.remove();
            this.ui.addMessage('Failed to get welcome message. Please try again.', false);
            throw error;
        } finally {
            this.setProcessingState(false);
        }
    }

    async clearHistory() {
        try {
            await ChatService.clearChat();
            await this.initializeFreshChat();
        } catch (error) {
            console.error('Error clearing chat:', error);
            this.ui.addMessage('Failed to clear chat history. Please try again.', false);
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