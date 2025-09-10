/**
 * MCP Tools Sidebar Manager
 * Handles sidebar creation, data fetching, rendering and user interaction
 */
class MCPToolsSidebar {
    constructor(options = {}) {
        this.options = {
            apiBaseUrl: 'http://localhost:9004/api',
            updateInterval: 2000,
            maxRetries: 3,
            position: 'right',
            width: '400px',
            ...options
        };
        
        this.container = null;
        this.isVisible = true;
        this.isMinimized = false;
        this.data = null;
        this.lastDataHash = null;
        this.updateTimer = null;
        this.retryCount = 0;
        
        this.init();
    }
    
    async init() {
        try {
            this.createSidebarContainer();
            this.bindEvents();
            await this.fetchAndRenderData();
            this.startPolling();
            
            console.log('MCP Tools Sidebar initialized successfully');
        } catch (error) {
            console.error('Sidebar initialization failed:', error);
        }
    }
    
    createSidebarContainer() {
        const existingSidebar = document.getElementById('mcp-tools-sidebar');
        if (existingSidebar) {
            existingSidebar.remove();
        }
        
        this.container = document.createElement('div');
        this.container.id = 'mcp-tools-sidebar';
        this.container.className = 'mcp-sidebar-container';
        this.container.style.cssText = `
            position: fixed;
            top: 0;
            ${this.options.position}: 0;
            width: ${this.options.width};
            height: 100vh;
            background: #ffffff;
            border-left: 1px solid #e1e5e9;
            box-shadow: -2px 0 10px rgba(0,0,0,0.1);
            z-index: 1000;
            display: flex;
            flex-direction: column;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 14px;
            overflow: hidden;
            transition: transform 0.3s ease;
        `;
        
        const header = document.createElement('div');
        header.className = 'mcp-sidebar-header';
        header.style.cssText = `
            padding: 16px;
            background: #f8f9fa;
            border-bottom: 1px solid #e1e5e9;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        `;
        
        const title = document.createElement('h3');
        title.textContent = '🔧 MCP Tools';
        title.style.cssText = 'margin: 0; font-size: 16px; color: #333;';
        
        const controls = document.createElement('div');
        controls.style.cssText = 'display: flex; gap: 8px;';
        
        const minimizeBtn = document.createElement('button');
        minimizeBtn.textContent = '📌';
        minimizeBtn.title = 'Minimize/Expand';
        minimizeBtn.style.cssText = `
            background: none;
            border: 1px solid #ccc;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        `;
        minimizeBtn.addEventListener('click', () => this.toggleMinimize());
        
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '✕';
        closeBtn.title = 'Close sidebar';
        closeBtn.style.cssText = `
            background: none;
            border: 1px solid #ccc;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            color: #666;
        `;
        closeBtn.addEventListener('click', () => this.hide());
        
        controls.appendChild(minimizeBtn);
        controls.appendChild(closeBtn);
        header.appendChild(title);
        header.appendChild(controls);
        
        const content = document.createElement('div');
        content.className = 'mcp-sidebar-content';
        content.style.cssText = `
            flex: 1;
            padding: 16px;
            overflow-y: auto;
        `;
        
        content.innerHTML = `
            <div class="loading-state" style="text-align: center; padding: 40px 20px; color: #666;">
                <div style="font-size: 24px; margin-bottom: 12px;">⏳</div>
                <div>Loading tool calls...</div>
            </div>
        `;
        
        this.container.appendChild(header);
        this.container.appendChild(content);
        document.body.appendChild(this.container);
    }
    
