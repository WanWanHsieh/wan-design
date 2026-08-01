<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { apiClient } from '../../api/client'
import type { Role } from '../../types'

interface AdminUserListItem {
  id: number
  email: string
  full_name: string
  is_active: boolean
  roles: string[]
}

const users = ref<AdminUserListItem[]>([])
const roles = ref<Role[]>([])
const dialogVisible = ref(false)
const form = ref({ email: '', password: '', full_name: '', role_ids: [] as number[] })

async function loadData() {
  const [usersRes, rolesRes] = await Promise.all([
    apiClient.get<AdminUserListItem[]>('/api/v1/admin/users'),
    apiClient.get<Role[]>('/api/v1/admin/roles'),
  ])
  users.value = usersRes.data
  roles.value = rolesRes.data
}

function openCreate() {
  form.value = { email: '', password: '', full_name: '', role_ids: [] }
  dialogVisible.value = true
}

async function handleSave() {
  try {
    await apiClient.post('/api/v1/admin/users', form.value)
    dialogVisible.value = false
    ElMessage.success('已建立後台人員')
    await loadData()
  } catch {
    ElMessage.error('建立失敗,請確認 Email 是否重複')
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
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="新增後台人員" width="92%" class="sm:!w-[480px]">
      <el-form label-position="top">
        <el-form-item label="Email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密碼">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.full_name" />
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
