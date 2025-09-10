# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pixelle MCP is an AIGC solution based on the MCP (Model Context Protocol) that seamlessly converts ComfyUI workflows into MCP tools with zero code. It integrates LLM capabilities with ComfyUI's ecosystem, supporting full-modal conversion (Text, Image, Sound/Speech, Video).

## Architecture

The project consists of three main services:

- **mcp-base** (Port 9001): Basic service providing file storage and shared service capabilities
- **mcp-server** (Port 9002): MCP server providing AIGC tools and services, built on ComfyUI
- **mcp-client** (Port 9003): Web interface built on Chainlit framework for MCP client functionality

## Development Commands

### Starting Services

**All services together:**
```bash
./run.sh                    # Start all services (foreground)
./run.sh start --daemon     # Start all services (background)
```

**Individual services (requires uv):**
```bash
# Base service
cd mcp-base && uv sync && uv run main.py

# Server service  
cd mcp-server && uv sync && uv run main.py

# Client service
cd mcp-client && uv sync && uv run main.py
```

**Using Docker:**
```bash
docker compose up -d
```

### Service Management

```bash
./run.sh stop           # Stop all services
./run.sh restart        # Restart all services  
./run.sh status         # Check service status
./run.sh logs [service] # View logs for specific service
```

### Testing

The project uses pytest for testing. Test dependencies are defined in mcp-base/pyproject.toml:
```bash
cd mcp-base
uv run pytest
```

## Configuration

The project uses a unified YAML configuration system (`config.yml`) that manages all three services. Key configuration areas:

- **ComfyUI Integration**: Base URL, API keys, executor type (HTTP/WebSocket)
- **LLM Models**: Supports OpenAI, Ollama, Gemini, DeepSeek, Claude, Qwen
- **Service Endpoints**: Host/port configuration for each service
- **Authentication**: Chainlit auth settings

Copy `config.yml.example` to `config.yml` and configure as needed.

## Core Components

### Workflow-to-MCP Tool System

The system automatically converts ComfyUI workflows (exported as API format) into MCP tools using a custom DSL syntax in node titles:

**Parameter Definition:**
```
$<param_name>.[~]<field_name>[!][:<description>]
```

- `param_name`: Parameter name for the MCP tool function
- `~`: Optional URL upload processing marker  
- `field_name`: Node input field mapping
- `!`: Required parameter marker
- `description`: Parameter description

**Example:**
- `$image.image!:Input image URL` - Creates required image parameter
- `$width.width:Image width, default 512` - Creates optional width parameter

### File Structure

- `mcp-server/workflows/`: Default workflow templates
- `mcp-server/data/custom_workflows/`: User-added workflows (auto-converted to MCP tools)
- `mcp-server/tools/`: Python-based MCP tools
- `mcp-client/auth/`: Authentication configuration
- `mcp-client/chat/`: Chat handling and conversation management

## Development Notes

- All services require Python 3.11+ and use `uv` for dependency management
- The system supports hot-reload in development mode using `chainlit run main.py -w`
- ComfyUI service must be running and accessible for workflow execution
- Workflows should be tested in ComfyUI canvas before deployment as MCP tools
- Use meaningful English names for workflow files as they become tool names

## Service URLs

- **Client**: http://localhost:9003 (Default credentials: dev/dev)  
- **Server**: http://localhost:9002/sse
- **Base Service**: http://localhost:9001/docs
- use the "comfy" conda environment and then use uv under mcp-base/ mcp-client/ and mcp-server/ paths to execute python
- conda的地址为/home/wangjianhua/miniconda3/condabin/conda