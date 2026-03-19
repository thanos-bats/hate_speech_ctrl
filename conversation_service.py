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
    user_lines: List[str] = []
    chat_lines: List[str] = []

    for msg in raw.get("messages", []):
        role = msg.get("role", "user")
        if role == "assistant":
            continue
        contents = msg.get("content") or []

        for c in contents:
            if c.get("type") == "text":
                t = (c.get("text") or "").strip()
                if t:
                    user_lines.append(t)
            if c.get("type") == "image" or c.get("_class", "").endswith("ConversationMessageImageContent"):
                if c.get("chat"):
                    for pair in parse_image_chat(c.get("chat")):
                        for speaker, utterance in pair.items():
                            chat_lines.append(f"{utterance}")

    return SimpleConversation(
        id=raw.get("id"),
        app_id=raw.get("appId"),
        user_id=raw.get("userId"),
        text="\n".join(user_lines),
        ocr="\n".join(chat_lines),
    )
