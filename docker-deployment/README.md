# Docker Deployment

This directory contains container definitions to run the CODEX-HAIRSTYLEAPP stack locally with Docker.

## Prerequisites

- Docker Engine 24+
- Docker Compose V2
- A valid Google Gemini API key with access to the image endpoints

## Setup

1. Copy `.env.example` to `.env` and set `GOOGLE_GEMINI_API_KEY`:
   ```bash
   cp docker-deployment/.env.example docker-deployment/.env
   echo "GOOGLE_GEMINI_API_KEY=your-key" >> docker-deployment/.env
   ```
   Alternatively, export the variable in your shell before running Compose.

2. Build and launch the containers:
   ```bash
   cd docker-deployment
   docker compose up --build
   ```

   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000

3. Stop the stack when you are done:
   ```bash
   docker compose down
   ```

## Notes

- The frontend container compiles the Angular app in production mode and serves the static assets with Nginx.
- The backend container runs Uvicorn with the FastAPI application exposed on port 8000.
- The Angular client defaults to `http://localhost:8000` for API requests. If you need a different origin, inject `window.__APP_API_BASE__` before bootstrapping the app (for example by editing `index.html`).
- Uploaded images are processed in memory only; the containers do not persist user data.
