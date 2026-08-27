from fastapi import APIRouter, HTTPException, Request, status

from app.services import line_service

router = APIRouter(prefix="/line", tags=["line"])


@router.post("/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    if not line_service.verify_signature(body, signature):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid signature")

    payload = await request.json()
    for event in payload.get("events", []):
        if event.get("type") != "message":
            continue
        message = event.get("message", {})
        if message.get("type") != "text":
            continue
        reply_token = event.get("replyToken")
        user_id = event.get("source", {}).get("userId")
        if reply_token and user_id:
            line_service.reply_message(
                reply_token, f"你的 LINE User ID 是:\n{user_id}\n\n請把這串複製貼給小幫手設定訂單通知。"
            )

    return {"status": "ok"}
