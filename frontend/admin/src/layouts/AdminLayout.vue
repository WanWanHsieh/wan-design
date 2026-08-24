<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { apiClient } from '../api/client'
import type { Product } from '../types'
import logo from '../images/logo.png'

const auth = useAuthStore()
const router = useRouter()
const lowStockCount = ref(0)
const storefrontUrl = import.meta.env.VITE_STOREFRONT_URL ?? 'http://localhost:5173'
const mobileMenuOpen = ref(false)

const accountDialogVisible = ref(false)
const accountSaving = ref(false)
const accountForm = reactive({
  email: '',
  full_name: '',
  current_password: '',
  new_password: '',
  confirm_password: '',
})

function openAccountDialog() {
  accountForm.email = auth.user?.email ?? ''
  accountForm.full_name = auth.user?.full_name ?? ''
  accountForm.current_password = ''
  accountForm.new_password = ''
  accountForm.confirm_password = ''
  accountDialogVisible.value = true
}

async function handleAccountSave() {
  if (!accountForm.current_password) {
    ElMessage.error('請輸入目前密碼以確認身份')
    return
  }
  if (accountForm.new_password && accountForm.new_password !== accountForm.confirm_password) {
    ElMessage.error('新密碼與確認密碼不一致')
    return
  }
  accountSaving.value = true
  try {
    await apiClient.put('/api/v1/admin/auth/me', {
      current_password: accountForm.current_password,
      email: accountForm.email,
      full_name: accountForm.full_name,
      new_password: accountForm.new_password || null,
    })
    await auth.fetchMe()
    ElMessage.success('帳號資料已更新')
    accountDialogVisible.value = false
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail ?? '更新失敗,請確認目前密碼是否正確')
  } finally {
    accountSaving.value = false
  }
}

async function loadLowStockCount() {
  try {
    const { data } = await apiClient.get<Product[]>('/api/v1/admin/products', {
      params: { track_stock: true },
    })
    lowStockCount.value = data.filter((p) => p.stock_quantity <= 0).length
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
        <div class="flex items-center gap-2">
          <span class="mr-2 text-sm text-taupe">{{ auth.user?.full_name }}</span>
          <el-button size="small" @click="openAccountDialog">帳號設定</el-button>
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

    <el-dialog v-model="accountDialogVisible" title="帳號設定" width="92%" class="sm:!w-[420px]">
      <el-form label-position="top">
        <el-form-item label="Email">
          <el-input v-model="accountForm.email" type="email" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="accountForm.full_name" />
        </el-form-item>
        <el-form-item label="新密碼(留空表示不更改)">
          <el-input v-model="accountForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item v-if="accountForm.new_password" label="確認新密碼">
          <el-input v-model="accountForm.confirm_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="目前密碼(必填,用來確認身份)">
          <el-input v-model="accountForm.current_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accountDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="accountSaving" @click="handleAccountSave">儲存</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>
