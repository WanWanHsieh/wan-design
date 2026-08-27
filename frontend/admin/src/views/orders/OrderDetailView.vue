<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient, imageUrl } from '../../api/client'
import type { Material, Order, Product } from '../../types'

interface LineItem {
  productId: number | null
  variantId: number | null
  materialId: number | null
  quantity: number
  customNote: string | null
  extraCharge: number
}

const route = useRoute()
const router = useRouter()
const orderId = computed(() => route.params.id as string)

const order = ref<Order | null>(null)
const products = ref<Product[]>([])
const materials = ref<Material[]>([])
const loading = ref(true)
const saving = ref(false)

const realName = ref('')
const contactSource = ref<'ig' | 'line' | 'fb' | ''>('')
const customerName = ref('')
const phone = ref('')
const shippingMethod = ref<'family_mart' | 'seven_eleven' | 'address'>('family_mart')
const shippingStoreCode = ref('')
const shippingAddress = ref('')
const expectedDeliveryDate = ref('')
const notes = ref('')
const orderStatus = ref('pending')
const lineItems = ref<LineItem[]>([])
const adjustmentAmount = ref(0)
const adjustmentNote = ref('')

const STATUS_LABELS: Record<string, string> = {
  pending: '待處理',
  shipped: '已出貨',
  completed: '已完成',
  cancelled: '已取消',
}

