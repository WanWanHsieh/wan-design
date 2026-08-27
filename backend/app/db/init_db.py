from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin_user import AdminUser
from app.models.rbac import Permission, Role

DEFAULT_PERMISSIONS = [
    ("products.read", "檢視商品/分類"),
    ("products.write", "新增/編輯/刪除商品與分類"),
    ("categories.read", "檢視分類"),
    ("categories.write", "新增/編輯/刪除分類"),
    ("materials.read", "檢視原材料(布料)"),
    ("materials.write", "新增/編輯/刪除原材料(布料)"),
    ("orders.read", "檢視訂單"),
    ("orders.write", "編輯/刪除訂單"),
    ("users.read", "檢視後台使用者"),
    ("users.write", "新增/編輯後台使用者"),
    ("roles.read", "檢視角色與權限"),
    ("roles.write", "新增/編輯角色與權限"),
    ("settings.read", "檢視網站設定(公告等)"),
    ("settings.write", "編輯網站設定(公告等)"),
]

DEFAULT_ROLES = {
    "SuperAdmin": [code for code, _ in DEFAULT_PERMISSIONS],
    "ProductManager": ["products.read", "products.write", "categories.read", "categories.write"],
    "MaterialManager": ["materials.read", "materials.write"],
    "OrderManager": ["orders.read", "orders.write"],
    "Viewer": [
        "products.read",
        "categories.read",
        "materials.read",
        "orders.read",
        "users.read",
        "roles.read",
    ],
}


def seed_permissions(db: Session) -> dict[str, Permission]:
    existing = {p.code: p for p in db.query(Permission).all()}
    for code, description in DEFAULT_PERMISSIONS:
        if code not in existing:
            permission = Permission(code=code, description=description)
            db.add(permission)
            existing[code] = permission
    db.commit()
    return existing


def seed_roles(db: Session, permissions_by_code: dict[str, Permission]) -> dict[str, Role]:
    existing = {r.name: r for r in db.query(Role).all()}
    for name, codes in DEFAULT_ROLES.items():
        if name not in existing:
            role = Role(name=name)
            db.add(role)
            existing[name] = role
        existing[name].permissions = [permissions_by_code[c] for c in codes]
    db.commit()
    return existing


def seed_bootstrap_admin(db: Session, roles_by_name: dict[str, Role]) -> None:
    existing = db.query(AdminUser).filter(AdminUser.email == settings.BOOTSTRAP_ADMIN_EMAIL).first()
    if existing is not None:
        return
    admin_user = AdminUser(
        email=settings.BOOTSTRAP_ADMIN_EMAIL,
        password_hash=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD),
        full_name=settings.BOOTSTRAP_ADMIN_NAME,
        is_active=True,
    )
    admin_user.roles = [roles_by_name["SuperAdmin"]]
    db.add(admin_user)
    db.commit()


def run_seed() -> None:
    db = SessionLocal()
    try:
        permissions_by_code = seed_permissions(db)
        roles_by_name = seed_roles(db, permissions_by_code)
        seed_bootstrap_admin(db, roles_by_name)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
    print("Seed complete.")
