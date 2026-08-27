<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import type { Material } from '../types'

const route = useRoute()
const material = ref<Material | null>(null)
const error = ref<string | null>(null)

const lightboxVisible = ref(false)
const lightboxIndex = ref(0)

const fabricImages = computed(
  () => material.value?.images.filter((img) => img.image_type === 'fabric') ?? [],
)
const showcaseImages = computed(
  () => material.value?.images.filter((img) => img.image_type === 'showcase') ?? [],
)
const mainImage = computed(
  () => fabricImages.value.find((img) => img.is_primary) ?? fabricImages.value[0],
)
const galleryImages = computed(() =>
  mainImage.value ? [mainImage.value, ...showcaseImages.value] : [],
)

const lightboxSrc = computed(() => {
  const image = galleryImages.value[lightboxIndex.value]
  return image ? imageUrl(image.storage_key) : ''
})
const lightboxAlt = computed(() => material.value?.name ?? '')
const hasPrevImage = computed(() => lightboxIndex.value > 0)
const hasNextImage = computed(() => lightboxIndex.value < galleryImages.value.length - 1)

onMounted(async () => {
  try {
    const { data } = await apiClient.get<Material>(
      `/api/v1/storefront/materials/${route.params.id}`,
    )
    material.value = data
  } catch {
    error.value = '找不到這個布料。'
  }
})

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
</script>

<template>
  <main class="mx-auto max-w-4xl px-4 py-10">
    <RouterLink
      to="/materials"
      class="mb-6 inline-flex items-center gap-1 text-sm text-taupe hover:text-terracotta"
    >
      ← 返回布料列表
    </RouterLink>

    <p v-if="error" class="text-red-600">{{ error }}</p>
    <div v-else-if="material">
      <div class="grid gap-8 sm:grid-cols-2">
        <div class="aspect-square overflow-hidden rounded-2xl bg-cream-dark shadow-[0_2px_10px_rgba(180,140,110,0.12)]">
          <img
            v-if="mainImage"
            :src="imageUrl(mainImage.storage_key)"
            :alt="material.name"
            class="h-full w-full cursor-zoom-in object-cover"
            @click="openLightbox(mainImage.storage_key)"
          />
          <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
        </div>
        <div>
          <span
            v-if="material.code"
            class="inline-block rounded-full bg-cream-dark px-2 py-0.5 text-xs font-medium text-brown"
          >
            {{ material.code }}
          </span>
          <h1 class="mt-2 text-2xl font-bold text-brown">{{ material.name }}</h1>
          <p v-if="material.origin || material.fabric_type" class="mt-2 text-sm text-taupe">
            <template v-if="material.origin">產地:{{ material.origin }}</template>
            <template v-if="material.origin && material.fabric_type"> ・ </template>
            <template v-if="material.fabric_type">{{ material.fabric_type }}</template>
          </p>
        </div>
      </div>

      <div v-if="showcaseImages.length" class="mt-12">
        <h2 class="mb-4 flex items-center gap-2 text-lg font-bold text-brown">
          <span aria-hidden="true">✂️</span>商品展示
        </h2>
        <div class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
          <div
            v-for="image in showcaseImages"
            :key="image.id"
            class="overflow-hidden rounded-3xl border border-beige bg-white shadow-[0_4px_14px_rgba(180,140,110,0.14)] transition duration-300 hover:-translate-y-1 hover:rotate-1 hover:shadow-[0_10px_24px_rgba(180,140,110,0.24)]"
          >
            <div class="aspect-square bg-cream-dark">
              <img
                :src="imageUrl(image.thumbnail_key ?? image.storage_key)"
                :alt="material.name"
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
