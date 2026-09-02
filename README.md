# Wan's Design 丸藝手作坊 — 購物網站

手作商品(圍兜兜、飾品、平安符等)電商平台:前台購物 + 後台管理。技術棧:FastAPI(Python) + Vue3/TypeScript + PostgreSQL。

## 正式環境網址

- 前台購物網站:https://wan-design-storefront-sable.vercel.app
- 後台管理系統:https://wan-design-admin.vercel.app
- 後端 API:https://wan-design-backend.onrender.com(文件在 `/docs`)

前台部署於 Vercel,後端 API 部署於 Render,資料庫使用 Supabase(PostgreSQL),商品/布料圖片儲存於 Cloudflare R2。

## 專案結構

- `backend/` — FastAPI API 服務(前台 + 後台共用一套 API)
- `frontend/storefront/` — 前台購物網站(Vue3 + TypeScript + Vite + Tailwind CSS)
- `frontend/admin/` — 後台管理系統(Vue3 + TypeScript + Vite + Element Plus)

## 本機開發(Docker Compose)

```bash
docker compose -p shopping-site up --build
```

啟動後:

- 後端 API: http://localhost:8000 (文件在 `/docs`)
- 前台: http://localhost:5173
- 後台: http://localhost:5174

### 初始化資料庫

首次啟動後,執行資料庫遷移與預設資料種子:

```bash
docker compose -p shopping-site exec backend alembic upgrade head
docker compose -p shopping-site exec backend python -m app.db.init_db
```

種子腳本會建立預設角色(SuperAdmin/ProductManager/Viewer)與一個 bootstrap 管理員帳號,
帳密設定於 `backend/.env` 的 `BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD`
(預設為 `admin@example.com` / `ChangeMe123!`,正式環境請務必更改)。

## 不使用 Docker 的本機開發

**後端**

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
python -m app.db.init_db
uvicorn app.main:app --reload
```

**前端**

```bash
cd frontend/storefront && npm install && npm run dev
cd frontend/admin && npm install && npm run dev
```

## 目前進度

已上線正式環境,主要功能:

**前台**

- 商品瀏覽(分類、現貨/訂製商品、本週主打)、布料瀏覽與搜尋排序
- 結帳流程:現貨購物車 + 訂製項目合併下單、布料視覺化選擇彈窗、下單前即時庫存檢查
- 訂單查詢(姓名+電話)、購物須知頁(運費/付款方式/商品保養說明)
- 響應式排版(手機/平板/桌面皆可使用)

**後台**

- 商品 / 現貨商品 / 原材料 / 分類 CRUD,批量匯入(CSV + 圖片 ZIP)
- 訂單管理(狀態流程、金額調整、合併重複訂單)、角色權限(RBAC)、後台人員管理
- 網站公告、低庫存提醒、新訂單 LINE 通知

**基礎設施**

- 認證權限(JWT + RBAC)、圖片儲存於 Cloudflare R2、資料庫遷移(Alembic)
