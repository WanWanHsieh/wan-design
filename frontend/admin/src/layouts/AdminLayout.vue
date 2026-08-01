<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { apiClient } from '../api/client'
import type { Product } from '../types'
import logo from '../images/logo.png'

const LOW_STOCK_THRESHOLD = 2

const auth = useAuthStore()
const router = useRouter()
const lowStockCount = ref(0)
const storefrontUrl = import.meta.env.VITE_STOREFRONT_URL ?? 'http://localhost:5173'
const mobileMenuOpen = ref(false)

async function loadLowStockCount() {
  try {
    const { data } = await apiClient.get<Product[]>('/api/v1/admin/products', {
      params: { track_stock: true },
    })
    lowStockCount.value = data.filter((p) => p.stock_quantity <= LOW_STOCK_THRESHOLD).length
  } catch {
    lowStockCount.value = 0
  }
}

onMounted(async () => {
  if (!auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
      router.push({ name: 'login' })
    }
  }
  await loadLowStockCount()
})

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}
</script>

<template>
  <el-container class="h-screen bg-cream">
    <el-aside width="200px" class="hidden border-r border-beige bg-white sm:block">
      <div class="flex items-center gap-2 px-4 py-4 text-lg font-bold text-brown">
        <img :src="logo" alt="Wan's Design" class="h-8 w-8 rounded-full object-cover" />
        後台管理
      </div>
      <el-menu :default-active="$route.name as string" router background-color="transparent">
        <el-menu-item index="product-list" :route="{ name: 'product-list' }">商品管理</el-menu-item>
        <el-menu-item index="ready-stock-list" :route="{ name: 'ready-stock-list' }">
          <span class="flex w-full items-center justify-between">
            現貨管理
            <el-tag v-if="lowStockCount > 0" type="warning" size="small" round>{{ lowStockCount }}</el-tag>
          </span>
        </el-menu-item>
        <el-menu-item index="category-list" :route="{ name: 'category-list' }">分類管理</el-menu-item>
        <el-menu-item index="material-list" :route="{ name: 'material-list' }">原材料管理</el-menu-item>
        <el-menu-item index="order-list" :route="{ name: 'order-list' }">訂單管理</el-menu-item>
        <el-menu-item index="role-list" :route="{ name: 'role-list' }">角色權限</el-menu-item>
        <el-menu-item index="user-list" :route="{ name: 'user-list' }">後台人員</el-menu-item>
      </el-menu>
      <a
        :href="storefrontUrl"
        target="_blank"
        rel="noopener"
        class="mt-4 block px-4 text-xs text-taupe/60 transition hover:text-terracotta"
      >
        回前台
      </a>
    </el-aside>

    <el-container>
      <el-header class="flex items-center justify-between border-b border-beige bg-white sm:justify-end">
        <button
          type="button"
          aria-label="開啟選單"
          class="flex h-8 w-8 flex-col items-center justify-center gap-1.5 sm:hidden"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <span class="block h-0.5 w-5 bg-brown"></span>
          <span class="block h-0.5 w-5 bg-brown"></span>
          <span class="block h-0.5 w-5 bg-brown"></span>
        </button>
        <div class="flex items-center">
          <span class="mr-4 text-sm text-taupe">{{ auth.user?.full_name }}</span>
          <el-button size="small" @click="handleLogout">登出</el-button>
        </div>
      </el-header>

      <nav v-if="mobileMenuOpen" class="flex flex-col gap-1 border-b border-beige bg-white px-4 py-3 text-sm sm:hidden">
          <RouterLink
            :to="{ name: 'product-list' }"
            class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
            active-class="font-medium text-terracotta"
            @click="closeMobileMenu"
          >
            商品管理
          </RouterLink>
          <RouterLink
            :to="{ name: 'ready-stock-list' }"
            class="flex items-center justify-between rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
            active-class="font-medium text-terracotta"
            @click="closeMobileMenu"
          >
            現貨管理
            <el-tag v-if="lowStockCount > 0" type="warning" size="small" round>{{ lowStockCount }}</el-tag>
          </RouterLink>
          <RouterLink
            :to="{ name: 'category-list' }"
            class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
            active-class="font-medium text-terracotta"
            @click="closeMobileMenu"
          >
            分類管理
          </RouterLink>
          <RouterLink
            :to="{ name: 'material-list' }"
            class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
            active-class="font-medium text-terracotta"
            @click="closeMobileMenu"
          >
            原材料管理
          </RouterLink>
          <RouterLink
            :to="{ name: 'order-list' }"
            class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
            active-class="font-medium text-terracotta"
            @click="closeMobileMenu"
          >
            訂單管理
          </RouterLink>
          <RouterLink
            :to="{ name: 'role-list' }"
            class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
            active-class="font-medium text-terracotta"
            @click="closeMobileMenu"
          >
            角色權限
          </RouterLink>
          <RouterLink
            :to="{ name: 'user-list' }"
            class="rounded-lg px-2 py-2 text-taupe transition hover:bg-beige/40 hover:text-terracotta"
            active-class="font-medium text-terracotta"
            @click="closeMobileMenu"
          >
            後台人員
          </RouterLink>
      </nav>
      <el-main class="overflow-x-auto">
        <RouterView />
        <footer class="mt-8 border-t border-beige py-4 text-center sm:hidden">
          <a
            :href="storefrontUrl"
            target="_blank"
            rel="noopener"
            class="text-xs text-taupe/60 transition hover:text-terracotta"
          >
            回前台
          </a>
        </footer>
      </el-main>
    </el-container>
  </el-container>
</template>
