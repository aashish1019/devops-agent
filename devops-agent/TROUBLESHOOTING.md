# Troubleshooting Guide

## Error: "Failed to start analysis"

### Check 1: Backend is Running
Make sure the backend server is running:
```bash
cd D:\PW1\devops-agent\backend
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

### Check 2: Frontend Can Connect to Backend
Open browser console (F12) and check for errors.

Test backend manually:
```bash
curl http://localhost:5000/api/health
```
Or open in browser: `http://localhost:5000/api/health`

### Check 3: Git is Installed
The backend needs Git to clone repositories. Check:
```bash
git --version
```

If Git is not installed:
- Download from: https://git-scm.com/download/win
- Make sure to add Git to PATH during installation

### Check 4: CORS Issues
If you see CORS errors in browser console, make sure:
- `flask-cors` is installed: `pip install flask-cors`
- Backend has `CORS(app)` enabled (already in code)

### Check 5: Network Connectivity
- Backend should be on: `http://localhost:5000`
- Frontend should be on: `http://localhost:3000`
- Frontend proxy should point to backend (configured in package.json)

### Check 6: Repository URL Format
Make sure the URL is correct:
- ✅ Good: `https://github.com/username/repo.git`
- ✅ Good: `https://github.com/username/repo`
- ❌ Bad: `github.com/username/repo` (missing https://)

### Check 7: Browser Console Errors
Open browser DevTools (F12) → Console tab
Look for:
- Network errors (red)
- CORS errors
- API connection errors

### Common Solutions

1. **Restart both servers**:
   - Stop backend (Ctrl+C)
   - Stop frontend (Ctrl+C)
   - Start backend first
   - Then start frontend

2. **Check ports are not in use**:
   ```bash
   netstat -ano | findstr :5000
   netstat -ano | findstr :3000
   ```

3. **Clear browser cache**:
   - Hard refresh: Ctrl+Shift+R
   - Or clear cache in browser settings

4. **Check firewall/antivirus**:
   - May be blocking localhost connections

## Still Having Issues?

Check the backend terminal for error messages - they will show what went wrong during analysis.
