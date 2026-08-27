<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient } from './api/client'
import ToastNotification from './components/ToastNotification.vue'
import { useCartStore } from './stores/cart'
import { useOrderDraftStore } from './stores/orderDraft'
import type { Announcement } from './types'
import logo from './images/logo.png'

const cart = useCartStore()
const orderDraft = useOrderDraftStore()
const checkoutCount = computed(() => cart.totalQuantity + orderDraft.totalQuantity)
const mobileMenuOpen = ref(false)
const announcement = ref<Announcement | null>(null)

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

onMounted(async () => {
  try {
    const { data } = await apiClient.get<Announcement>('/api/v1/storefront/announcement')
    announcement.value = data
  } catch {
    announcement.value = null
  }
})
</script>

<template>
  <div class="min-h-screen bg-cream">
    <div
      v-if="announcement?.is_active && announcement.message.trim()"
      class="bg-terracotta px-4 py-2 text-center text-sm text-white"
    >
      <p class="whitespace-pre-line">{{ announcement.message }}</p>
    </div>
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
            to="/shopping-guide"
            class="text-taupe transition hover:text-terracotta"
            active-class="font-medium text-terracotta"
          >
            📖購物須知
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
        <RouterLink
          to="/shopping-guide"
          class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
          active-class="font-medium text-terracotta"
          @click="closeMobileMenu"
        >
          📖購物須知
        </RouterLink>
      </nav>
    </header>
    <RouterView v-slot="{ Component }">
      <keep-alive :include="['ProductListView', 'FeaturedProductsView', 'InStockProductListView', 'MaterialListView']">
        <component :is="Component" />
      </keep-alive>
    </RouterView>
    <footer class="mt-8 border-t border-beige py-6 text-center">
      <p class="mb-3 text-sm font-medium text-brown">聯絡我們</p>
      <div class="mb-4 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm text-taupe">
        <a
          href="https://instagram.com/wan_design_0304"
          target="_blank"
          rel="noopener"
          class="transition hover:text-terracotta"
        >
          <span aria-hidden="true">📷</span> Instagram
        </a>
        <a
          href="https://www.facebook.com/wandesign0304"
          target="_blank"
          rel="noopener"
          class="transition hover:text-terracotta"
        >
          <span aria-hidden="true">👍</span> 粉絲團
        </a>
        <a
          href="https://www.facebook.com/groups/157339132839155/"
          target="_blank"
          rel="noopener"
          class="transition hover:text-terracotta"
        >
          <span aria-hidden="true">👥</span> 社團
        </a>
        <a
          href="https://liff.line.me/1645278921-kWRPP32q/?accountId=894onjvt"
          target="_blank"
          rel="noopener"
          class="transition hover:text-terracotta"
        >
          <span aria-hidden="true">💬</span> LINE 私訊
        </a>
      </div>
    </footer>

    <ToastNotification />
  </div>
</template>
