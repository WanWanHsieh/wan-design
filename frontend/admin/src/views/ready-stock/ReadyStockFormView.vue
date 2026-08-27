<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UploadRequestOptions } from 'element-plus'
import { apiClient, imageUrl } from '../../api/client'
import { generateSku, generateSlug } from '../../utils/codegen'
import type { Category, Product, ProductImage } from '../../types'

const route = useRoute()
const router = useRouter()

const productId = computed(() => (route.params.id ? Number(route.params.id) : null))
const isEdit = computed(() => productId.value !== null)

const form = ref({
  sku: '',
  name: '',
  slug: '',
  description: '',
  category_id: null as number | null,
  base_price: 0,
  status: 'active',
  stock_quantity: 1,
  is_featured: false,
  sale_price: null as number | null,
  sale_starts_at: null as string | null,
  sale_ends_at: null as string | null,
})

const saleEnabled = ref(false)
const saleDateRange = computed<[string, string] | null>({
  get: (): [string, string] | null => {
    if (!form.value.sale_starts_at && !form.value.sale_ends_at) return null
    return [form.value.sale_starts_at ?? '', form.value.sale_ends_at ?? '']
  },
  set: (value: [string, string] | null) => {
    form.value.sale_starts_at = value?.[0] || null
    form.value.sale_ends_at = value?.[1] || null
  },
})

watch(saleEnabled, (enabled) => {
  if (!enabled) {
    form.value.sale_price = null
    form.value.sale_starts_at = null
    form.value.sale_ends_at = null
  }
})

interface PendingImage {
  file: File
  previewUrl: string
  imageType: 'main' | 'reference'
}

const images = ref<ProductImage[]>([])
const pendingImages = ref<PendingImage[]>([])
const categories = ref<Category[]>([])
const saving = ref(false)

const mainImages = computed(() => images.value.filter((img) => img.image_type === 'main'))
const referenceImages = computed(() => images.value.filter((img) => img.image_type === 'reference'))
const pendingMainImages = computed(() => pendingImages.value.filter((img) => img.imageType === 'main'))
const pendingReferenceImages = computed(() =>
  pendingImages.value.filter((img) => img.imageType === 'reference'),
)

const selectableCategories = computed(() =>
  categories.value.filter(
    (c) =>
      c.id === form.value.category_id ||
      c.parent_id !== null ||
      !categories.value.some((other) => other.parent_id === c.id),
  ),
)

function regenerateSku() {
  form.value.sku = generateSku('RS')
}

function regenerateSlug() {
  form.value.slug = generateSlug('rs')
}

async function loadCategories() {
  const { data } = await apiClient.get<Category[]>('/api/v1/admin/categories')
  categories.value = data
}

async function loadProduct() {
  if (!productId.value) return
  const { data } = await apiClient.get<Product>(`/api/v1/admin/products/${productId.value}`)
  form.value = {
    sku: data.sku,
    name: data.name,
    slug: data.slug,
    description: data.description ?? '',
    category_id: data.category_id,
    base_price: data.base_price,
    status: data.status,
    stock_quantity: data.stock_quantity,
    is_featured: data.is_featured,
    sale_price: data.sale_price,
    sale_starts_at: data.sale_starts_at,
    sale_ends_at: data.sale_ends_at,
  }
  saleEnabled.value = data.sale_price !== null
  images.value = data.images
}

async function uploadImageFile(
  targetProductId: number,
  file: File,
  imageType: 'main' | 'reference',
  isPrimary: boolean,
  sortOrder: number,
) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('is_primary', String(isPrimary))
  formData.append('sort_order', String(sortOrder))
  formData.append('image_type', imageType)
  await apiClient.post(`/api/v1/admin/products/${targetProductId}/images`, formData)
}

async function flushPendingImages(targetProductId: number) {
  for (const imageType of ['main', 'reference'] as const) {
    const pendingOfType = pendingImages.value.filter((img) => img.imageType === imageType)
    for (let i = 0; i < pendingOfType.length; i++) {
      await uploadImageFile(targetProductId, pendingOfType[i].file, imageType, i === 0 && imageType === 'main', i)
    }
  }
  for (const pending of pendingImages.value) URL.revokeObjectURL(pending.previewUrl)
  pendingImages.value = []
}

