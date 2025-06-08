class TokenBuffer {
    constructor(minChunkSize, maxDelay, container, chatUI) {
        this.buffer = '';
        this.minChunkSize = minChunkSize;
        this.maxDelay = maxDelay;
        this.timeout = null;
        this.container = container.messageDiv;
        this.loadingDots = container.loadingDots;
        this.contentDiv = null;
        this.chatUI = chatUI;  // Store reference to ChatUI for scrolling
    }

    initializeContent() {
        if (!this.contentDiv) {
            this.contentDiv = document.createElement('div');
            this.contentDiv.className = 'message-content';
            this.container.insertBefore(this.contentDiv, this.loadingDots);
        }
    }

    append(text) {
        this.initializeContent();
        this.buffer += text;
        
        if (this.buffer.length >= this.minChunkSize) {
            this.flush();
            return;
        }
        
        if (!this.timeout) {
            this.timeout = setTimeout(() => this.flush(), this.maxDelay);
        }
    }

    flush() {
        if (this.buffer) {
            const span = document.createElement('span');
            span.textContent = this.buffer;
            span.className = 'token';
            this.contentDiv.appendChild(span);
            this.buffer = '';
            this.chatUI.smoothScrollToBottom();  // Scroll after adding new content
        }
        if (this.timeout) {
            clearTimeout(this.timeout);
            this.timeout = null;
        }
    }

    clear() {
        this.buffer = '';
        if (this.timeout) {
            clearTimeout(this.timeout);
            this.timeout = null;
        }
    }

    complete() {
        this.flush();
        if (this.loadingDots) {
            this.loadingDots.remove();
        }
    }
}

export default TokenBuffer; 