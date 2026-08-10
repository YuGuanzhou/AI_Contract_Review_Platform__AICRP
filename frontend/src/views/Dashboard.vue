<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>仪表板</h1>
      <p>欢迎使用智能合同审查平台</p>
      <div class="header-actions">
        <el-button type="primary" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button @click="handleQuickUpload">
          <el-icon><Upload /></el-icon>
          快速上传合同
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stat-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>总合同数</span>
            <el-icon><Document /></el-icon>
          </div>
        </template>
        <div class="card-content">
          <h2>{{ dashboardData.summary?.total_contracts || 0 }}</h2>
          <p>个合同</p>
          <div class="card-trend">
            <span class="trend-text">较上月 +12%</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>已审核合同</span>
            <el-icon><Checked /></el-icon>
          </div>
        </template>
        <div class="card-content">
          <h2>{{ dashboardData.summary?.total_reviews || 0 }}</h2>
          <p>个审核记录</p>
          <div class="card-trend">
            <span class="trend-text">AI审核: {{ dashboardData.review_stats?.ai_reviews || 0 }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>平均风险分</span>
            <el-icon><Warning /></el-icon>
          </div>
        </template>
        <div class="card-content">
          <h2 :class="getRiskScoreClass(dashboardData.summary?.avg_risk_score || 0)">
            {{ dashboardData.summary?.avg_risk_score?.toFixed(1) || '0.0' }}
          </h2>
          <p>风险评分</p>
          <div class="card-trend">
            <span class="trend-text">高风险合同: {{ dashboardData.summary?.high_risk_count || 0 }}个</span>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>活跃状态</span>
            <el-icon><User /></el-icon>
          </div>
        </template>
        <div class="card-content">
          <h2>{{ recentActivities.length }}</h2>
          <p>最近活动</p>
          <div class="card-trend">
            <span class="trend-text">今日上传: {{ todayUploads }}个</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 图表和表格区域 -->
    <div class="dashboard-content">
      <!-- 风险分布 -->
      <el-card class="chart-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>风险分布</span>
            <el-select v-model="riskChartType" size="small" style="width: 120px">
              <el-option label="饼图" value="pie" />
              <el-option label="柱状图" value="bar" />
            </el-select>
          </div>
        </template>
        <div class="chart-container">
          <div v-if="riskDistribution.length === 0" class="empty-chart">
            <el-empty description="暂无风险数据" />
          </div>
          <div v-else class="risk-distribution">
            <div class="risk-items">
              <div v-for="item in riskDistribution" :key="item.risk_level" class="risk-item">
                <div class="risk-level" :class="`risk-${item.risk_level}`">
                  {{ getRiskLevelText(item.risk_level) }}
                </div>
                <div class="risk-count">{{ item.count }}个</div>
                <div class="risk-progress">
                  <el-progress
                    :percentage="getRiskPercentage(item)"
                    :color="getRiskColor(item.risk_level)"
                    :show-text="false"
                  />
                </div>
                <div class="risk-score">平均 {{ item.avg_score.toFixed(1) }}分</div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 最近活动 -->
      <el-card class="activity-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>最近活动</span>
            <el-button type="text" @click="viewAllActivities">查看全部</el-button>
          </div>
        </template>
        <div class="activity-list">
          <el-timeline v-if="recentActivities.length > 0">
            <el-timeline-item
              v-for="activity in recentActivities"
              :key="activity.id"
              :timestamp="formatTime(activity.timestamp)"
              placement="top"
              :type="getActivityType(activity.action)"
            >
              <el-card shadow="hover">
                <h4>{{ activity.title }}</h4>
                <p>{{ getActivityDescription(activity) }}</p>
                <div class="activity-footer">
                  <el-tag size="small" :type="getStatusTagType(activity.status)">
                    {{ getStatusText(activity.status) }}
                  </el-tag>
                  <el-tag v-if="activity.risk_level" size="small" :type="getRiskTagType(activity.risk_level)">
                    {{ getRiskLevelText(activity.risk_level) }}
                  </el-tag>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无活动记录" />
        </div>
      </el-card>

      <!-- 高风险合同 -->
      <el-card class="high-risk-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>高风险合同</span>
            <el-button type="text" @click="viewHighRiskContracts">处理高风险</el-button>
          </div>
        </template>
        <div class="high-risk-list">
          <el-table :data="dashboardData.high_risk_contracts || []" style="width: 100%">
            <el-table-column prop="title" label="合同标题" width="200">
              <template #default="{ row }">
                <router-link :to="`/contracts/${row.id}`" class="contract-link">
                  {{ row.title }}
                </router-link>
              </template>
            </el-table-column>
            <el-table-column prop="risk_score" label="风险评分" width="120">
              <template #default="{ row }">
                <el-tag :type="getRiskTagType(row.risk_level)" size="small">
                  {{ row.risk_score.toFixed(1) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="risk_level" label="风险等级" width="100">
              <template #default="{ row }">
                <el-tag :type="getRiskTagType(row.risk_level)" size="small">
                  {{ getRiskLevelText(row.risk_level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="uploaded_at" label="上传时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.uploaded_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="text" size="small" @click="reviewContract(row.id)">
                  立即审核
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!dashboardData.high_risk_contracts?.length" class="empty-table">
            <el-empty description="暂无高风险合同" />
          </div>
        </div>
      </el-card>

      <!-- 合同状态分布 -->
      <el-card class="status-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>合同状态分布</span>
          </div>
        </template>
        <div class="status-distribution">
          <div v-for="(count, status) in dashboardData.status_distribution || {}"
               :key="status"
               class="status-item">
            <div class="status-label">{{ getStatusText(status) }}</div>
            <div class="status-count">{{ count }}</div>
            <el-progress
              :percentage="getStatusPercentage(status, count)"
              :color="getStatusColor(status)"
            />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Upload,
  Document,
  Checked,
  Warning,
  User
} from '@element-plus/icons-vue'
import { getDashboardStats, getUserStats } from '@/api/dashboard'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const dashboardData = ref<any>({})
const userStats = ref<any>({})
const riskChartType = ref('pie')

// 计算属性
const recentActivities = computed(() => {
  return userStats.value.recent_activities || []
})

const riskDistribution = computed(() => {
  return dashboardData.value.risk_distribution || []
})

const todayUploads = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return recentActivities.value.filter((activity: any) =>
    activity.action === 'uploaded' &&
    activity.timestamp?.startsWith(today)
  ).length
})

// 将后端状态映射为前端状态
const mapBackendStatusToFrontend = (backendStatus: string): string => {
  const statusMap: Record<string, string> = {
    'uploaded': 'pending',
    'parsing': 'pending',
    'parsed': 'pending',
    'ai_pending': 'pending',
    'ai_reviewed': 'reviewing',
    'manual_pending': 'reviewing',
    'reviewed': 'approved',
    'revised': 'revision',
    'archived': 'approved',
    'error': 'rejected'
  }
  return statusMap[backendStatus] || 'pending'
}

// 分组后的状态分布
const groupedStatusDistribution = computed(() => {
  const raw = dashboardData.value.status_distribution || {}
  const grouped: Record<string, number> = {}
  for (const [status, count] of Object.entries(raw)) {
    const frontendStatus = mapBackendStatusToFrontend(status)
    grouped[frontendStatus] = (grouped[frontendStatus] || 0) + (count as number)
  }
  return grouped
})

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchDashboardData(),
      fetchUserStats()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const fetchDashboardData = async () => {
  try {
    const response = await getDashboardStats()
    dashboardData.value = response
  } catch (error) {
    console.error('获取仪表板数据失败:', error)
  }
}

const fetchUserStats = async () => {
  try {
    const response = await getUserStats()
    userStats.value = response
  } catch (error) {
    console.error('获取用户统计失败:', error)
  }
}

const handleQuickUpload = () => {
  router.push('/contracts/upload')
}

const viewAllActivities = () => {
  router.push('/user/contracts')
}

const viewHighRiskContracts = () => {
  router.push('/user/contracts?risk_level=high')
}

const reviewContract = (contractId: number) => {
  router.push(`/contracts/${contractId}/review`)
}

const getRiskScoreClass = (score: number) => {
  if (score >= 70) return 'high-risk'
  if (score >= 30) return 'medium-risk'
  return 'low-risk'
}

const getRiskLevelText = (level: string) => {
  const map: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险',
    unknown: '未知'
  }
  return map[level] || level
}

const getRiskPercentage = (item: any) => {
  const total = riskDistribution.value.reduce((sum: number, i: any) => sum + i.count, 0)
  return total > 0 ? Math.round((item.count / total) * 100) : 0
}

const getRiskColor = (level: string) => {
  const colors: Record<string, string> = {
    high: '#f56c6c',
    medium: '#e6a23c',
    low: '#67c23a',
    unknown: '#909399'
  }
  return colors[level] || '#909399'
}

const getRiskTagType = (level: string) => {
  const types: Record<string, string> = {
    high: 'danger',
    medium: 'warning',
    low: 'success',
    unknown: 'info'
  }
  return types[level] || 'info'
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getActivityType = (action: string) => {
  const types: Record<string, string> = {
    uploaded: 'primary',
    parsed: 'success',
    reviewed: 'warning',
    updated: 'info'
  }
  return types[action] || 'info'
}

const getActivityDescription = (activity: any) => {
  const actions: Record<string, string> = {
    uploaded: '上传了合同',
    parsed: '完成了合同解析',
    reviewed: '完成了合同审核',
    updated: '更新了合同信息'
  }
  return `${actions[activity.action] || '操作了合同'}`
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    // 原始状态
    uploaded: '已上传',
    parsing: '解析中',
    parsed: '已解析',
    ai_pending: '待AI审核',
    ai_reviewed: 'AI审核完成',
    manual_pending: '待人工审核',
    reviewed: '审核完毕',
    archived: '已归档',
    error: '错误',
    // 前端聚合状态
    pending: '待审核',
    reviewing: '审核中',
    approved: '已通过',
    revision: '需修改',
    rejected: '已拒绝'
  }
  return map[status] || status
}

const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    // 原始状态
    uploaded: 'info',
    parsing: 'warning',
    parsed: 'success',
    ai_pending: 'warning',
    ai_reviewed: 'success',
    manual_pending: 'warning',
    reviewed: 'success',
    archived: 'info',
    error: 'danger',
    // 前端聚合状态
    pending: 'info',
    reviewing: 'warning',
    approved: 'success',
    revision: 'warning',
    rejected: 'danger'
  }
  return types[status] || 'info'
}

