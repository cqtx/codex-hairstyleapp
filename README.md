# Nano Banana Hairstyle App

Blend your portrait with an inspiration hairstyle using Google Gemini "Nano Banana" models. The project ships an Angular client for uploads and previews plus a FastAPI backend that performs safety checks and orchestrates the style-transfer call. All processing happens in memory; no user assets are stored.

## Highlights
- Angular standalone UI with drag-free uploads, client-side size checks, and inline before/after previews
- FastAPI service that validates images with Gemini safety guardrails before invoking the hairstyle transfer endpoint
- In-memory processing and streaming responses keep user data transient
- Run locally with Node/Python tooling or via the provided Docker Compose stack

## Repository layout
```
documentation/          High-level docs and background
source/frontend/        Angular application (standalone components, signals API)
source/backend/         FastAPI service that proxies Google Gemini requests
docker-deployment/      Dockerfiles + Compose stack for full project
```

## Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- Google API key with access to Gemini image endpoints (`GOOGLE_GEMINI_API_KEY`)
- (Optional) Docker Engine 24+ and Docker Compose v2 for containerized runs

## Local development

### 1. Backend (FastAPI)
```bash
cd source/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_GEMINI_API_KEY="<your-key>"
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (Angular)
```bash
cd source/frontend
npm install
npm start
```
The Angular dev server runs on http://localhost:4200 and expects the API at http://localhost:8000. To point elsewhere, set `window.__APP_API_BASE__` before bootstrapping (for example in `src/index.html`).

## Running with Docker Compose
```bash
cp docker-deployment/.env.example docker-deployment/.env
# edit docker-deployment/.env to include GOOGLE_GEMINI_API_KEY
cd docker-deployment
docker compose up --build
```
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- Tear down with `docker compose down`

## Environment & configuration
- `GOOGLE_GEMINI_API_KEY` must be set before starting the backend; the service exits if it is missing
- Uploads are limited to ~7 MB on the client to keep requests responsive
- The backend enables permissive CORS by default; tighten the origins list before production deployment

## Testing
- Frontend unit tests: `cd source/frontend && npm test`
- Backend tests (pytest): `cd source/backend && pytest`

## API quick reference
`POST /api/style-transfer`

Form-data fields:
- `user_image`: portrait to keep (image/*)
- `reference_image`: hairstyle inspiration (image/*)

Successful responses return JSON with `mimeType` and base64-encoded `data`. Example:
```bash
curl -F "user_image=@portrait.jpg" \
     -F "reference_image=@hair.jpg" \
     http://localhost:8000/api/style-transfer
```

## Documentation
Additional context lives in `documentation/README.md`, including background on model selection, UX flow, and future roadmap.

## License
No license has been published yet.
