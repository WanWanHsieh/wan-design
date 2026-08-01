<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient } from '../../api/client'
import { generateSlug } from '../../utils/codegen'
import type { Category, Product } from '../../types'

interface CategoryNode extends Category {
  children: CategoryNode[]
}

const categories = ref<Category[]>([])
const products = ref<Product[]>([])

function categoryPrices(categoryId: number): string {
  const prices = products.value.filter((p) => p.category_id === categoryId).map((p) => p.base_price)
  if (prices.length === 0) return '-'
  return prices.map((price) => `NT$ ${price}`).join('、')
}

const categoryTree = computed<CategoryNode[]>(() => {
  const nodes = categories.value.map((c) => ({ ...c, children: [] as CategoryNode[] }))
  const byId = new Map(nodes.map((n) => [n.id, n]))
  const roots: CategoryNode[] = []
  for (const node of nodes) {
    if (node.parent_id !== null && byId.has(node.parent_id)) {
      byId.get(node.parent_id)!.children.push(node)
    } else {
      roots.push(node)
    }
  }
  return roots
})

interface FlatCategoryRow {
  node: CategoryNode
  depth: number
}

const expandedIds = ref<Record<number, boolean>>({})

function toggleExpand(id: number) {
  expandedIds.value[id] = !expandedIds.value[id]
}

const flatCategoryRows = computed<FlatCategoryRow[]>(() => {
  const rows: FlatCategoryRow[] = []
  function visit(nodes: CategoryNode[], depth: number) {
    for (const node of nodes) {
      rows.push({ node, depth })
      if (node.children.length > 0 && expandedIds.value[node.id]) {
        visit(node.children, depth + 1)
      }
    }
  }
  visit(categoryTree.value, 0)
  return rows
})
const dialogVisible = ref(false)
const editing = ref<Category | null>(null)
const form = ref({ name: '', slug: '', description: '', parent_id: null as number | null, sort_order: 0 })

async function loadCategories() {
  const [categoriesRes, productsRes] = await Promise.all([
    apiClient.get<Category[]>('/api/v1/admin/categories'),
    apiClient.get<Product[]>('/api/v1/admin/products', { params: { track_stock: false } }),
  ])
  categories.value = categoriesRes.data
  products.value = productsRes.data
}

function regenerateSlug() {
  form.value.slug = generateSlug('cat')
}

function openCreate() {
  editing.value = null
  form.value = { name: '', slug: generateSlug('cat'), description: '', parent_id: null, sort_order: 0 }
  dialogVisible.value = true
}

function openEdit(category: Category) {
  editing.value = category
  form.value = {
    name: category.name,
    slug: category.slug,
    description: category.description ?? '',
    parent_id: category.parent_id,
    sort_order: category.sort_order,
  }
  dialogVisible.value = true
}

async function saveOnce() {
  if (editing.value) {
    await apiClient.put(`/api/v1/admin/categories/${editing.value.id}`, form.value)
  } else {
    await apiClient.post('/api/v1/admin/categories', { ...form.value, is_active: true })
  }
}

async function handleSave() {
  try {
    try {
      await saveOnce()
    } catch (err: any) {
      if (err?.response?.status === 409 && !editing.value) {
        regenerateSlug()
        await saveOnce()
      } else {
        throw err
      }
    }
    dialogVisible.value = false
    ElMessage.success('已儲存')
    await loadCategories()
  } catch {
    ElMessage.error('儲存失敗,請確認 Slug 是否重複')
  }
}

async function handleDelete(category: Category) {
  await ElMessageBox.confirm(`確定要刪除「${category.name}」嗎?`, '刪除分類', { type: 'warning' })
  await apiClient.delete(`/api/v1/admin/categories/${category.id}`)
  ElMessage.success('已刪除')
  await loadCategories()
}

onMounted(loadCategories)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold">分類管理</h1>
      <el-button type="primary" @click="openCreate">新增分類</el-button>
    </div>

    <el-table
      :data="categoryTree"
      row-key="id"
      default-expand-all
      :tree-props="{ children: 'children' }"
      stripe
      class="hidden sm:block"
    >
      <el-table-column prop="name" label="名稱" />
      <el-table-column label="價格" width="140">
        <template #default="{ row }">{{ categoryPrices(row.id) }}</template>
      </el-table-column>
      <el-table-column prop="slug" label="Slug" />
      <el-table-column prop="is_active" label="啟用" width="80">
        <template #default="{ row }">{{ row.is_active ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">編輯</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">刪除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="flex flex-col gap-3 sm:hidden">
      <div
        v-for="{ node, depth } in flatCategoryRows"
        :key="node.id"
        class="rounded-xl border border-beige bg-white p-3 shadow-[0_2px_8px_rgba(180,140,110,0.08)]"
        :style="{ marginLeft: `${depth * 16}px` }"
      >
        <div class="flex items-center justify-between gap-2">
          <button
            v-if="node.children.length > 0"
            type="button"
            class="flex items-center gap-1 font-medium text-brown"
            @click="toggleExpand(node.id)"
          >
            <span
              class="inline-block transition-transform"
              :class="expandedIds[node.id] ? 'rotate-90' : ''"
            >
              ›
            </span>
            {{ node.name }}
            <span class="text-xs text-taupe/60">({{ node.children.length }})</span>
          </button>
          <span v-else class="font-medium text-brown">{{ node.name }}</span>
          <span
            class="flex-none rounded-full px-2 py-0.5 text-xs"
            :class="node.is_active ? 'bg-sage/15 text-sage-dark' : 'bg-beige/60 text-taupe'"
          >
            {{ node.is_active ? '啟用' : '停用' }}
          </span>
        </div>
        <div class="mt-1 text-sm text-taupe">價格:{{ categoryPrices(node.id) }}</div>
        <div class="text-xs text-taupe/70">Slug:{{ node.slug }}</div>
        <div class="mt-3 flex gap-2">
          <el-button size="small" class="flex-1" @click="openEdit(node)">編輯</el-button>
          <el-button size="small" type="danger" class="flex-1" @click="handleDelete(node)">刪除</el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editing ? '編輯分類' : '新增分類'" width="92%" class="sm:!w-[480px]">
      <el-form label-position="top">
        <el-form-item label="名稱">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="Slug">
          <div class="flex w-full gap-2">
            <el-input v-model="form.slug" />
            <el-button @click="regenerateSlug">重新產生</el-button>
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="上層分類">
          <el-select v-model="form.parent_id" clearable>
            <el-option
              v-for="c in categories.filter((c) => c.id !== editing?.id)"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">儲存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
