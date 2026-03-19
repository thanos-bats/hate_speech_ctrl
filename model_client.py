from typing import Dict, Optional
import ast
import logging
import requests
from config import HATE_SPEECH_API_URL
from schemas import HateSpeechResponse, SimpleConversation

logger = logging.getLogger(__name__)


def run_hate_speech_model(simple: SimpleConversation) -> HateSpeechResponse:
    payload = {
        "id": simple.id,
        "app_id": simple.app_id,
        "user_id": simple.user_id,
        "text": simple.text,
    }
    print(f"[model_client] Payload to model: {payload}")

    try:
        resp = requests.post(
            HATE_SPEECH_API_URL,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        hs_data = resp.json()
        logger.info("Model response received: %s", hs_data)
        print(f"[model_client] Model response received: {hs_data}")
    except Exception as exc:
        logger.exception("Failed to call hate speech model API")
        print(f"[model_client] Error calling model API: {exc!r}")
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
        logger.exception("Failed to parse model response")
        print(f"[model_client] Error parsing model response: {exc!r}")
        raise RuntimeError(f"Error parsing hate speech model response: {exc}. Raw response: {hs_data}")

    if not class_name or confidence is None:
        logger.error("Model response missing class/confidence: %s", hs_data)
        print(f"[model_client] Missing class/confidence in model response: {hs_data}")
        raise RuntimeError(f"Failed to obtain valid prediction from model. Raw response: {hs_data}")

    result = HateSpeechResponse(
        id=simple.id,
        app_id=simple.app_id,
        user_id=simple.user_id,
        class_name=class_name,
        confidence_score=confidence,
        conversation=simple.text,
        ocr=simple.ocr,
    )
    logger.info(
        "Parsed model result: id=%s class=%s confidence_score=%s",
        result.id,
        result.class_name,
        result.confidence_score,
    )
    print(
        f"[model_client] Parsed result: id={result.id} class={result.class_name} "
        f"confidence_score={result.confidence_score}"
    )
    return result
