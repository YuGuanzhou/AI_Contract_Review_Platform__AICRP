<template>
  <div class="contract-detail">
    <div class="header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/user/contracts' }">我的合同</el-breadcrumb-item>
        <el-breadcrumb-item>合同详情</el-breadcrumb-item>
      </el-breadcrumb>
      <div class="header-actions">
        <el-button type="primary" @click="handleReview">开始审核</el-button>
        <el-button @click="handleDownload">下载合同</el-button>
        <el-button @click="handleBack">返回</el-button>
      </div>
    </div>

    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <h3>合同基本信息</h3>
          <el-tag :type="getStatusType(contract.status)">{{ getStatusText(contract.status) }}</el-tag>
        </div>
      </template>

      <div class="contract-info" v-loading="loading">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="info-item">
              <label>合同名称</label>
              <div class="value">{{ contract.title }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>合同编号</label>
              <div class="value">CONTRACT-{{ contract.id }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>上传时间</label>
              <div class="value">{{ contract.uploadTime }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>合同类型</label>
              <div class="value">{{ getContractTypeName(contract.contract_type) }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>上传用户</label>
              <div class="value">{{ contract.uploadUser }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>文件大小</label>
              <div class="value">{{ contract.fileSizeFormatted }}</div>
            </div>
          </el-col>
        </el-row>

        <div class="file-preview">
          <h4>合同文件预览</h4>
          <div v-if="contract.id" class="preview-container">
            <PdfPreviewSimpleFixed
              :pdf-url="pdfPreviewUrl"
              :initial-page="1"
              :auto-load="true"
              :with-credentials="true"
              @loaded="onPdfLoaded"
              @error="onPdfError"
            />
          </div>
          <div v-else class="preview-placeholder">
            <el-icon :size="60" color="#409EFF"><Document /></el-icon>
            <p>{{ contract.original_filename }}</p>
            <p class="hint">PDF 文件预览区域</p>
          </div>
        </div>

        <div class="ai-analysis">
          <h4>AI初步分析结果</h4>
          <div v-if="contract.risk_score !== null && contract.risk_score !== undefined" class="risk-overview">
            <el-tag :type="riskTagType(contract.risk_level)">风险等级：{{ riskLevelText(contract.risk_level) }}</el-tag>
            <span class="risk-score">AI风险评分：{{ contract.risk_score }}</span>
          </div>
          <el-card v-if="contract.review_summary" shadow="never" class="summary-card">
            <div v-html="contract.review_summary"></div>
          </el-card>
          <el-empty v-else description="暂无AI分析结果" :image-size="100" />
        </div>

        <div class="review-history" v-if="contract.reviews && contract.reviews.length > 0">
          <h4>审核记录</h4>
          <el-timeline>
            <el-timeline-item
              v-for="review in contract.reviews"
              :key="review.id"
              :timestamp="review.time"
              placement="top"
            >
              <el-card>
                <h4>{{ review.reviewer }} - {{ review.action }}</h4>
                <p>{{ review.comment }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document } from '@element-plus/icons-vue'
import PdfPreviewSimpleFixed from '@/components/PdfPreviewSimpleFixed.vue'
import { getContract } from '@/api/contract'
import { startReview } from '@/api/reviewer'
import type { Contract } from '@/api/contract'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

// 合同详情数据
const contract = ref<Contract & {
  // 前端额外字段
  uploadTime?: string
  uploadUser?: string
  fileSizeFormatted?: string
  aiAnalysis?: string
  reviews?: Array<{
    id: number
    reviewer: string
    action: string
    time: string
    comment: string
  }>
}>({
  id: 0,
  user_id: 0,
  title: '',
  description: '',
  contract_type: 'other',
  status: 'uploaded',
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
  // 前端计算字段
  uploadTime: '',
  uploadUser: 'AI',
  fileSizeFormatted: '0 B',
  aiAnalysis: '',
  reviews: []
})

// 加载状态
const loading = ref(false)

// PDF预览URL
const pdfPreviewUrl = computed(() => {
  if (!contract.value.id) return ''
  return `/api/contracts/${contract.value.id}/preview`
})

// 格式化文件大小
const formatFileSize = (bytes: number | null): string => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

// 格式化日期时间
const formatDateTime = (dateTime: string | null): string => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取合同类型中文名称
const getContractTypeName = (type: string): string => {
  const typeMap: Record<string, string> = {
    'purchase': '采购合同',
    'sales': '销售合同',
    'service': '服务合同',
    'employment': '雇佣合同',
    'lease': '租赁合同',
    'partnership': '合伙合同',
    'other': '其他合同'
  }
  return typeMap[type] || type
}

// 获取状态标签类型
const getStatusType = (status: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  const statusMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    'uploaded': 'info',
    'parsing': 'warning',
    'parsed': 'info',
    'ai_pending': 'warning',
    'manual_pending': 'warning',
    'reviewing': 'warning',
    'reviewed': 'success',
    'revised': 'info',
    'archived': 'info',
    'error': 'danger'
  }
  return statusMap[status] || 'info'
}

// 获取状态中文文本
const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'uploaded': '已上传',
    'parsing': '解析中',
    'parsed': '已解析',
    'ai_pending': '待AI审核',
    'manual_pending': '待人工审核',
    'reviewing': '审核中',
    'reviewed': '已审核',
    'revised': '已修订',
    'archived': '已归档',
    'error': '错误'
  }
  return statusMap[status] || status
}

// 风险等级 -> el-tag 类型（兼容中英文值）
const riskTagType = (level: string | null | undefined): 'danger' | 'warning' | 'success' | 'info' => {
  const l = (level || '').toLowerCase()
  if (l.includes('高') || l === 'high' || l === 'danger') return 'danger'
  if (l.includes('低') || l === 'low' || l === 'success') return 'success'
  if (l) return 'warning'
  return 'info'
}

// 风险等级中文文本
const riskLevelText = (level: string | null | undefined): string => {
  const map: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险',
    unknown: '未知',
  }
  return map[level || ''] || level || '未知'
}

// 获取合同详情
const fetchContractDetail = async () => {
  const id = route.params.id
  if (!id) return
  
  loading.value = true
  try {
    const contractData = await getContract(Number(id))
    
    // 更新合同数据
    contract.value = {
      ...contractData,
      // 计算前端字段
      uploadTime: formatDateTime(contractData.uploaded_at),
      uploadUser: `用户${contractData.user_id}`,
      fileSizeFormatted: formatFileSize(contractData.file_size),
      aiAnalysis: contractData.review_summary || '<p>暂无AI分析结果</p>',
      reviews: [] // 暂时留空，后续可以从审核记录API获取
    }
  } catch (error: any) {
    console.error('获取合同详情失败:', error)
    ElMessage.error('获取合同详情失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchContractDetail()
})

const handleReview = async () => {
  const contractId = Number(route.params.id)
  if (!contractId) {
    ElMessage.error('合同ID无效')
    return
  }
  try {
    ElMessage.info('正在启动AI审核，请稍候...')
    await startReview(contractId)
    ElMessage.success('AI审核已启动，正在跳转到审核页面')
    router.push(`/contracts/${contractId}/review`)
  } catch (error: any) {
    console.error('启动审核失败:', error)
    ElMessage.error(`启动审核失败: ${error.message || '未知错误'}`)
  }
}

const handleDownload = () => {
  // 下载逻辑
  if (contract.value.id) {
    window.open(`/api/contracts/${contract.value.id}/download`, '_blank')
  }
}

// PDF加载完成回调
const onPdfLoaded = (totalPages: number) => {
  console.log(`PDF加载完成，共${totalPages}页`)
}

// PDF加载错误回调
const onPdfError = (error: string) => {
  console.error('PDF加载失败:', error)
}

const handleBack = () => {
  router.push('/user/contracts')
}
</script>

<script lang="ts">
// 过滤器定义
export default {
  filters: {
    statusType(status: string) {
      const map: Record<string, string> = {
        pending: 'warning',
        reviewing: 'info',
        completed: 'success'
      }
      return map[status] || 'info'
    },
    statusText(status: string) {
      const map: Record<string, string> = {
        pending: '待审核',
        reviewing: '审核中',
        completed: '已完成'
      }
      return map[status] || '未知状态'
    }
  }
}
</script>

<style scoped lang="scss">
.contract-detail {
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .main-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }

  .contract-info {
    .info-item {
      margin-bottom: 20px;

      label {
        display: block;
        font-weight: bold;
        color: #606266;
        margin-bottom: 8px;
        font-size: 14px;
      }

      .value {
        font-size: 16px;
        color: #303133;
      }
    }

    .file-preview {
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #ebeef5;

      .preview-placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 300px;
        border: 2px dashed #dcdfe6;
        border-radius: 8px;
        background-color: #f5f7fa;
        margin-top: 15px;

        p {
          margin-top: 10px;
          color: #606266;

          &.hint {
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }

    .ai-analysis,
    .review-history {
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #ebeef5;

      h4 {
        margin-bottom: 15px;
        color: #303133;
      }
    }

    .ai-analysis {
      .risk-overview {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;

        .risk-score {
          font-size: 14px;
          color: #606266;
        }
      }

      .summary-card {
        margin-top: 12px;
      }
    }
  }
}
</style>