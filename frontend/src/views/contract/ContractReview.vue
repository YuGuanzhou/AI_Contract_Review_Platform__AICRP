<template>
  <div class="contract-review">
    <div class="header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/user/contracts' }">我的合同</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: `/contracts/${contractId}` }">合同详情</el-breadcrumb-item>
        <el-breadcrumb-item>合同审核</el-breadcrumb-item>
      </el-breadcrumb>
      <div class="header-actions">
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
      
      <div class="main-content" :class="layoutMode">
        <div class="preview-section">
          <el-card class="contract-preview-card">
            <template #header>
              <div class="card-header">
                <h3>合同预览 - {{ contract.name }}</h3>
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
                <p class="file-info">文件：{{ contract.fileName }}</p>
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
                <el-tag size="small" type="info">{{ contract.fileName }}</el-tag>
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
                    <p>1. 第5条付款条款：建议明确付款期限为30天</p>
                    <p>2. 第8条违约责任：违约金比例较高，建议协商调整</p>
                    <p>3. 第12条争议解决：建议增加仲裁条款</p>
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
              <el-collapse v-model="activeAnalysisPanels">
                <el-collapse-item title="条款完整性分析" name="completeness">
                  <div class="analysis-item">
                    <el-progress :percentage="85" :color="getProgressColor(85)" />
                    <p>合同主要条款完整度较高，缺少不可抗力条款</p>
                  </div>
                </el-collapse-item>
                <el-collapse-item title="法律风险检测" name="risks">
                  <div class="analysis-item">
                    <el-alert
                      title="发现3个潜在风险点"
                      type="warning"
                      :closable="false"
                      show-icon
                    />
                    <ul>
                      <li>违约金比例超过法定上限</li>
                      <li>管辖法院约定不明确</li>
                      <li>知识产权归属条款缺失</li>
                    </ul>
                  </div>
                </el-collapse-item>
                <el-collapse-item title="合规性检查" name="compliance">
                  <div class="analysis-item">
                    <el-alert
                      title="符合行业标准"
                      type="success"
                      :closable="false"
                      show-icon
                    />
                    <p>合同符合《民法典》相关规定，条款设置合理</p>
                  </div>
                </el-collapse-item>
                <el-collapse-item title="关键信息提取" name="extraction">
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="合同金额">¥ 1,250,000.00</el-descriptions-item>
                    <el-descriptions-item label="合同期限">2024-01-01 至 2024-12-31</el-descriptions-item>
                    <el-descriptions-item label="交付时间">合同签订后30个工作日内</el-descriptions-item>
                    <el-descriptions-item label="付款方式">30%预付款，70%验收后付款</el-descriptions-item>
                  </el-descriptions>
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

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const contractId = ref('')
const currentPage = ref(1)
const totalPages = ref(12)
const submitting = ref(false)
const activeAnalysisPanels = ref(['completeness', 'risks', 'compliance'])
const pdfViewerRef = ref<InstanceType<typeof PdfPreview>>()
const layoutMode = ref('horizontal') // horizontal, vertical, previewOnly
const isReviewer = computed(() => ['reviewer', 'admin'].includes(userStore.userRole))
const reviewSectionVisible = ref(true)

const contract = ref({
  fileName: 'purchase_agreement.pdf',
  name: '采购协议合同'
})

const reviewForm = ref({
  result: 'approved',
  riskLevel: 'medium',
  keyClauses: '第5条付款条款，第8条违约责任，第12条争议解决',
  comments: '',
  attachments: [] as string[]
})

const fileList = ref<UploadFile[]>([])

// PDF预览URL
const pdfPreviewUrl = computed(() => {
  if (!contractId.value) return ''
  return `/api/contracts/${contractId.value}/preview`
})

onMounted(() => {
  contractId.value = route.params.id as string
  // 加载合同信息和AI分析
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

const handleSubmitReview = () => {
  submitting.value = true
  // 模拟提交
  setTimeout(() => {
    submitting.value = false
    ElMessage.success('审核意见已提交')
    router.push(`/contracts/${contractId.value}`)
  }, 1000)
}

const handleSaveDraft = () => {
  ElMessage.info('草稿已保存')
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
  if (percentage >= 80) return '#67C23A'
  if (percentage >= 60) return '#E6A23C'
  return '#F56C6C'
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
            .analysis-item {
              .el-progress {
                margin-bottom: 10px;
              }

              ul {
                margin: 10px 0 0 20px;
                color: #606266;
              }

              p {
                margin: 10px 0;
                color: #606266;
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