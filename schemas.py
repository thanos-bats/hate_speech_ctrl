from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SimpleConversation(BaseModel):
    id: Optional[str] = None
    app_id: Optional[str] = None
    user_id: Optional[str] = None
    messages: List[Dict[str, Any]]


class TokenRequest(BaseModel):
    client_id: str
    client_secret: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class HateSpeechRequest(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "id": "46ed8885-6e93-4d2c-a704-e3f97421cd15",
                "appId": "62dfb91a0007ff0000000001",
                "userId": "698ca587b2a1122576abf9af",
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "What is your name?"}],
                    },
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": "Hello! I am your assistant."}],
                    },
                ],
            }
        },
    )


class HateSpeechResponse(BaseModel):
    id: Optional[str] = None
    app_id: Optional[str] = None
    user_id: Optional[str] = None
    class_name: str = Field(alias="class")
    confidence_score: float

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "46ed8885-6e93-4d2c-a704-e3f97421cd15",
                "app_id": "62dfb91a0007ff0000000001",
                "user_id": "698ca587b2a1122576abf9af",
                "class": "no-bullying",
                "confidence_score": 0.6352346,
            }
        },
    )
