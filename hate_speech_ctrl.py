from typing import Any, Dict
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


@app.post("/token", response_model=TokenResponse)
def token_endpoint(body: TokenRequest) -> TokenResponse:
    return issue_token(body)


@app.post("/refresh", response_model=RefreshTokenResponse)
def refresh_endpoint(body: TokenRefreshRequest) -> RefreshTokenResponse:
    return refresh_access_token(body)


@app.post("/hate_speech", response_model=HateSpeechResponse)
def hate_speech_endpoint(
    raw: HateSpeechRequest,
    _token_payload: Dict[str, Any] = Depends(verify_jwt_token),
) -> HateSpeechResponse:
    simple = simplify_conversation(raw.model_dump())
    try:
        return run_hate_speech_model(simple)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error calling hate-speech service: {exc}")
