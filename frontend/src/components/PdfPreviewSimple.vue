<template>
  <div class="pdf-preview-simple">
    <div class="pdf-controls" v-if="totalPages > 0">
      <button @click="prevPage" :disabled="currentPage <= 1">上一页</button>
      <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
      <button @click="nextPage" :disabled="currentPage >= totalPages">下一页</button>
      
      <div class="zoom-controls">
        <button @click="zoomOut">-</button>
        <span>{{ Math.round(zoom * 100) }}%</span>
        <button @click="zoomIn">+</button>
      </div>
    </div>
    
    <div class="pdf-container" ref="pdfContainer">
      <div v-if="loading" class="loading">加载PDF中...</div>
      <div v-else-if="error" class="error">
        <p>{{ error }}</p>
        <button @click="loadPdf">重试</button>
      </div>
      <div v-else class="pdf-content">
        <canvas ref="pdfCanvas" class="pdf-canvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

// 动态导入pdfjs-dist，避免构建问题
let pdfjsLib: any = null

interface Props {
  pdfUrl: string
  initialPage?: number
}

const props = withDefaults(defineProps<Props>(), {
  initialPage: 1
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

// 加载PDF.js库
const loadPdfJs = async () => {
  if (pdfjsLib) return pdfjsLib
  
  try {
    // 动态导入PDF.js
    pdfjsLib = await import('pdfjs-dist')
    
    // 设置worker - 使用CDN避免路径问题
    const version = '2.16.105' // 使用稳定的2.x版本
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${version}/pdf.worker.min.js`
    
    return pdfjsLib
  } catch (err) {
    console.error('加载PDF.js库失败:', err)
    throw err
  }
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
    
    // 确保PDF.js已加载
    const pdf = await loadPdfJs()
    
    // 使用fetch获取PDF文件
    const response = await fetch(props.pdfUrl, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/pdf, */*'
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const pdfBlob = await response.blob()
    const pdfUrl = URL.createObjectURL(pdfBlob)
    
    // 加载PDF文档
    const loadingTask = pdf.getDocument(pdfUrl)
    pdfDoc.value = await loadingTask.promise
    
    totalPages.value = pdfDoc.value.numPages
    console.log('PDF文档加载成功，总页数:', totalPages.value)
    emit('loaded', totalPages.value)
    
    // 渲染初始页面
    await renderPage(currentPage.value)
    
    // 清理blob URL
    URL.revokeObjectURL(pdfUrl)
    
  } catch (err: any) {
    console.error('PDF加载失败:', err)
    error.value = `PDF加载失败: ${err.message || '未知错误'}`
    emit('error', error.value)
  } finally {
    loading.value = false
  }
}

// 渲染指定页面
const renderPage = async (pageNum: number) => {
  if (!pdfDoc.value || pageNum < 1 || pageNum > totalPages.value) {
    return
  }

  try {
    console.log(`渲染第${pageNum}页...`)
    const page = await pdfDoc.value.getPage(pageNum)
    
    // 设置渲染比例
    const viewport = page.getViewport({ scale: zoom.value })
    
    // 获取canvas上下文
    const canvas = pdfCanvas.value
    if (!canvas) {
      throw new Error('Canvas元素未找到')
    }
    
    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('无法获取Canvas 2D上下文')
    }
    
    // 设置canvas尺寸
    canvas.width = viewport.width
    canvas.height = viewport.height
    
    console.log(`Canvas尺寸: ${canvas.width}x${canvas.height}`)
    
    // 渲染页面 - 使用PDF.js 2.x兼容的API
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }
    
    // 注意：PDF.js 2.x中render()返回一个包含promise的对象
    const renderTask = page.render(renderContext)
    await renderTask.promise
    
    console.log(`第${pageNum}页渲染完成`)
    emit('page-change', pageNum)
    
  } catch (err: any) {
    console.error(`渲染第${pageNum}页失败:`, err)
    error.value = `渲染页面失败: ${err.message}`
  }
}

// 上一页
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    renderPage(currentPage.value)
  }
}

// 下一页
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
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
  if (newUrl) {
    loadPdf()
  }
})

// 监听缩放变化
watch(zoom, () => {
  if (currentPage.value > 0) {
    renderPage(currentPage.value)
  }
})

// 生命周期
onMounted(() => {
  if (props.pdfUrl) {
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
  zoomIn,
  zoomOut
})
</script>

<style scoped>
.pdf-preview-simple {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.pdf-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.page-info {
  margin: 0 10px;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-left: auto;
}

button {
  padding: 5px 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.pdf-container {
  flex: 1;
  overflow: auto;
  position: relative;
}

.loading, .error {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.error {
  color: #dc3545;
}

.pdf-content {
  padding: 20px;
  display: flex;
  justify-content: center;
}

.pdf-canvas {
  display: block;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  background: white;
}
</style>