async function loadAll() {
  loading.value = true
  order.value = null
  try {
    const [orderRes, productsRes, materialsRes] = await Promise.all([
      apiClient.get<Order>(`/api/v1/admin/orders/${orderId.value}`),
      apiClient.get<Product[]>('/api/v1/admin/products'),
      apiClient.get<{ items: Material[] }>('/api/v1/admin/materials', { params: { page_size: 1000 } }),
    ])
    order.value = orderRes.data
    products.value = productsRes.data
    materials.value = materialsRes.data.items

    realName.value = orderRes.data.real_name ?? ''
    contactSource.value = (orderRes.data.contact_source as typeof contactSource.value) ?? ''
    customerName.value = orderRes.data.customer_name
    phone.value = orderRes.data.phone
    shippingMethod.value = orderRes.data.shipping_method as typeof shippingMethod.value
    shippingStoreCode.value = orderRes.data.shipping_store_code ?? ''
    shippingAddress.value = orderRes.data.shipping_address ?? ''
    expectedDeliveryDate.value = orderRes.data.expected_delivery_date
    notes.value = orderRes.data.notes ?? ''
    orderStatus.value = orderRes.data.status
    adjustmentAmount.value = orderRes.data.adjustment_amount
    adjustmentNote.value = orderRes.data.adjustment_note ?? ''
    lineItems.value = orderRes.data.items.map((item) => ({
      productId: item.product_id,
      variantId: item.variant_id,
      materialId: item.material_id,
      quantity: item.quantity,
      customNote: item.custom_note,
      extraCharge: item.extra_charge,
    }))
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
watch(orderId, loadAll)

function addLineItem() {
  lineItems.value.push({
    productId: null,
    variantId: null,
    materialId: null,
    quantity: 1,
    customNote: null,
    extraCharge: 0,
  })
}

function removeLineItem(index: number) {
  lineItems.value.splice(index, 1)
}

function handleProductChange(item: LineItem) {
  item.variantId = null
}

function variantsForProduct(productId: number | null) {
  return products.value.find((p) => p.id === productId)?.variants ?? []
}

function primaryFabricImage(materialId: number | null) {
  const material = materials.value.find((m) => m.id === materialId)
  if (!material) return null
  const fabricImages = material.images.filter((img) => img.image_type === 'fabric')
  return fabricImages.find((img) => img.is_primary) ?? fabricImages[0] ?? null
}

function primaryProductImage(productId: number | null) {
  const product = products.value.find((p) => p.id === productId)
  if (!product || !product.images.length) return null
  return product.images.find((img) => img.is_primary) ?? product.images[0]
}

function itemUnitPrice(item: LineItem): number {
  const product = products.value.find((p) => p.id === item.productId)
  if (!product) return 0
  const basePrice = product.has_variants
    ? product.variants.find((v) => v.id === item.variantId)?.price ?? null
    : product.base_price
  if (basePrice === null) return 0
  const extraCharge = item.extraCharge || 0
  if (item.materialId === null) return basePrice + extraCharge
  const material = materials.value.find((m) => m.id === item.materialId)
  if (!material) return 0
  return basePrice + material.price_addon + extraCharge
}

function itemSubtotal(item: LineItem): number {
  return itemUnitPrice(item) * (item.quantity || 0)
}

const itemsTotal = computed(() =>
  lineItems.value.reduce((sum, item) => sum + itemSubtotal(item), 0),
)

const totalAmount = computed(() => itemsTotal.value + (adjustmentAmount.value || 0))

const canSave = computed(() => {
  if (!customerName.value.trim() || !phone.value.trim() || !expectedDeliveryDate.value) return false
  if (shippingMethod.value === 'address' && !shippingAddress.value.trim()) return false
  if (shippingMethod.value !== 'address' && !shippingStoreCode.value.trim()) return false
  if (lineItems.value.length === 0) return false
  return lineItems.value.every((item) => {
    if (!item.productId || item.quantity <= 0) return false
    if (variantsForProduct(item.productId).length > 0 && !item.variantId) return false
    return true
  })
})

async function handleSave() {
  saving.value = true
  try {
    await apiClient.put(`/api/v1/admin/orders/${orderId.value}`, {
      real_name: realName.value.trim() || null,
      contact_source: contactSource.value || null,
      customer_name: customerName.value,
      phone: phone.value,
      shipping_method: shippingMethod.value,
      shipping_store_code: shippingMethod.value === 'address' ? null : shippingStoreCode.value,
      shipping_address: shippingMethod.value === 'address' ? shippingAddress.value : null,
      expected_delivery_date: expectedDeliveryDate.value,
      notes: notes.value.trim() || null,
      status: orderStatus.value,
      adjustment_amount: adjustmentAmount.value || 0,
      adjustment_note: adjustmentNote.value.trim() || null,
      items: lineItems.value.map((item) => ({
        product_id: item.productId,
        variant_id: item.variantId,
        material_id: item.materialId,
        quantity: item.quantity,
        custom_note: item.customNote?.trim() || null,
        extra_charge: item.extraCharge || 0,
      })),
    })
    ElMessage.success('已儲存變更')
    await loadAll()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail ?? '儲存失敗,請確認資料填寫正確')
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!order.value) return
  await ElMessageBox.confirm(
    `確定要刪除訂單「${order.value.order_no}」(${order.value.customer_name})嗎?此操作無法復原。`,
    '刪除訂單',
    {
      type: 'warning',
      confirmButtonText: '刪除',
      confirmButtonClass: 'el-button--danger',
    },
  )
  await apiClient.delete(`/api/v1/admin/orders/${orderId.value}`)
  ElMessage.success('已刪除')
  router.push({ name: 'order-list' })
}
</script>

<template>
  <div class="max-w-3xl">
    <div class="mb-4 flex items-center justify-between">
      <el-button @click="router.push({ name: 'order-list' })">← 返回訂單列表</el-button>
      <el-button type="danger" @click="handleDelete">刪除訂單</el-button>
    </div>

    <template v-if="order && !loading">
      <h1 class="mb-4 text-xl font-semibold">
        訂單 {{ order.order_no }}
        <span class="ml-2 text-sm font-normal text-gray-500">
          建立於 {{ new Date(order.created_at).toLocaleString('zh-TW') }}
        </span>
      </h1>

      <el-form label-position="top">
        <el-form-item label="訂單狀態">
          <el-select v-model="orderStatus" class="w-40">
            <el-option v-for="(label, value) in STATUS_LABELS" :key="value" :label="label" :value="value" />
          </el-select>
        </el-form-item>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <el-form-item label="真實姓名">
            <el-input v-model="realName" />
          </el-form-item>
          <el-form-item label="電話">
            <el-input v-model="phone" />
          </el-form-item>
          <el-form-item label="通訊來源">
            <el-select v-model="contactSource" placeholder="請選擇" class="w-full">
              <el-option label="IG" value="ig" />
              <el-option label="LINE" value="line" />
              <el-option label="FB" value="fb" />
            </el-select>
          </el-form-item>
          <el-form-item label="通訊名字(收件人)">
            <el-input v-model="customerName" />
          </el-form-item>
        </div>

        <el-form-item label="寄送方式">
          <el-radio-group v-model="shippingMethod">
            <el-radio value="family_mart">好賣家(全家)</el-radio>
            <el-radio value="seven_eleven">賣貨便(7-11)</el-radio>
            <el-radio value="address">地址配送</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="shippingMethod !== 'address'" label="店號">
          <el-input v-model="shippingStoreCode" placeholder="請輸入門市店號" />
        </el-form-item>
        <el-form-item v-else label="寄送地址">
          <el-input v-model="shippingAddress" placeholder="請輸入完整收件地址" />
        </el-form-item>

        <el-form-item label="預期收到日期">
          <el-date-picker v-model="expectedDeliveryDate" value-format="YYYY-MM-DD" />
        </el-form-item>

        <el-form-item label="備註(客人的其他需求)">
          <el-input v-model="notes" type="textarea" :rows="3" placeholder="無" />
        </el-form-item>

        <el-divider />
        <div class="mb-2 flex items-center justify-between">
          <span class="font-medium">訂購項目</span>
          <el-button size="small" @click="addLineItem">新增項目</el-button>
        </div>

        <div
          v-for="(item, index) in lineItems"
          :key="index"
          class="mb-3 flex flex-wrap items-end gap-3 rounded border border-gray-200 p-3"
        >
          <el-form-item label="商品" class="!mb-0 w-full sm:w-56">
            <div class="flex items-center gap-2">
              <el-image
                v-if="primaryProductImage(item.productId)"
                :src="imageUrl(primaryProductImage(item.productId)!.thumbnail_key ?? primaryProductImage(item.productId)!.storage_key)"
                :preview-src-list="[imageUrl(primaryProductImage(item.productId)!.storage_key)]"
                preview-teleported
                fit="cover"
                class="h-8 w-8 flex-none cursor-zoom-in rounded"
              />
              <el-select v-model="item.productId" filterable placeholder="請選擇" @change="handleProductChange(item)">
                <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </div>
          </el-form-item>
          <el-form-item
            v-if="variantsForProduct(item.productId).length > 0"
            label="規格"
            class="!mb-0 w-full sm:w-40"
          >
            <el-select v-model="item.variantId" filterable placeholder="請選擇">
              <el-option v-for="v in variantsForProduct(item.productId)" :key="v.id" :label="v.name" :value="v.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="布料" class="!mb-0 w-full sm:min-w-[220px] sm:flex-1">
            <div class="flex items-center gap-2">
              <el-image
                v-if="primaryFabricImage(item.materialId)"
                :src="imageUrl(primaryFabricImage(item.materialId)!.thumbnail_key ?? primaryFabricImage(item.materialId)!.storage_key)"
                :preview-src-list="[imageUrl(primaryFabricImage(item.materialId)!.storage_key)]"
                preview-teleported
                fit="cover"
                class="h-8 w-8 flex-none cursor-zoom-in rounded"
              />
              <el-select v-model="item.materialId" filterable clearable placeholder="現貨商品不需選擇">
                <el-option v-for="m in materials" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
            </div>
          </el-form-item>
          <el-form-item label="數量" class="!mb-0 w-full sm:w-28">
            <el-input-number v-model="item.quantity" :min="1" />
          </el-form-item>
          <el-form-item label="客製說明" class="!mb-0 w-full sm:min-w-[200px] sm:flex-1">
            <el-input v-model="item.customNote" placeholder="例如:繡名字、加大尺寸" clearable />
          </el-form-item>
          <el-form-item label="加價(每件)" class="!mb-0 w-full sm:w-32">
            <el-input-number v-model="item.extraCharge" :step="10" />
          </el-form-item>
          <div class="flex w-full items-center justify-between">
            <span class="text-sm text-gray-600">小計:NT$ {{ itemSubtotal(item) }}</span>
            <el-button
              v-if="lineItems.length > 1"
              size="small"
              type="danger"
              text
              @click="removeLineItem(index)"
            >
              移除
            </el-button>
          </div>
        </div>

        <el-divider />
        <div class="mb-2 font-medium">價格調整(折扣或加價,套用在整張訂單)</div>
        <div class="mb-4 flex flex-wrap items-end gap-3">
          <el-form-item label="調整金額(負數為折扣)" class="!mb-0 w-full sm:w-48">
            <el-input-number v-model="adjustmentAmount" :step="10" />
          </el-form-item>
          <el-form-item label="說明" class="!mb-0 w-full sm:min-w-[220px] sm:flex-1">
            <el-input v-model="adjustmentNote" placeholder="例如:老客戶折扣、加急處理費" clearable />
          </el-form-item>
        </div>

        <div class="mt-4 flex items-center justify-between border-t border-gray-200 pt-4">
          <div>
            <p v-if="adjustmentAmount" class="text-sm text-gray-500">
              商品小計:NT$ {{ itemsTotal }}(調整 {{ adjustmentAmount > 0 ? '+' : '' }}{{ adjustmentAmount }})
            </p>
            <span class="text-lg font-semibold">總價:NT$ {{ totalAmount }}</span>
          </div>
          <el-button type="primary" :loading="saving" :disabled="!canSave" @click="handleSave">
            儲存變更
          </el-button>
        </div>
      </el-form>
    </template>
  </div>
</template>
