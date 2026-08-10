<template>
  <div class="contract-management">
    <div class="page-header">
      <h1>合同管理</h1>
      <p>管理系统所有合同，支持筛选、查看详情等操作</p>
    </div>

    <!-- 搜索和筛选区域 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="searchText"
          placeholder="搜索合同标题"
          clearable
          style="width: 300px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="filterStatus" placeholder="状态" clearable @change="handleSearch">
          <el-option label="已上传" value="uploaded" />
          <el-option label="解析中" value="parsing" />
          <el-option label="已解析" value="parsed" />
          <el-option label="待AI审核" value="ai_pending" />
          <el-option label="AI审核完成" value="ai_reviewed" />
          <el-option label="待人工审核" value="manual_pending" />
          <el-option label="审核完毕" value="reviewed" />
          <el-option label="已归档" value="archived" />
          <el-option label="错误" value="error" />
        </el-select>
        <el-select v-model="filterContractType" placeholder="合同类型" clearable @change="handleSearch">
          <el-option label="采购合同" value="purchase" />
          <el-option label="销售合同" value="sales" />
          <el-option label="服务合同" value="service" />
          <el-option label="劳动合同" value="employment" />
          <el-option label="租赁合同" value="lease" />
          <el-option label="合作协议" value="partnership" />
          <el-option label="其他" value="other" />
        </el-select>
        <el-input
          v-model="filterUserId"
          placeholder="用户ID"
          clearable
          style="width: 120px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>搜索
        </el-button>
        <el-button @click="resetFilters">
          <el-icon><Refresh /></el-icon>重置
        </el-button>
      </div>
    </el-card>

    <!-- 合同表格 -->
    <el-card shadow="never" class="table-card">
      <el-table
        :data="contractList"
        v-loading="loading"
        style="width: 100%"
        :default-sort="{ prop: 'uploaded_at', order: 'descending' }"
      >
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column prop="title" label="标题" width="200" />
        <el-table-column prop="user_id" label="用户ID" width="100" />
        <el-table-column prop="contract_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getContractTypeTagType(row.contract_type)" size="small">
              {{ getContractTypeText(row.contract_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="130">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag
              v-if="row.risk_level"
              :type="row.risk_level === 'high' ? 'danger' : row.risk_level === 'medium' ? 'warning' : 'success'"
              size="small"
            >
              {{ row.risk_level === 'high' ? '高风险' : row.risk_level === 'medium' ? '中风险' : '低风险' }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_at" label="上传时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.uploaded_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="openDetail(row)">详情</el-button>
            <el-button type="text" size="small" @click="downloadContract(row.id)">下载</el-button>
            <el-button type="text" size="small" class="text-danger" @click="deleteContract(row.id)">删除</el-button>
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

    <!-- 合同详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="合同详情"
      width="800px"
      :before-close="handleDetailDialogClose"
    >
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="合同ID">{{ detailContract.id }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ detailContract.user_id }}</el-descriptions-item>
          <el-descriptions-item label="标题">{{ detailContract.title }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ detailContract.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="合同类型">{{ getContractTypeText(detailContract.contract_type) }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ getStatusText(detailContract.status) }}</el-descriptions-item>
          <el-descriptions-item label="风险等级">{{ detailContract.risk_level || '-' }}</el-descriptions-item>
          <el-descriptions-item label="风险评分">{{ detailContract.risk_score || '-' }}</el-descriptions-item>
          <el-descriptions-item label="文件大小">{{ formatFileSize(detailContract.file_size) }}</el-descriptions-item>
          <el-descriptions-item label="文件类型">{{ detailContract.file_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ formatDate(detailContract.uploaded_at) }}</el-descriptions-item>
          <el-descriptions-item label="解析时间">{{ formatDate(detailContract.parsed_at) }}</el-descriptions-item>
          <el-descriptions-item label="审核时间">{{ formatDate(detailContract.reviewed_at) }}</el-descriptions-item>
          <el-descriptions-item label="归档时间">{{ formatDate(detailContract.archived_at) }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="detailContract.review_summary" style="margin-top: 20px;">
          <h4>审核摘要</h4>
          <p>{{ detailContract.review_summary }}</p>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="goToContractDetail(detailContract.id)">查看完整详情</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getContracts, deleteContract as apiDeleteContract, downloadContract as apiDownloadContract } from '@/api/contract'
import type { Contract } from '@/api/contract'
import { useRouter } from 'vue-router'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const contractList = ref<Contract[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchText = ref('')
const filterStatus = ref('')
const filterContractType = ref('')
const filterUserId = ref('')

// 详情对话框相关
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const detailContract = reactive({
  id: 0,
  user_id: 0,
  title: '',
  description: '',
  contract_type: '',
  status: '',
  original_filename: '',
  file_path: '',
  file_size: 0,
  file_type: '',
  file_hash: '',
  parsed_text: '',
  parsed_json: null,
  page_count: 0,
  word_count: 0,
  risk_level: '',
  risk_score: 0,
  review_summary: '',
  uploaded_at: '',
  parsed_at: '',
  reviewed_at: '',
  archived_at: '',
})

// 获取合同列表
const fetchContractList = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const params: any = {
      skip,
      limit: pageSize.value,
    }
    if (searchText.value) params.search = searchText.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterContractType.value) params.contract_type = filterContractType.value
    if (filterUserId.value) {
      const userId = parseInt(filterUserId.value)
      if (!isNaN(userId)) params.user_id = userId
    }
    const response = await getContracts(
      params.skip,
      params.limit,
      params.status,
      params.contract_type,
      params.search,
      params.user_id
    )
    contractList.value = response.contracts
    total.value = response.total
  } catch (error) {
    ElMessage.error('获取合同列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchContractList()
}

const resetFilters = () => {
  searchText.value = ''
  filterStatus.value = ''
  filterContractType.value = ''
  filterUserId.value = ''
  currentPage.value = 1
  fetchContractList()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  fetchContractList()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchContractList()
}

// 工具函数
const getContractTypeTagType = (type: string) => {
  const map: Record<string, 'success' | 'primary' | 'warning' | 'danger' | 'info'> = {
    purchase: 'success',
    sales: 'primary',
    service: 'warning',
    employment: 'danger',
    lease: 'info',
    partnership: 'success',
    other: 'info',
  }
  return map[type] || 'info'
}

const getContractTypeText = (type: string) => {
  const map: Record<string, string> = {
    purchase: '采购合同',
    sales: '销售合同',
    service: '服务合同',
    employment: '劳动合同',
    lease: '租赁合同',
    partnership: '合作协议',
    other: '其他',
  }
  return map[type] || '未知'
}

const getStatusTagType = (status: string) => {
  const map: Record<string, 'success' | 'primary' | 'warning' | 'danger' | 'info'> = {
    uploaded: 'info',
    parsing: 'warning',
    parsed: 'success',
    ai_pending: 'warning',
    ai_reviewed: 'success',
    manual_pending: 'warning',
    reviewed: 'success',
    archived: 'info',
    error: 'danger',
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    uploaded: '已上传',
    parsing: '解析中',
    parsed: '已解析',
    ai_pending: '待AI审核',
    ai_reviewed: 'AI审核完成',
    manual_pending: '待人工审核',
    reviewed: '审核完毕',
    archived: '已归档',
    error: '错误',
  }
  return map[status] || '未知'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatFileSize = (bytes: number | null) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 操作函数
const openDetail = (contract: Contract) => {
  Object.assign(detailContract, contract)
  detailDialogVisible.value = true
}

const handleDetailDialogClose = (done: () => void) => {
  ElMessageBox.confirm('确定关闭吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => done())
    .catch(() => {})
}

const goToContractDetail = (id: number) => {
  router.push(`/contracts/${id}`)
  detailDialogVisible.value = false
}

const downloadContract = async (id: number) => {
  try {
    const blob = await apiDownloadContract(id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `contract_${id}.pdf`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('下载开始')
  } catch (error) {
    ElMessage.error('下载失败')
    console.error(error)
  }
}

const deleteContract = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定删除该合同吗？此操作不可恢复。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await apiDeleteContract(id)
    ElMessage.success('删除成功')
    fetchContractList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

onMounted(() => {
  fetchContractList()
})
</script>

<style scoped>
.contract-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 8px 0 0;
  color: #666;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.table-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.text-danger {
  color: #f56c6c;
}
</style>