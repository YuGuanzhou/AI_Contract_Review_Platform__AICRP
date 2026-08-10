<template>
  <div class="review-workstation">
    <div class="header">
      <h2>审核工作站</h2>
      <p class="subtitle">待审核合同列表，请及时处理</p>
    </div>

    <el-card class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="filterText"
          placeholder="搜索合同名称"
          clearable
          style="width: 300px"
          @clear="handleFilter"
          @keyup.enter="handleFilter"
        >
          <template #append>
            <el-button :icon="Search" @click="handleFilter" />
          </template>
        </el-input>
        <div class="filter-actions">
          <el-button type="primary" :icon="Refresh" @click="fetchData">刷新</el-button>
          <el-button :icon="Download" @click="exportData">导出</el-button>
        </div>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="contract_number" label="合同编号" width="120" />
        <el-table-column prop="contract_name" label="合同名称" min-width="200" />
        <el-table-column prop="uploader" label="上传人" width="120" />
        <el-table-column prop="uploader_company" label="所属公司" width="150" />
        <el-table-column prop="file_type" label="文件类型" width="100" />
        <el-table-column prop="risk_score" label="风险评分" width="100">
          <template #default="{ row }">
            <el-tag :type="getRiskTagType(row.risk_score)">
              {{ row.risk_score.toFixed(1) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ai_findings_count" label="AI发现数" width="100" />
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="waiting_hours" label="等待时长" width="100">
          <template #default="{ row }">
            {{ row.waiting_hours }} 小时
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="180">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="handleReview(row.id)"
            >
              审核
            </el-button>
            <el-button
              size="small"
              :icon="View"
              @click="handleViewDetail(row.id)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Download,
  Edit,
  View,
} from '@element-plus/icons-vue'
import { getPendingContracts } from '@/api/reviewer'
import type { PendingContract } from '@/types/reviewer'

const router = useRouter()

// 数据
const loading = ref(false)
const tableData = ref<PendingContract[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterText = ref('')
const selectedRows = ref<PendingContract[]>([])

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const res = await getPendingContracts({
      page: currentPage.value,
      page_size: pageSize.value,
      filter: filterText.value || undefined,
      sort_by: 'uploaded_at',
    })
    tableData.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error('获取数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 过滤
const handleFilter = () => {
  currentPage.value = 1
  fetchData()
}

// 分页
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchData()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchData()
}

// 选择
const handleSelectionChange = (val: PendingContract[]) => {
  selectedRows.value = val
}

// 审核合同
const handleReview = (contractId: number) => {
  router.push({
    name: 'ContractReview',
    params: { id: contractId },
  })
}

// 查看详情
const handleViewDetail = (contractId: number) => {
  router.push({
    name: 'ContractDetail',
    params: { id: contractId },
  })
}

// 导出数据
const exportData = () => {
  ElMessage.info('导出功能开发中')
}

// 工具函数
const getRiskTagType = (score: number) => {
  if (score >= 70) return 'danger'
  if (score >= 40) return 'warning'
  return 'success'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.review-workstation {
  padding: 20px;

  .header {
    margin-bottom: 24px;

    h2 {
      margin: 0;
      font-size: 24px;
      color: #303133;
    }

    .subtitle {
      margin: 8px 0 0;
      font-size: 14px;
      color: #909399;
    }
  }

  .filter-card {
    margin-bottom: 20px;

    .filter-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }

  .table-card {
    .pagination {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>