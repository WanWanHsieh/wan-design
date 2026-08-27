<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { apiClient } from '../../api/client'
import type { Announcement } from '../../types'

const message = ref('')
const isActive = ref(false)
const loading = ref(true)
const saving = ref(false)
const updatedAt = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    const { data } = await apiClient.get<Announcement>('/api/v1/admin/announcement')
    message.value = data.message
    isActive.value = data.is_active
    updatedAt.value = data.updated_at
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const { data } = await apiClient.put<Announcement>('/api/v1/admin/announcement', {
      message: message.value,
      is_active: isActive.value,
    })
    updatedAt.value = data.updated_at
    ElMessage.success('已儲存')
  } catch {
    ElMessage.error('儲存失敗')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="max-w-2xl">
    <h1 class="mb-4 text-xl font-semibold">網站公告</h1>
    <p class="mb-4 text-sm text-taupe">
      在前台每一頁的頂端顯示一條公告(例如促銷活動、免運資訊)。關閉「顯示公告」時,前台不會顯示這個區塊。
    </p>

    <el-form v-loading="loading" label-position="top">
      <el-form-item label="公告內容">
        <el-input
          v-model="message"
          type="textarea"
          :rows="4"
          placeholder="例如:🎉 現貨商品滿 $500 免運中!"
        />
      </el-form-item>
      <el-form-item label="顯示公告">
        <el-switch v-model="isActive" />
      </el-form-item>
    </el-form>

    <el-button type="primary" :loading="saving" @click="handleSave">儲存</el-button>
    <p v-if="updatedAt" class="mt-3 text-xs text-taupe/60">上次更新:{{ new Date(updatedAt).toLocaleString() }}</p>
  </div>
</template>
