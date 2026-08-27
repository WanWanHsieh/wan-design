<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { imageUrl } from '../api/client'
import ImageLightbox from './ImageLightbox.vue'
import type { Material, MaterialImage } from '../types'

const ORIGINS = ['台灣', '韓國', '美國', '日本', '其他']
const FABRIC_TYPES = ['二紗', '棉布', '厚棉']
const PAGE_SIZE = 24

const props = defineProps<{
  modelValue: boolean
  materials: Material[]
  selectedId: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  select: [materialId: number]
}>()

const search = ref('')
const selectedOrigin = ref<string | null>(null)
const selectedFabricType = ref<string | null>(null)
const codeOrder = ref<'asc' | 'desc' | null>(null)
const page = ref(1)

const lightboxVisible = ref(false)
const lightboxSrc = ref('')
const lightboxAlt = ref('')

function primaryFabricImage(material: Material): MaterialImage | null {
  const fabricImages = material.images.filter((img) => img.image_type === 'fabric')
  return fabricImages.find((img) => img.is_primary) ?? fabricImages[0] ?? null
}

function hasShowcaseImage(material: Material): boolean {
  return material.images.some((img) => img.image_type === 'showcase')
}

function openLightbox(material: Material) {
  const image = primaryFabricImage(material)
  if (!image) return
  lightboxSrc.value = imageUrl(image.storage_key)
  lightboxAlt.value = material.name
  lightboxVisible.value = true
}

const filtered = computed(() => {
  let list = props.materials
  if (selectedOrigin.value) list = list.filter((m) => m.origin === selectedOrigin.value)
  if (selectedFabricType.value) list = list.filter((m) => m.fabric_type === selectedFabricType.value)
  const keyword = search.value.trim().toLowerCase()
  if (keyword) {
    list = list.filter(
      (m) => m.name.toLowerCase().includes(keyword) || (m.code ?? '').toLowerCase().includes(keyword),
    )
  }
  return list
})

const sorted = computed(() => {
  if (!codeOrder.value) return filtered.value
  const list = [...filtered.value]
  list.sort((a, b) => {
    const codeA = a.code ?? ''
    const codeB = b.code ?? ''
    return codeOrder.value === 'asc' ? codeA.localeCompare(codeB) : codeB.localeCompare(codeA)
  })
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(sorted.value.length / PAGE_SIZE)))

const paged = computed(() => sorted.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))

watch([search, selectedOrigin, selectedFabricType, codeOrder], () => {
  page.value = 1
})

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) page.value = 1
  },
)

function toggleCodeOrder() {
  if (codeOrder.value === 'asc') codeOrder.value = 'desc'
  else if (codeOrder.value === 'desc') codeOrder.value = null
  else codeOrder.value = 'asc'
}

function goToPage(newPage: number) {
  if (newPage < 1 || newPage > totalPages.value) return
  page.value = newPage
}

