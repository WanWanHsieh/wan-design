# 購物網站

中大型電商平台:前台購物 + 後台管理。技術棧:FastAPI(Python) + Vue3/TypeScript + PostgreSQL。

## 專案結構

- `backend/` — FastAPI API 服務(前台 + 後台共用一套 API)
- `frontend/storefront/` — 前台購物網站(Vue3 + TypeScript + Vite + Tailwind CSS)
- `frontend/admin/` — 後台管理系統(Vue3 + TypeScript + Vite + Element Plus)

詳細架構決策與分階段計畫請見 `docs/`(若尚未建立,請參考專案討論記錄)。

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

- [x] Phase 0:專案骨架(Docker Compose、後端/前端 skeleton)
- [x] Phase 1:認證權限(JWT + RBAC)、商品/分類 CRUD(後台)、商品列表/詳情(前台)
- [ ] Phase 2:購物車、結帳、訂單建立、沙盒金流
- [ ] Phase 3:電子發票、庫存扣減、報表儀表板
