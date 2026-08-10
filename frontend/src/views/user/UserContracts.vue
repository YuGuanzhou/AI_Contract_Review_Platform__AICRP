<template>
  <div class="user-contracts">
    <div class="page-header">
      <h1>我的合同</h1>
      <p>查看和管理您上传的所有合同</p>
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
        <el-table-column prop="title" label="标题" width="200">
          <template #default="{ row }">
            <router-link :to="`/contracts/${row.id}`" class="contract-link">
              {{ row.title }}
            </router-link>
          </template>
        </el-table-column>
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
        <el-table-column prop="uploaded_at" label="上传时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.uploaded_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="viewDetail(row.id)">详情</el-button>
            <el-button type="text" size="small" @click="downloadContract(row.id)">下载</el-button>
            <el-popconfirm
              title="确定删除此合同吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDeleteContract(row.id)"
            >
              <template #reference>
                <el-button type="text" size="small" style="color: var(--el-color-danger)">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { getContracts, deleteContract } from '@/api/contract'
import { downloadContract as downloadContractApi } from '@/api/contract'

const router = useRouter()

// 响应式数据
const searchText = ref('')
const filterStatus = ref('')
const filterContractType = ref('')
const loading = ref(false)
const contractList = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 加载合同列表
const loadContracts = async () => {
  loading.value = true
  try {
    const response = await getContracts(
      (currentPage.value - 1) * pageSize.value,
      pageSize.value,
      filterStatus.value || undefined,
      filterContractType.value || undefined,
      searchText.value || undefined
    )
    contractList.value = response.contracts || []
    total.value = response.total || 0
  } catch (error) {
    ElMessage.error('加载合同列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadContracts()
}

// 重置筛选
const resetFilters = () => {
  searchText.value = ''
  filterStatus.value = ''
  filterContractType.value = ''
  currentPage.value = 1
  loadContracts()
}

// 分页
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadContracts()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadContracts()
}

// 查看详情
const viewDetail = (contractId: number) => {
  router.push(`/contracts/${contractId}`)
}

// 下载合同
const downloadContract = async (contractId: number) => {
  try {
    const blob = await downloadContractApi(contractId)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `contract_${contractId}.pdf`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
    console.error(error)
  }
}

// 删除合同
const handleDeleteContract = async (contractId: number) => {
  try {
    await deleteContract(contractId)
    ElMessage.success('删除成功')
    loadContracts()
  } catch (error) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 合同类型文本和标签类型
const getContractTypeText = (type: string) => {
  const map: Record<string, string> = {
    purchase: '采购合同',
    sales: '销售合同',
    service: '服务合同',
    employment: '劳动合同',
    lease: '租赁合同',
    partnership: '合作协议',
    other: '其他'
  }
  return map[type] || type
}

const getContractTypeTagType = (type: string) => {
  const map: Record<string, 'primary' | 'success' | 'info' | 'warning' | 'danger'> = {
    purchase: 'primary',
    sales: 'success',
    service: 'info',
    employment: 'warning',
    lease: 'danger',
    partnership: 'primary',
    other: 'info'
  }
  return map[type] || 'info'
}

// 状态文本和标签类型
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
    error: '错误'
  }
  return map[status] || status
}

const getStatusTagType = (status: string) => {
  const map: Record<string, 'success' | 'primary' | 'warning' | 'danger' | 'info'> = {
    uploaded: 'info',
    parsing: 'warning',
    parsed: 'primary',
    ai_pending: 'warning',
    ai_reviewed: 'success',
    manual_pending: 'warning',
    reviewed: 'success',
    archived: 'info',
    error: 'danger'
  }
  return map[status] || 'info'
}

// 生命周期
onMounted(() => {
  loadContracts()
})
</script>

<style scoped lang="scss">
.user-contracts {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;

  .page-header {
    margin-bottom: 24px;

    h1 {
      margin: 0 0 8px;
      font-size: 28px;
      font-weight: 600;
    }

    p {
      color: var(--el-text-color-secondary);
      font-size: 16px;
    }
  }

  .filter-card {
    margin-bottom: 20px;

    .filter-row {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
  }

  .table-card {
    .contract-link {
      color: var(--el-color-primary);
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }
    }

    .pagination-wrapper {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>