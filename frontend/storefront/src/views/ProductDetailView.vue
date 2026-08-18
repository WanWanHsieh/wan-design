<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import PriceTag from '../components/PriceTag.vue'
import { useOrderDraftStore } from '../stores/orderDraft'
import type { ProductDetail } from '../types'

const route = useRoute()
const orderDraft = useOrderDraftStore()
const product = ref<ProductDetail | null>(null)
const error = ref<string | null>(null)
const addedFlash = ref(false)
const selectedImageIndex = ref(0)

const lightboxVisible = ref(false)
const lightboxSrc = ref('')
const lightboxAlt = ref('')

const sortedImages = computed(() => {
  if (!product.value) return []
  return [...product.value.images].sort((a, b) => Number(b.is_primary) - Number(a.is_primary))
})

const selectedImage = computed(() => sortedImages.value[selectedImageIndex.value] ?? null)

function selectImage(index: number) {
  selectedImageIndex.value = index
}

function openLightbox() {
  if (!selectedImage.value || !product.value) return
  lightboxSrc.value = imageUrl(selectedImage.value.storage_key)
  lightboxAlt.value = product.value.name
  lightboxVisible.value = true
}

function addToOrderDraft() {
  if (!product.value) return
  orderDraft.addItem(product.value.id, 1)
  addedFlash.value = true
  setTimeout(() => {
    addedFlash.value = false
  }, 1200)
}

onMounted(async () => {
  try {
    const { data } = await apiClient.get<ProductDetail>(
      `/api/v1/storefront/products/${route.params.slug}`,
    )
    product.value = data
  } catch {
    error.value = '找不到這個商品。'
  }
})
</script>

<template>
  <main class="mx-auto max-w-4xl px-4 py-10">
    <RouterLink to="/" class="mb-6 inline-flex items-center gap-1 text-sm text-taupe hover:text-terracotta">
      ← 返回商品列表
    </RouterLink>

    <p v-if="error" class="text-red-600">{{ error }}</p>
    <div v-else-if="product" class="grid gap-8 sm:grid-cols-2">
      <div>
        <div class="aspect-square overflow-hidden rounded-2xl bg-cream-dark shadow-[0_2px_10px_rgba(180,140,110,0.12)]">
          <img
            v-if="selectedImage"
            :src="imageUrl(selectedImage.storage_key)"
            :alt="product.name"
            class="h-full w-full cursor-zoom-in object-cover"
            @click="openLightbox"
          />
          <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
        </div>
        <div v-if="sortedImages.length > 1" class="mt-3 grid grid-cols-4 gap-2">
          <button
            v-for="(image, index) in sortedImages"
            :key="image.id"
            type="button"
            class="aspect-square overflow-hidden rounded-lg border-2 transition"
            :class="index === selectedImageIndex ? 'border-terracotta' : 'border-transparent hover:border-beige'"
            @click="selectImage(index)"
          >
            <img
              :src="imageUrl(image.thumbnail_key ?? image.storage_key)"
              :alt="product.name"
              class="h-full w-full object-cover"
            />
          </button>
        </div>
        <p v-if="sortedImages.length > 1" class="mt-2 text-xs text-taupe">
          點選縮圖查看其他花色參考
        </p>
      </div>
      <div>
        <span
          class="inline-block rounded-full px-2 py-0.5 text-xs font-medium"
          :class="product.track_stock ? 'bg-sage/15 text-sage-dark' : 'bg-terracotta-light text-terracotta-dark'"
        >
          {{ product.track_stock ? '現貨' : '訂製商品・需選布料' }}
        </span>
        <h1 class="mt-2 text-2xl font-bold text-brown">{{ product.name }}</h1>
        <p class="mt-2">
          <PriceTag
            :base-price="product.base_price"
            :effective-price="product.effective_price"
            :is-on-sale="product.is_on_sale"
            size="lg"
          />
        </p>
        <p class="mt-4 whitespace-pre-line text-brown/80">{{ product.description }}</p>

        <button
          v-if="!product.track_stock"
          type="button"
          class="mt-6 rounded-full bg-terracotta px-6 py-2 font-medium text-white transition hover:bg-terracotta-dark"
          @click="addToOrderDraft"
        >
          {{ addedFlash ? '已加入!' : '加入訂購清單' }}
        </button>
        <p v-if="!product.track_stock" class="mt-2 text-xs text-taupe">
          此商品為訂製款,加入訂購清單後可繼續選購,最後一起前往訂購頁選布料下單。
        </p>

        <dl
          v-if="Object.keys(product.custom_attributes).length"
          class="mt-6 divide-y divide-beige border-t border-beige text-sm"
        >
          <div
            v-for="(value, key) in product.custom_attributes"
            :key="key"
            class="flex justify-between py-2"
          >
            <dt class="text-taupe">{{ key }}</dt>
            <dd class="text-brown">{{ value }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
