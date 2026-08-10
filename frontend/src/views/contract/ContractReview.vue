<template>
  <div class="contract-review">
    <div class="header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/user/contracts' }">我的合同</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: `/contracts/${contractId}` }">合同详情</el-breadcrumb-item>
        <el-breadcrumb-item>合同审核</el-breadcrumb-item>
      </el-breadcrumb>
      <div class="header-actions">
        <el-button v-if="isReviewer && !hasAiReview" type="primary" :loading="aiLoading" @click="handleTriggerAiReview">触发AI审核</el-button>
        <el-button v-if="isReviewer && hasAiReview" type="text" :loading="aiLoading" @click="handleTriggerAiReview">重新AI审核</el-button>
        <el-button type="primary" @click="handleSubmitReview" :loading="submitting" v-if="isReviewer">提交审核</el-button>
        <el-button @click="handleSaveDraft">保存草稿</el-button>
        <el-button @click="handleBack">返回</el-button>
      </div>
    </div>

    <div class="review-container">
      <div class="layout-toggle">
        <el-radio-group v-model="layoutMode" size="small">
          <el-radio-button label="horizontal">左右布局</el-radio-button>
          <el-radio-button label="vertical">上下布局</el-radio-button>
          <el-radio-button label="previewOnly">仅预览</el-radio-button>
        </el-radio-group>
      </div>

      <div class="main-content" :class="layoutMode" v-loading="loading">
        <div class="preview-section">
          <el-card class="contract-preview-card">
            <template #header>
              <div class="card-header">
                <h3>合同预览 - {{ contract.title || '未命名合同' }}</h3>
                <div class="card-actions">
                  <el-button type="text" @click="toggleFullscreen" title="全屏预览">
                    <el-icon><FullScreen /></el-icon>
                    全屏
                  </el-button>
                  <el-button type="text" @click="toggleLayout" title="切换布局">
                    <el-icon><Switch /></el-icon>
                    布局
                  </el-button>
                </div>
              </div>
            </template>
            <div class="preview-content">
              <div v-if="contractId" class="pdf-viewer-container">
                <PdfPreview
                  :pdf-url="pdfPreviewUrl"
                  :initial-page="currentPage"
                  :auto-load="true"
                  :with-credentials="true"
                  @loaded="onPdfLoaded"
                  @error="onPdfError"
                  @page-change="onPageChange"
                  ref="pdfViewerRef"
                />
              </div>
              <div v-else class="pdf-viewer-placeholder">
                <el-icon :size="80" color="#409EFF"><Document /></el-icon>
                <p>PDF 预览区域</p>
                <p class="file-info">文件：{{ contract.original_filename }}</p>
                <p class="file-tip">请上传或选择合同文件进行预览</p>
              </div>
            </div>
            <div class="preview-footer" v-if="contractId">
              <div class="page-navigation">
                <el-button :icon="ArrowLeft" @click="prevPage" :disabled="currentPage <= 1" size="small">上一页</el-button>
                <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
                <el-button @click="nextPage" :disabled="currentPage >= totalPages" size="small">下一页 <el-icon><ArrowRight /></el-icon></el-button>
              </div>
              <div class="file-info-footer">
                <el-tag size="small" type="info">{{ contract.original_filename }}</el-tag>
                <el-tag size="small" type="success">{{ totalPages }} 页</el-tag>
              </div>
            </div>
          </el-card>
        </div>

        <div class="review-section" v-if="layoutMode !== 'previewOnly'">
          <el-card class="review-form-card">
            <template #header>
              <h3>审核意见</h3>
              <el-button type="text" @click="toggleReviewSection" class="collapse-review">
                <el-icon><Fold /></el-icon>
              </el-button>
            </template>
            <div class="review-form">
              <el-form :model="reviewForm" label-width="90px">
                <el-form-item label="审核结果">
                  <el-radio-group v-model="reviewForm.result">
                    <el-radio label="approved">通过</el-radio>
                    <el-radio label="rejected">拒绝</el-radio>
                    <el-radio label="needs_revision">需要修改</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="风险等级">
                  <el-select v-model="reviewForm.riskLevel" placeholder="选择风险等级">
                    <el-option label="低风险" value="low" />
                    <el-option label="中风险" value="medium" />
                    <el-option label="高风险" value="high" />
                  </el-select>
                </el-form-item>
                <el-form-item label="重点条款">
                  <el-input
                    v-model="reviewForm.keyClauses"
                    type="textarea"
                    :rows="3"
                    placeholder="请标注需要重点关注的合同条款"
                  />
                </el-form-item>
                <el-form-item label="审核意见">
                  <el-input
                    v-model="reviewForm.comments"
                    type="textarea"
                    :rows="6"
                    placeholder="请详细说明审核意见，包括存在的问题、修改建议等"
                  />
                </el-form-item>
                <el-form-item label="附件">
                  <el-upload
                    class="upload-demo"
                    action="#"
                    :on-change="handleFileChange"
                    :auto-upload="false"
                    :file-list="fileList"
                    :limit="3"
                  >
                    <el-button type="primary" :icon="Upload">上传附件</el-button>
                    <template #tip>
                      <div class="el-upload__tip">支持上传PDF、Word、图片等格式，最多3个文件</div>
                    </template>
                  </el-upload>
                </el-form-item>
                <el-form-item label="AI建议">
                  <el-card shadow="never" class="ai-suggestion">
                    <p v-for="(suggestion, index) in aiSuggestions" :key="index">{{ index + 1 }}. {{ suggestion }}</p>
                    <el-empty v-if="!aiSuggestions.length" description="暂无AI建议" :image-size="40" />
                  </el-card>
                </el-form-item>
              </el-form>
            </div>
          </el-card>

          <el-card class="ai-analysis-card">
            <template #header>
              <h3>AI智能分析报告</h3>
            </template>
            <div class="ai-analysis-content">
              <!-- 风险概览 -->
              <div class="risk-overview">
                <el-progress
                  type="dashboard"
                  :percentage="reviewDetails.risk_score || 0"
                  :color="getProgressColor(reviewDetails.risk_score || 0)"
                >
                  <template #default>
                    <span class="risk-score-text">{{ reviewDetails.risk_score || 0 }}</span>
                  </template>
                </el-progress>
                <div class="risk-overview-info">
                  <el-tag :type="riskTagType(reviewDetails.risk_level)" size="large">
                    {{ riskLevelText(reviewDetails.risk_level) }}
                  </el-tag>
                  <p class="review-summary">{{ reviewDetails.review_summary || '暂无AI审核摘要' }}</p>
                </div>
              </div>

              <!-- 无 AI 审核结果时的空态 -->
              <el-empty v-if="!hasAiReview" description="该合同尚未进行AI审核">
                <el-button type="primary" :loading="aiLoading" @click="handleTriggerAiReview">触发 AI 审核</el-button>
              </el-empty>

              <el-collapse v-else v-model="activeAnalysisPanels">
                <el-collapse-item v-if="basicInfoEntries.length" title="合同基本信息" name="basic_info">
                  <el-descriptions :column="1" border>
                    <el-descriptions-item v-for="[key, value] in basicInfoEntries" :key="key" :label="key">
                      {{ value }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-collapse-item>
                <el-collapse-item v-if="keyClauseEntries.length" title="关键条款分析" name="key_clauses">
                  <el-descriptions :column="1" border>
                    <el-descriptions-item v-for="[key, value] in keyClauseEntries" :key="key" :label="key">
                      {{ value }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-collapse-item>
                <el-collapse-item v-if="riskPoints.length" title="具体风险点" name="risks">
                  <div v-for="(risk, index) in riskPoints" :key="index" class="risk-item">
                    <div class="risk-item-header">
                      <el-tag :type="riskTagType(risk['风险等级'] || risk.risk_level)" size="small">
                        {{ riskLevelText(risk['风险等级'] || risk.risk_level) }}
                      </el-tag>
                      <span class="risk-position">{{ risk['条款位置'] || risk.clause_location || risk.clause_reference || risk.clause || `风险点 ${index + 1}` }}</span>
                    </div>
                    <p class="risk-desc">{{ risk['风险描述'] || risk.risk_description || risk.description }}</p>
                    <p class="risk-suggestion" v-if="risk['修改建议'] || risk.modification_suggestion || risk.suggestion">
                      <span class="suggestion-label">修改建议：</span>{{ risk['修改建议'] || risk.modification_suggestion || risk.suggestion }}
                    </p>
                  </div>
                </el-collapse-item>
                <el-collapse-item v-if="overallEvalEntries.length" title="总体评价" name="overall">
                  <el-descriptions :column="1" border>
                    <el-descriptions-item v-for="[key, value] in overallEvalEntries" :key="key" :label="key">
                      {{ value }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-collapse-item>
                <el-collapse-item v-if="modificationGroups.length" title="修改建议" name="suggestions">
                  <div v-for="[group, items] in modificationGroups" :key="group" class="suggestion-group">
                    <h4 class="suggestion-group-title">{{ group }}</h4>
                    <ul v-if="Array.isArray(items) && items.length">
                      <li v-for="(item, idx) in items" :key="idx">{{ item }}</li>
                    </ul>
                    <p v-else class="suggestion-empty">无</p>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document, FullScreen, ArrowLeft, ArrowRight, Upload, Switch, Fold } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'
import PdfPreview from '@/components/PdfPreview.vue'
import { useUserStore } from '@/stores/user'
import {
  getContract,
  getContractReviewDetails,
  triggerAiReview,
  submitContractReview,
  type Contract,
  type ContractReviewDetails,
  type SubmitReviewPayload
} from '@/api/contract'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const contractId = ref('')
const currentPage = ref(1)
const totalPages = ref(0)
const loading = ref(false)
const submitting = ref(false)
const aiLoading = ref(false)
const activeAnalysisPanels = ref(['basic_info', 'key_clauses', 'risks', 'overall', 'suggestions'])
const pdfViewerRef = ref<InstanceType<typeof PdfPreview>>()
const layoutMode = ref('horizontal') // horizontal, vertical, previewOnly
const isReviewer = computed(() => ['reviewer', 'admin'].includes(userStore.userRole))
const reviewSectionVisible = ref(true)

const contract = ref<Contract>({
  id: 0,
  user_id: 0,
  title: '',
  description: null,
  contract_type: '',
  status: '',
  original_filename: '',
  file_path: null,
  file_size: null,
  file_type: null,
  file_hash: null,
  parsed_text: null,
  parsed_json: null,
  page_count: null,
  word_count: null,
  risk_level: null,
  risk_score: null,
  review_summary: null,
  uploaded_at: '',
  parsed_at: null,
  reviewed_at: null,
  archived_at: null,
})

const reviewDetails = ref<ContractReviewDetails>({
  success: false,
  contract_id: 0,
  status: '',
  risk_score: 0,
  risk_level: '',
  review_summary: null,
  has_ai_review: false,
  ai_review_result: null,
  risk_points: [],
  suggestions: null,
  reviewed_at: null,
})

const reviewForm = ref({
  result: 'approved',
  riskLevel: 'medium',
  keyClauses: '',
  comments: '',
  attachments: [] as string[]
})

const fileList = ref<UploadFile[]>([])

// PDF预览URL
const pdfPreviewUrl = computed(() => {
  if (!contractId.value) return ''
  return `/api/contracts/${contractId.value}/preview`
})

// AI 审核结果
const aiReviewResult = computed<any>(() => reviewDetails.value?.ai_review_result || {})
const hasAiReview = computed(() => !!reviewDetails.value?.has_ai_review)

// 动态渲染的各区块数据（兼容中英文 key）
const basicInfoEntries = computed(() => Object.entries(aiReviewResult.value.basic_info || {}))
const keyClauseEntries = computed(() => Object.entries(aiReviewResult.value.key_clauses || {}))
const overallEvalEntries = computed(() => Object.entries(aiReviewResult.value.overall_evaluation || {}))
const modificationGroups = computed<[string, string[]][]>(() => {
  const raw: any = aiReviewResult.value.modification_suggestions || {}
  // 组名中英映射（真实 DeepSeek 返回英文 key，mock 返回中文 key）
  const labelMap: Record<string, string> = {
    must_modify: '必须修改项',
    suggested_optimization: '建议优化项',
    suggest_optimize: '建议优化项',
    notes: '注意事项',
    必须修改项: '必须修改项',
    建议优化项: '建议优化项',
    注意事项: '注意事项',
  }
  return Object.entries(raw)
    .filter(([, items]) => Array.isArray(items) && items.length)
    .map(([key, items]) => [labelMap[key] || key, items as string[]])
})
const riskPoints = computed<any[]>(() => {
  if (reviewDetails.value?.risk_points?.length) return reviewDetails.value.risk_points
  return aiReviewResult.value.specific_risks || []
})

// AI 建议（由 修改建议 + 具体风险点 动态生成）
const aiSuggestions = computed(() => {
  const suggestions: string[] = []
  const mod: any = aiReviewResult.value.modification_suggestions
  if (mod) {
    const must = mod['必须修改项'] || mod.must_modify
    const optimize = mod['建议优化项'] || mod.suggested_optimization || mod.suggest_optimize
    const notes = mod['注意事项'] || mod.notes
    if (Array.isArray(must)) suggestions.push(...must)
    if (Array.isArray(optimize)) suggestions.push(...optimize)
    if (Array.isArray(notes)) suggestions.push(...notes)
  }
  riskPoints.value.forEach((r: any) => {
    const pos = r['条款位置'] || r.clause_location || r.clause_reference || r.clause || ''
    const sug = r['修改建议'] || r.modification_suggestion || r.suggestion || ''
    const desc = r['风险描述'] || r.risk_description || r.description || ''
    if (sug) suggestions.push(`${pos ? pos + '：' : ''}${sug}`)
    else if (desc) suggestions.push(`${pos ? pos + '：' : ''}${desc}`)
  })
  return Array.from(new Set(suggestions)).slice(0, 10)
})

// 加载合同信息 + AI 审核详情
const loadData = async () => {
  if (!contractId.value) return
  loading.value = true
  try {
    const [contractData, detailsData] = await Promise.all([
      getContract(Number(contractId.value)),
      getContractReviewDetails(Number(contractId.value)),
    ])
    contract.value = contractData
    reviewDetails.value = detailsData
    totalPages.value = contractData.page_count || 0
    if (detailsData.risk_level) {
      reviewForm.value.riskLevel = detailsData.risk_level
    }
    if (detailsData.risk_points?.length) {
      reviewForm.value.keyClauses = detailsData.risk_points
        .map((r: any) => r['条款位置'] || r.clause_location || r.clause_reference || r.clause || '')
        .filter(Boolean)
        .join('，')
    }
  } catch (error: any) {
    console.error('加载审核数据失败:', error)
    const detail = error?.response?.data?.detail
    ElMessage.error(detail || '加载审核数据失败')
  } finally {
    loading.value = false
  }
}

// 触发 / 重新 AI 审核
const handleTriggerAiReview = async () => {
  if (!contractId.value) return
  aiLoading.value = true
  try {
    await triggerAiReview(Number(contractId.value))
    ElMessage.success('AI 审核完成')
    // 重新拉取审核详情
    const detailsData = await getContractReviewDetails(Number(contractId.value))
    reviewDetails.value = detailsData
  } catch (error: any) {
    console.error('触发AI审核失败:', error)
    const detail = error?.response?.data?.detail
    ElMessage.error(detail || 'AI 审核失败，请稍后重试')
  } finally {
    aiLoading.value = false
  }
}

onMounted(() => {
  contractId.value = route.params.id as string
  loadData()
})

// PDF加载完成回调
const onPdfLoaded = (loadedTotalPages: number) => {
  totalPages.value = loadedTotalPages
  console.log(`PDF加载完成，共${loadedTotalPages}页`)
}

// PDF加载错误回调
const onPdfError = (error: string) => {
  console.error('PDF加载失败:', error)
}

// 页面变化回调
const onPageChange = (page: number) => {
  currentPage.value = page
}

// 提交人工审核
const handleSubmitReview = async () => {
  if (!contractId.value) return
  submitting.value = true
  try {
    const payload: SubmitReviewPayload = {
      manual_review_result: {
        result: reviewForm.value.result,
        key_clauses: reviewForm.value.keyClauses,
        comments: reviewForm.value.comments,
        attachments: fileList.value.map((f) => f.name),
      },
      risk_level: reviewForm.value.riskLevel,
      risk_score: reviewDetails.value.risk_score,
      review_summary: reviewForm.value.comments || reviewDetails.value.review_summary || '',
    }
    await submitContractReview(Number(contractId.value), payload)
    ElMessage.success('审核意见已提交')
    router.push(`/contracts/${contractId.value}`)
  } catch (error: any) {
    console.error('提交审核失败:', error)
    const detail = error?.response?.data?.detail
    ElMessage.error(detail || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

const handleSaveDraft = () => {
  ElMessage.info('草稿已保存在本地，请继续完善后提交')
}

const handleBack = () => {
  router.push(`/contracts/${contractId.value}`)
}

const handleFileChange = (file: UploadFile) => {
  console.log('文件变更', file)
}

const prevPage = () => {
  if (pdfViewerRef.value) {
    pdfViewerRef.value.prevPage()
  } else if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (pdfViewerRef.value) {
    pdfViewerRef.value.nextPage()
  } else if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const toggleFullscreen = () => {
  if (pdfViewerRef.value) {
    pdfViewerRef.value.toggleFullscreen()
  }
}

// 切换布局模式
const toggleLayout = () => {
  const modes = ['horizontal', 'vertical', 'previewOnly']
  const currentIndex = modes.indexOf(layoutMode.value)
  const nextIndex = (currentIndex + 1) % modes.length
  layoutMode.value = modes[nextIndex]
}

// 切换审核区域显示
const toggleReviewSection = () => {
  reviewSectionVisible.value = !reviewSectionVisible.value
  if (!reviewSectionVisible.value) {
    layoutMode.value = 'previewOnly'
  } else {
    layoutMode.value = 'horizontal'
  }
}

const getProgressColor = (percentage: number) => {
  if (percentage >= 70) return '#F56C6C'
  if (percentage >= 30) return '#E6A23C'
  return '#67C23A'
}

// 风险等级 -> el-tag 类型（兼容中英文值）
const riskTagType = (level: string): 'danger' | 'warning' | 'success' | 'info' => {
  const l = (level || '').toLowerCase()
  if (l.includes('高') || l === 'high' || l === 'danger' || l === 'critical') return 'danger'
  if (l.includes('低') || l === 'low' || l === 'success') return 'success'
  if (l) return 'warning'
  return 'info'
}

const riskLevelText = (level: string): string => {
  const map: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险',
    unknown: '未知',
  }
  return map[level] || level || '未知'
}
</script>

<style scoped lang="scss">
.contract-review {
  height: calc(100vh - 60px); /* 整个页面使用视口高度 */
  display: flex;
  flex-direction: column;

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-shrink: 0;

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .review-container {
    flex: 1;
    display: flex;
    flex-direction: column;

    .layout-toggle {
      margin-bottom: 15px;
      display: flex;
      justify-content: flex-end;
      flex-shrink: 0;

      .el-radio-group {
        background: #f5f7fa;
        padding: 4px;
        border-radius: 6px;
      }
    }

    .main-content {
      display: flex;
      gap: 20px;
      transition: all 0.3s ease;
      flex: 1;
      min-height: 0; /* 重要：允许内容收缩 */

      &.horizontal {
        flex-direction: row;
        height: 100%;

        .preview-section {
          flex: 3;
          min-width: 0;
          height: 100%;

          .contract-preview-card {
            height: 100%;
            min-height: 0;
          }
        }

        .review-section {
          flex: 2;
          min-width: 400px;
          max-width: 500px;
          height: 100%;
          overflow-y: auto;
        }
      }

      &.vertical {
        flex-direction: column;
        height: 100%;

        .preview-section {
          width: 100%;
          flex: 3;
          min-height: 0;

          .contract-preview-card {
            height: 100%;
          }
        }

        .review-section {
          width: 100%;
          flex: 2;
          margin-top: 20px;
          overflow-y: auto;
        }
      }

      &.previewOnly {
        .preview-section {
          width: 100%;
          height: 100%;

          .contract-preview-card {
            height: 100%;
            min-height: 0;
          }
        }

        .review-section {
          display: none;
        }
      }

      .preview-section {
        .contract-preview-card {
          height: 100%;
          min-height: 800px; /* 显著增加最小高度 */
          display: flex;
          flex-direction: column;

          .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;

            h3 {
              margin: 0;
              font-size: 18px;
              font-weight: 600;
            }

            .card-actions {
              display: flex;
              gap: 10px;
            }
          }

          .preview-content {
            flex: 1;
            min-height: 700px; /* 进一步增加内容区域最小高度 */

            .pdf-viewer-container {
              height: 100%;
              min-height: 700px;
            }

            .pdf-viewer-placeholder {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              height: 700px; /* 进一步增加占位符高度 */
              border: 2px dashed #dcdfe6;
              border-radius: 8px;
              background-color: #fafafa;
              margin-bottom: 20px;

              p {
                margin-top: 10px;
                color: #606266;

                &.file-info {
                  font-size: 14px;
                  color: #909399;
                  margin-top: 5px;
                }

                &.file-tip {
                  font-size: 12px;
                  color: #c0c4cc;
                  margin-top: 5px;
                }
              }
            }
          }

          .preview-footer {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #ebeef5;
            display: flex;
            justify-content: space-between;
            align-items: center;

            .page-navigation {
              display: flex;
              align-items: center;
              gap: 10px;

              .page-info {
                font-size: 14px;
                color: #606266;
                font-weight: 500;
              }
            }

            .file-info-footer {
              display: flex;
              gap: 8px;
            }
          }
        }
      }

      .review-section {
        display: flex;
        flex-direction: column;
        gap: 20px;

        .review-form-card {
          .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;

            h3 {
              margin: 0;
              font-size: 16px;
              font-weight: 600;
            }

            .collapse-review {
              padding: 0;
              height: auto;
            }
          }

          .review-form {
            .ai-suggestion {
              background-color: #f0f9ff;
              border-color: #d9ecff;
              padding: 12px;

              p {
                margin: 5px 0;
                color: #606266;
                font-size: 14px;
              }
            }
          }
        }

        .ai-analysis-card {
          .ai-analysis-content {
            .risk-overview {
              display: flex;
              align-items: center;
              gap: 20px;
              margin-bottom: 16px;
              padding: 12px;
              background: #f5f7fa;
              border-radius: 8px;

              .risk-score-text {
                font-size: 20px;
                font-weight: bold;
                color: #303133;
              }

              .risk-overview-info {
                flex: 1;

                .review-summary {
                  margin-top: 8px;
                  font-size: 13px;
                  color: #606266;
                  line-height: 1.5;
                }
              }
            }

            .risk-item {
              padding: 12px;
              border: 1px solid #ebeef5;
              border-radius: 6px;
              margin-bottom: 10px;
              background: #fff;

              .risk-item-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 6px;

                .risk-position {
                  font-weight: 600;
                  color: #303133;
                  font-size: 14px;
                }
              }

              .risk-desc {
                color: #606266;
                font-size: 14px;
                margin-bottom: 4px;
              }

              .risk-suggestion {
                color: #409eff;
                font-size: 13px;

                .suggestion-label {
                  color: #909399;
                }
              }
            }

            .suggestion-group {
              margin-bottom: 12px;

              .suggestion-group-title {
                font-size: 14px;
                font-weight: 600;
                color: #303133;
                margin-bottom: 6px;
              }

              ul {
                margin: 0 0 0 20px;
                color: #606266;
              }

              .suggestion-empty {
                color: #c0c4cc;
                font-size: 13px;
              }
            }
          }
        }
      }
    }
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .contract-review {
    .review-container {
      .main-content {
        &.horizontal {
          flex-direction: column;

          .review-section {
            max-width: 100%;
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .contract-review {
    .header {
      flex-direction: column;
      align-items: flex-start;
      gap: 15px;

      .header-actions {
        width: 100%;
        justify-content: flex-end;
      }
    }

    .review-container {
      .layout-toggle {
        justify-content: center;
      }

      .main-content {
        .preview-section {
          .contract-preview-card {
            min-height: 600px;

            .preview-footer {
              flex-direction: column;
              gap: 10px;
              align-items: stretch;

              .page-navigation {
                justify-content: center;
              }

              .file-info-footer {
                justify-content: center;
              }
            }
          }
        }
      }
    }
  }
}
</style>
