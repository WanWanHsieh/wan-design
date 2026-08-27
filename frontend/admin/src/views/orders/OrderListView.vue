<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiClient, imageUrl } from '../../api/client'
import type { OrderItem, OrderListItem } from '../../types'

const orders = ref<OrderListItem[]>([])
const loading = ref(true)
const router = useRouter()

const selectedOrders = ref<OrderListItem[]>([])
const mergeDialogVisible = ref(false)
const primaryOrderId = ref<number | null>(null)
const merging = ref(false)

const SHIPPING_LABELS: Record<string, string> = {
  family_mart: '好賣家(全家)',
  seven_eleven: '賣貨便(7-11)',
  address: '地址配送',
}

const STATUS_LABELS: Record<string, string> = {
  pending: '待處理',
  shipped: '已出貨',
  completed: '已完成',
  cancelled: '已取消',
}

const STATUS_DOT_COLORS: Record<string, string> = {
  pending: '#909399',
  shipped: '#E6A23C',
  completed: '#67C23A',
  cancelled: '#F56C6C',
}

async function loadOrders() {
  loading.value = true
  try {
    const { data } = await apiClient.get<OrderListItem[]>('/api/v1/admin/orders')
    orders.value = data
  } finally {
    loading.value = false
  }
}

onMounted(loadOrders)

const updatingIds = ref(new Set<number>())

async function updateStatus(order: OrderListItem, nextStatus: string) {
  if (updatingIds.value.has(order.id) || order.status === nextStatus) return
  updatingIds.value.add(order.id)

  const previousStatus = order.status
  order.status = nextStatus
  try {
    await apiClient.put(`/api/v1/admin/orders/${order.id}`, { status: nextStatus })
    ElMessage.success(`已更新為「${STATUS_LABELS[nextStatus]}」`)
  } catch (err: any) {
    order.status = previousStatus
    ElMessage.error(err?.response?.data?.detail ?? '更新失敗,請稍後再試')
  } finally {
    updatingIds.value.delete(order.id)
  }
}

function handleSelectionChange(rows: OrderListItem[]) {
  selectedOrders.value = rows
}

function openMergeDialog() {
  if (selectedOrders.value.length !== 2) return
  primaryOrderId.value = selectedOrders.value[0].id
  mergeDialogVisible.value = true
}

async function handleConfirmMerge() {
  if (primaryOrderId.value === null || selectedOrders.value.length !== 2) return
  const [a, b] = selectedOrders.value
  const secondaryId = primaryOrderId.value === a.id ? b.id : a.id
  merging.value = true
  try {
    await apiClient.post(`/api/v1/admin/orders/${primaryOrderId.value}/merge`, {
      secondary_order_id: secondaryId,
    })
    ElMessage.success('已合併訂單')
    mergeDialogVisible.value = false
    selectedOrders.value = []
    await loadOrders()
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail ?? '合併失敗,請稍後再試')
  } finally {
    merging.value = false
  }
}

const mobileExpandedIds = ref<Record<number, boolean>>({})

function toggleMobileExpand(id: number) {
  mobileExpandedIds.value[id] = !mobileExpandedIds.value[id]
}

const updatingItemIds = new Set<number>()

