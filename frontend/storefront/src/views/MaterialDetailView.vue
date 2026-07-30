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
const lightboxSrc = ref('')
const lightboxAlt = ref('')

const fabricImages = computed(
  () => material.value?.images.filter((img) => img.image_type === 'fabric') ?? [],
)
const showcaseImages = computed(
  () => material.value?.images.filter((img) => img.image_type === 'showcase') ?? [],
)
const mainImage = computed(
  () => fabricImages.value.find((img) => img.is_primary) ?? fabricImages.value[0],
)

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
  lightboxSrc.value = imageUrl(storageKey)
  lightboxAlt.value = material.value?.name ?? ''
  lightboxVisible.value = true
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
          <h1 class="text-2xl font-bold text-brown">{{ material.name }}</h1>
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
            class="overflow-hidden rounded-2xl border border-beige bg-white shadow-[0_2px_10px_rgba(180,140,110,0.12)]"
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

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
