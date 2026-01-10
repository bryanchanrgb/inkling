# Quick Start Guide

Get the Inkling web application running in 5 minutes!

## Prerequisites Check

- ✅ Python 3.10+ installed? Run: `python --version`
- ✅ Node.js 16+ installed? Run: `node --version`
- ✅ AI API key configured? Check your `.env` file

## Quick Setup

### 1. Install Backend Dependencies
```bash
pip install -e .
```

Or with uv:
```bash
uv sync
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 3. Start the Application

**Windows:**
```bash
start_dev.bat
```

**Linux/Mac:**
```bash
chmod +x start_dev.sh
./start_dev.sh
```

**Or manually in two terminals:**

Terminal 1 (Backend):
```bash
python run_api.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm start
```

### 4. Open in Browser

Visit: **http://localhost:3000**

The backend API is available at: **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

## First Steps

1. Click "Create New Topic" in the navigation
2. Enter a topic name (e.g., "Python Programming")
3. Wait for AI to generate the knowledge graph and questions
4. Click "Start Quiz" on any topic to begin learning!

## Troubleshooting

**Backend won't start?**
- Check if port 8000 is free
- Verify your `.env` file has an API key
- Run `pip list` to check dependencies

**Frontend won't start?**
- Check if port 3000 is free
- Delete `frontend/node_modules` and run `npm install` again
- Check Node.js version: `node --version` (needs 16+)

**CORS errors?**
- Make sure backend is running on port 8000
- Check browser console for specific errors

## Need More Help?

See [SETUP.md](SETUP.md) for detailed setup instructions.

