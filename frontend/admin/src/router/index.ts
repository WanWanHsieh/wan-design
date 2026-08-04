import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import ProductListView from '../views/products/ProductListView.vue'
import ProductFormView from '../views/products/ProductFormView.vue'
import ProductBulkImportView from '../views/products/ProductBulkImportView.vue'
import ReadyStockListView from '../views/ready-stock/ReadyStockListView.vue'
import ReadyStockFormView from '../views/ready-stock/ReadyStockFormView.vue'
import CategoryListView from '../views/categories/CategoryListView.vue'
import MaterialListView from '../views/materials/MaterialListView.vue'
import MaterialFormView from '../views/materials/MaterialFormView.vue'
import MaterialBulkImportView from '../views/materials/MaterialBulkImportView.vue'
import OrderListView from '../views/orders/OrderListView.vue'
import OrderDetailView from '../views/orders/OrderDetailView.vue'
import RoleListView from '../views/roles/RoleListView.vue'
import UserListView from '../views/users/UserListView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    {
      path: '/',
      component: AdminLayout,
      children: [
        {
          path: '',
          redirect: { name: 'product-list' },
        },
        {
          path: 'products',
          name: 'product-list',
          component: ProductListView,
          meta: { permission: 'products.read' },
        },
        {
          path: 'products/new',
          name: 'product-new',
          component: ProductFormView,
          meta: { permission: 'products.write' },
        },
        {
          path: 'products/bulk-import',
          name: 'product-bulk-import',
          component: ProductBulkImportView,
          meta: { permission: 'products.write' },
        },
        {
          path: 'products/:id',
          name: 'product-edit',
          component: ProductFormView,
          meta: { permission: 'products.write' },
        },
        {
          path: 'ready-stock',
          name: 'ready-stock-list',
          component: ReadyStockListView,
          meta: { permission: 'products.read' },
        },
        {
          path: 'ready-stock/new',
          name: 'ready-stock-new',
          component: ReadyStockFormView,
          meta: { permission: 'products.write' },
        },
        {
          path: 'ready-stock/:id',
          name: 'ready-stock-edit',
          component: ReadyStockFormView,
          meta: { permission: 'products.write' },
        },
        {
          path: 'categories',
          name: 'category-list',
          component: CategoryListView,
          meta: { permission: 'categories.read' },
        },
        {
          path: 'materials',
          name: 'material-list',
          component: MaterialListView,
          meta: { permission: 'materials.read' },
        },
        {
          path: 'materials/new',
          name: 'material-new',
          component: MaterialFormView,
          meta: { permission: 'materials.write' },
        },
        {
          path: 'materials/bulk-import',
          name: 'material-bulk-import',
          component: MaterialBulkImportView,
          meta: { permission: 'materials.write' },
        },
        {
          path: 'materials/:id',
          name: 'material-edit',
          component: MaterialFormView,
          meta: { permission: 'materials.write' },
        },
        {
          path: 'orders',
          name: 'order-list',
          component: OrderListView,
          meta: { permission: 'orders.read' },
        },
        {
          path: 'orders/:id',
          name: 'order-detail',
          component: OrderDetailView,
          meta: { permission: 'orders.read' },
        },
        {
          path: 'roles',
          name: 'role-list',
          component: RoleListView,
          meta: { permission: 'roles.read' },
        },
        {
          path: 'users',
          name: 'user-list',
          component: UserListView,
          meta: { permission: 'users.read' },
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    return true
  }
  if (!auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  const requiredPermission = to.meta.permission as string | undefined
  if (requiredPermission && auth.user && !auth.permissions.has(requiredPermission)) {
    return false
  }
  return true
})

export default router
