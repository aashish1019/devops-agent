# 🤖 Autonomous DevOps CI/CD Healing Agent

An intelligent DevOps agent with a React dashboard that automatically analyzes GitHub repositories, discovers and runs tests, identifies failures, generates fixes, and commits them to new branches.

## Features

- 🔍 **Automatic Repository Analysis**: Clones and analyzes GitHub repository structure
- 🧪 **Test Discovery**: Automatically discovers test files (pytest, npm/jest, etc.)
- 🐛 **Failure Detection**: Identifies and classifies failures (SYNTAX, LOGIC, IMPORT, TYPE_ERROR, INDENTATION, LINTING)
- 🔧 **Auto-Fixing**: Generates targeted fixes for detected errors
- 📝 **Auto-Commit**: Commits fixes with `[AI-AGENT]` prefix to new branches
- 📊 **Real-time Dashboard**: React-based dashboard with live progress updates
- 🔄 **CI/CD Monitoring**: Iterates until all tests pass (up to 5 retries)

## Architecture

```
devops-agent/
├── backend/          # Flask API server
│   ├── app.py       # Main API endpoints
│   └── requirements.txt
├── frontend/        # React dashboard
│   ├── src/
│   │   ├── App.js   # Main React component
│   │   └── App.css  # Styling
│   └── package.json
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- Git installed and configured

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend runs on `http://localhost:5000`

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`

## Usage

1. Open the React dashboard at `http://localhost:3000`
2. Enter a GitHub repository URL (e.g., `https://github.com/username/repo.git`)
3. Click "Analyze Repository"
4. Watch real-time progress as the agent:
   - Clones the repository
   - Discovers test files
   - Runs tests
   - Detects failures
   - Generates fixes
   - Commits to new branch
5. View comprehensive results including:
   - Test files discovered
   - Failures detected
   - Fixes applied
   - Test output
   - Download results.json

## API Endpoints

### POST `/api/analyze`
Analyze a GitHub repository.

**Request:**
```json
{
  "repo_url": "https://github.com/username/repo.git"
}
```

**Response:**
```json
{
  "job_id": "job_1234567890",
  "results": {
    "repository": "https://github.com/username/repo.git",
    "branch": "REPO_AI_Fix",
    "total_failures": 2,
    "total_fixes": 2,
    "iterations": 1,
    "final_status": "PASSED",
    "test_files": ["test_app.py"],
    "fixes": [...]
  }
}
```

### GET `/api/status/<job_id>`
Get status of an analysis job.

## Error Classification

The agent classifies errors into:
- **SYNTAX**: Syntax errors in code
- **IMPORT**: Missing or incorrect imports
- **TYPE_ERROR**: Type compatibility issues
- **INDENTATION**: Indentation errors
- **LINTING**: Code style/linting issues
- **LOGIC**: Logic/assertion failures

## Branch Naming Convention

Branches are created in format: `{REPO_NAME}_AI_Fix`

Example: `MYPROJECT_AI_Fix`

## Real-World Tools Integration

This agent now uses **real automated code fixing tools**:

### Automated Fixes (No AI Needed)
- **autopep8** - Auto-fixes Python linting issues
- **black** - Python code formatter
- **ESLint** - JavaScript/TypeScript linting fixes

### Static Analysis (Detection)
- **flake8** - Python linting detection
- **pylint** - Advanced error detection
- **mypy** - Type error detection
- **bandit** - Security vulnerability scanning

### AI/LLM (For Logic Bugs Only)
- Only complex logic bugs and test failures use AI/LLM
- Reduces costs and improves accuracy

See `INTEGRATION_GUIDE.md` for details.

## Production Considerations

For production use, you should:

1. **AI Integration**: Replace placeholder `generate_fix()` with actual AI/LLM calls (OpenAI GPT, Anthropic Claude, etc.)
2. **Agent Frameworks**: Consider AutoGen or LangGraph for multi-agent orchestration
3. **Authentication**: Add GitHub token authentication for private repos
4. **Security**: Implement rate limiting, input validation, and sandboxing
5. **Scalability**: Use task queues (Celery, RQ) for async processing
6. **Database**: Store job history in a database (PostgreSQL, MongoDB)
7. **Error Handling**: Enhanced error handling and retry logic
8. **CI/CD Integration**: Connect with GitHub Actions, GitLab CI, etc.

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a PR.
