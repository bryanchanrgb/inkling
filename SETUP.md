# Inkling Web Application Setup Guide

This guide will help you set up and run the Inkling web application with React frontend and FastAPI backend.

## Quick Start

Get up and running in 5 minutes:

1. **Install Backend Dependencies:**
   ```bash
   pip install -e .
   ```

2. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Start the Application:**
   - **Windows:** `start_dev.bat`
   - **Linux/Mac:** `chmod +x start_dev.sh && ./start_dev.sh`
   - **Or manually:** Run `python run_api.py` in one terminal and `cd frontend && npm start` in another

4. **Open in Browser:** http://localhost:3000

For detailed instructions, continue reading below.

---

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

## Exposing to Public Internet (ngrok)

To access your application from other devices or share it with others, you can use ngrok to create a secure tunnel to your local server.

### Installing ngrok

1. **Download ngrok:**
   - Visit [ngrok.com/download](https://ngrok.com/download)
   - Download for your operating system (Windows, macOS, or Linux)
   - Extract the executable to a location in your PATH, or keep it in a convenient directory

2. **Sign up for a free account:**
   - Go to [ngrok.com/signup](https://ngrok.com/signup)
   - Create a free account (required for custom domains and longer sessions)

3. **Authenticate:**
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```
   (Get your auth token from the ngrok dashboard after signing up)

### Exposing the Application

Since your React app proxies API requests to the backend, you only need to expose the frontend port (3000):

1. **Start your application** (backend and frontend) as described in Step 4

2. **In a new terminal, start ngrok:**
   ```bash
   ngrok http 3000
   ```

3. **Copy the public URL:**
   ngrok will display a forwarding URL like:
   ```
   Forwarding  https://abc123.ngrok-free.app -> http://localhost:3000
   ```

4. **Access from any device:**
   - Open the `https://` URL on any device (phone, tablet, another computer)
   - The React dev server will proxy API requests to your local backend automatically

### ngrok Tips

- **Free tier limitations:** Free accounts have session time limits and random URLs each time
- **Custom domains:** Paid plans allow custom domains and reserved URLs
- **HTTPS:** ngrok provides HTTPS automatically (required for some mobile features)
- **Inspect traffic:** Visit http://localhost:4040 to see requests going through ngrok
- **Keep it running:** Keep the ngrok terminal open while you want the public URL active

### Security Note

When exposing your application publicly:
- Only expose during development/testing
- Don't expose production applications without proper security measures
- Be aware that anyone with the ngrok URL can access your application
- Consider using ngrok's IP restrictions or authentication features for sensitive applications

## Features

The web application provides:

1. **Topics Page** - View all learning topics, start quizzes, and view progress
2. **Create Topic** - Create new topics with AI-generated subtopics and questions
3. **Quiz Interface** - Take interactive quizzes with immediate feedback
4. **Quiz History** - View your quiz history and performance
5. **Progress Tracking** - View your progress by subtopic within each topic

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

### ngrok Issues
- Make sure ngrok is authenticated: `ngrok config check`
- Verify your application is running on port 3000 before starting ngrok
- Check the ngrok web interface at http://localhost:4040 for connection status
- Ensure your firewall allows ngrok connections

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
- Use ngrok's web interface (http://localhost:4040) to inspect requests and debug issues
