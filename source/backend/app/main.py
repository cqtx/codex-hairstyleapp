import base64
import imghdr
import json
import os
from typing import Any, Dict, Tuple

import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_GEMINI_API_KEY environment variable is required")

VERIFY_MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
IMAGE_MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image-preview:generateContent"

app = FastAPI(title="Nano Banana Hairstyle API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _detect_mime(image_bytes: bytes) -> str:
    image_format = imghdr.what(None, image_bytes)
    mapping = {
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "webp": "image/webp",
    }
    if image_format in mapping:
        return mapping[image_format]
    raise HTTPException(status_code=400, detail="Unsupported image type. Please use PNG, JPEG, GIF, BMP, TIFF, or WEBP.")


def _google_error(response: requests.Response, fallback: str, default_status: int = 502) -> Tuple[int, str]:
    try:
        payload: Dict[str, Any] = response.json()
    except (ValueError, json.JSONDecodeError):
        return default_status, fallback
    error = payload.get("error")
    if isinstance(error, dict):
        status_code = int(error.get("code", default_status))
        message = error.get("message", fallback)
        return status_code, message
    return default_status, fallback


def _analyze_image(image_bytes: bytes, image_role: str) -> None:
    mime_type = _detect_mime(image_bytes)
    prompt = (
        "You are an image safety inspector. Review the provided image and respond strictly with a JSON object "
        "containing the keys valid (boolean) and reason (string). The image is intended for a hairstyle try-on app. "
        "Set valid to false if ANY of the following are true: the image contains more than one person, contains animals, "
        "contains explicit sexual content, pornography, nudity, graphic or gory content, or anything offensive. "
        "Otherwise set valid to true."
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(image_bytes).decode("utf-8"),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    try:
        response = requests.post(
            VERIFY_MODEL_URL,
            params={"key": API_KEY},
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Analysis service error for {image_role} image.") from exc

    if response.status_code != 200:
        status_code, message = _google_error(response, f"Failed to analyze {image_role} image.")
        raise HTTPException(status_code=status_code, detail=message)

    try:
        ai_message = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, ValueError):
        raise HTTPException(status_code=502, detail="Unexpected response from analysis service.")

    try:
        result = json.loads(ai_message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not parse analysis response." ) from exc

    if not result.get("valid"):
        reason = result.get("reason", "Image rejected by safety checker.")
        raise HTTPException(status_code=400, detail={"image": image_role, "reason": reason})


PROMPT = (
    "# ROLE\n"
    "You are a precise photo editor. Your first priority is preservation fidelity of Image A. "
    "Your second priority is accurate transfer of the hairstyle from Image B.\n\n"
    "# INPUTS\n"
    "- Image A: The person to keep unchanged except for hair.\n"
    "- Image B: Source hairstyle to transfer (shape, length, texture, color, part/line).\n\n"
    "# OBJECTIVE\n"
    "Apply ONLY the hairstyle from Image B onto Image A.\n\n"
    "# PRESERVATION RULES (HARD CONSTRAINTS — DO NOT VIOLATE)\n"
    "1) Do NOT change anything in Image A except hair: face, skin tone, skin complexion, facial features, expression, "
    "eyebrows, eye shape, eyelashes, teeth, makeup, glasses, jewelry, clothing, background, camera/lens characteristics, "
    "perspective, and global lighting remain identical.\n"
    "2) Keep Image A’s anatomy intact: hairline position on the forehead, ear positions, neck contours, and head pose must remain consistent.\n"
    "3) No global edits: avoid smoothing, beautifying, color grading, denoising, or sharpening outside the hair region.\n\n"
    "# TRANSFER RULES (SOFT CONSTRAINTS — FOLLOW AFTER PRESERVATION)\n"
    "4) Recreate hairstyle from Image B: length, silhouette, volume, parting, bangs/fringe, curl/wave/straight texture, and color.\n"
    "5) Lighting & shading: match hairstyle to Image A’s lighting (direction, intensity, color temperature) by adjusting the HAIR ONLY. "
    "Add realistic shadows/highlights; do not brighten/darken the face or background.\n"
    "6) Integration details: maintain strand-level detail, flyaways, and semi-transparency at edges; avoid plastic or painted look. "
    "Respect natural occlusions (e.g., hair behind ears or glasses temples when appropriate).\n\n"
    "# FAILURE MODES TO AVOID\n"
    "- Altered skin/face/background/expression.\n"
    "- Incorrect head shape or shifted hairline.\n"
    "- Over-smoothing or stylization that reduces realism.\n"
    "- Color cast on the face or clothing from the edit.\n\n"
    "# TIE-BREAKER\n"
    "When in doubt, choose to preserve Image A rather than forcing details from Image B.\n\n"
    "# OUTPUT\n"
    "- Photorealistic composite at the same aspect ratio and resolution as Image A.\n"
    "- No borders, watermarks, or text.\n\n"
    "If a rule must be broken, never break preservation rules."
)


def _build_prompt() -> str:
    return PROMPT


def _generate_hairstyle(user_bytes: bytes, reference_bytes: bytes) -> Tuple[str, str]:
    user_mime = _detect_mime(user_bytes)
    ref_mime = _detect_mime(reference_bytes)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": _build_prompt()},
                    {"text": "User portrait:"},
                    {
                        "inline_data": {
                            "mime_type": user_mime,
                            "data": base64.b64encode(user_bytes).decode("utf-8"),
                        }
                    },
                    {"text": "Reference hairstyle:"},
                    {
                        "inline_data": {
                            "mime_type": ref_mime,
                            "data": base64.b64encode(reference_bytes).decode("utf-8"),
                        }
                    },
                ],
            }
        ],
    }
    try:
        response = requests.post(
            IMAGE_MODEL_URL,
            params={"key": API_KEY},
            json=payload,
            timeout=120,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Generation service error.") from exc

    if response.status_code != 200:
        status_code, message = _google_error(response, "Failed to generate hairstyle image.")
        raise HTTPException(status_code=status_code, detail=message)

    try:
        candidate = response.json()["candidates"][0]
        parts = candidate["content"]["parts"]
    except (KeyError, IndexError, ValueError):
        raise HTTPException(status_code=502, detail="Unexpected response from generation service.")

    fallback_text = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        inline_data = part.get("inline_data") or part.get("inlineData")
        if inline_data and inline_data.get("data"):
            mime_type = inline_data.get("mime_type") or inline_data.get("mimeType") or "image/png"
            return mime_type, inline_data["data"]
        text_value = part.get("text")
        if text_value:
            fallback_text.append(text_value)

    if fallback_text:
        message = fallback_text[0]
        raise HTTPException(status_code=502, detail=message)

    raise HTTPException(status_code=502, detail="Image payload missing from response.")


@app.post("/api/style-transfer")
async def style_transfer(user_image: UploadFile = File(...), reference_image: UploadFile = File(...)):
    try:
        user_bytes = await user_image.read()
        reference_bytes = await reference_image.read()
    finally:
        await user_image.close()
        await reference_image.close()

    if not user_bytes or not reference_bytes:
        raise HTTPException(status_code=400, detail="Both images are required.")

    _analyze_image(user_bytes, "user")
    _analyze_image(reference_bytes, "reference")

    mime_type, generated_b64 = _generate_hairstyle(user_bytes, reference_bytes)

    return {"mimeType": mime_type, "data": generated_b64}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
