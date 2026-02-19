# 🚀 Quick Start Guide

## ✅ Setup Complete!

All dependencies are installed and ready to use.

## Start the Application

### Terminal 1 - Backend Server
```bash
cd D:\PW1\devops-agent\backend
python app.py
```
Backend will run on: `http://localhost:5000`

### Terminal 2 - Frontend Dashboard
```bash
cd D:\PW1\devops-agent\frontend
npm install
npm start
```
Frontend will run on: `http://localhost:3000`

## Test the Agent

1. Open browser: `http://localhost:3000`
2. Enter a GitHub repository URL (e.g., `https://github.com/aashish1019/P11.git`)
3. Click "Analyze Repository"
4. Watch the agent:
   - Clone the repository
   - Discover test files
   - Run tests
   - Auto-fix linting issues (autopep8, black)
   - Detect issues (flake8, pylint, mypy, bandit)
   - Generate fixes for logic bugs
   - Create branch and commit

## Installed Tools

✅ **autopep8** - Auto-fixes Python linting  
✅ **black** - Python code formatter  
✅ **flake8** - Linting detection  
✅ **pylint** - Advanced error detection  
✅ **mypy** - Type error detection  
✅ **bandit** - Security scanning  

## Features

- 🔍 Automatic repository analysis
- 🧪 Test discovery and execution
- 🐛 Comprehensive error detection
- 🔧 Automated code fixing (linting/style)
- 🤖 AI-ready for logic bug fixes
- 📊 Real-time dashboard
- 📝 Auto-commit with [AI-AGENT] prefix

## Example Usage

```bash
# Analyze a repository
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/username/repo.git"}'
```

## Next Steps

1. **Add AI Integration**: Replace `generate_fix()` in `backend/app.py` with actual LLM calls
2. **GitHub Authentication**: Add token support for private repos
3. **Deploy**: Deploy to cloud (Heroku, AWS, etc.)

## Troubleshooting

- **Backend not starting**: Check if port 5000 is available
- **Frontend not connecting**: Ensure backend is running first
- **Git errors**: Make sure Git is installed and in PATH
- **Tool errors**: Check `backend/tools.py` for tool availability

## Documentation

- `README.md` - Full documentation
- `INTEGRATION_GUIDE.md` - Tool integration details
- `TOOLS_INTEGRATION_SUMMARY.md` - Tools overview

---

**Status**: ✅ Ready to use!
**Branch**: `kyu-nahin-ho-rahe-padhai`
**Repository**: https://github.com/aashish1019/devops-agent
