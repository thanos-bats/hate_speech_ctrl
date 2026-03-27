from typing import Any, Dict, Tuple
import ast
import requests
import random

from config import HATE_SPEECH_API_URL
from schemas import HateSpeechResponse, ImagePrediction, SimpleConversation

# Set to True later to reactivate the reporting conversation model call.
ENABLE_REPORTING_CONVERSATION_MODEL = False

def _parse_prediction(hs_data: Dict[str, Any]) -> Tuple[str, float]:
    prediction = (hs_data.get("prediction") or "").strip().lower()
    probs_raw = hs_data.get("probabilities") or ""
    probs: Dict[str, float] = {}

    if isinstance(probs_raw, str) and probs_raw:
        probs = ast.literal_eval(probs_raw)

    if prediction == "bullying":
        class_name = "bullying"
        confidence = float(probs.get("bullying"))
    elif prediction == "no-bullying":
        class_name = "no-bullying"
        confidence = float(probs.get("no-bullying"))
    else:
        raise RuntimeError(f"Unexpected prediction label: {prediction!r}")

    if confidence is None:
        raise RuntimeError(f"Missing confidence for prediction: {prediction!r}")

    return class_name, confidence


def _call_model(api_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(api_url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

def run_reporting_hate_speech_model(simple: SimpleConversation) -> Tuple[str, float]:
    """
    "Reporting" hate-speech classification for the conversation text.

    For the current phase this is intentionally disabled, and we return
    seeded random placeholders.
    """
    seed = f"{simple.id or ''}:{simple.user_id or ''}:{simple.app_id or ''}"
    conversation_payload: Dict[str, Any] = {
        "id": simple.id,
        "app_id": simple.app_id,
        "user_id": simple.user_id,
        "text": simple.text,
    }

    if ENABLE_REPORTING_CONVERSATION_MODEL:
        try:
            hs_data = _call_model(HATE_SPEECH_API_URL, conversation_payload)
            return _parse_prediction(hs_data)
        except Exception as exc:
            raise RuntimeError(f"Conversation hate-speech model failed: {exc}") from exc

    # Placeholder output while the reporting model is inactive.
    rng = random.Random(f"{seed}:reporting")
    class_name = rng.choice(["bullying", "no-bullying"])
    confidence = rng.random()
    return class_name, confidence


def run_hate_speech_into_images(simple: SimpleConversation) -> Dict[str, ImagePrediction]:
    """
    Hate-speech classification per image (OCR-derived text).
    """
    ocr_map: Dict[str, str] = simple.ocr or {}
    if not ocr_map:
        # The API layer converts ValueError -> HTTP 400 (Bad Request).
        raise ValueError("No images found in conversation. Please provide at least one image.")

    seed = f"{simple.id or ''}:{simple.user_id or ''}:{simple.app_id or ''}"
    image_predictions: Dict[str, ImagePrediction] = {}

    for media_id, ocr_text in ocr_map.items():
        rng = random.Random(f"{seed}:ocr:{media_id}")
        image_class = rng.choice(["bullying", "no-bullying"])
        image_confidence = rng.random()

        image_predictions[media_id] = ImagePrediction(
            class_name=image_class,
            confidence_score=image_confidence,
        )

    return image_predictions


def run_hate_speech_model(simple: SimpleConversation) -> HateSpeechResponse:
    # Reporting model is deactivated — skip run_reporting_hate_speech_model().
    images = run_hate_speech_into_images(simple)

    return HateSpeechResponse(
        id=simple.id,
        app_id=simple.app_id,
        user_id=simple.user_id,
        images=images,
    )
