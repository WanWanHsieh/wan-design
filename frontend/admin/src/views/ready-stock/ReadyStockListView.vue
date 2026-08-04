<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient, imageUrl } from '../../api/client'
import type { Product } from '../../types'

const LOW_STOCK_THRESHOLD = 2

const products = ref<Product[]>([])
const loading = ref(true)
const router = useRouter()

const lowStockCount = computed(
  () => products.value.filter((p) => p.stock_quantity <= LOW_STOCK_THRESHOLD).length,
)

function stockTagType(qty: number): 'success' | 'warning' | 'danger' {
  if (qty <= 0) return 'danger'
  if (qty <= LOW_STOCK_THRESHOLD) return 'warning'
  return 'success'
}

function stockLabel(qty: number): string {
  if (qty <= 0) return '已售完'
  if (qty <= LOW_STOCK_THRESHOLD) return `低庫存 ${qty}`
  return `現貨 ${qty}`
}

async function loadProducts() {
  loading.value = true
  try {
    const { data } = await apiClient.get<Product[]>('/api/v1/admin/products', {
      params: { track_stock: true },
    })
    products.value = data
  } finally {
    loading.value = false
  }
}

async function handleDelete(product: Product) {
  await ElMessageBox.confirm(`確定要刪除「${product.name}」嗎?`, '刪除現貨商品', { type: 'warning' })
  await apiClient.delete(`/api/v1/admin/products/${product.id}`)
  ElMessage.success('已刪除')
  await loadProducts()
}

onMounted(loadProducts)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold">現貨管理</h1>
      <el-button type="primary" @click="router.push({ name: 'ready-stock-new' })">新增現貨商品</el-button>
    </div>
    <p class="mb-4 text-sm text-gray-500">
      同一款式可以建立多筆現貨,每筆代表一件實際庫存(各自花色照片、庫存量)。
    </p>

    <div
      v-if="lowStockCount > 0"
      class="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-800"
    >
      ⚠️ 有 {{ lowStockCount }} 項現貨庫存偏低(≤{{ LOW_STOCK_THRESHOLD }}件或已售完),建議儘快補貨。
    </div>

    <el-table :data="products" v-loading="loading" stripe class="hidden sm:block">
      <el-table-column label="圖片" width="80">
        <template #default="{ row }">
          <img
            v-if="row.images[0]"
            :src="imageUrl(row.images[0].thumbnail_key ?? row.images[0].storage_key)"
            class="h-12 w-12 rounded object-cover"
          />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名稱" />
      <el-table-column label="價格" width="120">
        <template #default="{ row }">
          <span v-if="row.is_on_sale" class="text-taupe/60 line-through">{{ row.base_price }}</span>
          <span v-if="row.is_on_sale" class="ml-1 font-medium text-red-600">{{ row.sale_price }}</span>
          <span v-else>{{ row.base_price }}</span>
        </template>
      </el-table-column>
      <el-table-column label="庫存" width="120">
        <template #default="{ row }">
          <el-tag :type="stockTagType(row.stock_quantity)" size="small">
            {{ stockLabel(row.stock_quantity) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="狀態" width="100" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="router.push({ name: 'ready-stock-edit', params: { id: row.id } })">
            編輯
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">刪除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-loading="loading" class="flex flex-col gap-3 sm:hidden">
      <div
        v-for="row in products"
        :key="row.id"
        class="flex gap-3 rounded-xl border border-beige bg-white p-3 shadow-[0_2px_8px_rgba(180,140,110,0.08)]"
      >
        <img
          v-if="row.images[0]"
          :src="imageUrl(row.images[0].thumbnail_key ?? row.images[0].storage_key)"
          class="h-16 w-16 flex-none rounded-lg object-cover"
        />
        <div class="flex-1">
          <div class="font-medium text-brown">{{ row.name }}</div>
          <div class="mt-1 flex items-center gap-2 text-sm text-taupe">
            <span v-if="row.is_on_sale">
              <span class="text-taupe/60 line-through">NT$ {{ row.base_price }}</span>
              <span class="ml-1 font-medium text-red-600">NT$ {{ row.sale_price }}</span>
            </span>
            <span v-else>NT$ {{ row.base_price }}</span>
            <el-tag :type="stockTagType(row.stock_quantity)" size="small">
              {{ stockLabel(row.stock_quantity) }}
            </el-tag>
          </div>
          <div class="mt-1 text-xs text-taupe/70">狀態:{{ row.status }}</div>
          <div class="mt-2 flex gap-2">
            <el-button size="small" class="flex-1" @click="router.push({ name: 'ready-stock-edit', params: { id: row.id } })">
              編輯
            </el-button>
            <el-button size="small" type="danger" class="flex-1" @click="handleDelete(row)">刪除</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
