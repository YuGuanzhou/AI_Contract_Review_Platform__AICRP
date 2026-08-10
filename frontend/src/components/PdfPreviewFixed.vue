<template>
  <div class="pdf-preview-fixed">
    <div class="pdf-controls" v-if="totalPages > 0">
      <el-button-group>
        <el-button :icon="ArrowLeft" @click="prevPage" :disabled="currentPage <= 1" size="small">上一页</el-button>
        <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
        <el-button @click="nextPage" :disabled="currentPage >= totalPages" size="small">下一页 <el-icon><ArrowRight /></el-icon></el-button>
      </el-button-group>
      <div class="controls-right">
        <el-input-number
          v-model="zoom"
          :min="0.5"
          :max="3"
          :step="0.1"
          size="small"
          style="width: 100px; margin-right: 10px;"
        />
        <el-button :icon="ZoomIn" @click="zoomIn" size="small" circle />
        <el-button :icon="ZoomOut" @click="zoomOut" size="small" circle />
      </div>
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
        <canvas
          ref="pdfCanvas"
          class="pdf-canvas"
          :style="{
            width: `${canvasWidth}px`,
            height: `${canvasHeight}px`,
            margin: '10px auto'
          }"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ArrowLeft, ArrowRight, ZoomIn, ZoomOut, Loading, Warning } from '@element-plus/icons-vue'
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
const pdfCanvas = ref<HTMLCanvasElement>()
const pdfDoc = ref<any>(null)
const currentPage = ref(props.initialPage)
const totalPages = ref(0)
const zoom = ref(1)
const loading = ref(false)
const error = ref('')
const canvasWidth = ref(0)
const canvasHeight = ref(0)

// PDF.js库引用 - 使用全局变量避免重复导入
declare global {
  interface Window {
    pdfjsLib: any
  }
}

// 加载PDF.js库
const loadPdfJs = async () => {
  if (window.pdfjsLib && window.pdfjsLib.GlobalWorkerOptions) {
    return window.pdfjsLib
  }
  
  return new Promise((resolve, reject) => {
    // 检查是否已经在加载中
    if (window._pdfjsLoading) {
      // 等待加载完成
      const checkInterval = setInterval(() => {
        if (window.pdfjsLib && window.pdfjsLib.GlobalWorkerOptions) {
          clearInterval(checkInterval)
          resolve(window.pdfjsLib)
        }
      }, 100)
      return
    }
    
    window._pdfjsLoading = true
    
    try {
      // 使用CDN加载PDF.js，避免构建问题
      const version = '2.16.105'
      
      // 加载主库
      const script = document.createElement('script')
      script.src = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${version}/pdf.min.js`
      
      script.onload = () => {
        console.log('PDF.js库加载成功')
        
        // 确保pdfjsLib对象已挂载到window
        if (!window.pdfjsLib) {
          // 如果CDN没有自动挂载，尝试从全局对象获取
          window.pdfjsLib = (window as any).pdfjsLib || (window as any).pdfjsDist
        }
        
        if (window.pdfjsLib) {
          // 设置worker
          window.pdfjsLib.GlobalWorkerOptions = window.pdfjsLib.GlobalWorkerOptions || {}
          window.pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${version}/pdf.worker.min.js`
          console.log('PDF.js worker设置完成')
          
          window._pdfjsLoading = false
          resolve(window.pdfjsLib)
        } else {
          window._pdfjsLoading = false
          reject(new Error('PDF.js库加载后未找到全局对象'))
        }
      }
      
      script.onerror = (err) => {
        console.error('PDF.js库加载失败:', err)
        window._pdfjsLoading = false
        reject(new Error(`PDF.js库加载失败: ${err}`))
      }
      
      document.head.appendChild(script)
      
    } catch (err) {
      window._pdfjsLoading = false
      console.error('加载PDF.js库失败:', err)
      reject(err)
    }
  })
}

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
    
    // 确保PDF.js库已加载
    await loadPdfJs()
    
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
    
    const pdfUrl = URL.createObjectURL(pdfBlob)
    
    // 使用blob URL加载PDF
    console.log('使用PDF.js加载文档...')
    const loadingTask = window.pdfjsLib.getDocument({
      url: pdfUrl,
      disableAutoFetch: false,
      disableStream: false
    })
    
    pdfDoc.value = await loadingTask.promise
    console.log('PDF文档加载成功，总页数:', pdfDoc.value.numPages)
    
    totalPages.value = pdfDoc.value.numPages
    emit('loaded', totalPages.value)
    
    // 渲染初始页面
    await renderPage(currentPage.value)
    
    // 清理blob URL
    URL.revokeObjectURL(pdfUrl)
    console.log('PDF加载完成')
    
  } catch (err: any) {
    console.error('PDF加载失败:', err)
    console.error('错误堆栈:', err.stack)
    error.value = `PDF加载失败: ${err.message || '未知错误'}`
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

// 渲染指定页面
const renderPage = async (pageNum: number) => {
  if (!pdfDoc.value || pageNum < 1 || pageNum > totalPages.value) {
    console.warn(`无法渲染页面${pageNum}: PDF文档未加载或页码无效`)
    return
  }

  try {
    console.log(`开始渲染第${pageNum}页...`)
    
    // 获取页面
    const page = await pdfDoc.value.getPage(pageNum)
    console.log(`第${pageNum}页获取成功`)
    
    // 设置渲染比例
    const viewport = page.getViewport({ scale: zoom.value * 1.5 })
    console.log(`页面尺寸: ${viewport.width}x${viewport.height}`)
    
    // 更新canvas尺寸
    canvasWidth.value = viewport.width
    canvasHeight.value = viewport.height
    
    // 获取canvas上下文
    const canvas = pdfCanvas.value
    if (!canvas) {
      console.error('Canvas元素未找到')
      return
    }
    
    // 设置canvas尺寸
    canvas.width = viewport.width
    canvas.height = viewport.height
    
    const context = canvas.getContext('2d')
    if (!context) {
      console.error('无法获取canvas 2d上下文')
      return
    }
    
    console.log(`开始渲染canvas，尺寸: ${canvas.width}x${canvas.height}`)
    
    // 渲染页面
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }
    
    const renderTask = page.render(renderContext)
    await renderTask
    
    console.log(`第${pageNum}页渲染完成`)
    
  } catch (err: any) {
    console.error(`渲染第${pageNum}页失败:`, err)
    console.error('错误详情:', err.message)
    console.error('错误堆栈:', err.stack)
    error.value = `渲染页面失败: ${err.message}`
  }
}

