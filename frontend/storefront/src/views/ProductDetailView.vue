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

const lightboxVisible = ref(false)
const lightboxIndex = ref(0)

const mainImage = computed(
  () => product.value?.images.find((img) => img.is_primary) ?? product.value?.images[0] ?? null,
)
const otherImages = computed(
  () => product.value?.images.filter((img) => img.id !== mainImage.value?.id) ?? [],
)
const galleryImages = computed(() =>
  mainImage.value ? [mainImage.value, ...otherImages.value] : [],
)

const lightboxSrc = computed(() => {
  const image = galleryImages.value[lightboxIndex.value]
  return image ? imageUrl(image.storage_key) : ''
})
const lightboxAlt = computed(() => product.value?.name ?? '')
const hasPrevImage = computed(() => lightboxIndex.value > 0)
const hasNextImage = computed(() => lightboxIndex.value < galleryImages.value.length - 1)

function openLightbox(storageKey: string) {
  const index = galleryImages.value.findIndex((img) => img.storage_key === storageKey)
  lightboxIndex.value = index >= 0 ? index : 0
  lightboxVisible.value = true
}

function prevImage() {
  if (hasPrevImage.value) lightboxIndex.value -= 1
}

function nextImage() {
  if (hasNextImage.value) lightboxIndex.value += 1
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
    <div v-else-if="product">
      <div class="grid gap-8 sm:grid-cols-2">
      <div class="aspect-square overflow-hidden rounded-2xl bg-cream-dark shadow-[0_2px_10px_rgba(180,140,110,0.12)]">
        <img
          v-if="mainImage"
          :src="imageUrl(mainImage.storage_key)"
          :alt="product.name"
          class="h-full w-full cursor-zoom-in object-cover"
          @click="openLightbox(mainImage.storage_key)"
        />
        <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
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

        <div v-if="product.has_variants" class="mt-4 rounded-xl border border-beige bg-cream/40 p-3">
          <p class="text-sm font-medium text-brown">規格選項</p>
          <ul class="mt-1 space-y-1 text-sm text-brown/80">
            <li v-for="variant in product.variants" :key="variant.id" class="flex justify-between">
              <span>{{ variant.name }}</span>
              <span>NT$ {{ variant.price }}</span>
            </li>
          </ul>
          <p class="mt-1 text-xs text-taupe">實際規格選擇請於前往訂購頁時進行。</p>
        </div>

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

      <div v-if="otherImages.length" class="mt-12">
        <h2 class="mb-4 flex items-center gap-2 text-lg font-bold text-brown">
          <span aria-hidden="true">🎨</span>其他花色參考
        </h2>
        <div class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
          <div
            v-for="image in otherImages"
            :key="image.id"
            class="overflow-hidden rounded-3xl border border-beige bg-white shadow-[0_4px_14px_rgba(180,140,110,0.14)] transition duration-300 hover:-translate-y-1 hover:rotate-1 hover:shadow-[0_10px_24px_rgba(180,140,110,0.24)]"
          >
            <div class="aspect-square bg-cream-dark">
              <img
                :src="imageUrl(image.thumbnail_key ?? image.storage_key)"
                :alt="product.name"
                class="h-full w-full cursor-zoom-in object-cover"
                @click="openLightbox(image.storage_key)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <ImageLightbox
      v-model="lightboxVisible"
      :src="lightboxSrc"
      :alt="lightboxAlt"
      :has-prev="hasPrevImage"
      :has-next="hasNextImage"
      @prev="prevImage"
      @next="nextImage"
    />
  </main>
</template>