    bindEvents() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'S') {
                e.preventDefault();
                this.toggle();
            }
        });
        
        window.addEventListener('resize', () => {
            this.adjustLayout();
        });
    }
    
    async fetchData() {
        try {
            const response = await fetch(`${this.options.apiBaseUrl}/tool-calls`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                signal: AbortSignal.timeout(10000)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.retryCount = 0;
            return data;
            
        } catch (error) {
            this.retryCount++;
            console.error(`API request failed (attempt ${this.retryCount}/${this.options.maxRetries}):`, error);
            
            if (this.retryCount >= this.options.maxRetries) {
                throw new Error(`API request failed after ${this.options.maxRetries} retries: ${error.message}`);
            }
            
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, this.retryCount) * 1000));
            return this.fetchData();
        }
    }
    
    hasDataChanged(newData) {
        const newHash = JSON.stringify(newData);
        if (newHash !== this.lastDataHash) {
            this.lastDataHash = newHash;
            return true;
        }
        return false;
    }
    
    async fetchAndRenderData() {
        try {
            const newData = await this.fetchData();
            
            if (this.hasDataChanged(newData)) {
                this.data = newData;
                this.renderContent();
            }
            
        } catch (error) {
            this.renderError(error);
        }
    }
    
    renderContent() {
        const contentDiv = this.container.querySelector('.mcp-sidebar-content');
        if (!contentDiv) return;
        
        if (!this.data || !this.data.tools || this.data.tools.length === 0) {
            contentDiv.innerHTML = `
                <div class="empty-state" style="text-align: center; padding: 40px 20px; color: #666;">
                    <div style="font-size: 48px; margin-bottom: 16px;">🔧</div>
                    <h4 style="margin: 0 0 8px 0; color: #333;">No tool calls yet</h4>
                    <p style="margin: 0; font-size: 13px;">
                        When you use MCP tools in conversation,<br>
                        related information will be displayed here
                    </p>
                    <div style="margin-top: 16px; font-size: 12px; color: #999;">
                        Use <kbd>Ctrl+Shift+S</kbd> to toggle sidebar
                    </div>
                </div>
            `;
            return;
        }
        
        const statsHtml = this.renderStats(this.data.stats);
        const toolsHtml = this.data.tools.map(tool => this.renderTool(tool)).join('');
        
        contentDiv.innerHTML = `
            ${statsHtml}
            <div class="tools-list" style="margin-top: 16px;">
                ${toolsHtml}
            </div>
        `;
        
        this.bindToolInteractions(contentDiv);
    }
    
    renderStats(stats) {
        return `
            <div class="stats-section" style="
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 12px 16px;
                border-radius: 8px;
                border-left: 4px solid #007bff;
                margin-bottom: 16px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; color: #333;">Total: ${stats.total}</span>
                    <span style="font-size: 12px; color: #666;">
                        Success: <span style="color: #28a745;">${stats.success}</span> | 
                        Error: <span style="color: #dc3545;">${stats.error}</span>
                        ${stats.pending > 0 ? ` | Pending: <span style="color: #ffc107;">${stats.pending}</span>` : ''}
                    </span>
                </div>
            </div>
        `;
    }
    
    renderTool(tool) {
        const statusConfig = {
            success: { emoji: '✅', color: '#d4edda', borderColor: '#28a745' },
            error: { emoji: '❌', color: '#f8d7da', borderColor: '#dc3545' },
            pending: { emoji: '⏳', color: '#fff3cd', borderColor: '#ffc107' }
        };
        
        const config = statusConfig[tool.status] || statusConfig.pending;
        const timestamp = tool.timestamp ? new Date(tool.timestamp).toLocaleTimeString() : '';
        
        return `
            <div class="tool-item" data-tool-id="${tool.id}" style="
                background: linear-gradient(135deg, ${config.color} 0%, ${config.color}dd 100%);
                border: 1px solid ${config.borderColor};
                border-radius: 8px;
                margin-bottom: 12px;
                overflow: hidden;
            ">
                <div class="tool-header" style="
                    padding: 12px 16px;
                    cursor: pointer;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    user-select: none;
                ">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 16px;">${config.emoji}</span>
                        <span style="font-weight: 500; color: #333;">${tool.name}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 11px; color: #666;">
                        ${tool.duration ? `<span>Duration: ${tool.duration}</span>` : ''}
                        ${timestamp ? `<span>Time: ${timestamp}</span>` : ''}
                        <span class="collapse-icon" style="font-size: 12px; transition: transform 0.2s;">🔽</span>
                    </div>
                </div>
                <div class="tool-content" style="
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.3s ease;
                ">
                    <div style="padding: 0 16px 16px;">
                        <div class="tool-section" style="margin-bottom: 16px;">
                            <h5 style="
                                margin: 0 0 8px 0;
                                font-size: 12px;
                                font-weight: 600;
                                color: #0056b3;
                                background: #e7f1ff;
                                padding: 4px 8px;
                                border-left: 3px solid #007bff;
                                border-radius: 0 4px 4px 0;
                            ">📥 Input Parameters</h5>
                            <div class="tool-input" style="
                                background: #fff;
                                border: 1px solid #dee2e6;
                                border-radius: 6px;
                                padding: 12px;
                                max-height: 200px;
                                overflow-y: auto;
                                font-size: 12px;
                                font-family: 'Monaco', 'Menlo', monospace;
                                position: relative;
                            ">
                                ${this.formatInput(tool.input)}
                                <button class="copy-btn" data-copy-type="input" style="
                                    position: absolute;
                                    top: 8px;
                                    right: 8px;
                                    background: rgba(255,255,255,0.9);
                                    border: 1px solid #ccc;
                                    padding: 4px 6px;
                                    border-radius: 4px;
                                    font-size: 10px;
                                    cursor: pointer;
                                    opacity: 0.7;
                                ">📋</button>
                            </div>
                        </div>
                        <div class="tool-section">
                            <h5 style="
                                margin: 0 0 8px 0;
                                font-size: 12px;
                                font-weight: 600;
                                color: #1e7e34;
                                background: #e8f5e8;
                                padding: 4px 8px;
                                border-left: 3px solid #28a745;
                                border-radius: 0 4px 4px 0;
                            ">📤 Execution Result</h5>
                            <div class="tool-output" style="
                                background: #fff;
                                border: 1px solid #dee2e6;
                                border-radius: 6px;
                                padding: 12px;
                                max-height: 200px;
                                overflow-y: auto;
                                font-size: 12px;
                                font-family: 'Monaco', 'Menlo', monospace;
                                position: relative;
                                white-space: pre-wrap;
                                word-break: break-word;
                            ">
                                ${this.formatOutput(tool.output)}
                                <button class="copy-btn" data-copy-type="output" style="
                                    position: absolute;
                                    top: 8px;
                                    right: 8px;
                                    background: rgba(255,255,255,0.9);
                                    border: 1px solid #ccc;
                                    padding: 4px 6px;
                                    border-radius: 4px;
                                    font-size: 10px;
                                    cursor: pointer;
                                    opacity: 0.7;
                                ">📋</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    formatInput(input) {
        if (!input || Object.keys(input).length === 0) {
            return '<em style="color: #666;">No parameters</em>';
        }
        
        try {
            return JSON.stringify(input, null, 2)
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        } catch (error) {
            return String(input);
        }
    }
    
    formatOutput(output) {
        if (!output) {
            return '<em style="color: #666;">No output</em>';
        }
        
        if (typeof output === 'object' && output.value !== undefined) {
            let text = output.value;
            if (output.truncated) {
                text += `\n\n[Content truncated, full length: ${output.full_length} characters]`;
            }
            return text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
        
        return String(output).replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
    
    bindToolInteractions(container) {
        container.querySelectorAll('.tool-header').forEach(header => {
            header.addEventListener('click', (e) => {
                if (e.target.classList.contains('copy-btn')) return;
                
                const toolItem = header.closest('.tool-item');
                const content = toolItem.querySelector('.tool-content');
                const icon = header.querySelector('.collapse-icon');
                
                if (content.style.maxHeight === '0px' || !content.style.maxHeight) {
                    content.style.maxHeight = content.scrollHeight + 'px';
                    icon.style.transform = 'rotate(180deg)';
                } else {
                    content.style.maxHeight = '0px';
                    icon.style.transform = 'rotate(0deg)';
                }
            });
        });
        
        container.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                
                const toolItem = btn.closest('.tool-item');
                const toolId = toolItem.dataset.toolId;
                const copyType = btn.dataset.copyType;
                
                try {
                    const tool = this.data.tools.find(t => t.id === toolId);
                    if (!tool) return;
                    
                    let textToCopy = '';
                    if (copyType === 'input') {
                        textToCopy = JSON.stringify(tool.input, null, 2);
                    } else if (copyType === 'output') {
                        textToCopy = typeof tool.output === 'object' ? tool.output.value : tool.output;
                    }
                    
                    await navigator.clipboard.writeText(textToCopy);
                    
                    const originalText = btn.textContent;
                    btn.textContent = '✅';
                    btn.style.background = '#d4edda';
                    
                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.style.background = 'rgba(255,255,255,0.9)';
                    }, 2000);
                    
                } catch (error) {
                    console.error('Copy failed:', error);
                    btn.textContent = '❌';
                    setTimeout(() => btn.textContent = '📋', 2000);
                }
            });
        });
    }
    
    renderError(error) {
        const contentDiv = this.container.querySelector('.mcp-sidebar-content');
        if (!contentDiv) return;
        
        contentDiv.innerHTML = `
            <div class="error-state" style="
                text-align: center;
                padding: 40px 20px;
                color: #dc3545;
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 8px;
                margin: 16px 0;
            ">
                <div style="font-size: 32px; margin-bottom: 16px;">❌</div>
                <h4 style="margin: 0 0 12px 0; color: #721c24;">Loading Failed</h4>
                <p style="margin: 0 0 16px 0; font-size: 13px;">
                    ${error.message || 'Unable to connect to API server'}
                </p>
                <button onclick="window.mcpSidebar.fetchAndRenderData()" style="
                    background: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                ">Retry</button>
            </div>
        `;
    }
    
    startPolling() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        this.updateTimer = setInterval(() => {
            if (this.isVisible && !this.isMinimized) {
                this.fetchAndRenderData();
            }
        }, this.options.updateInterval);
    }
    
    stopPolling() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }
    
    adjustLayout() {
        if (!this.container) return;
        
        const screenWidth = window.innerWidth;
        
        if (screenWidth < 768) {
            this.container.style.width = '100vw';
            this.container.style.right = this.isVisible ? '0' : '-100vw';
        } else {
            this.container.style.width = this.options.width;
            this.container.style.right = this.isVisible ? '0' : `-${this.options.width}`;
        }
    }
    
    show() {
        if (!this.container) return;
        
        this.isVisible = true;
        this.container.style.transform = 'translateX(0)';
        this.adjustLayout();
        this.startPolling();
        
        this.fetchAndRenderData();
    }
    
    hide() {
        if (!this.container) return;
        
        this.isVisible = false;
        this.container.style.transform = 'translateX(100%)';
        this.stopPolling();
    }
    
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    toggleMinimize() {
        const content = this.container.querySelector('.mcp-sidebar-content');
        if (!content) return;
        
        this.isMinimized = !this.isMinimized;
        
        if (this.isMinimized) {
            content.style.display = 'none';
            this.container.style.height = 'auto';
        } else {
            content.style.display = 'block';
            this.container.style.height = '100vh';
        }
    }
    
    destroy() {
        this.stopPolling();
        
        if (this.container) {
            this.container.remove();
            this.container = null;
        }
        
        this.data = null;
        this.lastDataHash = null;
    }
}

// Export class for external use
window.MCPToolsSidebar = MCPToolsSidebar;
console.log('sidebar-manager.js loaded successfully');