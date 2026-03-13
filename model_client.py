from typing import Dict, Optional
import ast
import requests
from config import HATE_SPEECH_API_URL
from schemas import HateSpeechResponse, SimpleConversation

def run_hate_speech_model(simple: SimpleConversation) -> HateSpeechResponse:
    payload = {
        "id": simple.id,
        "app_id": simple.app_id,
        "user_id": simple.user_id,
        "messages": simple.messages,
    }

    try:
        resp = requests.post(
            HATE_SPEECH_API_URL,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        hs_data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Error calling hate speech model API: {exc}")

    class_name: Optional[str] = None
    confidence: Optional[float] = None

    try:
        prediction = (hs_data.get("prediction") or "").strip().lower()
        probs_raw = hs_data.get("probabilities") or ""
        probs: Dict[str, float] = {}
        if isinstance(probs_raw, str) and probs_raw:
            probs = ast.literal_eval(probs_raw)

        if prediction == "bullying":
            class_name = prediction
            confidence = float(probs.get("bullying"))
        elif prediction == "no-bullying":
            class_name = prediction
            confidence = float(probs.get("no-bullying"))
    except Exception as exc:
        raise RuntimeError(f"Error parsing hate speech model response: {exc}. Raw response: {hs_data}")

    if not class_name or confidence is None:
        raise RuntimeError(f"Failed to obtain valid prediction from model. Raw response: {hs_data}")

    return HateSpeechResponse(
        id=simple.id,
        app_id=simple.app_id,
        user_id=simple.user_id,
        class_name=class_name,
        confidence_score=confidence,
    )
