# Nano Banana Hairstyle App

This project lets users blend their hairstyle with an inspiration photo using Google's "Nano Banana" (Gemini) API. The stack consists of an Angular web client and a FastAPI backend. No data is persisted; every request processes images in memory and streams the generated result back to the browser.

## Project layout

```
source/
  frontend/  → Angular single-page app
  backend/   → FastAPI service that talks to Google Gemini
```

## Requirements

- Node.js 18+ and npm (Angular CLI uses the local npm binaries)
- Python 3.10+
- Google API key with access to the Gemini image APIs

Export the key before starting the backend:

```bash
export GOOGLE_GEMINI_API_KEY="<your-key>"
```

> The backend refuses to start if `GOOGLE_GEMINI_API_KEY` is missing, so export it (or use a .env loader) before launching.

## Backend

1. Install dependencies:
   ```bash
   cd source/backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the API server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. The server exposes `POST /api/style-transfer` for the Angular client.

### What the backend does

- Validates both uploaded images with the Gemini `gemini-1.5-flash` model to ensure:
  - exactly one person is present
  - no gore, nudity, or animals appear
- Sends the portrait/reference pair to the `gemini-2.5-flash-image-preview:generateContent` endpoint, which supports multi-image composition and style transfer. The precise editing prompt preserves the subject in Image A while swapping only the hairstyle from Image B.
- Returns a JSON payload containing the MIME type and base64 image data; nothing is stored on disk

## Frontend

1. Install dependencies:
   ```bash
   cd source/frontend
   npm install
   ```
2. Start the dev server:
   ```bash
   npm run start
   ```
3. The app expects the backend at `http://localhost:8000`. To point elsewhere, set `window.__APP_API_BASE__` before Angular bootstraps (e.g. via a `<script>` tag in `index.html`). The portrait preview remains in place when you swap hairstyle references so you can iterate quickly.

### UX flow

- Users upload a self portrait and a reference hairstyle photo
- Thumbnails are shown immediately in the browser; large files (>7 MB) are rejected client-side
- Clicking “Generate hairstyle” sends both files to the backend
- A spinner appears until the Nano Banana API responds
- The app displays the generated result alongside the hairstyle reference card and enables a “Download image” button; the browser handles saving so the server never writes the file

## Known limitations

- Final visual accuracy depends entirely on the Gemini API
- Validation is best-effort; if the Gemini safety model misclassifies an image, the request may fail
- The preview `gemini-2.5-flash-image-preview` model enforces strict quotas. Ensure your API key is enabled for image generation or swap in a model your project can access.
- The CLI tests are not run automatically; run `npm run test` and `pytest` as you add features

## Next steps

- Add persistent job history tied to user accounts
- Queue long-running generations and provide progress polling
- Harden validation with additional local heuristics (face detection, size limits)