async function submitOnce() {
  const payload = { ...form.value, track_stock: true, custom_attributes: {} }
  if (isEdit.value) {
    await apiClient.put(`/api/v1/admin/products/${productId.value}`, payload)
    ElMessage.success('已更新')
    router.push({ name: 'ready-stock-list' })
    return
  }
  const { data } = await apiClient.post<Product>('/api/v1/admin/products', {
    ...payload,
    attribute_values: [],
  })
  await flushPendingImages(data.id)
  ElMessage.success('已建立')
  router.push({ name: 'ready-stock-list' })
}

async function handleSubmit() {
  saving.value = true
  try {
    try {
      await submitOnce()
    } catch (err: any) {
      if (err?.response?.status === 409 && !isEdit.value) {
        regenerateSku()
        regenerateSlug()
        await submitOnce()
      } else {
        throw err
      }
    }
  } catch {
    ElMessage.error('儲存失敗,請確認 SKU / Slug 是否重複')
  } finally {
    saving.value = false
  }
}

function uploadImage(imageType: 'main' | 'reference') {
  return async (options: UploadRequestOptions) => {
    const file = options.file as File
    if (!productId.value) {
      pendingImages.value.push({ file, previewUrl: URL.createObjectURL(file), imageType })
      return
    }
    const groupCount = imageType === 'main' ? mainImages.value.length : referenceImages.value.length
    const formData = new FormData()
    formData.append('file', file)
    formData.append('is_primary', String(imageType === 'main' && groupCount === 0))
    formData.append('sort_order', String(groupCount))
    formData.append('image_type', imageType)
    const { data } = await apiClient.post<ProductImage>(
      `/api/v1/admin/products/${productId.value}/images`,
      formData,
    )
    images.value.push(data)
  }
}

const handleMainImageUpload = uploadImage('main')
const handleReferenceImageUpload = uploadImage('reference')

function removePendingImage(imageType: 'main' | 'reference', index: number) {
  const list = imageType === 'main' ? pendingMainImages.value : pendingReferenceImages.value
  const target = list[index]
  URL.revokeObjectURL(target.previewUrl)
  pendingImages.value = pendingImages.value.filter((img) => img !== target)
}

async function handleImageDelete(image: ProductImage) {
  if (!productId.value) return
  await apiClient.delete(`/api/v1/admin/products/${productId.value}/images/${image.id}`)
  images.value = images.value.filter((img) => img.id !== image.id)
}

onMounted(async () => {
  await loadCategories()
  if (isEdit.value) {
    await loadProduct()
  } else {
    regenerateSku()
    regenerateSlug()
  }
})

watch(productId, (newId) => {
  if (newId) loadProduct()
})
</script>

