<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import PriceTag from '../components/PriceTag.vue'
import { useCartStore } from '../stores/cart'
import { useOrderDraftStore } from '../stores/orderDraft'
import type { ProductListItem } from '../types'

const products = ref<ProductListItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const lightboxVisible = ref(false)
const lightboxSrc = ref('')
const lightboxAlt = ref('')

const orderDraft = useOrderDraftStore()
const cart = useCartStore()
const addedFlash = reactive<Record<number, boolean>>({})
const quantities = reactive<Record<number, number>>({})

function openLightbox(product: ProductListItem) {
  const image = product.primary_image ?? product.primary_thumbnail
  if (!image) return
  lightboxSrc.value = imageUrl(image)
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

function addToOrderDraft(product: ProductListItem) {
  orderDraft.addItem(product.id, 1)
  addedFlash[product.id] = true
  setTimeout(() => {
    addedFlash[product.id] = false
  }, 1200)
}

function availableStock(product: ProductListItem): number {
  return product.stock_quantity
}

function isSoldOut(product: ProductListItem): boolean {
  return availableStock(product) <= 0
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

onMounted(async () => {
  try {
    const [orderProductsRes, inStockProductsRes] = await Promise.all([
      apiClient.get<ProductListItem[]>('/api/v1/storefront/products'),
      apiClient.get<ProductListItem[]>('/api/v1/storefront/products', { params: { track_stock: true } }),
    ])
    const all = [...orderProductsRes.data, ...inStockProductsRes.data]
    products.value = all.filter((p) => p.is_featured)
    for (const p of products.value) quantities[p.id] = 1
  } catch {
    error.value = '無法載入主打商品,請確認後端服務是否啟動。'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="mx-auto max-w-6xl px-4 py-10">
    <h1 class="mb-6 flex items-center gap-2 text-2xl font-bold text-brown">
      <span aria-hidden="true">💛</span>本週主打商品
    </h1>

    <p v-if="loading" class="text-taupe">載入中...</p>
    <p v-else-if="error" class="text-red-600">{{ error }}</p>
    <p v-else-if="products.length === 0" class="text-taupe">目前還沒有主打商品,敬請期待!</p>

    <div v-else class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
      <div
        v-for="product in products"
        :key="product.id"
        class="group flex flex-col overflow-hidden rounded-3xl border border-beige bg-white shadow-[0_4px_14px_rgba(180,140,110,0.14)] transition duration-300 hover:-translate-y-1 hover:rotate-1 hover:shadow-[0_10px_24px_rgba(180,140,110,0.24)]"
      >
        <RouterLink :to="{ name: 'product-detail', params: { slug: product.slug } }" class="block">
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
        </RouterLink>
        <div class="border-t-2 border-dashed border-terracotta/25"></div>
        <div class="flex flex-1 flex-col gap-1 p-3">
          <RouterLink :to="{ name: 'product-detail', params: { slug: product.slug } }">
            <p class="truncate text-sm text-brown group-hover:text-terracotta">{{ product.name }}</p>
          </RouterLink>
          <PriceTag
            :base-price="product.base_price"
            :effective-price="product.effective_price"
            :is-on-sale="product.is_on_sale"
            :price-range="priceRange(product)"
          />
          <p v-if="!product.track_stock" class="text-xs text-taupe">訂製・需選布料</p>
          <p v-else-if="isSoldOut(product)" class="text-xs font-medium text-red-500">已售完</p>
          <p v-else class="text-xs text-taupe">剩 {{ availableStock(product) }} 件</p>

          <button
            v-if="!product.track_stock"
            type="button"
            class="mt-auto w-full rounded-full bg-terracotta px-3 py-1.5 text-xs font-medium text-white transition hover:bg-terracotta-dark"
            @click="addToOrderDraft(product)"
          >
            {{ addedFlash[product.id] ? '已加入!' : '加入訂購清單' }}
          </button>
          <div v-else-if="!isSoldOut(product)" class="mt-auto flex items-center gap-2">
            <input
              v-model.number="quantities[product.id]"
              type="number"
              min="1"
              :max="availableStock(product)"
              class="w-14 rounded-lg border border-beige px-2 py-1 text-sm focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
            />
            <button
              type="button"
              class="flex-1 whitespace-nowrap rounded-full bg-terracotta px-3 py-1.5 text-xs font-medium text-white transition hover:bg-terracotta-dark"
              @click="addToCart(product)"
            >
              {{ addedFlash[product.id] ? '已加入!' : '加入購物車' }}
            </button>
          </div>
          <button
            v-else
            type="button"
            disabled
            class="mt-auto rounded-full bg-beige px-3 py-1.5 text-xs font-medium text-taupe"
          >
            已售完
          </button>
        </div>
      </div>
    </div>

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
