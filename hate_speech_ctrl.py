from typing import Any, Dict
import logging
from fastapi import Depends, FastAPI, HTTPException
from auth_service import issue_token, refresh_access_token, verify_jwt_token
from conversation_service import simplify_conversation
from model_client import run_hate_speech_model
from schemas import (
    HateSpeechRequest,
    HateSpeechResponse,
    RefreshTokenResponse,
    TokenRefreshRequest,
    TokenRequest,
    TokenResponse,
)

app = FastAPI(title="Hate Speech Detection API")
logger = logging.getLogger(__name__)


@app.post("/token", response_model=TokenResponse)
def token_endpoint(body: TokenRequest) -> TokenResponse:
    return issue_token(body)


@app.post("/refresh", response_model=RefreshTokenResponse)
def refresh_endpoint(body: TokenRefreshRequest) -> RefreshTokenResponse:
    return refresh_access_token(body)


@app.post("/hate_speech", response_model=HateSpeechResponse, response_model_exclude_none=True)
def hate_speech_endpoint(
    raw: HateSpeechRequest,
    _token_payload: Dict[str, Any] = Depends(verify_jwt_token),
) -> HateSpeechResponse:
    logger.info("Received /hate_speech request")
    print("[hate_speech_ctrl] Received /hate_speech request")
    simple = simplify_conversation(raw.model_dump())
    try:
        return run_hate_speech_model(simple)
    except ValueError as exc:
        print(f"[hate_speech_ctrl] Validation error in /hate_speech: {exc!r}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed processing /hate_speech")
        print(f"[hate_speech_ctrl] Failed processing /hate_speech: {exc!r}")
        raise HTTPException(status_code=502, detail=f"Error calling hate-speech service: {exc}")
