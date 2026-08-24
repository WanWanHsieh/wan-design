<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient, imageUrl } from '../api/client'
import ImageLightbox from '../components/ImageLightbox.vue'
import { useOrderDraftStore } from '../stores/orderDraft'
import type { Category, Material, OrderResult, ProductListItem } from '../types'

interface LineItem {
  topCategoryId: number | null
  productId: number | null
  variantId: number | null
  materialId: number | null
  quantity: number
}

const UNCATEGORIZED_TOP_ID = -1

const orderDraft = useOrderDraftStore()
const products = ref<ProductListItem[]>([])
const materials = ref<Material[]>([])
const categories = ref<Category[]>([])
const loading = ref(true)
const loadError = ref<string | null>(null)

const customerName = ref('')
const phone = ref('')
const shippingMethod = ref<'family_mart' | 'seven_eleven' | 'address'>('family_mart')
const shippingStoreCode = ref('')
const shippingAddress = ref('')
const expectedDeliveryDate = ref('')
const notes = ref('')

const lineItems = ref<LineItem[]>([
  { topCategoryId: null, productId: null, variantId: null, materialId: null, quantity: 1 },
])

const submitting = ref(false)
const submitError = ref<string | null>(null)
const result = ref<OrderResult | null>(null)

const todayStr = new Date().toISOString().slice(0, 10)

const lightboxVisible = ref(false)
const lightboxSrc = ref('')
const lightboxAlt = ref('')

function openLightbox(storageKey: string, alt: string) {
  lightboxSrc.value = imageUrl(storageKey)
  lightboxAlt.value = alt
  lightboxVisible.value = true
}

onMounted(async () => {
  try {
    const [productsRes, materialsRes, categoriesRes] = await Promise.all([
      apiClient.get<ProductListItem[]>('/api/v1/storefront/products'),
      apiClient.get<{ items: Material[] }>('/api/v1/storefront/materials', { params: { page_size: 1000 } }),
      apiClient.get<Category[]>('/api/v1/storefront/categories'),
    ])
    products.value = productsRes.data
    materials.value = materialsRes.data.items
    categories.value = categoriesRes.data

    if (orderDraft.items.length > 0) {
      const draftLineItems = orderDraft.items
        .map((draftItem): LineItem | null => {
          const draftProduct = products.value.find((p) => p.id === draftItem.productId)
          if (!draftProduct) return null
          return {
            topCategoryId: topCategoryIdForCategory(draftProduct.category_id),
            productId: draftProduct.id,
            variantId: null,
            materialId: null,
            quantity: draftItem.quantity,
          }
        })
        .filter((item): item is LineItem => item !== null)
      if (draftLineItems.length > 0) {
        lineItems.value = draftLineItems
      }
    }
  } catch {
    loadError.value = '無法載入商品/布料資料,請稍後再試。'
  } finally {
    loading.value = false
  }
})

function topCategoryIdForCategory(categoryId: number | null): number {
  if (categoryId === null) return UNCATEGORIZED_TOP_ID
  const category = categories.value.find((c) => c.id === categoryId)
  if (!category) return UNCATEGORIZED_TOP_ID
  return category.parent_id === null ? category.id : category.parent_id
}

function categoryIdsUnderTop(topId: number): number[] {
  const childIds = categories.value.filter((c) => c.parent_id === topId).map((c) => c.id)
  return [topId, ...childIds]
}

const topCategories = computed(() => {
  const tops = categories.value
    .filter((c) => c.parent_id === null)
    .filter((c) => {
      const scope = categoryIdsUnderTop(c.id)
      return products.value.some((p) => p.category_id !== null && scope.includes(p.category_id))
    })
  const hasUncategorized = products.value.some((p) => p.category_id === null)
  return hasUncategorized ? [...tops, { id: UNCATEGORIZED_TOP_ID, name: '未分類' } as Category] : tops
})

function productsForTopCategory(topId: number | null): ProductListItem[] {
  if (topId === null) return []
  if (topId === UNCATEGORIZED_TOP_ID) return products.value.filter((p) => p.category_id === null)
  const scope = categoryIdsUnderTop(topId)
  return products.value.filter((p) => p.category_id !== null && scope.includes(p.category_id))
}

function handleTopCategoryChange(item: LineItem) {
  item.productId = null
  item.variantId = null
}

function handleProductChange(item: LineItem) {
  item.variantId = null
}

function variantsForProduct(productId: number | null) {
  return products.value.find((p) => p.id === productId)?.variants ?? []
}

function addLineItem() {
  lineItems.value.push({ topCategoryId: null, productId: null, variantId: null, materialId: null, quantity: 1 })
}

function removeLineItem(index: number) {
  lineItems.value.splice(index, 1)
}

