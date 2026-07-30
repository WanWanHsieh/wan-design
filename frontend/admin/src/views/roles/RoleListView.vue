<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { apiClient } from '../../api/client'
import type { Permission, Role } from '../../types'

const roles = ref<Role[]>([])
const permissions = ref<Permission[]>([])
const dialogVisible = ref(false)
const editing = ref<Role | null>(null)
const form = ref({ name: '', description: '', permission_ids: [] as number[] })

async function loadData() {
  const [rolesRes, permissionsRes] = await Promise.all([
    apiClient.get<Role[]>('/api/v1/admin/roles'),
    apiClient.get<Permission[]>('/api/v1/admin/roles/permissions'),
  ])
  roles.value = rolesRes.data
  permissions.value = permissionsRes.data
}

function openCreate() {
  editing.value = null
  form.value = { name: '', description: '', permission_ids: [] }
  dialogVisible.value = true
}

function openEdit(role: Role) {
  editing.value = role
  form.value = {
    name: role.name,
    description: role.description ?? '',
    permission_ids: role.permissions.map((p) => p.id),
  }
  dialogVisible.value = true
}

async function handleSave() {
  try {
    if (editing.value) {
      await apiClient.put(`/api/v1/admin/roles/${editing.value.id}`, form.value)
    } else {
      await apiClient.post('/api/v1/admin/roles', form.value)
    }
    dialogVisible.value = false
    ElMessage.success('已儲存')
    await loadData()
  } catch {
    ElMessage.error('儲存失敗')
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-xl font-semibold">角色權限管理</h1>
      <el-button type="primary" @click="openCreate">新增角色</el-button>
    </div>

    <el-table :data="roles" stripe>
      <el-table-column prop="name" label="角色名稱" width="180" />
      <el-table-column prop="description" label="說明" />
      <el-table-column label="權限">
        <template #default="{ row }">
          <el-tag v-for="p in row.permissions" :key="p.id" class="mr-1 mb-1" size="small">
            {{ p.code }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">編輯</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '編輯角色' : '新增角色'">
      <el-form label-position="top">
        <el-form-item label="角色名稱">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="說明">
          <el-input v-model="form.description" />
        </el-form-item>
        <el-form-item label="權限">
          <el-checkbox-group v-model="form.permission_ids">
            <el-checkbox v-for="p in permissions" :key="p.id" :label="p.id">
              {{ p.code }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">儲存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