// 上一页
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    emit('page-change', currentPage.value)
    renderPage(currentPage.value)
  }
}

// 下一页
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    emit('page-change', currentPage.value)
    renderPage(currentPage.value)
  }
}

// 跳转到指定页面
const goToPage = (pageNum: number) => {
  if (pageNum >= 1 && pageNum <= totalPages.value) {
    currentPage.value = pageNum
    emit('page-change', currentPage.value)
    renderPage(currentPage.value)
  }
}

// 放大
const zoomIn = () => {
  zoom.value = Math.min(3, zoom.value + 0.1)
  if (currentPage.value > 0) {
    renderPage(currentPage.value)
  }
}

// 缩小
const zoomOut = () => {
  zoom.value = Math.max(0.5, zoom.value - 0.1)
  if (currentPage.value > 0) {
    renderPage(currentPage.value)
  }
}

// 监听PDF URL变化
watch(() => props.pdfUrl, (newUrl) => {
  if (newUrl && props.autoLoad) {
    loadPdf()
  }
})

// 监听缩放变化
watch(zoom, () => {
  // 重新渲染当前页面
  if (currentPage.value > 0) {
    renderPage(currentPage.value)
  }
})

// 生命周期
onMounted(() => {
  if (props.autoLoad && props.pdfUrl) {
    loadPdf()
  }
})

onUnmounted(() => {
  // 清理资源
  if (pdfDoc.value) {
    pdfDoc.value.destroy()
  }
})

// 暴露方法给父组件
defineExpose({
  loadPdf,
  prevPage,
  nextPage,
  goToPage,
  zoomIn,
  zoomOut
})
</script>

<style scoped lang="scss">
.pdf-preview-fixed {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .pdf-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    background: #f5f7fa;
    border-bottom: 1px solid #e4e7ed;
    
    .page-info {
      margin: 0 15px;
      font-size: 14px;
      color: #606266;
    }
    
    .controls-right {
      display: flex;
      align-items: center;
    }
  }
  
  .pdf-container {
    flex: 1;
    overflow: auto;
    position: relative;
    
    .pdf-loading, .pdf-error {
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
      padding: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      
      .pdf-canvas {
        display: block;
        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
        background: white;
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