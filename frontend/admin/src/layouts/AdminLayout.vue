<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import logo from '../images/logo.png'

const auth = useAuthStore()
const router = useRouter()

onMounted(async () => {
  if (!auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
      router.push({ name: 'login' })
    }
  }
})

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <el-container class="h-screen bg-cream">
    <el-aside width="200px" class="border-r border-beige bg-white">
      <div class="flex items-center gap-2 px-4 py-4 text-lg font-bold text-brown">
        <img :src="logo" alt="Wan's Design" class="h-8 w-8 rounded-full object-cover" />
        後台管理
      </div>
      <el-menu :default-active="$route.name as string" router background-color="transparent">
        <el-menu-item index="product-list" :route="{ name: 'product-list' }">商品管理</el-menu-item>
        <el-menu-item index="ready-stock-list" :route="{ name: 'ready-stock-list' }">現貨管理</el-menu-item>
        <el-menu-item index="category-list" :route="{ name: 'category-list' }">分類管理</el-menu-item>
        <el-menu-item index="material-list" :route="{ name: 'material-list' }">原材料管理</el-menu-item>
        <el-menu-item index="order-list" :route="{ name: 'order-list' }">訂單管理</el-menu-item>
        <el-menu-item index="role-list" :route="{ name: 'role-list' }">角色權限</el-menu-item>
        <el-menu-item index="user-list" :route="{ name: 'user-list' }">後台人員</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="flex items-center justify-end border-b border-beige bg-white">
        <span class="mr-4 text-sm text-taupe">{{ auth.user?.full_name }}</span>
        <el-button size="small" @click="handleLogout">登出</el-button>
      </el-header>
      <el-main>
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>