async function toggleItemCompleted(orderId: number, item: OrderItem) {
  if (updatingItemIds.has(item.id)) return
  updatingItemIds.add(item.id)

  const previous = item.is_completed
  item.is_completed = !previous
  try {
    await apiClient.put(`/api/v1/admin/orders/${orderId}/items/${item.id}/completion`, {
      is_completed: item.is_completed,
    })
  } catch {
    item.is_completed = previous
    ElMessage.error('更新失敗,請稍後再試')
  } finally {
    updatingItemIds.delete(item.id)
  }
}
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold">訂單管理</h1>
      <el-button
        v-if="selectedOrders.length > 0"
        type="primary"
        :disabled="selectedOrders.length !== 2"
        @click="openMergeDialog"
      >
        合併選中的訂單({{ selectedOrders.length }}/2)
      </el-button>
    </div>

    <el-table
      :data="orders"
      v-loading="loading"
      stripe
      row-key="id"
      class="hidden sm:block"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="45" />
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="bg-gray-50 px-6 py-3">
            <div class="mb-2 text-sm font-medium text-gray-700">訂購項目</div>
            <div class="flex max-w-[100vw] flex-wrap gap-4 overflow-hidden">
              <div
                v-for="item in row.items"
                :key="item.id"
                class="flex items-center gap-2 rounded border border-gray-200 bg-white px-3 py-2"
              >
                <el-checkbox
                  :model-value="item.is_completed"
                  @click.prevent="toggleItemCompleted(row.id, item)"
                />
                <img
                  v-if="item.product_thumbnail"
                  :src="imageUrl(item.product_thumbnail)"
                  class="h-10 w-10 rounded object-cover"
                  :title="item.product_name_snapshot"
                />
                <img
                  v-if="item.material_thumbnail"
                  :src="imageUrl(item.material_thumbnail)"
                  class="h-10 w-10 rounded object-cover"
                  :title="item.material_name_snapshot"
                />
                <div class="text-sm" :class="{ 'text-gray-400 line-through': item.is_completed }">
                  <div :class="item.is_completed ? '' : 'text-gray-900'">
                    {{ item.product_name_snapshot }}<template v-if="item.variant_name_snapshot"> - {{ item.variant_name_snapshot }}</template>
                  </div>
                  <div class="text-gray-500">
                    <template v-if="item.material_name_snapshot">{{ item.material_name_snapshot }} × </template
                    >{{ item.quantity }}
                  </div>
                </div>
              </div>
            </div>
            <div v-if="row.notes" class="mt-3 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              <span class="font-medium">客人備註:</span>{{ row.notes }}
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="狀態" width="120">
        <template #default="{ row }">
          <el-select
            :model-value="row.status"
            size="small"
            :disabled="updatingIds.has(row.id)"
            @change="(val: string) => updateStatus(row, val)"
          >
            <template #prefix>
              <span
                class="inline-block h-2 w-2 rounded-full"
                :style="{ backgroundColor: STATUS_DOT_COLORS[row.status] ?? '#909399' }"
              />
            </template>
            <el-option v-for="(label, value) in STATUS_LABELS" :key="value" :label="label" :value="value" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="order_no" label="訂單編號" width="180" />
      <el-table-column prop="customer_name" label="收件人" width="120" />
      <el-table-column prop="phone" label="電話" width="140" />
      <el-table-column label="寄送方式" width="140">
        <template #default="{ row }">{{ SHIPPING_LABELS[row.shipping_method] ?? row.shipping_method }}</template>
      </el-table-column>
      <el-table-column prop="expected_delivery_date" label="預期收到日期" width="140" />
      <el-table-column label="總價" width="100">
        <template #default="{ row }">NT$ {{ row.total_amount }}</template>
      </el-table-column>
      <el-table-column label="建立時間">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-TW') }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" @click="router.push({ name: 'order-detail', params: { id: row.id } })">
            查看
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-loading="loading" class="flex flex-col gap-3 sm:hidden">
      <div
        v-for="row in orders"
        :key="row.id"
        class="rounded-xl border border-beige bg-white p-3 shadow-[0_2px_8px_rgba(180,140,110,0.08)]"
      >
        <div class="flex items-center justify-between gap-2">
          <span class="font-medium text-brown">{{ row.order_no }}</span>
          <el-select
            :model-value="row.status"
            size="small"
            :disabled="updatingIds.has(row.id)"
            class="w-28"
            @change="(val: string) => updateStatus(row, val)"
          >
            <template #prefix>
              <span
                class="inline-block h-2 w-2 rounded-full"
                :style="{ backgroundColor: STATUS_DOT_COLORS[row.status] ?? '#909399' }"
              />
            </template>
            <el-option v-for="(label, value) in STATUS_LABELS" :key="value" :label="label" :value="value" />
          </el-select>
        </div>
        <div class="mt-1 text-sm text-taupe">{{ row.customer_name }}・{{ row.phone }}</div>
        <div class="text-sm text-taupe">
          {{ SHIPPING_LABELS[row.shipping_method] ?? row.shipping_method }}・預期 {{ row.expected_delivery_date }}
        </div>
        <div class="mt-1 flex items-center justify-between">
          <span class="font-medium text-terracotta-dark">NT$ {{ row.total_amount }}</span>
          <span class="text-xs text-taupe/60">{{ new Date(row.created_at).toLocaleString('zh-TW') }}</span>
        </div>

        <button
          type="button"
          class="mt-2 flex w-full items-center justify-between rounded-lg bg-cream/60 px-2 py-1.5 text-sm text-taupe"
          @click="toggleMobileExpand(row.id)"
        >
          訂購項目({{ row.items.length }})
          <span class="inline-block transition-transform" :class="mobileExpandedIds[row.id] ? 'rotate-90' : ''">›</span>
        </button>
        <div v-if="mobileExpandedIds[row.id]" class="mt-2 flex flex-col gap-2">
          <div
            v-for="item in row.items"
            :key="item.id"
            class="flex items-center gap-2 rounded border border-beige bg-cream/40 px-2 py-1.5"
          >
            <el-checkbox
              :model-value="item.is_completed"
              @click.prevent="toggleItemCompleted(row.id, item)"
            />
            <img
              v-if="item.product_thumbnail"
              :src="imageUrl(item.product_thumbnail)"
              class="h-10 w-10 flex-none rounded object-cover"
              :title="item.product_name_snapshot"
            />
            <img
              v-if="item.material_thumbnail"
              :src="imageUrl(item.material_thumbnail)"
              class="h-10 w-10 flex-none rounded object-cover"
              :title="item.material_name_snapshot"
            />
            <div class="text-sm" :class="{ 'text-taupe line-through': item.is_completed }">
              <div :class="item.is_completed ? '' : 'text-brown'">
                {{ item.product_name_snapshot }}<template v-if="item.variant_name_snapshot"> - {{ item.variant_name_snapshot }}</template>
              </div>
              <div class="text-taupe">
                <template v-if="item.material_name_snapshot">{{ item.material_name_snapshot }} × </template
                >{{ item.quantity }}
              </div>
            </div>
          </div>
          <div v-if="row.notes" class="rounded border border-amber-200 bg-amber-50 px-2 py-1.5 text-sm text-amber-800">
            <span class="font-medium">客人備註:</span>{{ row.notes }}
          </div>
        </div>

        <el-button size="small" class="mt-3 w-full" @click="router.push({ name: 'order-detail', params: { id: row.id } })">
          查看
        </el-button>
      </div>
    </div>

    <el-dialog v-model="mergeDialogVisible" title="合併訂單" width="500">
      <p class="mb-3 text-sm text-gray-600">
        選擇要保留的主訂單,另一張訂單的商品會併入主訂單,原訂單將被刪除(此操作無法復原)。
      </p>
      <el-radio-group v-model="primaryOrderId" class="flex w-full flex-col gap-2">
        <label
          v-for="o in selectedOrders"
          :key="o.id"
          class="flex cursor-pointer items-start gap-2 rounded-lg border border-gray-200 p-3 hover:border-terracotta"
        >
          <el-radio :value="o.id" class="mt-0.5" />
          <div>
            <div class="font-medium">{{ o.order_no }}(NT$ {{ o.total_amount }})</div>
            <div class="text-sm text-gray-500">
              {{ o.customer_name }}・{{ o.phone }}・{{ o.items.length }} 項商品
            </div>
          </div>
        </label>
      </el-radio-group>
      <template #footer>
        <el-button @click="mergeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="merging" @click="handleConfirmMerge">確認合併</el-button>
      </template>
    </el-dialog>
  </div>
</template>
