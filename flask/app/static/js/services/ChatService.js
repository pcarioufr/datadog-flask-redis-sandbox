class ChatService {
    static async checkChatExists() {
        const response = await fetch('/ui/chat');
        return response.json();
    }

    static async loadPrompt() {
        const response = await fetch('/ui/prompt');
        return response.json();
    }

    static async loadDefaultPrompt() {
        const response = await fetch('/ui/prompt/default');
        return response.json();
    }

    static async savePrompt(prompt) {
        const response = await fetch('/ui/prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        if (!response.ok) throw new Error('Failed to save prompt');
        return response.json();
    }

    static async clearChat() {
        const response = await fetch('/ui/chat', {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to clear chat');
        return response.json();
    }

    static async getWelcomeMessage() {
        return fetch('/ui/chat/init', {
            headers: {
                'Accept': 'text/event-stream'
            }
        });
    }

    static async sendMessage(message) {
        return fetch('/ui/chat', {
            method: 'POST',
            headers: {
                'Accept': 'text/event-stream',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: message })
        });
    }

    static async saveModel(model) {
        const response = await fetch('/ui/model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save model');
        }
        
        return response.json();
    }

    static async getModel() {
        const response = await fetch('/ui/model');
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to get model');
        }
        return response.json();
    }

    static async getAvailableModels() {
        const response = await fetch('/ui/models');
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to get models');
        }
        return response.json();
    }
}

export default ChatService; 