function clearLineItems() {
  if (!confirm('確定要清空目前的訂購項目嗎?')) return
  orderDraft.clear()
  lineItems.value = [{ topCategoryId: null, productId: null, variantId: null, materialId: null, quantity: 1 }]
}

function itemUnitPrice(item: LineItem): number {
  const product = products.value.find((p) => p.id === item.productId)
  const material = materials.value.find((m) => m.id === item.materialId)
  if (!product || !material) return 0
  if (product.has_variants) {
    const variant = product.variants.find((v) => v.id === item.variantId)
    if (!variant) return 0
    return variant.price + material.price_addon
  }
  return product.effective_price + material.price_addon
}

function itemSubtotal(item: LineItem): number {
  return itemUnitPrice(item) * (item.quantity || 0)
}

function primaryFabricImage(materialId: number | null) {
  const material = materials.value.find((m) => m.id === materialId)
  if (!material) return null
  const fabricImages = material.images.filter((img) => img.image_type === 'fabric')
  return fabricImages.find((img) => img.is_primary) ?? fabricImages[0] ?? null
}

function materialThumbnail(materialId: number | null): string | null {
  const primary = primaryFabricImage(materialId)
  if (!primary) return null
  return primary.thumbnail_key ?? primary.storage_key
}

function materialFullImage(materialId: number | null): string | null {
  const primary = primaryFabricImage(materialId)
  return primary ? primary.storage_key : null
}

function productThumbnail(productId: number | null): string | null {
  const product = products.value.find((p) => p.id === productId)
  if (!product) return null
  return product.primary_thumbnail ?? product.primary_image
}

function productFullImage(productId: number | null): string | null {
  const product = products.value.find((p) => p.id === productId)
  return product ? product.primary_image : null
}

const totalAmount = computed(() =>
  lineItems.value.reduce((sum, item) => sum + itemSubtotal(item), 0),
)

