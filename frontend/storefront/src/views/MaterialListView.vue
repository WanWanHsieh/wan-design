<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import type { Material, MaterialImage } from '../types'

const ORIGINS = ['台灣', '韓國', '美國', '日本', '其他']
const FABRIC_TYPES = ['二紗', '棉布', '厚棉']

const materials = ref<Material[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 24
const loading = ref(true)
const error = ref<string | null>(null)
const selectedOrigin = ref<string | null>(null)
const selectedFabricType = ref<string | null>(null)
const codeOrder = ref<'asc' | 'desc' | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const lightboxVisible = ref(false)
const lightboxSrc = ref('')
const lightboxAlt = ref('')

async function loadMaterials() {
  loading.value = true
  try {
    const { data } = await apiClient.get<{ items: Material[]; total: number }>(
      '/api/v1/storefront/materials',
      {
        params: {
          origin: selectedOrigin.value ?? undefined,
          fabric_type: selectedFabricType.value ?? undefined,
          page: page.value,
          page_size: pageSize,
          code_order: codeOrder.value ?? undefined,
        },
      },
    )
    materials.value = data.items
    total.value = data.total
  } catch {
    error.value = '無法載入布料列表,請確認後端服務是否啟動。'
  } finally {
    loading.value = false
  }
}

watch([selectedOrigin, selectedFabricType, codeOrder], () => {
  page.value = 1
  loadMaterials()
})

function toggleCodeOrder() {
  if (codeOrder.value === 'asc') codeOrder.value = 'desc'
  else if (codeOrder.value === 'desc') codeOrder.value = null
  else codeOrder.value = 'asc'
}

function goToPage(newPage: number) {
  if (newPage < 1 || newPage > totalPages.value) return
  page.value = newPage
  loadMaterials()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(loadMaterials)

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

    <div class="mb-6 flex flex-wrap gap-2">
      <button
        type="button"
        class="rounded-full border px-3 py-1 text-sm transition"
        :class="!selectedOrigin ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
        @click="selectedOrigin = null"
      >
        全部產地
      </button>
      <button
        v-for="origin in ORIGINS"
        :key="origin"
        type="button"
        class="rounded-full border px-3 py-1 text-sm transition"
        :class="selectedOrigin === origin ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
        @click="selectedOrigin = origin"
      >
        {{ origin }}
      </button>
    </div>

    <div class="mb-6 flex flex-wrap gap-2">
      <button
        type="button"
        class="rounded-full border px-3 py-1 text-sm transition"
        :class="!selectedFabricType ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
        @click="selectedFabricType = null"
      >
        全部種類
      </button>
      <button
        v-for="fabricType in FABRIC_TYPES"
        :key="fabricType"
        type="button"
        class="rounded-full border px-3 py-1 text-sm transition"
        :class="selectedFabricType === fabricType ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
        @click="selectedFabricType = fabricType"
      >
        {{ fabricType }}
      </button>
    </div>

    <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
      <p v-if="!loading && !error && materials.length" class="text-sm text-taupe">
        💡 點進布料可查看實際作品參考圖(部分布料尚未提供參考圖)
      </p>
      <button
        type="button"
        class="flex-none rounded-full border border-beige px-3 py-1 text-sm text-taupe transition hover:border-terracotta hover:text-terracotta"
        @click="toggleCodeOrder"
      >
        編號排序
        <template v-if="codeOrder === 'asc'">:小到大 ↑</template>
        <template v-else-if="codeOrder === 'desc'">:大到小 ↓</template>
        <template v-else>:預設</template>
      </button>
    </div>

    <p v-if="loading" class="text-taupe">載入中...</p>
    <p v-else-if="error" class="text-red-600">{{ error }}</p>
    <p v-else-if="materials.length === 0" class="text-taupe">這個篩選條件目前沒有布料。</p>

    <template v-else>
      <div class="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4">
        <RouterLink
          v-for="material in materials"
          :key="material.id"
          :to="{ name: 'material-detail', params: { id: material.id } }"
          class="group block overflow-hidden rounded-2xl border border-beige bg-white shadow-[0_2px_10px_rgba(180,140,110,0.12)] transition hover:-translate-y-0.5 hover:shadow-[0_6px_16px_rgba(180,140,110,0.2)]"
        >
          <div class="relative aspect-square bg-cream-dark">
            <img
              v-if="primaryFabricImage(material)"
              :src="imageUrl(primaryFabricImage(material)!.thumbnail_key ?? primaryFabricImage(material)!.storage_key)"
              :alt="material.name"
              class="h-full w-full cursor-zoom-in object-cover"
              @click.stop.prevent="openLightbox(material)"
            />
            <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
            <span
              v-if="material.code"
              class="absolute left-2 top-2 rounded-full bg-white/90 px-2 py-0.5 text-xs font-medium text-brown shadow"
            >
              {{ material.code }}
            </span>
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

      <div v-if="totalPages > 1" class="mt-8 flex items-center justify-center gap-2">
        <button
          type="button"
          class="rounded-full border border-beige px-3 py-1 text-sm text-taupe transition hover:border-terracotta hover:text-terracotta disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="page <= 1"
          @click="goToPage(page - 1)"
        >
          上一頁
        </button>
        <span class="text-sm text-taupe">第 {{ page }} / {{ totalPages }} 頁</span>
        <button
          type="button"
          class="rounded-full border border-beige px-3 py-1 text-sm text-taupe transition hover:border-terracotta hover:text-terracotta disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="page >= totalPages"
          @click="goToPage(page + 1)"
        >
          下一頁
        </button>
      </div>
    </template>

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
