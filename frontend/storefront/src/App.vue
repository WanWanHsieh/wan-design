<script setup lang="ts">
import { computed, ref } from 'vue'
import { useCartStore } from './stores/cart'
import { useOrderDraftStore } from './stores/orderDraft'
import logo from './images/logo.png'

const cart = useCartStore()
const orderDraft = useOrderDraftStore()
const checkoutCount = computed(() => cart.totalQuantity + orderDraft.totalQuantity)
const adminUrl = import.meta.env.VITE_ADMIN_URL ?? 'http://localhost:5174'
const mobileMenuOpen = ref(false)

function closeMobileMenu() {
  mobileMenuOpen.value = false
}
</script>

<template>
  <div class="min-h-screen bg-cream">
    <header class="border-b border-beige bg-cream/80 backdrop-blur-sm">
      <div class="mx-auto flex max-w-6xl items-center gap-6 px-4 py-4">
        <RouterLink
          to="/"
          class="flex items-center gap-2 text-lg font-bold text-brown"
          @click="closeMobileMenu"
        >
          <img :src="logo" alt="Wan's Design" class="h-10 w-10 rounded-full object-cover" />
          Wan's Design
        </RouterLink>

        <nav class="hidden flex-1 items-center gap-5 text-sm sm:flex">
          <RouterLink
            to="/"
            class="text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            商品列表
          </RouterLink>
          <RouterLink
            to="/featured"
            class="text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            💛主打商品
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
            to="/order-lookup"
            class="text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            查詢訂單
          </RouterLink>
          <RouterLink
            to="/order"
            class="ml-auto flex items-center gap-1 text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            <span aria-hidden="true">🛒</span>
            訂購清單
            <span
              v-if="checkoutCount > 0"
              class="rounded-full bg-terracotta px-1.5 py-0.5 text-xs font-medium text-white"
            >
              {{ checkoutCount }}
            </span>
          </RouterLink>
        </nav>

        <div class="ml-auto flex items-center gap-4 sm:hidden">
          <RouterLink
            to="/order"
            class="relative flex items-center text-taupe"
            title="訂購清單"
            @click="closeMobileMenu"
          >
            <span aria-hidden="true" class="text-xl">🛒</span>
            <span
              v-if="checkoutCount > 0"
              class="absolute -right-2 -top-2 rounded-full bg-terracotta px-1.5 py-0.5 text-xs font-medium text-white"
            >
              {{ checkoutCount }}
            </span>
          </RouterLink>
          <button
            type="button"
            aria-label="開啟選單"
            class="flex h-8 w-8 flex-col items-center justify-center gap-1.5"
            @click="mobileMenuOpen = !mobileMenuOpen"
          >
            <span class="block h-0.5 w-5 bg-brown"></span>
            <span class="block h-0.5 w-5 bg-brown"></span>
            <span class="block h-0.5 w-5 bg-brown"></span>
          </button>
        </div>
      </div>

      <nav v-if="mobileMenuOpen" class="flex flex-col gap-1 border-t border-beige px-4 py-3 text-sm sm:hidden">
        <RouterLink
          to="/"
          class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
          active-class="font-medium text-terracotta"
          @click="closeMobileMenu"
        >
          商品列表
        </RouterLink>
        <RouterLink
          to="/featured"
          class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
          active-class="font-medium text-terracotta"
          @click="closeMobileMenu"
        >
          💛主打商品
        </RouterLink>
        <RouterLink
          to="/instock"
          class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
          active-class="font-medium text-terracotta"
          @click="closeMobileMenu"
        >
          現貨商品
        </RouterLink>
        <RouterLink
          to="/materials"
          class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
          active-class="font-medium text-terracotta"
          @click="closeMobileMenu"
        >
          布料列表
        </RouterLink>
        <RouterLink
          to="/order"
          class="flex items-center gap-1 rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
          active-class="font-medium text-terracotta"
          @click="closeMobileMenu"
        >
          <span aria-hidden="true">🛒</span>
          訂購清單
          <span
            v-if="checkoutCount > 0"
            class="rounded-full bg-terracotta px-1.5 py-0.5 text-xs font-medium text-white"
          >
            {{ checkoutCount }}
          </span>
        </RouterLink>
        <RouterLink
          to="/order-lookup"
          class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
          active-class="font-medium text-terracotta"
          @click="closeMobileMenu"
        >
          查詢訂單
        </RouterLink>
      </nav>
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
