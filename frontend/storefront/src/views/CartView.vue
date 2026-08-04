<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient, imageUrl } from '../api/client'
import PriceTag from '../components/PriceTag.vue'
import { useCartStore } from '../stores/cart'
import type { OrderResult, ProductListItem } from '../types'

const cart = useCartStore()
const products = ref<ProductListItem[]>([])
const loading = ref(true)
const loadError = ref<string | null>(null)

const customerName = ref('')
const phone = ref('')
const shippingMethod = ref<'family_mart' | 'seven_eleven' | 'address'>('family_mart')
const shippingStoreCode = ref('')
const shippingAddress = ref('')
const expectedDeliveryDate = ref('')
const notes = ref('')

const submitting = ref(false)
const submitError = ref<string | null>(null)
const result = ref<OrderResult | null>(null)

const todayStr = new Date().toISOString().slice(0, 10)

onMounted(async () => {
  try {
    const { data } = await apiClient.get<ProductListItem[]>('/api/v1/storefront/products', {
      params: { track_stock: true },
    })
    products.value = data
  } catch {
    loadError.value = '無法載入商品資料,請稍後再試。'
  } finally {
    loading.value = false
  }
})

function productOf(productId: number): ProductListItem | undefined {
  return products.value.find((p) => p.id === productId)
}

const cartRows = computed(() =>
  cart.items
    .map((item) => {
      const product = productOf(item.productId)
      return product ? { item, product } : null
    })
    .filter((row): row is { item: { productId: number; quantity: number }; product: ProductListItem } => row !== null),
)

const totalAmount = computed(() =>
  cartRows.value.reduce((sum, row) => sum + row.product.effective_price * row.item.quantity, 0),
)

function updateQuantity(productId: number, quantity: number) {
  cart.setQuantity(productId, quantity)
}

function handleClearCart() {
  if (!confirm('確定要清空購物車嗎?')) return
  cart.clear()
}

const canSubmit = computed(() => {
  if (cartRows.value.length === 0) return false
  if (!customerName.value.trim() || !phone.value.trim() || !expectedDeliveryDate.value) return false
  if (shippingMethod.value === 'address' && !shippingAddress.value.trim()) return false
  if (shippingMethod.value !== 'address' && !shippingStoreCode.value.trim()) return false
  return cartRows.value.every((row) => row.item.quantity > 0 && row.item.quantity <= row.product.stock_quantity)
})