const canSubmit = computed(() => {
  if (!customerName.value.trim() || !phone.value.trim() || !expectedDeliveryDate.value) return false
  if (shippingMethod.value === 'address' && !shippingAddress.value.trim()) return false
  if (shippingMethod.value !== 'address' && !shippingStoreCode.value.trim()) return false
  if (lineItems.value.length === 0) return false
  return lineItems.value.every((item) => {
    if (!item.productId || !item.materialId || item.quantity <= 0) return false
    if (variantsForProduct(item.productId).length > 0 && !item.variantId) return false
    return true
  })
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
      items: lineItems.value.map((item) => ({
        product_id: item.productId,
        variant_id: item.variantId,
        material_id: item.materialId,
        quantity: item.quantity,
      })),
    })
    result.value = data
    orderDraft.clear()
  } catch {
    submitError.value = '訂單送出失敗,請確認資料填寫正確後再試一次。'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="mx-auto max-w-3xl px-4 py-10">
    <h1 class="mb-6 flex items-center gap-2 text-2xl font-bold text-brown">
      <span aria-hidden="true">🪡</span>訂購單
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

      <div class="mt-4 rounded-xl border border-terracotta/30 bg-white/70 p-3 text-sm text-brown">
        <p class="font-medium">📱 訂購完成後,請加入官方 LINE 與小編確認訂單</p>
        <a
          href="https://line.me/R/ti/p/@894onjvt?from=page&searchId=894onjvt"
          target="_blank"
          rel="noopener noreferrer"
          class="mt-2 inline-block rounded-full bg-[#06C755] px-4 py-1.5 text-sm font-medium text-white transition hover:opacity-90"
        >
          加入 LINE 好友(ID:@894onjvt)
        </a>
      </div>

      <div class="mt-4 space-y-2">
        <div
          v-for="item in result.items"
          :key="item.id"
          class="flex items-center gap-3 rounded-xl bg-white/70 p-2 text-sm"
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
            @click="openLightbox(item.material_image ?? item.material_thumbnail!, item.material_name_snapshot ?? '')"
          />
          <span class="text-brown">
            {{ item.product_name_snapshot }}<template v-if="item.variant_name_snapshot"> - {{ item.variant_name_snapshot }}</template>
            × {{ item.material_name_snapshot }} × {{ item.quantity }}
            — NT$ {{ item.subtotal }}
          </span>
        </div>
      </div>

      <p v-if="result.notes" class="mt-4 text-sm text-brown/80">備註:{{ result.notes }}</p>
      <p class="mt-4 text-lg font-bold text-terracotta-dark">總金額:NT$ {{ result.total_amount }}</p>
    </div>

    <div v-else>
      <p v-if="loading" class="text-taupe">載入中...</p>
      <p v-else-if="loadError" class="text-red-600">{{ loadError }}</p>

      <form v-else class="space-y-8" @submit.prevent="handleSubmit">
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
            placeholder="有其他需求嗎?例如指定包裝方式、尺寸調整等"
            class="w-full rounded-lg border border-beige px-3 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
          />
        </section>

        <section class="rounded-2xl border border-beige bg-white p-5 shadow-[0_2px_10px_rgba(180,140,110,0.08)]">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="font-bold text-brown">訂購項目</h2>
            <div class="flex gap-2">
              <button
                type="button"
                class="rounded-full border border-taupe/40 px-3 py-1 text-sm text-taupe transition hover:border-red-400 hover:text-red-500"
                @click="clearLineItems"
              >
                清空清單
              </button>
              <button
                type="button"
                class="rounded-full border border-terracotta px-3 py-1 text-sm text-terracotta transition hover:bg-terracotta-light"
                @click="addLineItem"
              >
                + 新增項目
              </button>
            </div>
          </div>

          <div
            v-for="(item, index) in lineItems"
            :key="index"
            class="mb-3 flex flex-wrap items-end gap-3 rounded-xl border border-beige bg-cream/60 p-4"
          >
            <label class="block w-full text-sm text-brown sm:w-36">
              商品分類
              <select
                v-model="item.topCategoryId"
                required
                class="mt-1 w-full rounded-lg border border-beige bg-white px-2 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
                @change="handleTopCategoryChange(item)"
              >
                <option :value="null" disabled>請選擇</option>
                <option v-for="c in topCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </label>
            <label class="block w-full text-sm text-brown sm:w-56">
              選擇商品
              <div class="mt-1 flex items-center gap-2">
                <img
                  v-if="productThumbnail(item.productId)"
                  :src="imageUrl(productThumbnail(item.productId)!)"
                  class="h-10 w-10 flex-none cursor-zoom-in rounded-lg border border-beige object-cover"
                  @click.stop.prevent="openLightbox(productFullImage(item.productId)!, '商品預覽')"
                />
                <select
                  v-model="item.productId"
                  required
                  :disabled="!item.topCategoryId"
                  class="w-full rounded-lg border border-beige bg-white px-2 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta disabled:bg-beige/40"
                  @change="handleProductChange(item)"
                >
                  <option :value="null" disabled>{{ item.topCategoryId ? '請選擇' : '請先選分類' }}</option>
                  <option v-for="p in productsForTopCategory(item.topCategoryId)" :key="p.id" :value="p.id">
                    {{ p.name }}(NT$ {{ p.effective_price }}{{ p.has_variants ? ' 起' : '' }}{{ p.is_on_sale ? ' 特價中' : '' }})
                  </option>
                </select>
              </div>
            </label>
            <label
              v-if="variantsForProduct(item.productId).length > 0"
              class="block w-full text-sm text-brown sm:w-40"
            >
              選擇規格
              <select
                v-model="item.variantId"
                required
                class="mt-1 w-full rounded-lg border border-beige bg-white px-2 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
              >
                <option :value="null" disabled>請選擇</option>
                <option v-for="v in variantsForProduct(item.productId)" :key="v.id" :value="v.id">
                  {{ v.name }}(NT$ {{ v.price }})
                </option>
              </select>
            </label>
            <label class="block w-full text-sm text-brown sm:min-w-[220px] sm:flex-1">
              選擇布料
              <div class="mt-1 flex items-center gap-2">
                <img
                  v-if="materialThumbnail(item.materialId)"
                  :src="imageUrl(materialThumbnail(item.materialId)!)"
                  class="h-10 w-10 flex-none cursor-zoom-in rounded-lg border border-beige object-cover"
                  @click.stop.prevent="openLightbox(materialFullImage(item.materialId)!, '布料預覽')"
                />
                <select
                  v-model="item.materialId"
                  required
                  class="w-full rounded-lg border border-beige bg-white px-2 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
                >
                  <option :value="null" disabled>請選擇</option>
                  <option v-for="m in materials" :key="m.id" :value="m.id">
                    {{ m.name }}<template v-if="m.price_addon"> (+NT$ {{ m.price_addon }})</template>
                  </option>
                </select>
              </div>
            </label>
            <label class="block w-full text-sm text-brown sm:w-24">
              數量
              <input
                v-model.number="item.quantity"
                type="number"
                min="1"
                required
                class="mt-1 w-full rounded-lg border border-beige bg-white px-2 py-2 focus:border-terracotta focus:outline-none focus:ring-1 focus:ring-terracotta"
              />
            </label>
            <div class="flex w-full items-center justify-between text-sm">
              <span class="text-taupe">小計:NT$ {{ itemSubtotal(item) }}</span>
              <button
                v-if="lineItems.length > 1"
                type="button"
                class="text-red-500 hover:underline"
                @click="removeLineItem(index)"
              >
                移除
              </button>
            </div>
          </div>
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

    <ImageLightbox v-model="lightboxVisible" :src="lightboxSrc" :alt="lightboxAlt" />
  </main>
</template>
