import { createRouter, createWebHistory } from 'vue-router'
import ProductListView from '../views/ProductListView.vue'
import ProductDetailView from '../views/ProductDetailView.vue'
import FeaturedProductsView from '../views/FeaturedProductsView.vue'
import MaterialListView from '../views/MaterialListView.vue'
import MaterialDetailView from '../views/MaterialDetailView.vue'
import CheckoutView from '../views/CheckoutView.vue'
import InStockProductListView from '../views/InStockProductListView.vue'
import OrderLookupView from '../views/OrderLookupView.vue'
import ShoppingGuideView from '../views/ShoppingGuideView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'products', component: ProductListView },
    { path: '/featured', name: 'featured-products', component: FeaturedProductsView },
    { path: '/products/:slug', name: 'product-detail', component: ProductDetailView },
    { path: '/materials', name: 'materials', component: MaterialListView },
    { path: '/materials/:id', name: 'material-detail', component: MaterialDetailView },
    { path: '/order', name: 'order-create', component: CheckoutView },
    { path: '/instock', name: 'instock-products', component: InStockProductListView },
    { path: '/cart', name: 'cart', component: CheckoutView },
    { path: '/order-lookup', name: 'order-lookup', component: OrderLookupView },
    { path: '/shopping-guide', name: 'shopping-guide', component: ShoppingGuideView },
  ],
})

export default router
