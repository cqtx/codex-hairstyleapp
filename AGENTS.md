# Repository Guidelines

## Project Structure & Module Organization
- `source/frontend/`: Angular standalone app; primary entry in `src/app/app.component.*`. Assets live under `src/assets/`. Tests in `src/app/*.spec.ts`.
- `source/backend/`: FastAPI service served from `app/main.py`. Virtual environment recommended in `source/backend/.venv/` (ignored).
- `documentation/`: High-level README and usage notes.

## Build, Test, and Development Commands
- Frontend install: `cd source/frontend && npm install`.
- Frontend dev server: `npm start` (runs on `http://localhost:4200`, hot reload enabled).
- Frontend unit tests: `npm test` (Karma/Jasmine).
- Backend setup: `cd source/backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Backend dev server: `uvicorn app.main:app --reload --port 8000`.
- Backend quick check: `curl -F "user_image=@path" -F "reference_image=@path" http://localhost:8000/api/style-transfer`.

## Coding Style & Naming Conventions
- TypeScript/Angular: prefer standalone components, SCSS modules, and `signal` APIs; 2-space indentation (Angular CLI default). Use descriptive property names (e.g., `userPreview`, `resultImage`).
- Python/FastAPI: follow PEP 8 with 4-space indentation; keep helper functions private with leading underscore (e.g., `_analyze_image`).
- Environment: never hard-code API keys—read from `GOOGLE_GEMINI_API_KEY`.

## Testing Guidelines
- Frontend: unit specs alongside components (`*.spec.ts`). Aim to cover UI states (loading, error, populated) and signal-based logic.
- Backend: add pytest modules under `source/backend/tests/` (create directory if missing). Exercise safety checks and response parsing using FastAPI TestClient. Mock external HTTP calls when possible.

## Commit & Pull Request Guidelines
- Commits: use imperative tense summaries (e.g., `Add result card alongside uploads`). Commit small, reviewable changes per feature.
- Pull Requests: include problem statement, summary of changes, testing evidence (`npm test`, manual steps), and screenshots for UI updates. Link related issues and note any API/secret requirements.

## Security & Configuration Tips
- Export `GOOGLE_GEMINI_API_KEY` before running the backend; production deployments should load it from secure secret management.
- When sharing repro steps or scripts, redact personal images and rotate API keys if exposed.
