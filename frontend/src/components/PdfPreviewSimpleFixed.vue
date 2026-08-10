<template>
  <div class="pdf-preview-simple-fixed">
    <div class="pdf-controls" v-if="totalPages > 0">
      <el-button-group>
        <el-button :icon="ArrowLeft" @click="prevPage" :disabled="currentPage <= 1" size="small">上一页</el-button>
        <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
        <el-button @click="nextPage" :disabled="currentPage >= totalPages" size="small">下一页 <el-icon><ArrowRight /></el-icon></el-button>
      </el-button-group>
    </div>
    
    <div class="pdf-container" ref="pdfContainer">
      <div class="pdf-loading" v-if="loading">
        <el-icon class="loading-icon" :size="40"><Loading /></el-icon>
        <p>加载PDF文档中...</p>
      </div>
      
      <div class="pdf-error" v-else-if="error">
        <el-icon class="error-icon" :size="40"><Warning /></el-icon>
        <p>{{ error }}</p>
        <el-button type="primary" @click="loadPdf">重试</el-button>
      </div>
      
      <div class="pdf-viewer" v-else>
        <iframe
          v-if="pdfBlobUrl"
          :src="pdfBlobUrl"
          class="pdf-iframe"
          frameborder="0"
          style="width: 100%; height: 100%;"
        />
        <div v-else class="no-pdf">
          <el-icon :size="60" color="#409EFF"><Document /></el-icon>
          <p>PDF预览不可用</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ArrowLeft, ArrowRight, Loading, Warning, Document } from '@element-plus/icons-vue'
import { getToken } from '@/utils/auth'

interface Props {
  pdfUrl: string
  initialPage?: number
  autoLoad?: boolean
  withCredentials?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  initialPage: 1,
  autoLoad: true,
  withCredentials: true
})

const emit = defineEmits<{
  'page-change': [page: number]
  'loaded': [totalPages: number]
  'error': [error: string]
}>()

// 响应式数据
const pdfContainer = ref<HTMLElement>()
const pdfBlobUrl = ref('')
const currentPage = ref(props.initialPage)
const totalPages = ref(0)
const loading = ref(false)
const error = ref('')

// 加载PDF文档
const loadPdf = async () => {
  if (!props.pdfUrl) {
    error.value = 'PDF URL不能为空'
    return
  }

  loading.value = true
  error.value = ''
  
  try {
    console.log('开始加载PDF:', props.pdfUrl)
    
    // 使用fetch API获取PDF文件
    const response = await fetch(props.pdfUrl, {
      method: 'GET',
      credentials: props.withCredentials ? 'include' : 'same-origin',
      headers: getAuthHeaders()
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const pdfBlob = await response.blob()
    console.log('PDF blob大小:', pdfBlob.size, 'bytes')
    
    // 创建blob URL用于iframe显示
    const url = URL.createObjectURL(pdfBlob)
    pdfBlobUrl.value = url
    
    // 为了获取总页数，我们需要使用PDF.js
    // 但为了简化，我们假设PDF加载成功
    totalPages.value = 1 // 简化处理，实际应该解析PDF获取页数
    emit('loaded', totalPages.value)
    
    console.log('PDF加载完成')
    
  } catch (err: any) {
    console.error('PDF加载失败:', err)
    console.error('错误堆栈:', err.stack)
    const msg = err?.message || err?.name || '未知错误'
    if (/404/.test(msg) || /Failed to fetch/.test(msg)) {
      error.value = '合同文件不存在或已被删除，请重新上传后再预览'
    } else if (/Invalid PDF|structure/i.test(msg)) {
      error.value = '该文件不是有效的PDF文档，无法在线预览，请下载后查看'
    } else {
      error.value = `PDF加载失败: ${msg}`
    }
    emit('error', error.value)
  } finally {
    loading.value = false
  }
}

// 获取认证头
const getAuthHeaders = () => {
  const headers: Record<string, string> = {
    'Accept': 'application/pdf, */*'
  }
  
  try {
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  } catch (e) {
    console.warn('无法获取认证token:', e)
  }
  
  return headers
}

// 上一页
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    emit('page-change', currentPage.value)
  }
}

// 下一页
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    emit('page-change', currentPage.value)
  }
}

// 跳转到指定页面
const goToPage = (pageNum: number) => {
  if (pageNum >= 1 && pageNum <= totalPages.value) {
    currentPage.value = pageNum
    emit('page-change', currentPage.value)
  }
}

// 监听PDF URL变化
watch(() => props.pdfUrl, (newUrl) => {
  if (newUrl && props.autoLoad) {
    // 清理旧的blob URL
    if (pdfBlobUrl.value) {
      URL.revokeObjectURL(pdfBlobUrl.value)
      pdfBlobUrl.value = ''
    }
    loadPdf()
  }
})

// 生命周期
onMounted(() => {
  if (props.autoLoad && props.pdfUrl) {
    loadPdf()
  }
})

onUnmounted(() => {
  // 清理blob URL
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
  }
})

// 暴露方法给父组件
defineExpose({
  loadPdf,
  prevPage,
  nextPage,
  goToPage
})
</script>

<style scoped lang="scss">
.pdf-preview-simple-fixed {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .pdf-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 10px;
    background: #f5f7fa;
    border-bottom: 1px solid #e4e7ed;
    
    .page-info {
      margin: 0 15px;
      font-size: 14px;
      color: #606266;
    }
  }
  
  .pdf-container {
    flex: 1;
    overflow: auto;
    position: relative;
    
    .pdf-loading, .pdf-error, .no-pdf {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      height: 100%;
      color: #909399;
      
      .loading-icon {
        animation: rotate 2s linear infinite;
        margin-bottom: 10px;
      }
      
      .error-icon {
        color: #f56c6c;
        margin-bottom: 10px;
      }
    }
    
    .pdf-viewer {
      width: 100%;
      height: 100%;
      
      .pdf-iframe {
        width: 100%;
        height: 100%;
        border: none;
      }
    }
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>