const getStatusPercentage = (status: string, count: number) => {
  const total = Object.values(dashboardData.value.status_distribution || {}).reduce((sum: number, val: any) => sum + val, 0)
  return total > 0 ? Math.round((count / total) * 100) : 0
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    // 原始状态
    uploaded: '#409eff',
    parsing: '#e6a23c',
    parsed: '#67c23a',
    ai_pending: '#e6a23c',
    ai_reviewed: '#67c23a',
    manual_pending: '#e6a23c',
    reviewed: '#67c23a',
    archived: '#909399',
    error: '#f56c6c',
    // 前端聚合状态
    pending: '#409eff',
    reviewing: '#e6a23c',
    approved: '#67c23a',
    revision: '#e6a23c',
    rejected: '#f56c6c'
  }
  return colors[status] || '#909399'
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped lang="scss">
.dashboard {
  padding: 20px;
}

.dashboard-header {
  margin-bottom: 24px;
  
  h1 {
    font-size: 24px;
    margin-bottom: 8px;
    color: #303133;
  }

  p {
    color: #606266;
    margin-bottom: 16px;
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    span {
      font-weight: 500;
      color: #409eff;
    }

    .el-icon {
      color: #909399;
      font-size: 18px;
    }
  }

  .card-content {
    h2 {
      font-size: 36px;
      margin: 12px 0 8px;
      color: #303133;
      
      &.high-risk {
        color: #f56c6c;
      }
      
      &.medium-risk {
        color: #e6a23c;
      }
      
      &.low-risk {
        color: #67c23a;
      }
    }

    p {
      color: #909399;
      margin: 0 0 8px;
      font-size: 14px;
    }

    .card-trend {
      .trend-text {
        font-size: 12px;
        color: #67c23a;
      }
    }
  }
}

