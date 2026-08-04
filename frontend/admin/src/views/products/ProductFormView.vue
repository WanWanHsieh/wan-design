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
  status: 'draft',
  is_featured: false,
})

interface PendingImage {
  file: File
  previewUrl: string
}

const customAttributePairs = ref<{ key: string; value: string }[]>([])
const images = ref<ProductImage[]>([])
const pendingImages = ref<PendingImage[]>([])
const categories = ref<Category[]>([])
const saving = ref(false)

const selectableCategories = computed(() =>
  categories.value.filter(
    (c) =>
      c.id === form.value.category_id ||
      c.parent_id !== null ||
      !categories.value.some((other) => other.parent_id === c.id),
  ),
)

function regenerateSku() {
  form.value.sku = generateSku('PD')
}

function regenerateSlug() {
  form.value.slug = generateSlug('pd')
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
    is_featured: data.is_featured,
  }
  customAttributePairs.value = Object.entries(data.custom_attributes).map(([key, value]) => ({
    key,
    value: String(value),
  }))
  images.value = data.images
}

function addAttributePair() {
  customAttributePairs.value.push({ key: '', value: '' })
}

function removeAttributePair(index: number) {
  customAttributePairs.value.splice(index, 1)
}

function buildCustomAttributes(): Record<string, string> {
  const result: Record<string, string> = {}
  for (const pair of customAttributePairs.value) {
    if (pair.key.trim()) result[pair.key.trim()] = pair.value
  }
  return result
}

async function uploadImageFile(targetProductId: number, file: File, isPrimary: boolean, sortOrder: number) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('is_primary', String(isPrimary))
  formData.append('sort_order', String(sortOrder))
  await apiClient.post(`/api/v1/admin/products/${targetProductId}/images`, formData)
}

async function flushPendingImages(targetProductId: number) {
  for (let i = 0; i < pendingImages.value.length; i++) {
    await uploadImageFile(targetProductId, pendingImages.value[i].file, i === 0, i)
  }
  for (const pending of pendingImages.value) URL.revokeObjectURL(pending.previewUrl)
  pendingImages.value = []
}

async function submitOnce() {
  const payload = { ...form.value, custom_attributes: buildCustomAttributes() }
  if (isEdit.value) {
    await apiClient.put(`/api/v1/admin/products/${productId.value}`, payload)
    ElMessage.success('已更新')
    router.push({ name: 'product-list' })
    return
  }
  const { data } = await apiClient.post<Product>('/api/v1/admin/products', {
    ...payload,
    attribute_values: [],
  })
  await flushPendingImages(data.id)
  ElMessage.success('已建立')
  router.push({ name: 'product-list' })
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

async function handleImageUpload(options: UploadRequestOptions) {
  const file = options.file as File
  if (!productId.value) {
    pendingImages.value.push({ file, previewUrl: URL.createObjectURL(file) })
    return
  }
  const formData = new FormData()
  formData.append('file', file)
  formData.append('is_primary', String(images.value.length === 0))
  formData.append('sort_order', String(images.value.length))
  const { data } = await apiClient.post<ProductImage>(
    `/api/v1/admin/products/${productId.value}/images`,
    formData,
  )
  images.value.push(data)
}

function removePendingImage(index: number) {
  URL.revokeObjectURL(pendingImages.value[index].previewUrl)
  pendingImages.value.splice(index, 1)
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
    <h1 class="mb-4 text-xl font-semibold">{{ isEdit ? '編輯商品' : '新增商品' }}</h1>

    <el-form label-position="top" @submit.prevent="handleSubmit">
      <p class="mb-2 text-xs text-gray-400">SKU / Slug 已自動產生,通常不需要手動修改。</p>
      <div class="grid grid-cols-2 gap-4">
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
      <el-form-item label="商品名稱">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="4" />
      </el-form-item>
      <div class="grid grid-cols-3 gap-4">
        <el-form-item label="分類">
          <el-select v-model="form.category_id" clearable placeholder="請選擇分類">
            <el-option v-for="c in selectableCategories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="價格">
          <el-input-number v-model="form.base_price" :min="0" />
        </el-form-item>
        <el-form-item label="狀態">
          <el-select v-model="form.status">
            <el-option label="草稿" value="draft" />
            <el-option label="上架" value="active" />
            <el-option label="下架" value="archived" />
          </el-select>
        </el-form-item>
      </div>

      <el-form-item>
        <el-switch v-model="form.is_featured" />
        <span class="ml-2 text-sm text-brown">設為本週主打商品(顯示在前台「主打商品」頁面)</span>
      </el-form-item>

      <el-divider />
      <div class="mb-2 flex items-center justify-between">
        <span class="font-medium">自訂欄位 (可自行新增)</span>
        <el-button size="small" @click="addAttributePair">新增欄位</el-button>
      </div>
      <div v-for="(pair, index) in customAttributePairs" :key="index" class="mb-2 flex gap-2">
        <el-input v-model="pair.key" placeholder="欄位名稱,例如:材質" class="w-1/3" />
        <el-input v-model="pair.value" placeholder="欄位內容" />
        <el-button @click="removeAttributePair(index)">移除</el-button>
      </div>

      <el-divider />
      <el-button type="primary" :loading="saving" @click="handleSubmit">
        {{ isEdit ? '儲存變更' : '建立商品' }}
      </el-button>
    </el-form>

    <el-divider />
    <div class="mb-2 font-medium">商品照片</div>
    <p v-if="!isEdit" class="mb-2 text-xs text-gray-500">
      先選好照片,按下「建立商品」時會一起上傳,就不會搞混是哪一張。
    </p>
    <div class="mb-4 flex flex-wrap gap-3">
      <div v-for="image in images" :key="image.id" class="relative">
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
      <div v-for="(pending, index) in pendingImages" :key="pending.previewUrl" class="relative">
        <img :src="pending.previewUrl" class="h-24 w-24 rounded object-cover" />
        <el-tag v-if="images.length === 0 && index === 0" size="small" type="warning" class="absolute left-1 top-1">
          主圖
        </el-tag>
        <el-button
          size="small"
          type="danger"
          circle
          class="absolute -right-2 -top-2"
          @click="removePendingImage(index)"
        >
          ×
        </el-button>
      </div>
    </div>
    <el-upload :http-request="handleImageUpload" :show-file-list="false" accept="image/*">
      <el-button>上傳照片</el-button>
    </el-upload>
  </div>
</template>
