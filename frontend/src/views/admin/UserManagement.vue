<template>
  <div class="user-management">
    <div class="page-header">
      <h1>用户管理</h1>
      <p>管理系统用户账户，可以查看、编辑、禁用用户等操作</p>
    </div>

    <!-- 搜索和筛选区域 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="searchText"
          placeholder="搜索用户名、邮箱或姓名"
          clearable
          style="width: 300px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="filterRole" placeholder="角色" clearable @change="handleSearch">
          <el-option label="普通用户" value="user" />
          <el-option label="审核员" value="reviewer" />
          <el-option label="管理员" value="admin" />
        </el-select>
        <el-select v-model="filterActive" placeholder="激活状态" clearable @change="handleSearch">
          <el-option label="已激活" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>搜索
        </el-button>
        <el-button @click="resetFilters">
          <el-icon><Refresh /></el-icon>重置
        </el-button>
      </div>
    </el-card>

    <!-- 用户表格 -->
    <el-card shadow="never" class="table-card">
      <el-table
        :data="userList"
        v-loading="loading"
        style="width: 100%"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
      >
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column prop="username" label="用户名" width="150" sortable />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="full_name" label="姓名" width="150" />
        <el-table-column prop="company" label="公司" width="150" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)" size="small">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_verified" label="验证" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_verified ? 'success' : 'info'" size="small">
              {{ row.is_verified ? '已验证' : '未验证' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login ? formatDate(row.last_login) : '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button
              type="text"
              size="small"
              :class="row.is_active ? 'text-danger' : 'text-success'"
              @click="toggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-dropdown trigger="click" @command="(command) => handleRoleCommand(row, command)">
              <el-button type="text" size="small">角色<el-icon><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="user">设为普通用户</el-dropdown-item>
                  <el-dropdown-item command="reviewer">设为审核员</el-dropdown-item>
                  <el-dropdown-item command="admin">设为管理员</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑用户信息"
      width="500px"
      :before-close="handleEditDialogClose"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
        v-loading="editLoading"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="editForm.full_name" />
        </el-form-item>
        <el-form-item label="公司" prop="company">
          <el-input v-model="editForm.company" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" placeholder="请选择角色">
            <el-option label="普通用户" value="user" />
            <el-option label="审核员" value="reviewer" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="激活状态" prop="is_active">
          <el-switch v-model="editForm.is_active" />
        </el-form-item>
        <el-form-item label="验证状态" prop="is_verified">
          <el-switch v-model="editForm.is_verified" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEditForm" :loading="editLoading">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Search, Refresh, ArrowDown } from '@element-plus/icons-vue'
import { getUsers, updateUser } from '@/api/admin'
import type { ManagedUser } from '@/types/admin'

// 响应式数据
const loading = ref(false)
const userList = ref<ManagedUser[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchText = ref('')
const filterRole = ref('')
const filterActive = ref<boolean | null>(null)

// 编辑对话框相关
const editDialogVisible = ref(false)
const editLoading = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  id: 0,
  username: '',
  email: '',
  full_name: '',
  company: '',
  role: '' as 'user' | 'reviewer' | 'admin',
  is_active: true,
  is_verified: false,
})

const editRules: FormRules = {
  full_name: [{ required: false, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

// 方法
const fetchUserList = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchText.value || undefined,
      role: filterRole.value || undefined,
      is_active: filterActive.value !== null ? filterActive.value : undefined,
    }
    const response = await getUsers(params)
    userList.value = response.items
    total.value = response.total
  } catch (error) {
    ElMessage.error('获取用户列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchUserList()
}

const resetFilters = () => {
  searchText.value = ''
  filterRole.value = ''
  filterActive.value = null
  currentPage.value = 1
  fetchUserList()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchUserList()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchUserList()
}

const getRoleTagType = (role: string) => {
  switch (role) {
    case 'admin': return 'danger'
    case 'reviewer': return 'warning'
    default: return 'success'
  }
}

const getRoleText = (role: string) => {
  switch (role) {
    case 'admin': return '管理员'
    case 'reviewer': return '审核员'
    default: return '普通用户'
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 操作函数
const openEditDialog = (user: ManagedUser) => {
  editForm.id = user.id
  editForm.username = user.username
  editForm.email = user.email
  editForm.full_name = user.full_name || ''
  editForm.company = user.company || ''
  editForm.role = user.role
  editForm.is_active = user.is_active
  editForm.is_verified = user.is_verified
  editDialogVisible.value = true
}

const handleEditDialogClose = (done: () => void) => {
  ElMessageBox.confirm('确定关闭吗？未保存的修改将丢失。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      done()
    })
    .catch(() => {})
}

const submitEditForm = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    editLoading.value = true
    try {
      // 调用更新用户信息的API（假设存在）
      await updateUser(editForm.id, {
        full_name: editForm.full_name,
        company: editForm.company,
        role: editForm.role,
        is_active: editForm.is_active,
        is_verified: editForm.is_verified,
      })
      ElMessage.success('用户信息更新成功')
      editDialogVisible.value = false
      fetchUserList()
    } catch (error) {
      ElMessage.error('更新用户信息失败')
      console.error(error)
    } finally {
      editLoading.value = false
    }
  })
}

const toggleActive = async (user: ManagedUser) => {
  try {
    await ElMessageBox.confirm(
      `确定${user.is_active ? '禁用' : '启用'}用户 "${user.username}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    // 使用 updateUser API 切换激活状态
    await updateUser(user.id, { is_active: !user.is_active })
    ElMessage.success(`用户已${user.is_active ? '禁用' : '启用'}`)
    fetchUserList()
  } catch (error) {
    // 用户取消了操作
  }
}

const handleRoleCommand = async (user: ManagedUser, role: string) => {
  try {
    await ElMessageBox.confirm(
      `确定将用户 "${user.username}" 的角色改为 "${getRoleText(role)}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    // 使用 updateUser API 更新角色，确保角色类型正确
    await updateUser(user.id, { role: role as 'user' | 'reviewer' | 'admin' })
    ElMessage.success('角色更新成功')
    fetchUserList()
  } catch (error) {
    // 用户取消了操作
  }
}

// 生命周期
onMounted(() => {
  fetchUserList()
})
</script>

<style scoped lang="scss">
.user-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;

  h1 {
    font-size: 24px;
    margin-bottom: 8px;
    color: #303133;
  }

  p {
    color: #606266;
    margin: 0;
  }
}

.filter-card {
  margin-bottom: 20px;

  .filter-row {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }
}

.table-card {
  margin-bottom: 20px;

  .text-danger {
    color: #f56c6c;
  }

  .text-success {
    color: #67c23a;
  }
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.el-dropdown {
  margin-left: 8px;
}
</style>