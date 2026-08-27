<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import PriceTag from '../components/PriceTag.vue'
import { useCategoryNav } from '../composables/useCategoryNav'
import { useOrderDraftStore } from '../stores/orderDraft'
import { useToastStore } from '../stores/toast'
import type { Category, ProductListItem } from '../types'

const products = ref<ProductListItem[]>([])
const categories = ref<Category[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const lightboxVisible = ref(false)
const lightboxSrc = ref('')
const lightboxAlt = ref('')

const orderDraft = useOrderDraftStore()
const toast = useToastStore()
const addedFlash = reactive<Record<number, boolean>>({})

function addToOrderDraft(product: ProductListItem) {
  orderDraft.addItem(product.id, 1)
  addedFlash[product.id] = true
  setTimeout(() => {
    addedFlash[product.id] = false
  }, 1200)
  toast.show('已加入訂購清單 ✓', { label: '前往結帳', to: '/order' })
}

const nav = useCategoryNav(categories)

onMounted(async () => {
  try {
    const [productsRes, categoriesRes] = await Promise.all([
      apiClient.get<ProductListItem[]>('/api/v1/storefront/products'),
      apiClient.get<Category[]>('/api/v1/storefront/categories'),
    ])
    products.value = productsRes.data
    categories.value = categoriesRes.data
  } catch {
    error.value = '無法載入商品,請確認後端服務是否啟動。'
  } finally {
    loading.value = false
  }
})

const uncategorized = computed(() => products.value.filter((p) => p.category_id === null))

const visibleTopCategories = computed(() => nav.topCategories.value)

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

function openLightbox(product: ProductListItem) {
  if (!product.primary_image) return
  lightboxSrc.value = imageUrl(product.primary_image)
  lightboxAlt.value = product.name
  lightboxVisible.value = true
}

function priceRange(product: ProductListItem): { min: number; max: number } | null {
  if (!product.has_variants || product.variants.length === 0) return null
  const prices = product.variants.map((v) => v.price)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  return min === max ? null : { min, max }
}
</script>

<template>
  <main class="mx-auto max-w-6xl px-4 py-10">
    <h1 class="mb-2 flex items-center gap-2 text-2xl font-bold text-brown">
      <span aria-hidden="true">🌿</span>商品列表
    </h1>

    <nav class="mb-6 flex items-center gap-1 text-sm text-taupe">
      <button type="button" class="hover:text-terracotta" :class="{ 'font-medium text-terracotta': !nav.selectedTop.value && !nav.showingAll.value }" @click="nav.reset()">
        商品列表
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
    <p v-else-if="products.length === 0" class="text-taupe">
      目前還沒有上架的商品,請到後台管理新增商品。
    </p>

    <template v-else>
      <!-- Top level: browse by category -->
      <div v-if="!nav.selectedTop.value && !nav.showingAll.value">
        <div class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
          <button
            v-for="cat in visibleTopCategories"
            :key="cat.id"
            type="button"
            class="group block overflow-hidden rounded-3xl border border-beige bg-white text-left shadow-[0_4px_14px_rgba(180,140,110,0.14)] transition duration-300 hover:-translate-y-1 hover:rotate-1 hover:shadow-[0_10px_24px_rgba(180,140,110,0.24)]"
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
            <div class="border-t-2 border-dashed border-terracotta/25"></div>
            <div class="p-3">
              <p class="truncate text-sm font-medium text-brown group-hover:text-terracotta">{{ cat.name }}</p>
            </div>
          </button>
          <button
            type="button"
            class="flex items-center justify-center rounded-3xl border-2 border-dashed border-taupe/40 bg-cream/60 p-6 text-sm text-taupe transition hover:border-terracotta hover:text-terracotta"
            @click="nav.selectAll()"
          >
            瀏覽全部商品 →
          </button>
        </div>

        <div v-if="uncategorized.length" class="mt-10">
          <h2 class="mb-1 text-sm font-medium text-taupe">未分類商品</h2>
          <p class="mb-3 text-sm text-taupe">💡 點進商品可查看更多花色參考圖</p>
          <div class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
            <RouterLink
              v-for="product in uncategorized"
              :key="product.id"
              :to="{ name: 'product-detail', params: { slug: product.slug } }"
              class="group block overflow-hidden rounded-3xl border border-beige bg-white shadow-[0_4px_14px_rgba(180,140,110,0.14)] transition duration-300 hover:-translate-y-1 hover:rotate-1 hover:shadow-[0_10px_24px_rgba(180,140,110,0.24)]"
            >
              <div class="aspect-square bg-cream-dark">
                <img
                  v-if="product.primary_thumbnail || product.primary_image"
                  :src="imageUrl(product.primary_thumbnail ?? product.primary_image!)"
                  :alt="product.name"
                  class="h-full w-full cursor-zoom-in object-cover"
                  @click.stop.prevent="openLightbox(product)"
                />
                <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
              </div>
              <div class="border-t-2 border-dashed border-terracotta/25"></div>
              <div class="p-3">
                <p class="truncate text-sm text-brown group-hover:text-terracotta">{{ product.name }}</p>
                <p class="mt-1">
                  <PriceTag
                    :base-price="product.base_price"
                    :effective-price="product.effective_price"
                    :is-on-sale="product.is_on_sale"
                    :price-range="priceRange(product)"
                  />
                </p>
                <p class="mt-0.5 text-xs text-taupe">訂製・需選布料</p>
                <button
                  type="button"
                  class="mt-2 w-full rounded-full bg-terracotta px-3 py-1.5 text-xs font-medium text-white transition hover:bg-terracotta-dark"
                  @click.stop.prevent="addToOrderDraft(product)"
                >
                  {{ addedFlash[product.id] ? '已加入!' : '加入訂購清單' }}
                </button>
              </div>
            </RouterLink>
          </div>
        </div>
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

        <p v-if="visibleProducts.length" class="mb-4 text-sm text-taupe">
          💡 點進商品可查看更多花色參考圖
        </p>
        <p v-if="visibleProducts.length === 0" class="text-taupe">這個分類目前還沒有商品。</p>
        <div v-else class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
          <RouterLink
            v-for="product in visibleProducts"
            :key="product.id"
            :to="{ name: 'product-detail', params: { slug: product.slug } }"
            class="group block overflow-hidden rounded-3xl border border-beige bg-white shadow-[0_4px_14px_rgba(180,140,110,0.14)] transition duration-300 hover:-translate-y-1 hover:rotate-1 hover:shadow-[0_10px_24px_rgba(180,140,110,0.24)]"
          >
            <div class="aspect-square bg-cream-dark">
              <img
                v-if="product.primary_thumbnail || product.primary_image"
                :src="imageUrl(product.primary_thumbnail ?? product.primary_image!)"
                :alt="product.name"
                class="h-full w-full cursor-zoom-in object-cover"
                @click.stop.prevent="openLightbox(product)"
              />
              <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
            </div>
            <div class="border-t-2 border-dashed border-terracotta/25"></div>
            <div class="p-3">
              <p class="truncate text-sm text-brown group-hover:text-terracotta">{{ product.name }}</p>
              <p class="mt-1">
                <PriceTag
                  :base-price="product.base_price"
                  :effective-price="product.effective_price"
                  :is-on-sale="product.is_on_sale"
                  :price-range="priceRange(product)"
                />
              </p>
              <p class="mt-0.5 text-xs text-taupe">訂製・需選布料</p>
              <button
                type="button"
                class="mt-2 w-full rounded-full bg-terracotta px-3 py-1.5 text-xs font-medium text-white transition hover:bg-terracotta-dark"
                @click.stop.prevent="addToOrderDraft(product)"
              >
                {{ addedFlash[product.id] ? '已加入!' : '加入訂購清單' }}
              </button>
            </div>
          </RouterLink>
        </div>
      </div>
    </template>

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
