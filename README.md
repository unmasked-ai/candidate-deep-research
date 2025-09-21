# Candidate Deep Research - Multi Agent Demo

> [!TIP]
> Updated for Coral Server v1

## Overview

This is a candidate research application that demonstrates the power of multi-agent orchestration using the Coral Protocol. The app allows users to input candidate information and generates comprehensive research reports through coordinated AI agents.

This repository contains the complete application stack including the frontend, backend, and Coral server components.

### App Functionality
1. **User Input**: Users provide candidate details through the interface
2. **Multi-Agent Research**: The system orchestrates multiple specialized agents via Coral to gather comprehensive information
3. **Results Display**: Research findings are compiled and presented in an organized format
4. **PDF Export**: Users can export the complete research report as a PDF document

### Docker Hub Deployment
The agents in this repository are packaged and uploaded to Docker Hub under the username `donshelly` with the prefix `coral-allaboard-`. These containerized agents are utilized by the application to perform distributed research tasks.

## Prerequisites

```bash
./check-dependencies.sh
```

This script will automatically check for valid versions of all prerequisites.

## Running Coral Server

First, make sure you have pulled the coral-server submodule:
```bash
git submodule init
git submodule update
```

Now, we can cd into the coral-server folder, and start it.

```bash
cd coral-server
REGISTRY_FILE_PATH="../registry.toml" ./gradlew run
```

> [!NOTE]
> We use the `REGISTRY_FILE_PATH` environment variable to tell Coral Server where our custom `registry.toml` is.

## Running Coral Studio

```bash
npx @coral-protocol/coral-studio
```

We can then visit Coral Studio at [http://localhost:3000/](http://localhost:3000/)

# What next?
Check out our [docs](https://docs.coralprotocol.org/) for more information on how Coral Studio works, how to write agents that work with Coral, and using Coral in your applications.

