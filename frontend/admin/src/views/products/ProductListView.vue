<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient, imageUrl } from '../../api/client'
import type { Category, Product } from '../../types'

const products = ref<Product[]>([])
const categories = ref<Category[]>([])
const loading = ref(true)
const router = useRouter()

function categoryName(categoryId: number | null): string {
  if (categoryId === null) return '-'
  return categories.value.find((c) => c.id === categoryId)?.name ?? '-'
}

const UNCATEGORIZED_KEY = 'uncategorized'

interface ProductGroup {
  key: string
  name: string
  products: Product[]
}

const productGroups = computed<ProductGroup[]>(() => {
  const groups = new Map<string, ProductGroup>()
  for (const product of products.value) {
    const key = product.category_id === null ? UNCATEGORIZED_KEY : String(product.category_id)
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        name: product.category_id === null ? '未分類' : categoryName(product.category_id),
        products: [],
      })
    }
    groups.get(key)!.products.push(product)
  }
  return Array.from(groups.values())
})

const expandedGroups = ref<Record<string, boolean>>({})

function toggleGroup(key: string) {
  expandedGroups.value[key] = !expandedGroups.value[key]
}

async function loadProducts() {
  loading.value = true
  try {
    const [productsRes, categoriesRes] = await Promise.all([
      apiClient.get<Product[]>('/api/v1/admin/products', { params: { track_stock: false } }),
      apiClient.get<Category[]>('/api/v1/admin/categories'),
    ])
    products.value = productsRes.data
    categories.value = categoriesRes.data
  } finally {
    loading.value = false
  }
}

async function handleDelete(product: Product) {
  await ElMessageBox.confirm(`確定要刪除「${product.name}」嗎?`, '刪除商品', { type: 'warning' })
  await apiClient.delete(`/api/v1/admin/products/${product.id}`)
  ElMessage.success('已刪除')
  await loadProducts()
}

onMounted(loadProducts)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold">商品管理</h1>
      <div class="flex gap-2">
        <el-button @click="router.push({ name: 'product-bulk-import' })">批量匯入</el-button>
        <el-button type="primary" @click="router.push({ name: 'product-new' })">新增商品</el-button>
      </div>
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
      <el-table-column prop="sku" label="SKU" width="140" />
      <el-table-column prop="name" label="商品名稱" />
      <el-table-column label="類別" width="120">
        <template #default="{ row }">{{ categoryName(row.category_id) }}</template>
      </el-table-column>
      <el-table-column prop="base_price" label="價格" width="100" />
      <el-table-column prop="status" label="狀態" width="100" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="router.push({ name: 'product-edit', params: { id: row.id } })">
            編輯
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">刪除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-loading="loading" class="flex flex-col gap-3 sm:hidden">
      <div v-for="group in productGroups" :key="group.key">
        <button
          type="button"
          class="flex w-full items-center gap-1 rounded-xl bg-cream/60 px-3 py-2 font-medium text-brown"
          @click="toggleGroup(group.key)"
        >
          <span class="inline-block transition-transform" :class="expandedGroups[group.key] ? 'rotate-90' : ''">
            ›
          </span>
          {{ group.name }}
          <span class="text-xs text-taupe/60">({{ group.products.length }})</span>
        </button>

        <div v-if="expandedGroups[group.key]" class="mt-2 flex flex-col gap-3">
          <div
            v-for="row in group.products"
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
              <div class="text-xs text-taupe/70">{{ row.sku }}・{{ categoryName(row.category_id) }}</div>
              <div class="mt-1 text-sm text-taupe">NT$ {{ row.base_price }}・{{ row.status }}</div>
              <div class="mt-2 flex gap-2">
                <el-button size="small" class="flex-1" @click="router.push({ name: 'product-edit', params: { id: row.id } })">
                  編輯
                </el-button>
                <el-button size="small" type="danger" class="flex-1" @click="handleDelete(row)">刪除</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
