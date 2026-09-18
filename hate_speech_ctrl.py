import logging
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from auth_service import verify_jwt_token
from conversation_service import simplify_conversation
from model_client import run_hate_speech_model
from schemas import HateSpeechRequest, HateSpeechResponse

app = FastAPI(title="Hate Speech Detection API")
logger = logging.getLogger(__name__)


@app.post("/hate_speech", response_model=HateSpeechResponse, response_model_exclude_none=True)
def hate_speech_endpoint(
    raw: HateSpeechRequest,
    token_payload: Dict[str, Any] = Depends(verify_jwt_token),
) -> HateSpeechResponse:
    logger.info(f"Received /hate_speech request from sub: {token_payload.get('sub')}")
    simple = simplify_conversation(raw.model_dump())
    try:
        return run_hate_speech_model(simple)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed processing /hate_speech")
        raise HTTPException(status_code=502, detail=f"Error calling hate-speech service: {exc}")