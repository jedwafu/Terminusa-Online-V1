// Terminal Client for Terminusa Online

class TerminusaClient {
    constructor() {
        this.term = new Terminal({
            cursorBlink: true,
            cursorStyle: 'block',
            fontSize: 16,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            theme: {
                background: '#000000',
                foreground: '#ffffff',
                cursor: '#ffffff',
                selection: 'rgba(255, 255, 255, 0.3)',
                black: '#000000',
                red: '#e06c75',
                green: '#98c379',
                yellow: '#d19a66',
                blue: '#61afef',
                magenta: '#c678dd',
                cyan: '#56b6c2',
                white: '#abb2bf',
                brightBlack: '#5c6370',
                brightRed: '#e06c75',
                brightGreen: '#98c379',
                brightYellow: '#d19a66',
                brightBlue: '#61afef',
                brightMagenta: '#c678dd',
                brightCyan: '#56b6c2',
                brightWhite: '#ffffff'
            }
        });

        // Terminal addons
        this.fitAddon = new FitAddon.FitAddon();
        this.webLinksAddon = new WebLinksAddon.WebLinksAddon();
        this.webglAddon = new WebglAddon.WebglAddon();

        // Command line handling
        this.commandLine = '';
        this.commandHistory = [];
        this.historyIndex = -1;

        // WebSocket connection
        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        // Initialize
        this.initializeTerminal();
        this.connectWebSocket();
    }

    initializeTerminal() {
        // Load addons
        this.term.loadAddon(this.fitAddon);
        this.term.loadAddon(this.webLinksAddon);
        try {
            this.term.loadAddon(this.webglAddon);
        } catch (e) {
            console.warn('WebGL addon failed to load:', e);
        }

        // Open terminal in container
        this.term.open(document.getElementById('terminal-container'));
        this.fitAddon.fit();

        // Handle terminal input
        this.term.onKey(({ key, domEvent }) => {
            const printable = !domEvent.altKey && !domEvent.ctrlKey && !domEvent.metaKey;

            if (domEvent.keyCode === 13) { // Enter
                this.handleCommand();
            } else if (domEvent.keyCode === 8) { // Backspace
                if (this.commandLine.length > 0) {
                    this.commandLine = this.commandLine.slice(0, -1);
                    this.term.write('\b \b');
                }
            } else if (domEvent.keyCode === 38) { // Up arrow
                this.navigateHistory('up');
            } else if (domEvent.keyCode === 40) { // Down arrow
                this.navigateHistory('down');
            } else if (printable) {
                this.commandLine += key;
                this.term.write(key);
            }
        });

        // Handle resize
        window.addEventListener('resize', () => {
            this.fitAddon.fit();
        });
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.hostname}:6789`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('connected');
        };

        this.ws.onclose = () => {
            this.connected = false;
            this.updateConnectionStatus('disconnected');
            this.handleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus('error');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleServerMessage(data);
            } catch (e) {
                console.error('Failed to parse server message:', e);
            }
        };
    }

    handleServerMessage(data) {
        switch (data.type) {
            case 'output':
                this.term.writeln(data.content);
                break;
            case 'error':
                this.term.writeln(`\x1b[31m${data.content}\x1b[0m`); // Red text
                break;
            case 'success':
                this.term.writeln(`\x1b[32m${data.content}\x1b[0m`); // Green text
                break;
            case 'info':
                this.term.writeln(`\x1b[34m${data.content}\x1b[0m`); // Blue text
                break;
            case 'warning':
                this.term.writeln(`\x1b[33m${data.content}\x1b[0m`); // Yellow text
                break;
            case 'clear':
                this.term.clear();
                break;
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    handleCommand() {
        this.term.writeln('');
        if (this.commandLine.trim()) {
            // Add to history
            this.commandHistory.push(this.commandLine);
            if (this.commandHistory.length > 100) {
                this.commandHistory.shift();
            }
            this.historyIndex = this.commandHistory.length;

            // Send command to server
            if (this.connected) {
                this.ws.send(this.commandLine);
            } else {
                this.term.writeln('\x1b[31mNot connected to server\x1b[0m');
            }
        }
        this.commandLine = '';
        this.term.write('\x1b[32m>\x1b[0m '); // Green prompt
    }

    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return;

        if (direction === 'up' && this.historyIndex > 0) {
            this.historyIndex--;
        } else if (direction === 'down' && this.historyIndex < this.commandHistory.length) {
            this.historyIndex++;
        }

        // Clear current line
        this.term.write('\x1b[2K\r\x1b[32m>\x1b[0m ');
        
        if (this.historyIndex < this.commandHistory.length) {
            this.commandLine = this.commandHistory[this.historyIndex];
            this.term.write(this.commandLine);
        } else {
            this.commandLine = '';
        }
    }

    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateConnectionStatus('connecting');
            setTimeout(() => {
                this.connectWebSocket();
            }, 2000 * this.reconnectAttempts); // Exponential backoff
        } else {
            this.term.writeln('\x1b[31mFailed to connect to server after multiple attempts\x1b[0m');
        }
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;

        statusElement.className = status;
        switch (status) {
            case 'connected':
                statusElement.textContent = 'Connected';
                break;
            case 'disconnected':
                statusElement.textContent = 'Disconnected';
                break;
            case 'connecting':
                statusElement.textContent = 'Connecting...';
                break;
            case 'error':
                statusElement.textContent = 'Connection Error';
                break;
        }
    }
}

// Initialize terminal when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.terminusaClient = new TerminusaClient();
});
