<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UploadRequestOptions } from 'element-plus'
import { apiClient, imageUrl } from '../../api/client'
import { generateSku } from '../../utils/codegen'
import type { Material, MaterialImage } from '../../types'

const route = useRoute()
const router = useRouter()

const materialId = computed(() => (route.params.id ? Number(route.params.id) : null))
const isEdit = computed(() => materialId.value !== null)

const form = ref({
  code: '',
  name: '',
  unit: 'yard',
  unit_cost: 0,
  price_addon: 0,
  quantity_on_hand: 1,
  origin: '韓國',
  fabric_type: '',
  supplier: '',
  notes: '',
  status: 'active',
})

interface PendingImage {
  file: File
  previewUrl: string
  imageType: 'fabric' | 'showcase'
}

const customAttributePairs = ref<{ key: string; value: string }[]>([])
const images = ref<MaterialImage[]>([])
const pendingImages = ref<PendingImage[]>([])
const saving = ref(false)

const fabricImages = computed(() => images.value.filter((img) => img.image_type === 'fabric'))
const showcaseImages = computed(() => images.value.filter((img) => img.image_type === 'showcase'))
const pendingFabricImages = computed(() => pendingImages.value.filter((img) => img.imageType === 'fabric'))
const pendingShowcaseImages = computed(() => pendingImages.value.filter((img) => img.imageType === 'showcase'))

async function regenerateCode() {
  try {
    const { data } = await apiClient.get<{ total: number }>('/api/v1/admin/materials', {
      params: { page: 1, page_size: 1 },
    })
    form.value.code = `No.${String(data.total + 1).padStart(3, '0')}`
  } catch {
    form.value.code = generateSku('FAB')
  }
}

