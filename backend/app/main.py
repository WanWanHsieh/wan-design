from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine

app = FastAPI(title="Shopping Site API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(api_router)


# 也接受 HEAD：UptimeRobot 免費版只能用 HEAD 檢查，只接受 GET 會一直回 405 被當成故障
@app.api_route("/health", methods=["GET", "HEAD"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# 給 UptimeRobot 用：順便對資料庫做一次最簡單的查詢。
# Supabase 免費專案連續 7 天沒有資料庫活動會被暫停；每 5 分鐘查一次就不會，資料庫連不上時也會回 503 觸發通知。
# /health 維持不碰資料庫，Render 的健康檢查不會因為資料庫短暫斷線就判定服務壞掉。
@app.api_route("/health/db", methods=["GET", "HEAD"])
def health_db() -> JSONResponse:
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception:
        return JSONResponse({"status": "db_unavailable"}, status_code=503)
    return JSONResponse({"status": "ok"})