<template>
  <div class="max-w-3xl">
    <h1 class="mb-1 text-xl font-semibold">{{ isEdit ? '編輯現貨商品' : '新增現貨商品' }}</h1>
    <p class="mb-4 text-sm text-gray-500">
      每筆現貨代表一件實際庫存,建議用花色/款式命名(例如:扭結蝴蝶結髮帶-藍色小花)。
    </p>

    <el-form label-position="top" @submit.prevent="handleSubmit">
      <p class="mb-2 text-xs text-gray-400">SKU / Slug 已自動產生,通常不需要手動修改。</p>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <el-form-item label="SKU">
          <div class="flex gap-2">
            <el-input v-model="form.sku" />
            <el-button @click="regenerateSku">重新產生</el-button>
          </div>
        </el-form-item>
        <el-form-item label="Slug (網址代稱)">
          <div class="flex gap-2">
            <el-input v-model="form.slug" />
            <el-button @click="regenerateSlug">重新產生</el-button>
          </div>
        </el-form-item>
      </div>
      <el-form-item label="名稱">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="3" />
      </el-form-item>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <el-form-item label="款式分類(可選,用來歸類同款式的現貨)">
          <el-select v-model="form.category_id" clearable placeholder="請選擇分類">
            <el-option v-for="c in selectableCategories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="價格">
          <el-input-number v-model="form.base_price" :min="0" />
        </el-form-item>
        <el-form-item label="庫存數量">
          <el-input-number v-model="form.stock_quantity" :min="0" />
        </el-form-item>
      </div>
      <el-form-item label="狀態">
        <el-select v-model="form.status">
          <el-option label="草稿(前台不顯示)" value="draft" />
          <el-option label="上架" value="active" />
          <el-option label="下架" value="archived" />
        </el-select>
      </el-form-item>

      <el-form-item>
        <el-switch v-model="form.is_featured" />
        <span class="ml-2 text-sm text-brown">設為本週主打商品(顯示在前台「主打商品」頁面)</span>
      </el-form-item>

      <el-form-item>
        <el-switch v-model="saleEnabled" />
        <span class="ml-2 text-sm text-brown">設定特價</span>
      </el-form-item>
      <div v-if="saleEnabled" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <el-form-item label="特價">
          <el-input-number v-model="form.sale_price" :min="0" />
        </el-form-item>
        <el-form-item label="特價起訖日期(留空表示不限日期)">
          <el-date-picker
            v-model="saleDateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            start-placeholder="開始日期"
            end-placeholder="結束日期"
            class="w-full"
          />
        </el-form-item>
      </div>

      <el-divider />
      <el-button type="primary" :loading="saving" @click="handleSubmit">
        {{ isEdit ? '儲存變更' : '建立現貨商品' }}
      </el-button>
    </el-form>

    <el-divider />
    <div class="mb-2 font-medium">商品主圖</div>
    <p v-if="!isEdit" class="mb-2 text-xs text-gray-500">
      先選好照片,按下「建立現貨商品」時會一起上傳,就不會搞混是哪一張。
    </p>
    <div class="mb-4 flex flex-wrap gap-3">
      <div v-for="image in mainImages" :key="image.id" class="relative">
        <img :src="imageUrl(image.storage_key)" class="h-24 w-24 rounded object-cover" />
        <el-tag v-if="image.is_primary" size="small" class="absolute left-1 top-1">主圖</el-tag>
        <el-button
          size="small"
          type="danger"
          circle
          class="absolute -right-2 -top-2"
          @click="handleImageDelete(image)"
        >
          ×
        </el-button>
      </div>
      <div v-for="(pending, index) in pendingMainImages" :key="pending.previewUrl" class="relative">
        <img :src="pending.previewUrl" class="h-24 w-24 rounded object-cover" />
        <el-tag v-if="mainImages.length === 0 && index === 0" size="small" type="warning" class="absolute left-1 top-1">
          主圖
        </el-tag>
        <el-button
          size="small"
          type="danger"
          circle
          class="absolute -right-2 -top-2"
          @click="removePendingImage('main', index)"
        >
          ×
        </el-button>
      </div>
    </div>
    <el-upload :http-request="handleMainImageUpload" :show-file-list="false" accept="image/*">
      <el-button>上傳照片</el-button>
    </el-upload>

    <el-divider />
    <div class="mb-2 font-medium">其他花色參考照片(前台商品展示)</div>
    <p class="mb-2 text-sm text-gray-500">
      上傳這個商品不同花色/款式的參考照片(可多張),顧客在前台瀏覽這個商品時會看到這些照片作為參考。
    </p>
    <div class="mb-4 flex flex-wrap gap-3">
      <div v-for="image in referenceImages" :key="image.id" class="relative">
        <img :src="imageUrl(image.storage_key)" class="h-24 w-24 rounded object-cover" />
        <el-button
          size="small"
          type="danger"
          circle
          class="absolute -right-2 -top-2"
          @click="handleImageDelete(image)"
        >
          ×
        </el-button>
      </div>
      <div v-for="(pending, index) in pendingReferenceImages" :key="pending.previewUrl" class="relative">
        <img :src="pending.previewUrl" class="h-24 w-24 rounded object-cover" />
        <el-button
          size="small"
          type="danger"
          circle
          class="absolute -right-2 -top-2"
          @click="removePendingImage('reference', index)"
        >
          ×
        </el-button>
      </div>
    </div>
    <el-upload
      :http-request="handleReferenceImageUpload"
      :show-file-list="false"
      accept="image/*"
      multiple
    >
      <el-button>上傳參考照片</el-button>
    </el-upload>
  </div>
</template>
