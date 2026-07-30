<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import type { Material, MaterialImage } from '../types'

const materials = ref<Material[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const lightboxVisible = ref(false)
const lightboxSrc = ref('')
const lightboxAlt = ref('')

onMounted(async () => {
  try {
    const { data } = await apiClient.get<Material[]>('/api/v1/storefront/materials')
    materials.value = data
  } catch {
    error.value = '無法載入布料列表,請確認後端服務是否啟動。'
  } finally {
    loading.value = false
  }
})

function primaryFabricImage(material: Material): MaterialImage | null {
  const fabricImages = material.images.filter((img) => img.image_type === 'fabric')
  return fabricImages.find((img) => img.is_primary) ?? fabricImages[0] ?? null
}

function openLightbox(material: Material) {
  const image = primaryFabricImage(material)
  if (!image) return
  lightboxSrc.value = imageUrl(image.storage_key)
  lightboxAlt.value = material.name
  lightboxVisible.value = true
}
</script>

<template>
  <main class="mx-auto max-w-6xl px-4 py-10">
    <h1 class="mb-6 flex items-center gap-2 text-2xl font-bold text-brown">
      <span aria-hidden="true">🧶</span>布料列表
    </h1>

    <p v-if="loading" class="text-taupe">載入中...</p>
    <p v-else-if="error" class="text-red-600">{{ error }}</p>
    <p v-else-if="materials.length === 0" class="text-taupe">目前還沒有可選擇的布料樣式。</p>

    <div v-else class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
      <RouterLink
        v-for="material in materials"
        :key="material.id"
        :to="{ name: 'material-detail', params: { id: material.id } }"
        class="group block overflow-hidden rounded-2xl border border-beige bg-white shadow-[0_2px_10px_rgba(180,140,110,0.12)] transition hover:-translate-y-0.5 hover:shadow-[0_6px_16px_rgba(180,140,110,0.2)]"
      >
        <div class="aspect-square bg-cream-dark">
          <img
            v-if="primaryFabricImage(material)"
            :src="imageUrl(primaryFabricImage(material)!.thumbnail_key ?? primaryFabricImage(material)!.storage_key)"
            :alt="material.name"
            class="h-full w-full cursor-zoom-in object-cover"
            @click.stop.prevent="openLightbox(material)"
          />
          <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
        </div>
        <div class="p-3">
          <p class="truncate text-sm text-brown group-hover:text-terracotta">{{ material.name }}</p>
        </div>
      </RouterLink>
    </div>

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
