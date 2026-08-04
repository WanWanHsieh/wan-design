<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { apiClient, imageUrl } from '../api/client'
import PriceTag from '../components/PriceTag.vue'
import { useCartStore } from '../stores/cart'
import { useCategoryNav } from '../composables/useCategoryNav'
import type { Category, ProductListItem } from '../types'

const products = ref<ProductListItem[]>([])
const categories = ref<Category[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const cart = useCartStore()

const quantities = reactive<Record<number, number>>({})
const addedFlash = reactive<Record<number, boolean>>({})

const nav = useCategoryNav(categories)

function availableStock(product: ProductListItem): number {
  return Math.max(0, product.stock_quantity - cart.quantityOf(product.id))
}

function isSoldOut(product: ProductListItem): boolean {
  return availableStock(product) <= 0
}

onMounted(async () => {
  try {
    const [productsRes, categoriesRes] = await Promise.all([
      apiClient.get<ProductListItem[]>('/api/v1/storefront/products', { params: { track_stock: true } }),
      apiClient.get<Category[]>('/api/v1/storefront/categories'),
    ])
    products.value = productsRes.data
    categories.value = categoriesRes.data
    for (const p of productsRes.data) quantities[p.id] = 1
  } catch {
    error.value = '無法載入現貨商品,請稍後再試。'
  } finally {
    loading.value = false
  }
})

const uncategorized = computed(() => products.value.filter((p) => p.category_id === null))

function categoryHasProducts(categoryId: number): boolean {
  const scope = [categoryId, ...categories.value.filter((c) => c.parent_id === categoryId).map((c) => c.id)]
  return products.value.some((p) => p.category_id !== null && scope.includes(p.category_id))
}

const visibleTopCategories = computed(() => nav.topCategories.value.filter((c) => categoryHasProducts(c.id)))

const visibleChildCategories = computed(() =>
  nav.childCategories.value.filter((c) => products.value.some((p) => p.category_id === c.id)),
)

const visibleProducts = computed(() => {
  const scope = nav.categoryIdsInScope.value
  if (scope === null) return nav.showingAll.value ? products.value : []
  return products.value.filter((p) => p.category_id !== null && scope.includes(p.category_id))
})

function categoryThumbnail(categoryId: number): string | null {
  const scope = [categoryId, ...categories.value.filter((c) => c.parent_id === categoryId).map((c) => c.id)]
  const match = products.value.find(
    (p) => p.category_id !== null && scope.includes(p.category_id) && (p.primary_thumbnail || p.primary_image),
  )
  return match ? (match.primary_thumbnail ?? match.primary_image) : null
}

function addToCart(product: ProductListItem) {
  const qty = Math.min(quantities[product.id] ?? 1, availableStock(product))
  if (qty <= 0) return
  cart.addItem(product.id, qty)
  quantities[product.id] = 1
  addedFlash[product.id] = true
  setTimeout(() => {
    addedFlash[product.id] = false
  }, 1200)
}
</script>

<template>
  <main class="mx-auto max-w-6xl px-4 py-10">
    <h1 class="mb-2 flex items-center gap-2 text-2xl font-bold text-brown">
      <span aria-hidden="true">🎁</span>現貨商品
    </h1>
    <p class="mb-4 text-sm text-taupe">以下商品皆為現貨,加入購物車後即可直接下單,不需另外挑選布料。</p>

    <nav class="mb-6 flex items-center gap-1 text-sm text-taupe">
      <button type="button" class="hover:text-terracotta" :class="{ 'font-medium text-terracotta': !nav.selectedTop.value && !nav.showingAll.value }" @click="nav.reset()">
        現貨商品
      </button>
      <template v-if="nav.selectedTop.value">
        <span>›</span>
        <button
          type="button"
          class="hover:text-terracotta"
          :class="{ 'font-medium text-terracotta': !nav.selectedSub.value }"
          @click="nav.selectTop(nav.selectedTop.value.slug)"
        >
          {{ nav.selectedTop.value.name }}
        </button>
      </template>
      <template v-if="nav.selectedSub.value">
        <span>›</span>
        <span class="font-medium text-terracotta">{{ nav.selectedSub.value.name }}</span>
      </template>
      <template v-if="nav.showingAll.value">
        <span>›</span>
        <span class="font-medium text-terracotta">全部商品</span>
      </template>
    </nav>

    <p v-if="loading" class="text-taupe">載入中...</p>
    <p v-else-if="error" class="text-red-600">{{ error }}</p>
    <p v-else-if="products.length === 0" class="text-taupe">目前沒有上架的現貨商品。</p>

    <template v-else>
      <!-- Top level: browse by category -->
      <div v-if="!nav.selectedTop.value && !nav.showingAll.value">
        <div class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
          <button
            v-for="cat in visibleTopCategories"
            :key="cat.id"
            type="button"
            class="group block overflow-hidden rounded-2xl border border-beige bg-white text-left shadow-[0_2px_10px_rgba(180,140,110,0.12)] transition hover:-translate-y-0.5 hover:shadow-[0_6px_16px_rgba(180,140,110,0.2)]"
            @click="nav.selectTop(cat.slug)"
          >
            <div class="aspect-square bg-cream-dark">
              <img
                v-if="categoryThumbnail(cat.id)"
                :src="imageUrl(categoryThumbnail(cat.id)!)"
                :alt="cat.name"
                class="h-full w-full object-cover"
              />
              <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
            </div>
            <div class="p-3">
              <p class="truncate text-sm font-medium text-brown group-hover:text-terracotta">{{ cat.name }}</p>
            </div>
          </button>
          <button
            type="button"
            class="flex items-center justify-center rounded-2xl border border-dashed border-taupe/40 bg-cream/60 p-6 text-sm text-taupe transition hover:border-terracotta hover:text-terracotta"
            @click="nav.selectAll()"
          >
            瀏覽全部現貨 →
          </button>
        </div>

        <p v-if="uncategorized.length" class="mt-4 text-xs text-taupe">
          另有 {{ uncategorized.length }} 件未分類現貨,可點「瀏覽全部現貨」查看。
        </p>
      </div>

      <!-- Category selected: show sub-category chips + filtered products -->
      <div v-else>
        <div v-if="visibleChildCategories.length" class="mb-6 flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-full border px-3 py-1 text-sm transition"
            :class="!nav.selectedSub.value ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
            @click="nav.selectSub(null)"
          >
            全部
          </button>
          <button
            v-for="sub in visibleChildCategories"
            :key="sub.id"
            type="button"
            class="rounded-full border px-3 py-1 text-sm transition"
            :class="nav.selectedSub.value?.id === sub.id ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
            @click="nav.selectSub(sub.slug)"
          >
            {{ sub.name }}
          </button>
        </div>

        <p v-if="visibleProducts.length === 0" class="text-taupe">這個分類目前還沒有現貨商品。</p>
        <div v-else class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
          <div
            v-for="product in visibleProducts"
            :key="product.id"
            class="flex flex-col overflow-hidden rounded-2xl border border-beige bg-white shadow-[0_2px_10px_rgba(180,140,110,0.12)]"
          >
            <RouterLink :to="{ name: 'product-detail', params: { slug: product.slug } }" class="block">
              <div class="aspect-square bg-cream-dark">
                <img
                  v-if="product.primary_thumbnail ?? product.primary_image"
                  :src="imageUrl(product.primary_thumbnail ?? product.primary_image!)"
                  :alt="product.name"
                  class="h-full w-full object-cover"
                />
                <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
              </div>
            </RouterLink>
            <div class="flex flex-1 flex-col gap-2 p-3">
              <p class="truncate text-sm font-medium text-brown">{{ product.name }}</p>
              <PriceTag
          :base-price="product.base_price"
          :effective-price="product.effective_price"
          :is-on-sale="product.is_on_sale"
        />

              <p v-if="isSoldOut(product)" class="text-xs font-medium text-red-500">已售完</p>
              <p v-else class="text-xs text-taupe">剩 {{ availableStock(product) }} 件</p>

              <div v-if="!isSoldOut(product)" class="mt-auto flex flex-col gap-2 sm:flex-row sm:items-center">
                <input
                  v-model.number="quantities[product.id]"
                  type="number"
                  min="1"
                  :max="availableStock(product)"
                  class="w-full rounded-lg border border-beige px-2 py-1 text-sm focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta sm:w-16"
                />
                <button
                  type="button"
                  class="w-full whitespace-nowrap rounded-full bg-terracotta px-3 py-1.5 text-sm font-medium text-white transition hover:bg-terracotta-dark sm:flex-1"
                  @click="addToCart(product)"
                >
                  {{ addedFlash[product.id] ? '已加入!' : '加入購物車' }}
                </button>
              </div>
              <button
                v-else
                type="button"
                disabled
                class="mt-auto rounded-full bg-beige px-3 py-1.5 text-sm font-medium text-taupe"
              >
                已售完
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </main>
</template>
