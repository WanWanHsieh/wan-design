import base64
import hashlib
import hmac
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("line")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

REPLY_URL = "https://api.line.me/v2/bot/message/reply"
PUSH_URL = "https://api.line.me/v2/bot/message/push"


def verify_signature(body: bytes, signature: str | None) -> bool:
    if not settings.LINE_CHANNEL_SECRET:
        return True
    if not signature:
        return False
    expected = base64.b64encode(
        hmac.new(settings.LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(expected, signature)


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
    }


def reply_message(reply_token: str, text: str) -> None:
    try:
        response = httpx.post(
            REPLY_URL,
            headers=_headers(),
            json={"replyToken": reply_token, "messages": [{"type": "text", "text": text}]},
            timeout=10,
        )
        if response.status_code >= 400:
            logger.error("LINE reply failed: %s %s", response.status_code, response.text)
    except Exception:
        logger.exception("LINE reply failed")


def push_message(user_id: str, text: str) -> None:
    if not settings.line_configured:
        logger.info("新訂單 LINE 通知(未設定 LINE,僅記錄於 log):\n%s", text)
        return
    try:
        response = httpx.post(
            PUSH_URL,
            headers=_headers(),
            json={"to": user_id, "messages": [{"type": "text", "text": text}]},
            timeout=10,
        )
        if response.status_code >= 400:
            logger.error("LINE push failed: %s %s", response.status_code, response.text)
    except Exception:
        logger.exception("LINE push failed")
