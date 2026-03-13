from typing import Any, Dict, List
import re

from schemas import SimpleConversation


def clean_assistant_text(text: str) -> str:
    if not text:
        return text

    cleaned = text.replace("[PARAGRAPH_BREAK]", "\n\n")
    cleaned = re.sub(r"<source>.*?</source>", "", cleaned)
    cleaned = re.sub(r"<options>.*?</options>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<sources>.*?</sources>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s+\n", "\n\n", cleaned)
    return cleaned.strip()


def parse_image_chat(chat: str) -> List[Dict[str, str]]:
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

    for msg in raw.get("messages", []):
        role = msg.get("role", "user")
        contents = msg.get("content") or []

        text_parts: List[str] = []
        image_chats: List[Dict[str, str]] = []
        for c in contents:
            if c.get("type") == "text":
                t = c.get("text") or ""
                if t:
                    text_parts.append(t)
            if c.get("type") == "image" or c.get("_class", "").endswith("ConversationMessageImageContent"):
                chat = c.get("chat")
                if chat:
                    image_chats.extend(parse_image_chat(chat))

        combined_text = "\n\n".join(part.strip() for part in text_parts if part is not None)
        if combined_text or image_chats:
            value: Dict[str, Any] = {"text": combined_text}
            if image_chats:
                value["image_chats"] = image_chats
            messages.append({role: value})

    return SimpleConversation(
        id=raw.get("id"),
        app_id=raw.get("appId"),
        user_id=raw.get("userId"),
        messages=messages,
    )