.dashboard-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 20px;
  
  .chart-card,
  .activity-card,
  .high-risk-card,
  .status-card {
    height: 100%;
  }
  
  .chart-card {
    grid-column: 1;
    grid-row: 1;
  }
  
  .activity-card {
    grid-column: 2;
    grid-row: 1;
    max-height: 400px;
    overflow-y: auto;
  }
  
  .high-risk-card {
    grid-column: 1;
    grid-row: 2;
  }
  
  .status-card {
    grid-column: 2;
    grid-row: 2;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 0 12px;
  border-bottom: 1px solid #ebeef5;
  
  span {
    font-weight: 500;
    color: #303133;
  }
}

.chart-container {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .empty-chart {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.risk-distribution {
  width: 100%;
  
  .risk-items {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .risk-item {
    display: grid;
    grid-template-columns: 80px 80px 1fr 100px;
    align-items: center;
    gap: 12px;
    
    .risk-level {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 500;
      text-align: center;
      
      &.risk-high {
        background-color: #fef0f0;
        color: #f56c6c;
      }
      
      &.risk-medium {
        background-color: #fdf6ec;
        color: #e6a23c;
      }
      
      &.risk-low {
        background-color: #f0f9eb;
        color: #67c23a;
      }
      
      &.risk-unknown {
        background-color: #f4f4f5;
        color: #909399;
      }
    }
    
    .risk-count {
      font-weight: 500;
      color: #303133;
    }
    
    .risk-progress {
      flex: 1;
    }
    
    .risk-score {
      font-size: 12px;
      color: #909399;
      text-align: right;
    }
  }
}

.activity-list {
  .el-timeline {
    padding-left: 0;
    
    .el-timeline-item {
      padding-bottom: 16px;
      
      &:last-child {
        padding-bottom: 0;
      }
    }
    
    .el-card {
      margin: 0;
      
      h4 {
        margin: 0 0 8px;
        font-size: 14px;
        color: #303133;
      }
      
      p {
        margin: 0 0 12px;
        font-size: 12px;
        color: #606266;
      }
      
      .activity-footer {
        display: flex;
        gap: 8px;
      }
    }
  }
}

.high-risk-list {
  .contract-link {
    color: #409eff;
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
  
  .empty-table {
    padding: 40px 0;
  }
}

.status-distribution {
  .status-item {
    margin-bottom: 16px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .status-label {
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
      font-size: 14px;
      color: #606266;
    }
    
    .status-count {
      font-weight: 500;
      color: #303133;
    }
  }
}

@media (max-width: 1200px) {
  .dashboard-content {
    grid-template-columns: 1fr;
    
    .chart-card {
      grid-column: 1;
      grid-row: 1;
    }
    
    .activity-card {
      grid-column: 1;
      grid-row: 2;
    }
    
    .high-risk-card {
      grid-column: 1;
      grid-row: 3;
    }
    
    .status-card {
      grid-column: 1;
      grid-row: 4;
    }
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .risk-item {
    grid-template-columns: 1fr;
    gap: 8px !important;
    
    .risk-progress {
      grid-column: 1;
    }
    
    .risk-score {
      text-align: left !important;
    }
  }
}
</style>