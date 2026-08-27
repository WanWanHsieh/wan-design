from fastapi import APIRouter, HTTPException, Request, status

from app.services import line_service

router = APIRouter(prefix="/line", tags=["line"])


@router.post("/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    if not line_service.verify_signature(body, signature):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid signature")

    return {"status": "ok"}
