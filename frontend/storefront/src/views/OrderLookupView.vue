<script setup lang="ts">
import { ref } from 'vue'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import type { OrderResult } from '../types'

const customerName = ref('')
const phone = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const results = ref<OrderResult[]>([])
const searched = ref(false)

const lightboxVisible = ref(false)
const lightboxSrc = ref('')
const lightboxAlt = ref('')

function openLightbox(storageKey: string, alt: string) {
  lightboxSrc.value = imageUrl(storageKey)
  lightboxAlt.value = alt
  lightboxVisible.value = true
}

const STATUS_LABELS: Record<string, string> = {
  pending: '訂單成立',
  shipped: '已出貨',
  completed: '已完成',
  cancelled: '已取消',
}

const STATUS_CLASSES: Record<string, string> = {
  pending: 'bg-beige text-brown',
  shipped: 'bg-terracotta-light text-terracotta-dark',
  completed: 'bg-sage/20 text-sage-dark',
  cancelled: 'bg-red-100 text-red-600',
}

const shippingLabels: Record<string, string> = {
  family_mart: '好賣家(全家)',
  seven_eleven: '賣貨便(7-11)',
  address: '地址配送',
}

async function handleSearch() {
  error.value = null
  results.value = []
  searched.value = true
  loading.value = true
  try {
    const { data } = await apiClient.get<OrderResult[]>('/api/v1/storefront/orders/lookup', {
      params: { customer_name: customerName.value.trim(), phone: phone.value.trim() },
    })
    results.value = data
  } catch {
    error.value = '找不到符合的訂單,請確認姓名與電話是否輸入正確。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="mx-auto max-w-2xl px-4 py-10">
    <h1 class="mb-6 flex items-center gap-2 text-2xl font-bold text-brown">
      <span aria-hidden="true">🔎</span>查詢訂單
    </h1>

    <form
      class="mb-8 grid gap-4 rounded-2xl border border-beige bg-white p-5 shadow-[0_2px_10px_rgba(180,140,110,0.08)] sm:grid-cols-3 sm:items-end"
      @submit.prevent="handleSearch"
    >
      <label class="block text-sm text-brown sm:col-span-1">
        通訊名字
        <input
          v-model="customerName"
          type="text"
          required
          placeholder="下單時填寫的名字"
          class="mt-1 w-full rounded-lg border border-beige px-3 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
        />
      </label>
      <label class="block text-sm text-brown sm:col-span-1">
        聯絡電話
        <input
          v-model="phone"
          type="tel"
          required
          placeholder="下單時填寫的電話"
          class="mt-1 w-full rounded-lg border border-beige px-3 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
        />
      </label>
      <button
        type="submit"
        :disabled="loading"
        class="rounded-full bg-terracotta px-6 py-2 font-medium text-white transition hover:bg-terracotta-dark disabled:opacity-40 sm:col-span-1"
      >
        {{ loading ? '查詢中...' : '查詢' }}
      </button>
    </form>

    <p v-if="error" class="text-red-600">{{ error }}</p>
    <p v-else-if="searched && !loading && results.length === 0" class="text-taupe">
      沒有查到符合的訂單。
    </p>

    <div class="space-y-6">
      <div
        v-for="result in results"
        :key="result.id"
        class="rounded-2xl border border-beige bg-white p-6 shadow-[0_2px_10px_rgba(180,140,110,0.08)]"
      >
        <div class="mb-4 flex items-center justify-between">
          <div>
            <p class="text-sm text-taupe">訂單編號</p>
            <p class="font-bold text-brown">{{ result.order_no }}</p>
          </div>
          <span
            class="rounded-full px-3 py-1 text-sm font-medium"
            :class="STATUS_CLASSES[result.status] ?? 'bg-beige text-brown'"
          >
            {{ STATUS_LABELS[result.status] ?? result.status }}
          </span>
        </div>

        <div class="grid gap-2 text-sm text-brown/80 sm:grid-cols-2">
          <p>收件人:{{ result.customer_name }}</p>
          <p>聯絡電話:{{ result.phone }}</p>
          <p>寄送方式:{{ shippingLabels[result.shipping_method] ?? result.shipping_method }}</p>
          <p v-if="result.shipping_store_code">店號:{{ result.shipping_store_code }}</p>
          <p v-if="result.shipping_address">地址:{{ result.shipping_address }}</p>
          <p>預期收到日期:{{ result.expected_delivery_date }}</p>
        </div>

        <div class="mt-4 space-y-2">
          <div
            v-for="item in result.items"
            :key="item.id"
            class="flex items-center gap-3 rounded-xl bg-cream/60 p-2 text-sm"
          >
            <img
              v-if="item.product_thumbnail"
              :src="imageUrl(item.product_thumbnail)"
              class="h-12 w-12 flex-none cursor-zoom-in rounded-lg border border-beige object-cover"
              @click="openLightbox(item.product_image ?? item.product_thumbnail!, item.product_name_snapshot)"
            />
            <img
              v-if="item.material_thumbnail"
              :src="imageUrl(item.material_thumbnail)"
              class="h-12 w-12 flex-none cursor-zoom-in rounded-lg border border-beige object-cover"
              @click="openLightbox(item.material_image ?? item.material_thumbnail!, item.material_name_snapshot!)"
            />
            <span class="flex-1 text-brown" :class="{ 'text-taupe line-through': item.is_completed }">
              {{ item.product_name_snapshot }}
              <template v-if="item.material_name_snapshot"> × {{ item.material_name_snapshot }}</template>
              × {{ item.quantity }} — NT$ {{ item.subtotal }}
            </span>
            <span v-if="item.is_completed" class="flex-none text-xs text-sage-dark">已完成</span>
          </div>
        </div>

        <p v-if="result.notes" class="mt-4 text-sm text-brown/80">備註:{{ result.notes }}</p>
        <p class="mt-4 text-lg font-bold text-terracotta-dark">總金額:NT$ {{ result.total_amount }}</p>
      </div>
    </div>

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
