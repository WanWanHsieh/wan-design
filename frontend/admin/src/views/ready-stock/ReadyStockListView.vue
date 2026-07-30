<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient, imageUrl } from '../../api/client'
import type { Product } from '../../types'

const products = ref<Product[]>([])
const loading = ref(true)
const router = useRouter()

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

    <el-table :data="products" v-loading="loading" stripe>
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
      <el-table-column prop="base_price" label="價格" width="100" />
      <el-table-column label="庫存" width="120">
        <template #default="{ row }">
          <el-tag :type="row.stock_quantity > 0 ? 'success' : 'danger'" size="small">
            {{ row.stock_quantity > 0 ? `現貨 ${row.stock_quantity}` : '已售完' }}
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
  </div>
</template>