async function handleSubmit() {
  submitError.value = null
  submitting.value = true
  try {
    const { data } = await apiClient.post<OrderResult>('/api/v1/storefront/orders', {
      customer_name: customerName.value,
      phone: phone.value,
      shipping_method: shippingMethod.value,
      shipping_store_code: shippingMethod.value === 'address' ? null : shippingStoreCode.value,
      shipping_address: shippingMethod.value === 'address' ? shippingAddress.value : null,
      expected_delivery_date: expectedDeliveryDate.value,
      notes: notes.value.trim() || null,
      items: cartRows.value.map((row) => ({
        product_id: row.product.id,
        quantity: row.item.quantity,
      })),
    })
    result.value = data
    cart.clear()
  } catch (err: any) {
    submitError.value = err?.response?.data?.detail ?? '訂單送出失敗,請確認資料填寫正確後再試一次。'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="mx-auto max-w-3xl px-4 py-10">
    <h1 class="mb-6 flex items-center gap-2 text-2xl font-bold text-brown">
      <span aria-hidden="true">🛒</span>購物車
    </h1>

    <div
      v-if="result"
      class="rounded-2xl border border-sage/30 bg-sage/10 p-6 shadow-[0_2px_10px_rgba(180,140,110,0.12)]"
    >
      <p class="flex items-center gap-2 text-lg font-bold text-sage-dark">
        <span aria-hidden="true">🎉</span>訂單已送出!
      </p>
      <p class="mt-2 text-sm text-brown/80">訂單編號:{{ result.order_no }}</p>
      <p class="mt-1 text-sm text-brown/80">
        我們會依照您留下的聯絡電話({{ result.phone }})與您聯繫確認訂單與付款方式。
      </p>

      <div class="mt-4 space-y-2">
        <div
          v-for="item in result.items"
          :key="item.id"
          class="flex items-center gap-3 rounded-xl bg-white/70 p-2 text-sm"
        >
          <img
            v-if="item.product_thumbnail"
            :src="imageUrl(item.product_thumbnail)"
            class="h-12 w-12 flex-none rounded-lg border border-beige object-cover"
          />
          <span class="text-brown">
            {{ item.product_name_snapshot }} × {{ item.quantity }} — NT$ {{ item.subtotal }}
          </span>
        </div>
      </div>

      <p v-if="result.notes" class="mt-4 text-sm text-brown/80">備註:{{ result.notes }}</p>
      <p class="mt-4 text-lg font-bold text-terracotta-dark">總金額:NT$ {{ result.total_amount }}</p>

      <RouterLink
        to="/instock"
        class="mt-4 inline-block rounded-full border border-terracotta px-4 py-1.5 text-sm text-terracotta transition hover:bg-terracotta-light"
      >
        繼續選購現貨商品
      </RouterLink>
    </div>

    <div v-else>
      <p v-if="loading" class="text-taupe">載入中...</p>
      <p v-else-if="loadError" class="text-red-600">{{ loadError }}</p>

      <div v-else-if="cartRows.length === 0" class="rounded-2xl border border-beige bg-white p-6 text-center text-taupe shadow-[0_2px_10px_rgba(180,140,110,0.08)]">
        購物車還是空的,
        <RouterLink to="/instock" class="text-terracotta hover:underline">去逛逛現貨商品</RouterLink>
      </div>

      <form v-else class="space-y-8" @submit.prevent="handleSubmit">
        <section class="rounded-2xl border border-beige bg-white p-5 shadow-[0_2px_10px_rgba(180,140,110,0.08)]">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="font-bold text-brown">購物車項目</h2>
            <button
              type="button"
              class="rounded-full border border-taupe/40 px-3 py-1 text-sm text-taupe transition hover:border-red-400 hover:text-red-500"
              @click="handleClearCart"
            >
              清空購物車
            </button>
          </div>
          <div
            v-for="row in cartRows"
            :key="row.product.id"
            class="mb-3 flex flex-col gap-3 rounded-xl border border-beige bg-cream/60 p-3 sm:flex-row sm:items-center"
          >
            <div class="flex items-center gap-3">
              <img
                v-if="row.product.primary_thumbnail ?? row.product.primary_image"
                :src="imageUrl(row.product.primary_thumbnail ?? row.product.primary_image!)"
                class="h-14 w-14 flex-none rounded-lg border border-beige object-cover"
              />
              <div class="flex-1 sm:w-40 sm:flex-none">
                <p class="text-sm font-medium text-brown">{{ row.product.name }}</p>
                <p class="text-xs text-taupe">
                  <PriceTag
                    :base-price="row.product.base_price"
                    :effective-price="row.product.effective_price"
                    :is-on-sale="row.product.is_on_sale"
                  />
                  / 件・庫存 {{ row.product.stock_quantity }}
                </p>
                <p v-if="row.item.quantity > row.product.stock_quantity" class="text-xs text-red-500">
                  數量超過現有庫存,請調整
                </p>
              </div>
            </div>
            <div class="flex items-center justify-between gap-3 sm:flex-1 sm:justify-end">
              <input
                :value="row.item.quantity"
                type="number"
                min="1"
                :max="row.product.stock_quantity"
                class="w-16 rounded-lg border border-beige px-2 py-1 text-sm focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
                @change="updateQuantity(row.product.id, Number(($event.target as HTMLInputElement).value))"
              />
              <span class="text-right text-sm text-brown">NT$ {{ row.product.effective_price * row.item.quantity }}</span>
              <button type="button" class="text-red-500 hover:underline" @click="cart.removeItem(row.product.id)">
                移除
              </button>
            </div>
          </div>
        </section>

        <section class="rounded-2xl border border-beige bg-white p-5 shadow-[0_2px_10px_rgba(180,140,110,0.08)]">
          <h2 class="mb-3 font-bold text-brown">聯絡資訊</h2>
          <div class="grid gap-4 sm:grid-cols-2">
            <label class="block text-sm text-brown">
              通訊名字
              <input
                v-model="customerName"
                type="text"
                required
                class="mt-1 w-full rounded-lg border border-beige px-3 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
              />
            </label>
            <label class="block text-sm text-brown">
              聯絡電話
              <input
                v-model="phone"
                type="tel"
                required
                class="mt-1 w-full rounded-lg border border-beige px-3 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
              />
            </label>
          </div>
        </section>

        <section class="rounded-2xl border border-beige bg-white p-5 shadow-[0_2px_10px_rgba(180,140,110,0.08)]">
          <h2 class="mb-3 font-bold text-brown">寄送方式</h2>
          <div class="flex flex-wrap gap-4 text-sm text-brown">
            <label class="flex items-center gap-1">
              <input v-model="shippingMethod" type="radio" value="family_mart" class="accent-terracotta" />
              好賣家(全家)
            </label>
            <label class="flex items-center gap-1">
              <input v-model="shippingMethod" type="radio" value="seven_eleven" class="accent-terracotta" />
              賣貨便(7-11)
            </label>
            <label class="flex items-center gap-1">
              <input v-model="shippingMethod" type="radio" value="address" class="accent-terracotta" />
              地址配送
            </label>
          </div>
          <label v-if="shippingMethod !== 'address'" class="mt-3 block text-sm text-brown">
            店號
            <input
              v-model="shippingStoreCode"
              type="text"
              required
              placeholder="請輸入門市店號"
              class="mt-1 w-full rounded-lg border border-beige px-3 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
            />
          </label>
          <label v-else class="mt-3 block text-sm text-brown">
            寄送地址
            <input
              v-model="shippingAddress"
              type="text"
              required
              placeholder="請輸入完整收件地址"
              class="mt-1 w-full rounded-lg border border-beige px-3 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
            />
          </label>
        </section>

        <section class="rounded-2xl border border-beige bg-white p-5 shadow-[0_2px_10px_rgba(180,140,110,0.08)]">
          <h2 class="mb-3 font-bold text-brown">預期收到日期</h2>
          <input
            v-model="expectedDeliveryDate"
            type="date"
            required
            :min="todayStr"
            class="rounded-lg border border-beige px-3 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
          />
        </section>

        <section class="rounded-2xl border border-beige bg-white p-5 shadow-[0_2px_10px_rgba(180,140,110,0.08)]">
          <h2 class="mb-3 font-bold text-brown">備註(選填)</h2>
          <textarea
            v-model="notes"
            rows="3"
            placeholder="有其他需求嗎?例如指定包裝方式等"
            class="w-full rounded-lg border border-beige px-3 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
          />
        </section>

        <div class="flex items-center justify-between border-t border-beige pt-4">
          <span class="text-lg font-bold text-brown">總價:NT$ {{ totalAmount }}</span>
          <button
            type="submit"
            :disabled="!canSubmit || submitting"
            class="rounded-full bg-terracotta px-6 py-2 font-medium text-white transition hover:bg-terracotta-dark disabled:opacity-40"
          >
            {{ submitting ? '送出中...' : '送出訂單' }}
          </button>
        </div>
        <p v-if="submitError" class="text-right text-sm text-red-600">{{ submitError }}</p>
      </form>
    </div>
  </main>
</template>
