/**
 * Rocket.Chat Widget - Context Sensitive Chat Integration
 * Automatically detects page context and provides relevant chat functionality
 */

class RocketChatWidget {
    constructor() {
        this.isOpen = false;
        this.isMinimized = false;
        this.context = this.detectContext();
        this.rag = new ClientRAG();
        this.openrouterApiKey = null;
        this.init();
    }

    /**
     * Detect the current page context
     */
    detectContext() {
        const path = window.location.pathname;
        const page = path.split('/').pop() || 'index.html';
        
        // Get additional context from the page
        const context = {
            page: page,
            url: window.location.href,
            title: document.title,
            timestamp: new Date().toISOString()
        };

        // Add page-specific context
        switch (page) {
            case 'index.html':
                context.type = 'dashboard';
                context.description = 'Main dashboard with processing statistics';
                break;
            case 'browse.html':
                context.type = 'data_browser';
                context.description = 'Browse extracted budget data';
                context.filters = this.getBrowseFilters();
                break;
            case 'chat.html':
                context.type = 'chat_interface';
                context.description = 'RAG-powered chat with documents';
                break;
            case 'progress.html':
                context.type = 'processing_log';
                context.description = 'Processing timeline and history';
                break;
            case 'sankey.html':
                context.type = 'budget_visualization';
                context.description = 'Interactive budget flow diagram';
                context.visualization = this.getVisualizationContext();
                break;
            default:
                context.type = 'unknown';
                context.description = 'Unknown page';
        }

        // Add selected data context if available
        context.selectedData = this.getSelectedData();
        
        return context;
    }

    /**
     * Get browse page filters context
     */
    getBrowseFilters() {
        try {
            const branchFilter = document.getElementById('branchFilter')?.value;
            const categoryFilter = document.getElementById('categoryFilter')?.value;
            const searchFilter = document.getElementById('searchFilter')?.value;
            
            return {
                branch: branchFilter || null,
                category: categoryFilter || null,
                search: searchFilter || null
            };
        } catch (e) {
            return null;
        }
    }

    /**
     * Get visualization context for Sankey page
     */
    getVisualizationContext() {
        try {
            const fiscalYear = document.getElementById('fiscalYear')?.value;
            const minAmount = document.getElementById('minAmount')?.value;
            const flowType = document.getElementById('flowType')?.value;
            
            return {
                fiscalYear: fiscalYear || null,
                minAmount: minAmount || null,
                flowType: flowType || null
            };
        } catch (e) {
            return null;
        }
    }

    /**
     * Get selected data context (table rows, chart elements, etc.)
     */
    getSelectedData() {
        const selected = {
            tableRows: [],
            chartElements: [],
            searchResults: []
        };

        // Check for selected table rows
        try {
            const selectedRows = document.querySelectorAll('tr.selected, tr.highlighted');
            selectedRows.forEach(row => {
                const cells = Array.from(row.cells).map(cell => cell.textContent.trim());
                selected.tableRows.push(cells);
            });
        } catch (e) {
            // Ignore errors
        }

        // Check for selected chart elements (Plotly)
        try {
            if (window.Plotly) {
                const chartDiv = document.getElementById('sankeyChart');
                if (chartDiv && chartDiv.data) {
                    // This would need to be implemented based on Plotly selection events
                    selected.chartElements = [];
                }
            }
        } catch (e) {
            // Ignore errors
        }

        return selected;
    }

    /**
     * Initialize the widget
     */
    async init() {
        this.createWidget();
        this.attachEventListeners();
        this.updateContext();
        
        // Initialize RAG system
        await this.initializeRAG();
        
        // Check for API key
        this.checkApiKey();
    }

