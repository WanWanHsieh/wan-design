from fastapi import APIRouter

from app.api.v1.admin import auth as admin_auth
from app.api.v1.admin import categories as admin_categories
from app.api.v1.admin import materials as admin_materials
from app.api.v1.admin import orders as admin_orders
from app.api.v1.admin import products as admin_products
from app.api.v1.admin import roles as admin_roles
from app.api.v1.admin import users as admin_users
from app.api.v1.storefront import auth as storefront_auth
from app.api.v1.storefront import categories as storefront_categories
from app.api.v1.storefront import materials as storefront_materials
from app.api.v1.storefront import orders as storefront_orders
from app.api.v1.storefront import products as storefront_products

api_router = APIRouter(prefix="/api/v1")

storefront_router = APIRouter(prefix="/storefront")
storefront_router.include_router(storefront_auth.router)
storefront_router.include_router(storefront_products.router)
storefront_router.include_router(storefront_categories.router)
storefront_router.include_router(storefront_materials.router)
storefront_router.include_router(storefront_orders.router)

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin_auth.router)
admin_router.include_router(admin_users.router)
admin_router.include_router(admin_roles.router)
admin_router.include_router(admin_products.router)
admin_router.include_router(admin_categories.router)
admin_router.include_router(admin_materials.router)
admin_router.include_router(admin_orders.router)

api_router.include_router(storefront_router)
api_router.include_router(admin_router)
