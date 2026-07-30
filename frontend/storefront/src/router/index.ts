import { createRouter, createWebHistory } from 'vue-router'
import ProductListView from '../views/ProductListView.vue'
import ProductDetailView from '../views/ProductDetailView.vue'
import MaterialListView from '../views/MaterialListView.vue'
import MaterialDetailView from '../views/MaterialDetailView.vue'
import OrderCreateView from '../views/OrderCreateView.vue'
import InStockProductListView from '../views/InStockProductListView.vue'
import CartView from '../views/CartView.vue'
import OrderLookupView from '../views/OrderLookupView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'products', component: ProductListView },
    { path: '/products/:slug', name: 'product-detail', component: ProductDetailView },
    { path: '/materials', name: 'materials', component: MaterialListView },
    { path: '/materials/:id', name: 'material-detail', component: MaterialDetailView },
    { path: '/order', name: 'order-create', component: OrderCreateView },
    { path: '/instock', name: 'instock-products', component: InStockProductListView },
    { path: '/cart', name: 'cart', component: CartView },
    { path: '/order-lookup', name: 'order-lookup', component: OrderLookupView },
  ],
})

export default router
