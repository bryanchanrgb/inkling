# Inkling Web Application Setup Guide

This guide will help you set up and run the Inkling web application with React frontend and FastAPI backend.

## Prerequisites

- Python 3.10 or higher
- Node.js 16 or higher and npm
- An AI API key (OpenAI, Anthropic, or OpenRouter) configured in your `.env` file

## Step 1: Install Backend Dependencies

Install Python dependencies using uv (recommended) or pip:

```bash
# Using uv (if you have it installed)
uv sync

# Or using pip
pip install -e .
```

The backend dependencies include:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- All existing Inkling dependencies

## Step 2: Install Frontend Dependencies

Navigate to the frontend directory and install npm packages:

```bash
cd frontend
npm install
cd ..
```

## Step 3: Configure Environment Variables

Make sure you have a `.env` file in the project root with your AI API key:

```env
# For OpenAI
OPENAI_API_KEY=your_key_here

# OR for Anthropic
ANTHROPIC_API_KEY=your_key_here

# OR for OpenRouter
OPENROUTER_API_KEY=your_key_here
```

Also configure your provider in `config.yaml` (default is "openrouter").

## Step 4: Start the Application

### Option A: Start Both Servers Separately (Recommended for Development)

**Terminal 1 - Backend:**
```bash
python run_api.py
```

The API will be available at http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

The frontend will open automatically at http://localhost:3000

### Option B: Use Startup Scripts

**On Windows:**
```bash
start_dev.bat
```

**On Linux/Mac:**
```bash
chmod +x start_dev.sh
./start_dev.sh
```

Note: The startup scripts will launch both servers in separate windows.

## Step 5: Access the Application

Open your browser and navigate to:
- **Frontend:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs (FastAPI auto-generated docs)

## Features

The web application provides:

1. **Topics Page** - View all learning topics, start quizzes, and generate additional questions
2. **Create Topic** - Create new topics with AI-generated knowledge graphs and questions
3. **Quiz Interface** - Take interactive quizzes with immediate feedback
4. **Quiz History** - View your quiz history and performance

## Mobile Support

The application is fully responsive and works on:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- Tablet devices

## Troubleshooting

### Backend won't start
- Make sure Python 3.10+ is installed
- Check that all dependencies are installed: `pip list`
- Verify your `.env` file has the correct API key
- Check that port 8000 is not already in use

### Frontend won't start
- Make sure Node.js 16+ is installed: `node --version`
- Check that npm packages are installed: `cd frontend && npm list`
- Verify port 3000 is not already in use
- Try deleting `frontend/node_modules` and `frontend/package-lock.json`, then run `npm install` again

### CORS Errors
- Make sure the backend is running on port 8000
- The frontend is configured to proxy requests to http://localhost:8000
- Check that the backend CORS middleware allows requests from http://localhost:3000

### API Connection Issues
- Verify the backend is running: visit http://localhost:8000/docs
- Check browser console for error messages
- Verify the API base URL in `frontend/src/services/api.js`

## Production Deployment

For production deployment:

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. The built files will be in `frontend/build/`. Serve these static files using a web server like nginx, or configure your backend to serve them.

3. Run the backend with a production ASGI server:
```bash
uvicorn inkling.api:app --host 0.0.0.0 --port 8000
```

## Development Tips

- The backend API documentation is available at http://localhost:8000/docs
- Hot reload is enabled for both frontend and backend during development
- Backend logs will show in the terminal where `run_api.py` is running
- Frontend errors and logs appear in the browser console