function pickMaterial(material: Material) {
  emit('select', material.id)
  emit('update:modelValue', false)
}

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      @click.self="close"
    >
      <div class="flex max-h-[90vh] w-full max-w-4xl flex-col rounded-2xl bg-cream shadow-xl">
        <div class="flex items-center justify-between border-b border-beige px-5 py-4">
          <h2 class="text-lg font-bold text-brown">選擇布料</h2>
          <button type="button" class="text-2xl leading-none text-taupe hover:text-terracotta" @click="close">
            ×
          </button>
        </div>

        <div class="space-y-3 border-b border-beige px-5 py-3">
          <input
            v-model="search"
            type="text"
            placeholder="搜尋編號或名稱,例如:262 或 小花"
            class="w-full rounded-lg border border-beige px-3 py-2 text-sm focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
          />
          <div class="flex flex-wrap gap-2">
            <button
              type="button"
              class="rounded-full border px-3 py-1 text-xs transition"
              :class="!selectedOrigin ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
              @click="selectedOrigin = null"
            >
              全部產地
            </button>
            <button
              v-for="origin in ORIGINS"
              :key="origin"
              type="button"
              class="rounded-full border px-3 py-1 text-xs transition"
              :class="selectedOrigin === origin ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
              @click="selectedOrigin = origin"
            >
              {{ origin }}
            </button>
          </div>
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-full border px-3 py-1 text-xs transition"
                :class="!selectedFabricType ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
                @click="selectedFabricType = null"
              >
                全部種類
              </button>
              <button
                v-for="fabricType in FABRIC_TYPES"
                :key="fabricType"
                type="button"
                class="rounded-full border px-3 py-1 text-xs transition"
                :class="selectedFabricType === fabricType ? 'border-terracotta bg-terracotta text-white' : 'border-beige text-taupe hover:border-terracotta hover:text-terracotta'"
                @click="selectedFabricType = fabricType"
              >
                {{ fabricType }}
              </button>
            </div>
            <button
              type="button"
              class="flex-none rounded-full border border-beige px-3 py-1 text-xs text-taupe transition hover:border-terracotta hover:text-terracotta"
              @click="toggleCodeOrder"
            >
              編號排序
              <template v-if="codeOrder === 'asc'">:小到大 ↑</template>
              <template v-else-if="codeOrder === 'desc'">:大到小 ↓</template>
              <template v-else>:預設</template>
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto px-5 py-4">
          <p v-if="sorted.length === 0" class="text-sm text-taupe">這個篩選條件目前沒有布料。</p>
          <div v-else class="grid grid-cols-3 gap-4 sm:grid-cols-4 md:grid-cols-5">
            <button
              v-for="material in paged"
              :key="material.id"
              type="button"
              class="group block overflow-hidden rounded-2xl border-2 bg-white text-left shadow-[0_2px_8px_rgba(180,140,110,0.12)] transition hover:-translate-y-0.5 hover:shadow-[0_6px_16px_rgba(180,140,110,0.2)]"
              :class="material.id === selectedId ? 'border-terracotta' : 'border-beige'"
              @click="pickMaterial(material)"
            >
              <div class="relative aspect-square bg-cream-dark">
                <img
                  v-if="primaryFabricImage(material)"
                  :src="imageUrl(primaryFabricImage(material)!.thumbnail_key ?? primaryFabricImage(material)!.storage_key)"
                  :alt="material.name"
                  loading="lazy"
                  class="h-full w-full object-cover"
                />
                <div v-else class="flex h-full items-center justify-center text-xs text-taupe">無圖片</div>
                <span
                  v-if="material.code"
                  class="absolute left-1 top-1 rounded-full bg-white/90 px-1.5 py-0.5 text-[10px] font-medium text-brown shadow"
                >
                  {{ material.code }}
                </span>
                <span
                  v-if="hasShowcaseImage(material)"
                  class="absolute right-1 top-1 rounded-full bg-sage/90 px-1.5 py-0.5 text-[10px] font-medium text-white shadow"
                >
                  參考圖
                </span>
                <button
                  type="button"
                  class="absolute bottom-1 right-1 flex h-6 w-6 items-center justify-center rounded-full bg-black/50 text-xs text-white opacity-0 transition group-hover:opacity-100"
                  aria-label="放大預覽"
                  @click.stop="openLightbox(material)"
                >
                  🔍
                </button>
              </div>
              <div class="p-2">
                <p class="truncate text-xs text-brown">{{ material.name }}</p>
                <p v-if="material.price_addon" class="text-[10px] text-terracotta-dark">
                  +NT$ {{ material.price_addon }}
                </p>
              </div>
            </button>
          </div>
        </div>

        <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 border-t border-beige px-5 py-3">
          <button
            type="button"
            class="rounded-full border border-beige px-3 py-1 text-xs text-taupe transition hover:border-terracotta hover:text-terracotta disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="page <= 1"
            @click="goToPage(page - 1)"
          >
            上一頁
          </button>
          <span class="text-xs text-taupe">第 {{ page }} / {{ totalPages }} 頁</span>
          <button
            type="button"
            class="rounded-full border border-beige px-3 py-1 text-xs text-taupe transition hover:border-terracotta hover:text-terracotta disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="page >= totalPages"
            @click="goToPage(page + 1)"
          >
            下一頁
          </button>
        </div>
      </div>
    </div>

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </Teleport>
</template>