    /**
     * Create the widget HTML
     */
    createWidget() {
        // Create widget container
        const widget = document.createElement('div');
        widget.id = 'rocket-chat-widget';
        widget.innerHTML = `
            <div class="rc-widget-container">
                <!-- Chat Toggle Button -->
                <div class="rc-toggle-button" id="rc-toggle">
                    <div class="rc-toggle-icon">💬</div>
                    <div class="rc-toggle-text">Chat</div>
                </div>
                
                <!-- Chat Panel -->
                <div class="rc-chat-panel" id="rc-chat-panel" style="display: none;">
                    <div class="rc-chat-header">
                        <div class="rc-chat-title">
                            <span class="rc-chat-icon">🚀</span>
                            <span>Rocket.Chat</span>
                        </div>
                        <div class="rc-chat-controls">
                            <button class="rc-minimize-btn" id="rc-minimize">−</button>
                            <button class="rc-close-btn" id="rc-close">×</button>
                        </div>
                    </div>
                    
                    <div class="rc-context-info" id="rc-context-info">
                        <div class="rc-context-title">Current Context:</div>
                        <div class="rc-context-details" id="rc-context-details"></div>
                    </div>
                    
                    <div class="rc-chat-messages" id="rc-messages">
                    <div class="rc-welcome-message">
                        <div class="rc-message rc-bot-message">
                            <div class="rc-message-avatar">🤖</div>
                            <div class="rc-message-content">
                                <p>Hello! I can see you're on the <strong>${this.context.description}</strong> page.</p>
                                <p>${this.getWelcomeMessage()}</p>
                            </div>
                        </div>
                    </div>
                    </div>
                    
                    <div class="rc-chat-input-container">
                        <div class="rc-input-wrapper">
                            <input type="text" class="rc-chat-input" id="rc-input" placeholder="Ask about the data...">
                            <button class="rc-send-btn" id="rc-send">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add styles
        const styles = document.createElement('style');
        styles.textContent = `
            #rocket-chat-widget {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 10000;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            .rc-widget-container {
                position: relative;
            }

