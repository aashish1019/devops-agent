# 🚀 Agent Upgrade - Advanced CI Healing

## What Was Added

### 1️⃣ Failure Classification Module (`error_classifier.py`)

**Classifies failures into categories:**

| Pattern | Category |
|---------|----------|
| ModuleNotFoundError | DEPENDENCY |
| ImportError + missing package | DEPENDENCY |
| ValidationError | TYPE_ERROR |
| AssertionError | TEST_LOGIC |
| flake8 F401 | LINTING |
| SyntaxError | SYNTAX |
| IndentationError | INDENTATION |

**Fix priority order** (dependency first):
1. DEPENDENCY
2. IMPORT
3. LINTING
4. SYNTAX
5. INDENTATION
6. TYPE_ERROR
7. TEST_LOGIC
8. LOGIC

### 2️⃣ Dependency Resolver (`dependency_resolver.py`)

**When ImportError/ModuleNotFoundError occurs:**
1. Parse package name from error (e.g., `email_validator` → `email-validator`)
2. Check if exists in requirements.txt
3. If missing → append to requirements.txt
4. Run `pip install` to verify
5. Commit: `[AI-AGENT] Add missing dependency package-name`

**Package name mappings:**
- email_validator → email-validator
- yaml → pyyaml
- cv2 → opencv-python
- PIL → Pillow
- sklearn → scikit-learn

### 3️⃣ 3-Stage Execution Pipeline

**Stage 1 — Environment Check**
- Run `pip install -r requirements.txt`
- Run `pytest --collect-only` to catch import errors early
- If ImportError → classify as DEPENDENCY, fix, re-run

**Stage 2 — Static Checks**
- flake8, pylint, mypy, bandit (already integrated)
- Classify lint errors

**Stage 3 — Runtime Tests**
- Run `pytest`
- Classify logic/runtime/type errors

### 4️⃣ Layered Failure Iteration

**Fix order:**
1. Fix DEPENDENCY (add to requirements.txt) → pip install → rerun
2. Fix LINTING (autopep8/black)
3. Fix remaining errors

**Max iterations:** 5 (configurable)

## Key Insight

**Before:** Agent parsed stack trace → tried to modify schema code ❌  
**After:** Agent recognizes dependency error → modifies requirements.txt ✅

## New Files

- `backend/error_classifier.py` - Failure classification
- `backend/dependency_resolver.py` - Dependency fixing
- `AGENT_UPGRADE.md` - This file

## Usage

No configuration needed. The agent now:
1. Detects `ImportError: email-validator is not installed`
2. Classifies as DEPENDENCY (not syntax, not logic)
3. Adds `email-validator` to requirements.txt
4. Runs `pip install email-validator`
5. Re-runs tests
6. Continues to next error if any

## Testing

Test with a repo that has missing dependencies:
```python
# In some file: from pydantic import BaseModel  # needs pydantic[email] for email validation
# Error: email-validator is not installed
# Agent will add email-validator to requirements.txt automatically
```
