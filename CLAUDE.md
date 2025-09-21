# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent demo project for the Coral Protocol, designed to showcase orchestration of multiple AI agents. The project demonstrates how to set up and run Coral Server with custom agents for various tasks including web scraping (Firecrawl), GitHub integration, and user interface interactions.

## Key Architecture Components

### Coral Server
- Java-based server (using Gradle) located in the `coral-server` submodule
- Requires `REGISTRY_FILE_PATH` environment variable to locate agent configurations
- Started with: `cd coral-server && REGISTRY_FILE_PATH="../registry.toml" ./gradlew run`

### Agent System
All agents follow a similar pattern:
- Located in `agents/` directory with three main agents: `firecrawl`, `github`, and `interface`
- Each agent has:
  - `main.py`: Core implementation using LangChain and MCP adapters
  - `coral-agent.toml`: Agent configuration and metadata
  - `pyproject.toml`: Python dependencies (requires Python >=3.13)
  - `run_agent.sh`: Execution script

### Agent Registry
- `registry.toml`: Defines local agents and their paths for Coral Server
- Each agent is registered as a `[[local-agent]]` with its path

## Development Commands

### Prerequisites Check
```bash
./check-dependencies.sh
```

### Starting Coral Server
```bash
git submodule init
git submodule update
cd coral-server
REGISTRY_FILE_PATH="../registry.toml" ./gradlew run
```

### Starting Coral Studio (UI)
```bash
npx @coral-protocol/coral-studio
```
Access at: http://localhost:3000/

### Agent Installation
For Python agents (uses uv package manager):
```bash
cd agents/<agent-name>
./install.sh  # If available
```

## Important Implementation Details

### Agent Communication Pattern
- Agents use `REQUEST_QUESTION_TOOL` and `ANSWER_QUESTION_TOOL` for inter-agent communication
- Connection via WebSocket to Coral Server using `CORAL_CONNECTION_URL`
- Each agent requires environment configuration (loaded from `.env` or runtime environment)

### Configuration Environment Variables
Required for agents:
- `CORAL_CONNECTION_URL`: WebSocket connection to Coral Server
- `CORAL_AGENT_ID`: Unique agent identifier
- `MODEL_NAME`, `MODEL_PROVIDER`, `MODEL_API_KEY`: LLM configuration
- `MODEL_TEMPERATURE`, `MODEL_TOKEN_LIMIT`: Model parameters

### Python Requirements
- All agents require Python >=3.13
- Dependencies managed via `pyproject.toml` using uv package manager
- Key dependencies: LangChain ecosystem, langchain-mcp-adapters for MCP integration