            .rc-toggle-button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 20px;
                border-radius: 50px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 10px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                transition: all 0.3s ease;
                user-select: none;
            }

            .rc-toggle-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }

            .rc-toggle-icon {
                font-size: 20px;
            }

            .rc-toggle-text {
                font-weight: 600;
                font-size: 14px;
            }

            .rc-chat-panel {
                position: absolute;
                bottom: 70px;
                right: 0;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            .rc-chat-header {
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white;
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .rc-chat-title {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
            }

            .rc-chat-icon {
                font-size: 18px;
            }

            .rc-chat-controls {
                display: flex;
                gap: 10px;
            }

            .rc-minimize-btn, .rc-close-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 25px;
                height: 25px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                transition: background 0.3s;
            }

            .rc-minimize-btn:hover, .rc-close-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }

            .rc-context-info {
                background: #f8f9fa;
                padding: 12px 15px;
                border-bottom: 1px solid #dee2e6;
                font-size: 12px;
            }

            .rc-context-title {
                font-weight: 600;
                color: #495057;
                margin-bottom: 5px;
            }

            .rc-context-details {
                color: #6c757d;
                line-height: 1.4;
            }

            .rc-chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background: #f8f9fa;
            }

            .rc-message {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }

            .rc-user-message {
                flex-direction: row-reverse;
            }

            .rc-message-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                flex-shrink: 0;
            }

            .rc-bot-message .rc-message-avatar {
                background: #667eea;
                color: white;
            }

            .rc-user-message .rc-message-avatar {
                background: #28a745;
                color: white;
            }

            .rc-message-content {
                max-width: 80%;
                padding: 10px 15px;
                border-radius: 15px;
                line-height: 1.4;
                font-size: 14px;
            }

            .rc-bot-message .rc-message-content {
                background: white;
                color: #333;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }

            .rc-user-message .rc-message-content {
                background: #667eea;
                color: white;
            }

            .rc-chat-input-container {
                padding: 15px;
                background: white;
                border-top: 1px solid #dee2e6;
            }

            .rc-input-wrapper {
                display: flex;
                gap: 10px;
                align-items: center;
            }

            .rc-chat-input {
                flex: 1;
                padding: 10px 15px;
                border: 2px solid #dee2e6;
                border-radius: 25px;
                outline: none;
                font-size: 14px;
                transition: border-color 0.3s;
            }

            .rc-chat-input:focus {
                border-color: #667eea;
            }

            .rc-send-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 25px;
                cursor: pointer;
                font-weight: 600;
                font-size: 14px;
                transition: all 0.3s;
            }

            .rc-send-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
            }

            .rc-welcome-message {
                margin-bottom: 15px;
            }

            /* Minimized state */
            .rc-chat-panel.minimized {
                height: 50px;
            }

            .rc-chat-panel.minimized .rc-chat-messages,
            .rc-chat-panel.minimized .rc-context-info,
            .rc-chat-panel.minimized .rc-chat-input-container {
                display: none;
            }

            /* Mobile responsiveness */
            @media (max-width: 768px) {
                .rc-chat-panel {
                    width: calc(100vw - 40px);
                    right: -10px;
                }
            }
        `;

        document.head.appendChild(styles);
        document.body.appendChild(widget);
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Toggle button
        const toggleButton = document.getElementById('rc-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', () => {
                console.log('Toggle button clicked');
                this.toggleChat();
            });
        } else {
            console.error('Toggle button not found');
        }

        // Close button
        document.getElementById('rc-close').addEventListener('click', () => {
            this.closeChat();
        });

        // Minimize button
        document.getElementById('rc-minimize').addEventListener('click', () => {
            this.toggleMinimize();
        });

        // Send button
        document.getElementById('rc-send').addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter key in input
        document.getElementById('rc-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Update context when page changes
        window.addEventListener('popstate', () => {
            this.updateContext();
        });

        // Update context when filters change (for browse page)
        const filterElements = ['branchFilter', 'categoryFilter', 'searchFilter'];
        filterElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => {
                    this.updateContext();
                });
            }
        });
    }

    /**
     * Toggle chat panel
     */
    toggleChat() {
        const panel = document.getElementById('rc-chat-panel');
        if (this.isOpen) {
            panel.style.display = 'none';
            this.isOpen = false;
        } else {
            panel.style.display = 'flex';
            this.isOpen = true;
            this.updateContext();
            document.getElementById('rc-input').focus();
        }
    }

    /**
     * Close chat panel
     */
    closeChat() {
        document.getElementById('rc-chat-panel').style.display = 'none';
        this.isOpen = false;
    }

    /**
     * Toggle minimize
     */
    toggleMinimize() {
        const panel = document.getElementById('rc-chat-panel');
        if (this.isMinimized) {
            panel.classList.remove('minimized');
            this.isMinimized = false;
        } else {
            panel.classList.add('minimized');
            this.isMinimized = true;
        }
    }

    /**
     * Update context information
     */
    updateContext() {
        this.context = this.detectContext();
        const contextDetails = document.getElementById('rc-context-details');
        if (contextDetails) {
            let contextText = `${this.context.description}`;
            
            if (this.context.filters) {
                const activeFilters = Object.entries(this.context.filters)
                    .filter(([key, value]) => value)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join(', ');
                if (activeFilters) {
                    contextText += ` | Filters: ${activeFilters}`;
                }
            }

            if (this.context.visualization) {
                const viz = this.context.visualization;
                const vizInfo = [];
                if (viz.fiscalYear) vizInfo.push(`FY: ${viz.fiscalYear}`);
                if (viz.minAmount) vizInfo.push(`Min: $${viz.minAmount}K`);
                if (viz.flowType) vizInfo.push(`Type: ${viz.flowType}`);
                if (vizInfo.length > 0) {
                    contextText += ` | ${vizInfo.join(', ')}`;
                }
            }

            contextDetails.textContent = contextText;
        }
    }

    /**
     * Send message
     */
    async sendMessage() {
        const input = document.getElementById('rc-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addMessage('user', message);
        input.value = '';

        // Show typing indicator
        this.showTyping();

        try {
            // Determine API endpoint based on environment
            const apiUrl = this.getApiUrl();
            
            // Call the server-side chat endpoint
            const response = await fetch(`${apiUrl}/api/chat-widget`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    context: this.context,
                    history: this.getChatHistory()
                })
            });

            this.hideTyping();

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                if (response.status === 503) {
                    this.addMessage('bot', errorData.message || 'The chat service is not available. Please try again later.');
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return;
            }

            const data = await response.json();
            this.addMessage('bot', data.answer, data.sources);

        } catch (error) {
            this.hideTyping();
            console.error('Error sending message:', error);
            
            // Provide helpful fallback message
            const isGitHubPages = window.location.hostname.includes('github.io');
            if (isGitHubPages) {
                this.addMessage('bot', `I can see you're on the GitHub Pages site! The chat API isn't available here, but I can help you understand what you're looking at.\n\nYou're currently on: **${this.context.description}**\n\nFor full chat functionality, please run the local development server:\n\`\`\`bash\npython src/chat_api.py\n\`\`\`\n\nThen visit: http://localhost:5000`);
            } else {
                this.addMessage('bot', 'Sorry, I encountered an error. Please make sure the API server is running and try again.');
            }
        }
    }

    /**
     * Call OpenRouter API directly
     */
    async callOpenRouter(message, context, history) {
        const systemPrompt = `You are a helpful assistant that answers questions about Department of Defense appropriations and reprogramming documents.

You are currently helping a user who is on: ${this.context?.description || 'an unknown page'}

Use the following context from the documents to answer the user's question. If the context doesn't contain relevant information, say so.

DOCUMENT CONTEXT:
${context}

Instructions:
- Answer based on the provided context
- Be aware of the user's current page context: ${this.context?.description || 'unknown'}
- If the user has active filters, consider them when answering
- Cite specific documents when possible
- If the context doesn't have the answer, say "I don't have enough information in the documents to answer that."
- Be concise but thorough
- Use specific numbers and details from the documents
- If the user is browsing data, help them understand what they're looking at`;

        const messages = [
            { role: 'system', content: systemPrompt },
            ...history.slice(-5), // Last 5 messages
            { role: 'user', content: message }
        ];

        const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.openrouterApiKey}`,
                'Content-Type': 'application/json',
                'HTTP-Referer': window.location.origin,
                'X-Title': 'Comptroller War Gov Chat Widget'
            },
            body: JSON.stringify({
                model: 'anthropic/claude-3.5-sonnet',
                messages: messages,
                temperature: 0.7,
                max_tokens: 1000
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(`OpenRouter API error: ${response.status} - ${errorData.error?.message || 'Unknown error'}`);
        }

        const data = await response.json();
        return data.choices[0].message.content;
    }

    /**
     * Get API URL based on environment
     */
    getApiUrl() {
        const isGitHubPages = window.location.hostname.includes('github.io');
        const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        
        if (isGitHubPages) {
            // For GitHub Pages with Actions deployment, use the same domain
            return window.location.origin;
        } else if (isLocalhost) {
            return `http://${window.location.hostname}:5000`;
        } else {
            // Assume local development
            return 'http://localhost:5000';
        }
    }

    /**
     * Get welcome message based on environment
     */
    getWelcomeMessage() {
        const isGitHubPages = window.location.hostname.includes('github.io');
        
        if (isGitHubPages) {
            return `I can help you understand what you're looking at! The chat system is powered by AI and has access to the budget data.`;
        } else {
            return `How can I help you with the budget data?`;
        }
    }

    /**
     * Initialize the RAG system
     */
    async initializeRAG() {
        try {
            await this.rag.initialize();
            console.log('✅ RAG system initialized');
        } catch (error) {
            console.warn('⚠️ RAG system not available:', error.message);
            // Show a helpful message in the chat
            this.addMessage('bot', 'RAG system is not available. This means the document embeddings are not loaded. The chat will work but without document context.');
        }
    }

    /**
     * Check for OpenRouter API key
     */
    checkApiKey() {
        // API key is now handled server-side via GitHub Secrets
        // No need to prompt user for API key
        this.openrouterApiKey = 'server-managed';
    }

    // API key prompt removed - now handled server-side via GitHub Secrets

    /**
     * Add message to chat
     */
    addMessage(role, content, sources = null) {
        const messagesDiv = document.getElementById('rc-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `rc-message rc-${role}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'rc-message-avatar';
        avatar.textContent = role === 'user' ? 'U' : '🤖';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'rc-message-content';
        contentDiv.innerHTML = `<p>${content}</p>`;

        // Add sources if available
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.style.marginTop = '8px';
            sourcesDiv.style.fontSize = '12px';
            sourcesDiv.style.color = '#666';
            sourcesDiv.innerHTML = '<strong>Sources:</strong><br>' + 
                sources.map(s => `• ${s.filename} (${(s.score * 100).toFixed(0)}%)`).join('<br>');
            contentDiv.appendChild(sourcesDiv);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        messagesDiv.appendChild(messageDiv);

        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    /**
     * Show typing indicator
     */
    showTyping() {
        const messagesDiv = document.getElementById('rc-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'rc-message rc-bot-message';
        typingDiv.id = 'rc-typing';
        
        const avatar = document.createElement('div');
        avatar.className = 'rc-message-avatar';
        avatar.textContent = '🤖';
        
        const content = document.createElement('div');
        content.className = 'rc-message-content';
        content.innerHTML = '<p>Typing...</p>';
        
        typingDiv.appendChild(avatar);
        typingDiv.appendChild(content);
        messagesDiv.appendChild(typingDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    /**
     * Hide typing indicator
     */
    hideTyping() {
        const typing = document.getElementById('rc-typing');
        if (typing) {
            typing.remove();
        }
    }

    /**
     * Get chat history
     */
    getChatHistory() {
        const messages = document.querySelectorAll('#rc-messages .rc-message:not(.rc-welcome-message)');
        const history = [];
        
        messages.forEach(msg => {
            const role = msg.classList.contains('rc-user-message') ? 'user' : 'assistant';
            const content = msg.querySelector('.rc-message-content p').textContent;
            history.push({ role, content });
        });
        
        return history;
    }
}

// Initialize the widget when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rocketChatWidget = new RocketChatWidget();
});

// Export for potential external use
window.RocketChatWidget = RocketChatWidget;