<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const email = ref('')
const password = ref('')
const loading = ref(false)

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

async function handleSubmit() {
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch {
    ElMessage.error('登入失敗,請確認帳號密碼')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex h-screen items-center justify-center bg-gray-50">
    <el-card class="w-96">
      <h1 class="mb-6 text-center text-xl font-semibold">後台管理登入</h1>
      <el-form label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="Email">
          <el-input v-model="email" type="email" />
        </el-form-item>
        <el-form-item label="密碼">
          <el-input v-model="password" type="password" show-password @keyup.enter="handleSubmit" />
        </el-form-item>
        <el-button type="primary" class="w-full" :loading="loading" @click="handleSubmit">
          登入
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>
