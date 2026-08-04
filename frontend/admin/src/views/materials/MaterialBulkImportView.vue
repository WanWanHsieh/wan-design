<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiClient } from '../../api/client'

const router = useRouter()
const csvFile = ref<File | null>(null)
const zipFile = ref<File | null>(null)
const submitting = ref(false)
const result = ref<{ created: number; errors: { row: number; message: string }[] } | null>(null)

const TEMPLATE_CSV =
  '名稱,單位,成本,加價,庫存量,產地,供應商,備註,照片檔名\n' +
  '範例布料,碼,150,0,5,韓國,,,範例布料.jpg\n'

function downloadTemplate() {
  const blob = new Blob(['﻿' + TEMPLATE_CSV], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '原材料批量匯入範本.csv'
  a.click()
  URL.revokeObjectURL(url)
}

function handleCsvChange(event: Event) {
  csvFile.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

function handleZipChange(event: Event) {
  zipFile.value = (event.target as HTMLInputElement).files?.[0] ?? null
}

async function handleSubmit() {
  if (!csvFile.value) {
    ElMessage.error('請選擇 CSV 檔案')
    return
  }
  submitting.value = true
  result.value = null
  try {
    const formData = new FormData()
    formData.append('csv_file', csvFile.value)
    if (zipFile.value) {
      formData.append('zip_file', zipFile.value)
    }
    const { data } = await apiClient.post('/api/v1/admin/materials/bulk-import', formData)
    result.value = data
    ElMessage.success(`已建立 ${data.created} 筆原材料`)
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail ?? '匯入失敗,請確認檔案格式')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold">原材料批量匯入</h1>
      <el-button @click="router.push({ name: 'material-list' })">返回原材料管理</el-button>
    </div>

    <el-card class="mb-4">
      <p class="mb-2 text-sm text-gray-700">操作步驟:</p>
      <ol class="ml-4 list-decimal space-y-1 text-sm text-gray-600">
        <li>下載範本 CSV,依照欄位填入布料資料(可用 Excel 開啟編輯,填完存成 CSV 格式)</li>
        <li>把所有布料照片放同一個資料夾,檔名對應 CSV 裡的「照片檔名」欄位,壓縮成一個 ZIP</li>
        <li>選擇 CSV 跟 ZIP,按「開始匯入」</li>
      </ol>
      <el-button class="mt-3" @click="downloadTemplate">下載範本 CSV</el-button>
    </el-card>

    <el-card>
      <el-form label-position="top">
        <el-form-item label="CSV 檔案">
          <input type="file" accept=".csv" @change="handleCsvChange" />
        </el-form-item>
        <el-form-item label="照片 ZIP(選填)">
          <input type="file" accept=".zip" @change="handleZipChange" />
        </el-form-item>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">開始匯入</el-button>
      </el-form>
    </el-card>

    <el-card v-if="result" class="mt-4">
      <p class="font-medium text-brown">已建立 {{ result.created }} 筆原材料</p>
      <div v-if="result.errors.length" class="mt-3">
        <p class="mb-2 text-sm font-medium text-amber-700">提醒事項:</p>
        <ul class="ml-4 list-disc space-y-1 text-sm text-amber-700">
          <li v-for="(err, i) in result.errors" :key="i">第 {{ err.row }} 列:{{ err.message }}</li>
        </ul>
      </div>
    </el-card>
  </div>
</template>
