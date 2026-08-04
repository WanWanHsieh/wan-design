<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import { useOrderDraftStore } from '../stores/orderDraft'
import type { ProductListItem } from '../types'

const products = ref<ProductListItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const lightboxVisible = ref(false)
const lightboxSrc = ref('')
const lightboxAlt = ref('')

const orderDraft = useOrderDraftStore()
const addedFlash = reactive<Record<number, boolean>>({})

function openLightbox(product: ProductListItem) {
  const image = product.primary_image ?? product.primary_thumbnail
  if (!image) return
  lightboxSrc.value = imageUrl(image)
  lightboxAlt.value = product.name
  lightboxVisible.value = true
}

function addToOrderDraft(product: ProductListItem) {
  orderDraft.addItem(product.id, 1)
  addedFlash[product.id] = true
  setTimeout(() => {
    addedFlash[product.id] = false
  }, 1200)
}

onMounted(async () => {
  try {
    const { data } = await apiClient.get<ProductListItem[]>('/api/v1/storefront/products')
    products.value = data.filter((p) => p.is_featured)
  } catch {
    error.value = '無法載入主打商品,請確認後端服務是否啟動。'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="mx-auto max-w-6xl px-4 py-10">
    <div class="mb-8 rounded-2xl bg-terracotta-light px-6 py-8 text-center">
      <h1 class="flex items-center justify-center gap-2 text-2xl font-bold text-terracotta-dark">
        <span aria-hidden="true">💛</span>本週主打商品
      </h1>
      <p class="mt-2 text-sm text-brown/80">精選手作,每件都可以挑選自己喜歡的布料花色訂製。</p>
    </div>

    <p v-if="loading" class="text-taupe">載入中...</p>
    <p v-else-if="error" class="text-red-600">{{ error }}</p>
    <p v-else-if="products.length === 0" class="text-taupe">目前還沒有主打商品,敬請期待!</p>

    <div v-else class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
      <div
        v-for="product in products"
        :key="product.id"
        class="group overflow-hidden rounded-2xl border border-beige bg-white shadow-[0_2px_10px_rgba(180,140,110,0.12)]"
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
        <div class="p-3">
          <RouterLink :to="{ name: 'product-detail', params: { slug: product.slug } }">
            <p class="truncate text-sm text-brown group-hover:text-terracotta">{{ product.name }}</p>
          </RouterLink>
          <p class="mt-1 font-semibold text-terracotta-dark">NT$ {{ product.base_price }}</p>
          <p class="mt-0.5 text-xs text-taupe">{{ product.track_stock ? '現貨' : '訂製・需選布料' }}</p>
          <button
            v-if="!product.track_stock"
            type="button"
            class="mt-2 w-full rounded-full bg-terracotta px-3 py-1.5 text-xs font-medium text-white transition hover:bg-terracotta-dark"
            @click="addToOrderDraft(product)"
          >
            {{ addedFlash[product.id] ? '已加入!' : '加入訂購清單' }}
          </button>
        </div>
      </div>
    </div>

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
