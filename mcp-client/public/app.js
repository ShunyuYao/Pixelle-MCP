/*
 Copyright (C) 2025 AIDC-AI
 This project is licensed under the MIT License (SPDX-License-identifier: MIT).
*/

// 定义基础服务地址常量
const MCP_SERVER_BASE_URL = "http://localhost:9002";

function initMcp() {
    const mcpStorgeStr = localStorage.getItem("mcp_storage_key");
    let needInit = false;
    if (!mcpStorgeStr) {
        needInit = true;
    } else {
        try {
            const mcpStorge = JSON.parse(mcpStorgeStr);
            needInit = !mcpStorge || mcpStorge.length === 0;
        } catch (error) {
            needInit = true;
        }
    }
    if (!needInit) {
        return;
    }

    const defaultMcp = [
        {
            "name": "pixelle-mcp", 
            "tools": [],
            "clientType": "sse",
            "command": null,
            "url": MCP_SERVER_BASE_URL + "/sse",
            "status": "disconnected"
        }
    ];
    localStorage.setItem("mcp_storage_key", JSON.stringify(defaultMcp));
}

initMcp();

// =================
// MCP工具侧边栏集成
// =================

// 全局侧边栏实例
let mcpSidebar = null;

/**
 * 初始化MCP工具侧边栏
 */
function initMCPToolsSidebar() {
    try {
        // 等待DOM和所需脚本加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(createSidebar, 1000); // 延迟1秒确保页面完全加载
            });
        } else {
            setTimeout(createSidebar, 1000);
        }
    } catch (error) {
        console.error('初始化MCP工具侧边栏失败:', error);
    }
}

/**
 * 创建侧边栏实例
 */
function createSidebar() {
    try {
        // 检查侧边栏管理器类是否已加载
        if (typeof MCPToolsSidebar === 'undefined') {
            console.warn('MCPToolsSidebar类未找到，请确保sidebar-manager.js已正确加载');
            // 尝试重新加载
            loadSidebarManager();
            return;
        }
        
        // 销毁已存在的实例
        if (mcpSidebar) {
            mcpSidebar.destroy();
        }
        
        // 创建新的侧边栏实例
        mcpSidebar = new MCPToolsSidebar({
            apiBaseUrl: 'http://localhost:9004/api',
            updateInterval: 3000, // 3秒轮询间隔
            maxRetries: 5,
            position: 'right',
            width: '420px'
        });
        
        // 将实例挂载到全局，供调试和外部访问
        window.mcpSidebar = mcpSidebar;
        
        console.log('MCP工具侧边栏创建成功');
        
    } catch (error) {
        console.error('创建侧边栏实例失败:', error);
        
        // 显示错误提示
        showSidebarError(error);
    }
}

/**
 * 动态加载侧边栏管理器
 */
function loadSidebarManager() {
    if (document.querySelector('script[src*="sidebar-manager.js"]')) {
        return; // 已经加载
    }
    
    const script = document.createElement('script');
    script.src = '/public/sidebar-manager.js';
    script.onload = () => {
        console.log('sidebar-manager.js 加载完成');
        setTimeout(createSidebar, 500);
    };
    script.onerror = () => {
        console.error('加载 sidebar-manager.js 失败');
        showSidebarError(new Error('无法加载侧边栏管理器脚本'));
    };
    document.head.appendChild(script);
}

/**
 * 显示侧边栏错误信息
 */
function showSidebarError(error) {
    // 创建简单的错误提示
    const errorDiv = document.createElement('div');
    errorDiv.id = 'mcp-sidebar-error';
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #f8d7da;
        color: #721c24;
        padding: 12px 16px;
        border: 1px solid #f5c6cb;
        border-radius: 6px;
        z-index: 9999;
        max-width: 300px;
        font-size: 14px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    `;
    errorDiv.innerHTML = `
        <strong>侧边栏加载失败</strong><br>
        <small>${error.message}</small><br>
        <button onclick="this.parentElement.remove(); initMCPToolsSidebar();" style="
            background: #721c24;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            margin-top: 8px;
            font-size: 12px;
        ">重试</button>
    `;
    
    // 移除已存在的错误提示
    const existing = document.getElementById('mcp-sidebar-error');
    if (existing) {
        existing.remove();
    }
    
    document.body.appendChild(errorDiv);
    
    // 10秒后自动移除错误提示
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 10000);
}

/**
 * 侧边栏快捷键和全局控制
 */
function setupGlobalSidebarControls() {
    // 快捷键支持
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            if (mcpSidebar) {
                mcpSidebar.toggle();
            } else {
                console.log('侧边栏未初始化，尝试重新创建...');
                initMCPToolsSidebar();
            }
        }
    });
    
    // 页面可见性变化时的处理
    document.addEventListener('visibilitychange', function() {
        if (mcpSidebar) {
            if (document.hidden) {
                mcpSidebar.stopPolling();
            } else {
                mcpSidebar.startPolling();
            }
        }
    });
    
    // 窗口大小变化处理
    let resizeTimeout;
    window.addEventListener('resize', function() {
        if (resizeTimeout) {
            clearTimeout(resizeTimeout);
        }
        resizeTimeout = setTimeout(() => {
            if (mcpSidebar) {
                mcpSidebar.adjustLayout();
            }
        }, 250);
    });
}

/**
 * API健康检查
 */
async function checkAPIHealth() {
    try {
        const response = await fetch('http://localhost:9004/api/health', {
            method: 'GET',
            signal: AbortSignal.timeout(5000) // 5秒超时
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('MCP工具API服务健康:', data);
            return true;
        } else {
            console.warn('MCP工具API服务响应异常:', response.status);
            return false;
        }
    } catch (error) {
        console.warn('MCP工具API服务连接失败:', error.message);
        return false;
    }
}

/**
 * 延迟初始化（等待API服务启动）
 */
async function delayedInit() {
    let attempts = 0;
    const maxAttempts = 10;
    const delay = 2000; // 2秒间隔
    
    while (attempts < maxAttempts) {
        console.log(`检查API服务状态 (${attempts + 1}/${maxAttempts})...`);
        
        const isHealthy = await checkAPIHealth();
        if (isHealthy) {
            console.log('API服务就绪，初始化侧边栏...');
            initMCPToolsSidebar();
            return;
        }
        
        attempts++;
        if (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    
    console.warn('API服务启动超时，但仍尝试初始化侧边栏...');
    initMCPToolsSidebar();
}

// 设置全局控制
setupGlobalSidebarControls();

// 延迟初始化（给API服务一些启动时间）
setTimeout(delayedInit, 3000);

console.log('MCP工具侧边栏集成模块已加载');
