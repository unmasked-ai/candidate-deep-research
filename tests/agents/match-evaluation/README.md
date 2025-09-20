# Match Evaluation Agent - Test Suite

## Quick Start

```bash
# From the repository root or agent directory
cd agents/match-evaluation
uv sync

# Run all tests (no external dependencies)
uv run python ../../tests/agents/match-evaluation/test_ci.py

# Run original unit tests
uv run python ../../tests/agents/match-evaluation/test_scoring.py

# Run LLM integration tests (requires API key in .env)
uv run python ../../tests/agents/match-evaluation/test_complete.py
```

## Test Files Overview

### 🚀 CI/CD Tests (Automated)
- **`test_ci.py`** - Comprehensive CI test suite (no external dependencies)
- **`test_scoring.py`** - Unit tests for core scoring functions

### 🤖 LLM Integration Tests (Manual)
- **`test_complete.py`** - Real LLM integration with x.ai Grok
- **`test_simple_llm.py`** - Basic LLM connection testing
- **`test_llm_integration.py`** - Advanced LLM scenarios

### 🔧 Mock/Simulation Tests
- **`test_coral_mock.py`** - Mock Coral protocol testing
- **`test_full_agent.py`** - Complete agent simulation

## Test Results

### ✅ CI Test Suite (`test_ci.py`)
All tests passing:
- ✅ Imports: Schema and function imports
- ✅ Schema Validation: Pydantic model consistency
- ✅ Scoring Algorithm: Core logic with known inputs
- ✅ Justification Generation: Word count and content validation
- ✅ Error Handling: Invalid input management
- ✅ Performance: Response time benchmarks (< 0.1s)
- ✅ Decision Boundaries: Score → decision logic

### ✅ Unit Tests (`test_scoring.py`)
All tests passing:
- ✅ Perfect Match: 96/100 → proceed
- ✅ Poor Match: 24/100 → reject
- ✅ Moderate Match: 70/100 → maybe
- ✅ Missing Data: 62/100 → maybe (graceful degradation)

## Automated Testing (GitHub Actions)

Tests run automatically on:
- Every push to `main` branch
- Every pull request to `main` branch
- Manual workflow triggers

**Workflow File**: `agents/match-evaluation/.github/workflows/test.yml`

## Development Workflow

1. Make changes to agent code in `agents/match-evaluation/`
2. Run tests locally: `uv run python ../../tests/agents/match-evaluation/test_ci.py`
3. Ensure all tests pass before creating PR
4. GitHub Actions will automatically validate on PR creation
5. Tests must pass before merge to main is allowed

## Path Configuration

All test files include automatic path resolution to import the agent's `main.py`:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../agents/match-evaluation'))
```

This allows tests to run from any location while importing the agent code correctly.

---

**Note**: This test suite ensures the match-evaluation agent maintains quality and functionality across all development and deployment scenarios.