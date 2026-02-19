# Setup Instructions - Step by Step

## Step 1: Setup Backend

Open a terminal/command prompt and run:

```bash
cd D:\PW1\devops-agent\backend
pip install -r requirements.txt
```

## Step 2: Setup Frontend

Open a **NEW** terminal/command prompt and run:

```bash
cd D:\PW1\devops-agent\frontend
npm install
```

## Step 3: Start Backend Server

In the backend terminal:

```bash
cd D:\PW1\devops-agent\backend
python app.py
```

The backend will start on `http://localhost:5000`

## Step 4: Start Frontend Dashboard

Open a **NEW** terminal/command prompt:

```bash
cd D:\PW1\devops-agent\frontend
npm start
```

The frontend will start on `http://localhost:3000`

## Quick Setup (Alternative)

Or use the batch files:

```bash
cd D:\PW1\devops-agent
setup.bat    # Install dependencies
start.bat    # Start both servers
```

## Important Notes

- Backend and Frontend need to run in **separate terminals**
- Backend runs on port 5000
- Frontend runs on port 3000
- Make sure you're in the correct directory before running commands
