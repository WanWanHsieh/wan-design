<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import type { Material, MaterialImage } from '../types'

const materials = ref<Material[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const selectedOrigin = ref<string | null>(null)
const selectedFabricType = ref<string | null>(null)

const origins = computed(() => {
  const set = new Set(materials.value.map((m) => m.origin).filter((o): o is string => !!o))
  return Array.from(set).sort()
})

const fabricTypes = computed(() => {
  const set = new Set(materials.value.map((m) => m.fabric_type).filter((t): t is string => !!t))
  return Array.from(set).sort()
})

const filteredMaterials = computed(() =>
  materials.value.filter(
    (m) =>
      (!selectedOrigin.value || m.origin === selectedOrigin.value) &&
      (!selectedFabricType.value || m.fabric_type === selectedFabricType.value),
  ),
)

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

    <template v-else>
      <div v-if="origins.length > 0" class="mb-6 flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-full border px-3 py-1 text-sm transition"
          :class="!selectedOrigin ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
          @click="selectedOrigin = null"
        >
          全部
        </button>
        <button
          v-for="origin in origins"
          :key="origin"
          type="button"
          class="rounded-full border px-3 py-1 text-sm transition"
          :class="selectedOrigin === origin ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
          @click="selectedOrigin = origin"
        >
          {{ origin }}
        </button>
      </div>

      <div v-if="fabricTypes.length > 0" class="mb-6 flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-full border px-3 py-1 text-sm transition"
          :class="!selectedFabricType ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
          @click="selectedFabricType = null"
        >
          全部種類
        </button>
        <button
          v-for="fabricType in fabricTypes"
          :key="fabricType"
          type="button"
          class="rounded-full border px-3 py-1 text-sm transition"
          :class="selectedFabricType === fabricType ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
          @click="selectedFabricType = fabricType"
        >
          {{ fabricType }}
        </button>
      </div>

      <p v-if="filteredMaterials.length === 0" class="text-taupe">這個篩選條件目前沒有布料。</p>
      <div v-else class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
        <RouterLink
          v-for="material in filteredMaterials"
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
            <p v-if="material.origin || material.fabric_type" class="mt-0.5 text-xs text-taupe">
              <template v-if="material.origin">產地:{{ material.origin }}</template>
              <template v-if="material.origin && material.fabric_type"> ・ </template>
              <template v-if="material.fabric_type">{{ material.fabric_type }}</template>
            </p>
          </div>
        </RouterLink>
      </div>
    </template>

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
