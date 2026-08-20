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

function variantPriceRange(product: Product): string | null {
  if (!product.has_variants || product.variants.length === 0) return null
  const prices = product.variants.filter((v) => v.is_active).map((v) => v.price)
  if (prices.length === 0) return null
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  return min === max ? `NT$ ${min}` : `NT$ ${min}–${max}`
}

function categoryName(categoryId: number | null): string {
  if (categoryId === null) return '-'
  return categories.value.find((c) => c.id === categoryId)?.name ?? '-'
}

const UNCATEGORIZED_KEY = 'uncategorized'

function topCategoryFor(categoryId: number | null): Category | null {
  if (categoryId === null) return null
  let category = categories.value.find((c) => c.id === categoryId) ?? null
  while (category?.parent_id !== null && category?.parent_id !== undefined) {
    const parent = categories.value.find((c) => c.id === category!.parent_id)
    if (!parent) break
    category = parent
  }
  return category
}

interface ProductGroup {
  key: string
  name: string
  products: Product[]
}

const productGroups = computed<ProductGroup[]>(() => {
  const groups = new Map<string, ProductGroup>()
  for (const product of products.value) {
    const topCategory = topCategoryFor(product.category_id)
    const key = topCategory ? String(topCategory.id) : UNCATEGORIZED_KEY
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        name: topCategory ? topCategory.name : '未分類',
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

interface ProductTreeRow {
  key: string
  isCategory: boolean
  categoryLabel?: string
  product?: Product
  children?: ProductTreeRow[]
}

const productTree = computed<ProductTreeRow[]>(() =>
  productGroups.value.map((group) => ({
    key: group.key,
    isCategory: true,
    categoryLabel: group.name,
    children: group.products.map((product) => ({
      key: `p-${product.id}`,
      isCategory: false,
      product,
    })),
  })),
)

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

async function toggleFeatured(product: Product) {
  const next = !product.is_featured
  try {
    await apiClient.put(`/api/v1/admin/products/${product.id}`, { is_featured: next })
    product.is_featured = next
    ElMessage.success(next ? '已設為主打商品' : '已取消主打')
  } catch {
    ElMessage.error('更新失敗,請稍後再試')
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

    <el-table
      :data="productTree"
      v-loading="loading"
      row-key="key"
      :tree-props="{ children: 'children' }"
      stripe
      class="hidden sm:block"
    >
      <el-table-column label="圖片" width="80">
        <template #default="{ row }">
          <img
            v-if="!row.isCategory && row.product.images[0]"
            :src="imageUrl(row.product.images[0].thumbnail_key ?? row.product.images[0].storage_key)"
            class="h-12 w-12 rounded object-cover"
          />
        </template>
      </el-table-column>
      <el-table-column label="SKU" width="140">
        <template #default="{ row }">{{ row.isCategory ? '' : row.product.sku }}</template>
      </el-table-column>
      <el-table-column label="商品名稱">
        <template #default="{ row }">
          <span v-if="row.isCategory" class="font-medium text-brown">
            {{ row.categoryLabel }}({{ row.children.length }})
          </span>
          <span v-else>{{ row.product.name }}</span>
        </template>
      </el-table-column>
      <el-table-column label="類別" width="120">
        <template #default="{ row }">{{ row.isCategory ? '' : categoryName(row.product.category_id) }}</template>
      </el-table-column>
      <el-table-column label="價格" width="120">
        <template #default="{ row }">
          <template v-if="!row.isCategory">
            <span v-if="variantPriceRange(row.product)">{{ variantPriceRange(row.product) }} 起</span>
            <template v-else>
              <span v-if="row.product.is_on_sale" class="text-taupe/60 line-through">{{ row.product.base_price }}</span>
              <span v-if="row.product.is_on_sale" class="ml-1 font-medium text-red-600">{{ row.product.sale_price }}</span>
              <span v-else>{{ row.product.base_price }}</span>
            </template>
          </template>
        </template>
      </el-table-column>
      <el-table-column label="狀態" width="100">
        <template #default="{ row }">{{ row.isCategory ? '' : row.product.status }}</template>
      </el-table-column>
      <el-table-column label="主打" width="70">
        <template #default="{ row }">
          <button
            v-if="!row.isCategory"
            type="button"
            class="text-lg"
            :class="row.product.is_featured ? 'text-amber-500' : 'text-gray-300'"
            :title="row.product.is_featured ? '取消主打' : '設為主打'"
            @click="toggleFeatured(row.product)"
          >
            ★
          </button>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <template v-if="!row.isCategory">
            <el-button size="small" @click="router.push({ name: 'product-edit', params: { id: row.product.id } })">
              編輯
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.product)">刪除</el-button>
          </template>
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
              <div class="flex items-center gap-1">
                <span class="font-medium text-brown">{{ row.name }}</span>
                <button
                  type="button"
                  class="text-lg"
                  :class="row.is_featured ? 'text-amber-500' : 'text-gray-300'"
                  :title="row.is_featured ? '取消主打' : '設為主打'"
                  @click="toggleFeatured(row)"
                >
                  ★
                </button>
              </div>
              <div class="text-xs text-taupe/70">{{ row.sku }}・{{ categoryName(row.category_id) }}</div>
              <div class="mt-1 text-sm text-taupe">
                <template v-if="variantPriceRange(row)">{{ variantPriceRange(row) }} 起</template>
                <template v-else-if="row.is_on_sale">
                  <span class="text-taupe/60 line-through">NT$ {{ row.base_price }}</span>
                  <span class="ml-1 font-medium text-red-600">NT$ {{ row.sale_price }}</span>
                </template>
                <template v-else>NT$ {{ row.base_price }}</template>
                ・{{ row.status }}
              </div>
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
