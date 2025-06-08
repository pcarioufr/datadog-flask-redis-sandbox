class StreamProcessor {
    constructor(tokenBuffer) {
        this.tokenBuffer = tokenBuffer;
        this.reader = null;
        this.decoder = new TextDecoder();
        this.buffer = '';
        this.dataBuffer = '';
    }

    async processStream(response) {
        this.reader = response.body.getReader();
        
        try {
            while (true) {
                const {value, done} = await this.reader.read();
                if (done) {
                    await this.handleStreamEnd();
                    break;
                }
                await this.processChunk(value);
            }
        } catch (error) {
            throw error; // Propagate error to caller
        }
    }

    async handleStreamEnd() {
        // Handle any remaining data when stream ends
        if (this.dataBuffer) {
            try {
                const parsed = JSON.parse(this.dataBuffer);
                if (parsed.content) {
                    this.tokenBuffer.append(parsed.content);
                }
            } catch (e) {
                console.warn('Failed to parse final buffer:', e);
            }
        }
        this.tokenBuffer.complete();
    }

    async processChunk(value) {
        // Decode incoming chunks and add to buffer
        this.buffer += this.decoder.decode(value, {stream: true});
        
        // Process complete lines from buffer
        while (true) {
            const newlineIndex = this.buffer.indexOf('\n');
            if (newlineIndex === -1) break;  // No complete line yet
            
            // Extract and process one line
            const line = this.buffer.slice(0, newlineIndex);
            this.buffer = this.buffer.slice(newlineIndex + 1);
            
            await this.processLine(line);
        }
    }

    async processLine(line) {
        if (line.trim() === '') return;  // Skip empty lines
        
        // Handle SSE data events
        if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            // Skip completion marker
            if (data === '[DONE]') return;
            
            // Accumulate and parse JSON data
            this.dataBuffer += data;
            try {
                const parsed = JSON.parse(this.dataBuffer);
                if (parsed.content) {
                    this.tokenBuffer.append(parsed.content);
                    this.dataBuffer = '';  // Reset buffer after successful parse
                }
            } catch (e) {
                // Ignore expected JSON parsing errors for incomplete chunks
                if (!e.message.includes('Unexpected end of JSON input')) {
                    console.warn('Parse attempt failed:', e);
                }
            }
        }
    }
}

export default StreamProcessor; 