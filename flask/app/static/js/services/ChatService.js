class ChatService {
    static async checkChatExists() {
        const response = await fetch('/api/chat');
        return response.json();
    }

    static async loadPrompt() {
        const response = await fetch('/api/prompt');
        return response.json();
    }

    static async loadDefaultPrompt() {
        const response = await fetch('/api/prompt/default');
        return response.json();
    }

    static async savePrompt(prompt) {
        const response = await fetch('/api/prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        if (!response.ok) throw new Error('Failed to save prompt');
        return response.json();
    }

    static async clearChat() {
        const response = await fetch('/api/chat', { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to clear chat');
        return response.json();
    }

    static async getWelcomeMessage() {
        return fetch('/api/chat/welcome', {
            headers: {
                'Accept': 'text/event-stream'
            }
        });
    }

    static async sendMessage(message) {
        return fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Accept': 'text/event-stream',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: message })
        });
    }
}

export default ChatService; 