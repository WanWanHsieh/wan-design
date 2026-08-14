<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient, imageUrl } from '../../api/client'
import type { Material } from '../../types'

const materials = ref<Material[]>([])
const total = ref(0)
const loading = ref(true)
const router = useRouter()

const UNIT_LABELS: Record<string, string> = {
  meter: '公尺',
  yard: '碼',
  kg: '公斤',
  piece: '件',
}

const filters = ref({
  search: '',
  fabric_type: '',
  origin: '',
  status: '',
})
const page = ref(1)
const pageSize = ref(20)

let searchDebounce: ReturnType<typeof setTimeout> | null = null

async function loadMaterials() {
  loading.value = true
  try {
    const { data } = await apiClient.get<{
      items: Material[]
      total: number
      page: number
      page_size: number
    }>('/api/v1/admin/materials', {
      params: {
        search: filters.value.search || undefined,
        fabric_type: filters.value.fabric_type || undefined,
        origin: filters.value.origin || undefined,
        status: filters.value.status || undefined,
        page: page.value,
        page_size: pageSize.value,
      },
    })
    materials.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function resetAndReload() {
  page.value = 1
  loadMaterials()
}

watch(
  () => filters.value.search,
  () => {
    if (searchDebounce) clearTimeout(searchDebounce)
    searchDebounce = setTimeout(resetAndReload, 300)
  },
)
watch([() => filters.value.fabric_type, () => filters.value.origin, () => filters.value.status], resetAndReload)
watch(pageSize, resetAndReload)

function handlePageChange(newPage: number) {
  page.value = newPage
  loadMaterials()
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
      <div class="flex gap-2">
        <el-button @click="router.push({ name: 'material-bulk-import' })">批量匯入</el-button>
        <el-button type="primary" @click="router.push({ name: 'material-new' })">新增原材料</el-button>
      </div>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-2">
      <el-input
        v-model="filters.search"
        placeholder="搜尋名稱或編號"
        clearable
        class="w-full sm:w-52"
      />
      <el-select v-model="filters.fabric_type" placeholder="布料種類" clearable class="w-full sm:w-36">
        <el-option label="二紗" value="二紗" />
        <el-option label="棉布" value="棉布" />
        <el-option label="厚棉" value="厚棉" />
      </el-select>
      <el-select v-model="filters.origin" placeholder="產地" clearable class="w-full sm:w-32">
        <el-option label="台灣" value="台灣" />
        <el-option label="韓國" value="韓國" />
        <el-option label="美國" value="美國" />
        <el-option label="日本" value="日本" />
        <el-option label="其他" value="其他" />
      </el-select>
      <el-select v-model="filters.status" placeholder="狀態" clearable class="w-full sm:w-32">
        <el-option label="使用中" value="active" />
        <el-option label="已停用" value="discontinued" />
      </el-select>
    </div>

    <el-table :data="materials" v-loading="loading" stripe class="hidden sm:block">
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
      <el-table-column prop="fabric_type" label="布料種類" width="100" />
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

    <div v-loading="loading" class="flex flex-col gap-3 sm:hidden">
      <div
        v-for="row in materials"
        :key="row.id"
        class="flex gap-3 rounded-xl border border-beige bg-white p-3 shadow-[0_2px_8px_rgba(180,140,110,0.08)]"
      >
        <img
          v-if="fabricThumbnail(row)"
          :src="imageUrl(fabricThumbnail(row)!)"
          class="h-16 w-16 flex-none rounded-lg object-cover"
        />
        <div class="flex-1">
          <div class="font-medium text-brown">{{ row.name }}</div>
          <div class="text-xs text-taupe/70">{{ row.code }}・{{ row.status }}</div>
          <div class="mt-1 text-sm text-taupe">
            成本 NT$ {{ row.unit_cost }} / {{ UNIT_LABELS[row.unit] ?? row.unit }}・加價 NT$ {{ row.price_addon }}
          </div>
          <div class="text-sm text-taupe">
            庫存 {{ row.quantity_on_hand }} {{ UNIT_LABELS[row.unit] ?? row.unit }}
          </div>
          <div v-if="row.origin || row.fabric_type || row.supplier" class="text-xs text-taupe/70">
            <template v-if="row.origin">產地:{{ row.origin }}</template>
            <template v-if="row.origin && (row.fabric_type || row.supplier)"> ・ </template>
            <template v-if="row.fabric_type">種類:{{ row.fabric_type }}</template>
            <template v-if="row.fabric_type && row.supplier"> ・ </template>
            <template v-if="row.supplier">供應商:{{ row.supplier }}</template>
          </div>
          <div class="mt-2 flex gap-2">
            <el-button size="small" class="flex-1" @click="router.push({ name: 'material-edit', params: { id: row.id } })">
              編輯
            </el-button>
            <el-button size="small" type="danger" class="flex-1" @click="handleDelete(row)">刪除</el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-4 flex justify-center sm:justify-end">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>
