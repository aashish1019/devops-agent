# Integration Guide: Real-World Code Fixing Tools

## Overview

This DevOps Agent now integrates with real-world automated code fixing tools instead of placeholder logic.

## Tools Integrated

### Python Tools

1. **autopep8** - Auto-fixes Python linting issues (PEP 8)
2. **black** - Code formatter for Python
3. **flake8** - Linting tool for Python
4. **pylint** - Advanced linting and error detection
5. **mypy** - Static type checker
6. **bandit** - Security vulnerability scanner

### JavaScript/TypeScript Tools

1. **ESLint** - Linting and auto-fixing (via npx)

## Installation

Install all Python tools:

```bash
cd backend
pip install -r requirements.txt
```

For JavaScript projects, ESLint will be run via `npx` (no installation needed).

## How It Works

### 1. Automated Fixes (No AI Needed)

**Linting/Formatting Issues:**
- `autopep8` automatically fixes PEP 8 violations
- `black` formats code consistently
- `ESLint --fix` fixes JavaScript linting issues

These run **automatically** before AI fixes.

### 2. Static Analysis (Detection)

**Error Detection:**
- `flake8` - Detects linting issues
- `pylint` - Detects errors, warnings, and code smells
- `mypy` - Detects type errors
- `bandit` - Detects security vulnerabilities

These tools **detect** issues but don't fix them automatically (except linting).

### 3. AI/LLM Fixes (For Logic Bugs)

Only **logic bugs** and **test failures** are sent to AI/LLM for fixing.

## Workflow

```
1. Clone Repository
   ↓
2. Discover Test Files
   ↓
3. Run Tests → Detect Failures
   ↓
4. Run Static Analysis Tools → Detect Issues
   ↓
5. Auto-Fix Linting/Style Issues (autopep8, black, ESLint)
   ↓
6. Detect Remaining Issues (flake8, pylint, mypy, bandit)
   ↓
7. AI/LLM Fixes for Logic Bugs Only
   ↓
8. Commit & Push
```

## Benefits

✅ **Faster**: Automated tools fix issues instantly  
✅ **More Accurate**: Real tools vs placeholder logic  
✅ **Comprehensive**: Catches issues AI might miss  
✅ **Cost-Effective**: Only use AI for complex logic bugs  
✅ **Production-Ready**: Uses industry-standard tools  

## Configuration

### Disable Specific Tools

Edit `backend/tools.py` to disable tools you don't want:

```python
def auto_fix_python_file(file_path):
    # Comment out tools you don't want
    # success, output = run_autopep8(file_path)
    success, output = run_black(file_path)
    return fixes_applied
```

### Add More Tools

Add new tools in `backend/tools.py`:

```python
def run_your_tool(file_path):
    result = subprocess.run(['your-tool', file_path], ...)
    return issues, errors
```

## Next Steps

### Recommended Integrations

1. **LangGraph / AutoGen** - For multi-agent orchestration
2. **GitHub Actions** - For CI/CD automation
3. **SonarQube** - For deep static analysis
4. **GenProg / Recoder** - For program repair

### Example: Adding LangGraph

```python
from langgraph.graph import StateGraph

def create_repair_workflow():
    workflow = StateGraph()
    workflow.add_node("lint", run_linting_tools)
    workflow.add_node("fix", run_auto_fixes)
    workflow.add_node("test", run_tests)
    workflow.add_node("ai_fix", ai_repair_logic)
    return workflow
```

## References

- **AutoGen**: https://github.com/microsoft/autogen
- **LangGraph**: https://github.com/langchain-ai/langgraph
- **Program Repair**: https://github.com/program-repair
- **autopep8**: https://github.com/hhatto/autopep8
- **black**: https://github.com/psf/black
- **flake8**: https://github.com/PyCQA/flake8
