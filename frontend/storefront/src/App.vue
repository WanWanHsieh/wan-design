<script setup lang="ts">
import { useCartStore } from './stores/cart'
import logo from './images/logo.png'

const cart = useCartStore()
const adminUrl = import.meta.env.VITE_ADMIN_URL ?? 'http://localhost:5174'
</script>

<template>
  <div class="min-h-screen bg-cream">
    <header class="border-b border-beige bg-cream/80 backdrop-blur-sm">
      <div class="mx-auto flex max-w-6xl items-center gap-6 px-4 py-4">
        <RouterLink to="/" class="flex items-center gap-2 text-lg font-bold text-brown">
          <img :src="logo" alt="Wan's Design" class="h-10 w-10 rounded-full object-cover" />
          Wan's Design
        </RouterLink>
        <nav class="flex flex-1 items-center gap-5 text-sm">
          <RouterLink
            to="/"
            class="text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            商品列表
          </RouterLink>
          <RouterLink
            to="/instock"
            class="text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            現貨商品
          </RouterLink>
          <RouterLink
            to="/materials"
            class="text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            布料列表
          </RouterLink>
          <RouterLink
            to="/order"
            class="text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            立即訂購
          </RouterLink>
          <RouterLink
            to="/order-lookup"
            class="text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            查詢訂單
          </RouterLink>
          <RouterLink
            to="/cart"
            class="ml-auto flex items-center gap-1 text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            <span aria-hidden="true">🛒</span>
            購物車
            <span
              v-if="cart.totalQuantity > 0"
              class="rounded-full bg-terracotta px-1.5 py-0.5 text-xs font-medium text-white"
            >
              {{ cart.totalQuantity }}
            </span>
          </RouterLink>
        </nav>
      </div>
    </header>
    <RouterView />
    <footer class="mt-8 border-t border-beige py-4 text-center">
      <a
        :href="adminUrl"
        target="_blank"
        rel="noopener"
        class="text-xs text-taupe/60 transition hover:text-terracotta"
      >
        管理後台
      </a>
    </footer>
  </div>
</template>
