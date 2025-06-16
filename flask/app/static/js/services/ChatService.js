class ChatService {
    static async checkChatExists() {
        const response = await fetch('/ui/chat', {
            method: 'HEAD'
        });
        return response.ok;  // true if 200, false if 404
    }

    static async loadConfig() {
        const response = await fetch('/ui/config');
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to load configuration');
        }
        return response.json();
    }

    static async loadDefaultPrompt() {
        const response = await fetch('/ui/prompt/default');
        return response.json();
    }

    static async saveConfig(config) {
        const response = await fetch('/ui/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save configuration');
        }
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

    static async getModel() {
        const response = await fetch('/ui/config');
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