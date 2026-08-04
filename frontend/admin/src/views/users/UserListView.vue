<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient } from '../../api/client'
import type { Role } from '../../types'

interface AdminUserListItem {
  id: number
  email: string
  full_name: string
  is_active: boolean
  roles: string[]
}

interface AdminUserDetail extends AdminUserListItem {
  role_ids: number[]
}

const users = ref<AdminUserListItem[]>([])
const roles = ref<Role[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = ref({
  email: '',
  password: '',
  full_name: '',
  is_active: true,
  role_ids: [] as number[],
})

async function loadData() {
  const [usersRes, rolesRes] = await Promise.all([
    apiClient.get<AdminUserListItem[]>('/api/v1/admin/users'),
    apiClient.get<Role[]>('/api/v1/admin/roles'),
  ])
  users.value = usersRes.data
  roles.value = rolesRes.data
}

function openCreate() {
  editingId.value = null
  form.value = { email: '', password: '', full_name: '', is_active: true, role_ids: [] }
  dialogVisible.value = true
}

async function openEdit(row: AdminUserListItem) {
  const { data } = await apiClient.get<AdminUserDetail>(`/api/v1/admin/users/${row.id}`)
  editingId.value = data.id
  form.value = {
    email: data.email,
    password: '',
    full_name: data.full_name,
    is_active: data.is_active,
    role_ids: data.role_ids,
  }
  dialogVisible.value = true
}

async function handleSave() {
  try {
    if (editingId.value === null) {
      await apiClient.post('/api/v1/admin/users', form.value)
      ElMessage.success('已建立後台人員')
    } else {
      const payload: Record<string, unknown> = {
        email: form.value.email,
        full_name: form.value.full_name,
        is_active: form.value.is_active,
        role_ids: form.value.role_ids,
      }
      if (form.value.password) payload.password = form.value.password
      await apiClient.put(`/api/v1/admin/users/${editingId.value}`, payload)
      ElMessage.success('已更新後台人員')
    }
    dialogVisible.value = false
    await loadData()
  } catch {
    ElMessage.error(editingId.value === null ? '建立失敗,請確認 Email 是否重複' : '更新失敗,請確認 Email 是否重複')
  }
}

async function handleDelete(row: AdminUserListItem) {
  try {
    await ElMessageBox.confirm(`確定要刪除「${row.full_name}」這個後台人員嗎?`, '刪除確認', {
      type: 'warning',
      confirmButtonText: '刪除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await apiClient.delete(`/api/v1/admin/users/${row.id}`)
    ElMessage.success('已刪除')
    await loadData()
  } catch (err: unknown) {
    const message =
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '刪除失敗'
    ElMessage.error(message)
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold">後台人員管理</h1>
      <el-button type="primary" @click="openCreate">新增人員</el-button>
    </div>

    <el-table :data="users" stripe class="hidden sm:block">
      <el-table-column prop="email" label="Email" />
      <el-table-column prop="full_name" label="姓名" />
      <el-table-column label="角色">
        <template #default="{ row }">
          <el-tag v-for="r in row.roles" :key="r" class="mr-1" size="small">{{ r }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="啟用" width="80">
        <template #default="{ row }">{{ row.is_active ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">編輯</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">刪除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="flex flex-col gap-3 sm:hidden">
      <div
        v-for="row in users"
        :key="row.id"
        class="rounded-xl border border-beige bg-white p-3 shadow-[0_2px_8px_rgba(180,140,110,0.08)]"
      >
        <div class="flex items-center justify-between gap-2">
          <span class="font-medium text-brown">{{ row.full_name }}</span>
          <span
            class="flex-none rounded-full px-2 py-0.5 text-xs"
            :class="row.is_active ? 'bg-sage/15 text-sage-dark' : 'bg-beige/60 text-taupe'"
          >
            {{ row.is_active ? '啟用' : '停用' }}
          </span>
        </div>
        <div class="mt-1 text-sm text-taupe">{{ row.email }}</div>
        <div class="mt-2 flex flex-wrap gap-1">
          <el-tag v-for="r in row.roles" :key="r" size="small">{{ r }}</el-tag>
        </div>
        <div class="mt-3 flex gap-2">
          <el-button size="small" class="flex-1" @click="openEdit(row)">編輯</el-button>
          <el-button size="small" type="danger" class="flex-1" @click="handleDelete(row)">刪除</el-button>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId === null ? '新增後台人員' : '編輯後台人員'"
      width="92%"
      class="sm:!w-[480px]"
    >
      <el-form label-position="top">
        <el-form-item label="Email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item :label="editingId === null ? '密碼' : '新密碼(留空則不變更)'">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.full_name" />
        </el-form-item>
        <el-form-item v-if="editingId !== null" label="啟用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_ids" multiple>
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
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
