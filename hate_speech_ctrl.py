from typing import Any, Dict, List, Optional
import ast
import random
import re
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class SimpleConversation(BaseModel):
    id: Optional[str] = None
    app_id: Optional[str] = None
    user_id: Optional[str] = None
    # each message: {"user": {"text": ..., "image_chats": [{}, {}, ...]}} or same with "assistant"
    messages: List[Dict[str, Any]]

app = FastAPI(title="Hate Speech Conversation API")


def clean_assistant_text(text: str) -> str:
    if not text:
        return text

    # Replace paragraph markers with real line breaks
    cleaned = text.replace("[PARAGRAPH_BREAK]", "\n\n")

    # Drop simple <source>n</source> markers
    cleaned = re.sub(r"<source>.*?</source>", "", cleaned)

    # Drop <options>...</options> blocks entirely
    cleaned = re.sub(r"<options>.*?</options>", "", cleaned, flags=re.DOTALL)

    # Drop <sources>...</sources> blocks (which contain JSON with titles, etc.)
    cleaned = re.sub(r"<sources>.*?</sources>", "", cleaned, flags=re.DOTALL)

    # Normalize spaces and trim
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s+\n", "\n\n", cleaned)
    return cleaned.strip()


def parse_image_chat(chat: str) -> List[Dict[str, str]]:
    """
    Parse an OCR/analysis chat
    """
    convo: List[Dict[str, str]] = []
    if not chat:
        return convo

    for segment in chat.split("},"):
        segment = segment.strip().lstrip("{").rstrip("}")
        if not segment or ":" not in segment:
            continue
        speaker, msg_text = segment.split(":", 1)
        speaker = speaker.strip()
        msg_text = msg_text.strip()
        if msg_text:
            convo.append({speaker: msg_text})

    return convo


def simplify_conversation(raw: Dict[str, Any]) -> SimpleConversation:
    messages: List[Dict[str, Any]] = []

    for idx, msg in enumerate(raw.get("messages", [])):
        role = msg.get("role", "user")
        contents = msg.get("content") or []

        text_parts: List[str] = []
        image_chats: List[Dict[str, str]] = []
        for c in contents:
            if c.get("type") == "text":
                t = c.get("text") or ""
                if t:
                    text_parts.append(t)
            # Image or other media content
            if c.get("type") == "image" or c.get("_class", "").endswith("ConversationMessageImageContent"):
                chat = c.get("chat")
                if chat:
                    convo = parse_image_chat(chat)
                    if convo:
                        # flatten all segments from this image into the message-level list
                        image_chats.extend(convo)

        combined_text = "\n\n".join(part.strip() for part in text_parts if part is not None)
        # Clean assistant messages from noisy markup like <sources>{...}, <options>...</options>, etc.
        # if role.lower() == "assistant":
        #     combined_text = clean_assistant_text(combined_text)
        if combined_text or image_chats:
            value: Dict[str, Any] = {
                "text": combined_text,
            }
            # Only include image_chats key when we actually have conversations
            if image_chats:
                value["image_chats"] = image_chats
            messages.append({role: value})

    print(f"Built {len(messages)} simplified messages")

    result = SimpleConversation(
        id=raw.get("id"),
        app_id=raw.get("appId"),
        user_id=raw.get("userId"),
        messages=messages,
    )

    return result


def run_hate_speech_model(simple: SimpleConversation) -> Dict[str, Any]:
    """
    Take a SimpleConversation, call the external hate-speech API, and
    map its response to our compact format.

    External API (http://localhost:13333/hate_speech_both) returns:
        {
            "prediction": "no-bullying" | "bullying",
            "probabilities": "{'no-bullying': 0.63, 'bullying': 0.37}"
        }
    """
    payload = {
        "id": simple.id,
        "app_id": simple.app_id,
        "user_id": simple.user_id,
        "messages": simple.messages,
    }

    try:
        # Use localhost as the client target; 0.0.0.0 is only valid as a bind address.
        resp = requests.post(
            "http://localhost:13333/grooming_taxonomy_both",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        hs_data = resp.json()
        print(f"hate_speech_both response: {hs_data}")
    except Exception as e:
        print(f"Error calling hate_speech_both: {e!r}")
        hs_data = {}

    class_name: Optional[str] = None
    confidence: Optional[float] = None

    try:
        prediction = (hs_data.get("prediction") or "").strip().lower()
        probs_raw = hs_data.get("probabilities") or ""

        # probabilities comes as a string representation of a dict
        probs: Dict[str, float] = {}
        if isinstance(probs_raw, str) and probs_raw:
            probs = ast.literal_eval(probs_raw)

        if prediction == "bullying":
            class_name = prediction
            confidence = float(probs.get("bullying"))
        elif prediction == "no-bullying":
            class_name = prediction
            confidence = float(probs.get("no-bullying"))
    except Exception as e:
        print(f"Error parsing hate_speech_both response: {e!r}, data={hs_data}")

    # If we still don't have a valid prediction, signal an error to the caller
    if not class_name or confidence is None:
        raise RuntimeError(f"Failed to obtain valid prediction from hate_speech_both. Raw response: {hs_data}")

    return {
        "id": simple.id,
        "app_id": simple.app_id,
        "user_id": simple.user_id,
        "class": class_name,
        "confidence_score": confidence,
    }

@app.post("/hate_speech")
def hate_speech_endpoint(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Controller:
    1. Normalize the incoming conversation DTO to our SimpleConversation.
    2. Send it to the external hate-speech model at http://localhost:13333/hate_speech_both.
    3. Return a compact result with id, app_id, user_id, class, confidence_score.
    """
    print("Received /hate_speech request")

    simple = simplify_conversation(raw)
    try:
        return run_hate_speech_model(simple)
    except Exception as e:
        # Propagate as a clear HTTP error instead of faking a non-bullying result
        raise HTTPException(
            status_code=502,
            detail=f"Error calling hate-speech service: {e}",
        )
