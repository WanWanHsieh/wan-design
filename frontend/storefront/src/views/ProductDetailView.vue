<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient, imageUrl } from '../api/client'
import type { ProductDetail } from '../types'

const route = useRoute()
const product = ref<ProductDetail | null>(null)
const error = ref<string | null>(null)

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
      <div class="aspect-square overflow-hidden rounded-2xl bg-cream-dark shadow-[0_2px_10px_rgba(180,140,110,0.12)]">
        <img
          v-if="product.images[0]"
          :src="imageUrl(product.images[0].storage_key)"
          :alt="product.name"
          class="h-full w-full object-cover"
        />
        <div v-else class="flex h-full items-center justify-center text-taupe">無圖片</div>
      </div>
      <div>
        <h1 class="text-2xl font-bold text-brown">{{ product.name }}</h1>
        <p class="mt-2 text-xl font-bold text-terracotta-dark">NT$ {{ product.base_price }}</p>
        <p class="mt-4 whitespace-pre-line text-brown/80">{{ product.description }}</p>

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
  </main>
</template>
