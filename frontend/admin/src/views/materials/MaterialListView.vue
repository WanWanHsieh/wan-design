<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient, imageUrl } from '../../api/client'
import type { Material } from '../../types'

const materials = ref<Material[]>([])
const loading = ref(true)
const router = useRouter()

const UNIT_LABELS: Record<string, string> = {
  meter: '公尺',
  yard: '碼',
  kg: '公斤',
  piece: '件',
}

async function loadMaterials() {
  loading.value = true
  try {
    const { data } = await apiClient.get<Material[]>('/api/v1/admin/materials')
    materials.value = data
  } finally {
    loading.value = false
  }
}

async function handleDelete(material: Material) {
  await ElMessageBox.confirm(`確定要刪除「${material.name}」嗎?`, '刪除原材料', { type: 'warning' })
  await apiClient.delete(`/api/v1/admin/materials/${material.id}`)
  ElMessage.success('已刪除')
  await loadMaterials()
}

function fabricThumbnail(material: Material): string | null {
  const image = material.images.find((img) => img.image_type === 'fabric')
  if (!image) return null
  return image.thumbnail_key ?? image.storage_key
}

onMounted(loadMaterials)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold">原材料管理(布料)</h1>
      <el-button type="primary" @click="router.push({ name: 'material-new' })">新增原材料</el-button>
    </div>

    <el-table :data="materials" v-loading="loading" stripe>
      <el-table-column label="照片" width="80">
        <template #default="{ row }">
          <img
            v-if="fabricThumbnail(row)"
            :src="imageUrl(fabricThumbnail(row)!)"
            class="h-12 w-12 rounded object-cover"
          />
        </template>
      </el-table-column>
      <el-table-column prop="code" label="編號" width="120" />
      <el-table-column prop="name" label="布料樣式" />
      <el-table-column label="進貨成本">
        <template #default="{ row }">NT$ {{ row.unit_cost }} / {{ UNIT_LABELS[row.unit] ?? row.unit }}</template>
      </el-table-column>
      <el-table-column label="顧客加價" width="100">
        <template #default="{ row }">NT$ {{ row.price_addon }}</template>
      </el-table-column>
      <el-table-column label="庫存量">
        <template #default="{ row }">{{ row.quantity_on_hand }} {{ UNIT_LABELS[row.unit] ?? row.unit }}</template>
      </el-table-column>
      <el-table-column prop="origin" label="產地" width="100" />
      <el-table-column prop="supplier" label="供應商" />
      <el-table-column prop="status" label="狀態" width="100" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="router.push({ name: 'material-edit', params: { id: row.id } })">
            編輯
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">刪除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