async function loadMaterial() {
  if (!materialId.value) return
  const { data } = await apiClient.get<Material>(`/api/v1/admin/materials/${materialId.value}`)
  form.value = {
    code: data.code ?? '',
    name: data.name,
    unit: data.unit,
    unit_cost: data.unit_cost,
    price_addon: data.price_addon,
    quantity_on_hand: data.quantity_on_hand,
    origin: data.origin ?? '',
    fabric_type: data.fabric_type ?? '',
    supplier: data.supplier ?? '',
    notes: data.notes ?? '',
    status: data.status,
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

async function uploadImageFile(
  targetMaterialId: number,
  file: File,
  imageType: 'fabric' | 'showcase',
  isPrimary: boolean,
  sortOrder: number,
) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('is_primary', String(isPrimary))
  formData.append('sort_order', String(sortOrder))
  formData.append('image_type', imageType)
  await apiClient.post(`/api/v1/admin/materials/${targetMaterialId}/images`, formData)
}

async function flushPendingImages(targetMaterialId: number) {
  for (const imageType of ['fabric', 'showcase'] as const) {
    const pendingOfType = pendingImages.value.filter((img) => img.imageType === imageType)
    for (let i = 0; i < pendingOfType.length; i++) {
      await uploadImageFile(targetMaterialId, pendingOfType[i].file, imageType, i === 0, i)
    }
  }
  for (const pending of pendingImages.value) URL.revokeObjectURL(pending.previewUrl)
  pendingImages.value = []
}

async function submitOnce() {
  const payload = {
    ...form.value,
    code: form.value.code || null,
    origin: form.value.origin || null,
    fabric_type: form.value.fabric_type || null,
    custom_attributes: buildCustomAttributes(),
  }
  if (isEdit.value) {
    await apiClient.put(`/api/v1/admin/materials/${materialId.value}`, payload)
    ElMessage.success('已更新')
    router.push({ name: 'material-list' })
    return
  }
  const { data } = await apiClient.post<Material>('/api/v1/admin/materials', payload)
  await flushPendingImages(data.id)
  ElMessage.success('已建立')
  router.push({ name: 'material-list' })
}

async function handleSubmit() {
  saving.value = true
  try {
    try {
      await submitOnce()
    } catch (err: any) {
      if (err?.response?.status === 409 && !isEdit.value) {
        await regenerateCode()
        await submitOnce()
      } else {
        throw err
      }
    }
  } catch {
    ElMessage.error('儲存失敗,請確認編號是否重複')
  } finally {
    saving.value = false
  }
}

function uploadImage(imageType: 'fabric' | 'showcase') {
  return async (options: UploadRequestOptions) => {
    const file = options.file as File
    if (!materialId.value) {
      pendingImages.value.push({ file, previewUrl: URL.createObjectURL(file), imageType })
      return
    }
    const groupCount = imageType === 'fabric' ? fabricImages.value.length : showcaseImages.value.length
    const formData = new FormData()
    formData.append('file', file)
    formData.append('is_primary', String(groupCount === 0))
    formData.append('sort_order', String(groupCount))
    formData.append('image_type', imageType)
    const { data } = await apiClient.post<MaterialImage>(
      `/api/v1/admin/materials/${materialId.value}/images`,
      formData,
    )
    images.value.push(data)
  }
}

const handleFabricImageUpload = uploadImage('fabric')
const handleShowcaseImageUpload = uploadImage('showcase')

function removePendingImage(imageType: 'fabric' | 'showcase', index: number) {
  const list = imageType === 'fabric' ? pendingFabricImages.value : pendingShowcaseImages.value
  const target = list[index]
  URL.revokeObjectURL(target.previewUrl)
  pendingImages.value = pendingImages.value.filter((img) => img !== target)
}

async function handleImageDelete(image: MaterialImage) {
  if (!materialId.value) return
  await apiClient.delete(`/api/v1/admin/materials/${materialId.value}/images/${image.id}`)
  images.value = images.value.filter((img) => img.id !== image.id)
}

onMounted(() => {
  if (isEdit.value) {
    loadMaterial()
  } else {
    regenerateCode()
  }
})

watch(materialId, (newId) => {
  if (newId) loadMaterial()
})
</script>

<template>
  <div class="max-w-3xl">
    <h1 class="mb-4 text-xl font-semibold">{{ isEdit ? '編輯原材料' : '新增原材料' }}</h1>

    <el-form label-position="top" @submit.prevent="handleSubmit">
      <p v-if="!isEdit" class="mb-2 text-xs text-gray-400">編號已自動產生,通常不需要手動修改。</p>
      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="編號 (選填)">
          <div class="flex gap-2">
            <el-input v-model="form.code" placeholder="例如:FAB-001" />
            <el-button @click="regenerateCode">重新產生</el-button>
          </div>
        </el-form-item>
        <el-form-item label="布料樣式名稱">
          <el-input v-model="form.name" placeholder="例如:粉紅棉麻格紋" />
        </el-form-item>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="計價單位">
          <el-select v-model="form.unit">
            <el-option label="公尺" value="meter" />
            <el-option label="碼" value="yard" />
            <el-option label="公斤" value="kg" />
            <el-option label="件" value="piece" />
          </el-select>
        </el-form-item>
        <el-form-item label="目前庫存量">
          <el-input-number v-model="form.quantity_on_hand" :min="0" :precision="2" />
        </el-form-item>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="進貨成本 (NT$,內部參考用,不會顯示給客人)">
          <el-input-number v-model="form.unit_cost" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="顧客加價 (NT$,選這塊布料時商品要加多少錢)">
          <el-input-number v-model="form.price_addon" :min="0" :precision="2" />
        </el-form-item>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="產地 (選填)">
          <el-select v-model="form.origin" clearable placeholder="請選擇產地">
            <el-option label="台灣" value="台灣" />
            <el-option label="韓國" value="韓國" />
            <el-option label="美國" value="美國" />
            <el-option label="日本" value="日本" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="布料種類 (選填)">
          <el-select v-model="form.fabric_type" clearable placeholder="請選擇布料種類">
            <el-option label="二紗" value="二紗" />
            <el-option label="棉布" value="棉布" />
            <el-option label="厚棉" value="厚棉" />
          </el-select>
        </el-form-item>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <el-form-item label="供應商 (選填)">
          <el-input v-model="form.supplier" />
        </el-form-item>
      </div>
      <el-form-item label="備註">
        <el-input v-model="form.notes" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item label="狀態">
        <el-select v-model="form.status" class="w-40">
          <el-option label="使用中" value="active" />
          <el-option label="已停用" value="discontinued" />
        </el-select>
      </el-form-item>

      <el-divider />
      <div class="mb-2 flex items-center justify-between">
        <span class="font-medium">自訂欄位(例如:顏色、材質成分、布寬)</span>
        <el-button size="small" @click="addAttributePair">新增欄位</el-button>
      </div>
      <div v-for="(pair, index) in customAttributePairs" :key="index" class="mb-2 flex gap-2">
        <el-input v-model="pair.key" placeholder="欄位名稱,例如:材質成分" class="w-1/3" />
        <el-input v-model="pair.value" placeholder="欄位內容" />
        <el-button @click="removeAttributePair(index)">移除</el-button>
      </div>

      <el-divider />
      <el-button type="primary" :loading="saving" @click="handleSubmit">
        {{ isEdit ? '儲存變更' : '建立原材料' }}
      </el-button>
    </el-form>

    <el-divider />
    <div class="mb-2 font-medium">布料照片</div>
    <p v-if="!isEdit" class="mb-2 text-xs text-gray-500">
      先選好照片,按下「建立原材料」時會一起上傳,就不會搞混是哪一張。
    </p>
    <div class="mb-4 flex flex-wrap gap-3">
      <div v-for="image in fabricImages" :key="image.id" class="relative">
        <img :src="imageUrl(image.thumbnail_key ?? image.storage_key)" class="h-24 w-24 rounded object-cover" />
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
      <div v-for="(pending, index) in pendingFabricImages" :key="pending.previewUrl" class="relative">
        <img :src="pending.previewUrl" class="h-24 w-24 rounded object-cover" />
        <el-tag v-if="fabricImages.length === 0 && index === 0" size="small" type="warning" class="absolute left-1 top-1">
          主圖
        </el-tag>
        <el-button
          size="small"
          type="danger"
          circle
          class="absolute -right-2 -top-2"
          @click="removePendingImage('fabric', index)"
        >
          ×
        </el-button>
      </div>
    </div>
    <el-upload :http-request="handleFabricImageUpload" :show-file-list="false" accept="image/*">
      <el-button>上傳照片</el-button>
    </el-upload>

    <el-divider />
    <div class="mb-2 font-medium">成品樣式照片(前台商品展示)</div>
    <p class="mb-2 text-sm text-gray-500">
      上傳用這塊布料做出來的成品照片(可多張),顧客在前台瀏覽這塊布料時會看到這些照片作為展示。
    </p>
    <div class="mb-4 flex flex-wrap gap-3">
      <div v-for="image in showcaseImages" :key="image.id" class="relative">
        <img :src="imageUrl(image.thumbnail_key ?? image.storage_key)" class="h-24 w-24 rounded object-cover" />
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
      <div v-for="(pending, index) in pendingShowcaseImages" :key="pending.previewUrl" class="relative">
        <img :src="pending.previewUrl" class="h-24 w-24 rounded object-cover" />
        <el-button
          size="small"
          type="danger"
          circle
          class="absolute -right-2 -top-2"
          @click="removePendingImage('showcase', index)"
        >
          ×
        </el-button>
      </div>
    </div>
    <el-upload
      :http-request="handleShowcaseImageUpload"
      :show-file-list="false"
      accept="image/*"
      multiple
    >
      <el-button>上傳成品照片</el-button>
    </el-upload>
  </div>
</template>
