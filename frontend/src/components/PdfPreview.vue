<template>
  <div class="pdf-preview">
    <div class="pdf-controls" v-if="totalPages > 0">
      <div class="controls-left">
        <el-button-group>
          <el-button :icon="ArrowLeft" @click="prevPage" :disabled="currentPage <= 1" size="small">上一页</el-button>
          <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
          <el-button @click="nextPage" :disabled="currentPage >= totalPages" size="small">下一页 <el-icon><ArrowRight /></el-icon></el-button>
        </el-button-group>
        <el-button
          type="text"
          @click="toggleFitWidth"
          size="small"
          :class="{ 'active-fit': fitMode === 'width' }"
          class="fit-button"
        >
          <el-icon><ScaleToOriginal /></el-icon>
          适应宽度
        </el-button>
      </div>
      <div class="controls-right">
        <div class="zoom-controls">
          <el-button :icon="ZoomOut" @click="zoomOut" size="small" circle title="缩小" />
          <span class="zoom-percentage">{{ Math.round(zoom * 100) }}%</span>
          <el-button :icon="ZoomIn" @click="zoomIn" size="small" circle title="放大" />
        </div>
        <el-input-number
          v-model="zoom"
          :min="0.5"
          :max="3"
          :step="0.1"
          size="small"
          style="width: 100px; margin-left: 10px;"
          title="缩放比例"
        />
        <el-button
          :icon="FullScreen"
          @click="toggleFullscreen"
          size="small"
          circle
          title="全屏"
          class="fullscreen-button"
        />
      </div>
    </div>
    
    <div class="pdf-container" ref="pdfContainer">
      <div class="pdf-loading" v-if="loading">
        <el-icon class="loading-icon" :size="40"><Loading /></el-icon>
        <p>加载PDF文档中...</p>
        <p class="loading-tip">请稍候，正在渲染文档</p>
      </div>
      
      <div class="pdf-error" v-else-if="error">
        <el-icon class="error-icon" :size="40"><Warning /></el-icon>
        <p>{{ error }}</p>
        <el-button type="primary" @click="loadPdf">重试</el-button>
        <p class="error-tip">如果问题持续，请检查网络连接或文件格式</p>
      </div>
      
      <div class="pdf-viewer" v-else ref="pdfViewer">
        <div v-if="fallbackRendering" class="pdf-fallback">
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
        <template v-else>
          <canvas
            v-for="page in renderedPages"
            :key="page.pageNum"
            :ref="(el) => setCanvasRef(el, page.pageNum)"
            class="pdf-page"
            :style="getPageStyle(page)"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { ArrowLeft, ArrowRight, ZoomIn, ZoomOut, FullScreen, Loading, Warning, ScaleToOriginal, Document } from '@element-plus/icons-vue'
import { getToken } from '@/utils/auth'

// PDF.js库引用 - 使用动态导入避免版本兼容性问题
let pdfjsLib: any = null

// 动态加载PDF.js库
const loadPdfJs = async () => {
  if (pdfjsLib) return pdfjsLib
  
  try {
    // 动态导入PDF.js，避免构建时的静态分析问题
    pdfjsLib = await import('pdfjs-dist')
    
    // 设置worker - 使用稳定的2.x版本CDN
    const version = '2.16.105'
    const cdnUrl = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${version}/pdf.worker.min.js`
    console.log('设置PDF.js worker URL:', cdnUrl)
    pdfjsLib.GlobalWorkerOptions.workerSrc = cdnUrl
    
    return pdfjsLib
  } catch (err) {
    console.error('加载PDF.js库失败:', err)
    throw err
  }
}

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
const pdfViewer = ref<HTMLElement>()
const pdfDoc = ref<any>(null)
const pdfBlobUrl = ref('') // 用于备用渲染的Blob URL
const fallbackRendering = ref(false) // 是否使用备用iframe渲染
const currentPage = ref(props.initialPage)
const totalPages = ref(0)
const zoom = ref(1)
const loading = ref(false)
const error = ref('')
const renderedPages = ref<Array<{pageNum: number, width: number, height: number}>>([])
const canvasRefs = ref<Record<number, HTMLCanvasElement>>({})
const fitMode = ref<'width' | 'height' | 'none'>('none')
const containerWidth = ref(800) // 默认容器宽度

// 计算页面样式
const getPageStyle = computed(() => {
  return (page: {pageNum: number, width: number, height: number}) => {
    let width = page.width * zoom.value
    let height = page.height * zoom.value
    
    // 如果启用适应宽度模式
    if (fitMode.value === 'width' && pdfViewer.value) {
      const viewerWidth = pdfViewer.value.clientWidth - 40 // 减去padding
      if (viewerWidth > 0 && width > viewerWidth) {
        const scale = viewerWidth / width
        width = viewerWidth
        height = height * scale
      }
    }
    
    return {
      width: `${width}px`,
      height: `${height}px`,
      margin: '15px auto',
      maxWidth: '100%' // 确保不会超出容器
    }
  }
})

// 加载PDF文档
const loadPdf = async () => {
  if (!props.pdfUrl) {
    error.value = 'PDF URL不能为空'
    return
  }

  loading.value = true
  error.value = ''
  fallbackRendering.value = false // 重置备用渲染状态
  
  // 清理旧的blob URL
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
    pdfBlobUrl.value = ''
  }
  
  try {
    console.log('开始加载PDF:', props.pdfUrl)
    
    // 确保PDF.js库已加载
    const pdf = await loadPdfJs()
    
    // 使用fetch API获取PDF文件，以便添加认证头
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
    pdfBlobUrl.value = pdfUrl // 存储以备备用渲染使用
    
    // 使用blob URL加载PDF
    console.log('使用PDF.js加载文档...')
    const loadingTask = pdf.getDocument({
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
    
    // 注意：不再在此处清理blob URL，保留以备备用渲染使用，将在组件卸载时清理
    console.log('PDF加载完成')
    
  } catch (err: any) {
    console.error('PDF加载失败:', err)
    console.error('错误堆栈:', err.stack)
    const msg = err?.message || err?.name || '未知错误'
    // 区分常见错误，给出可操作的提示
    if (/404/.test(msg) || /Failed to fetch/.test(msg)) {
      error.value = '合同文件不存在或已被删除，请重新上传后再预览'
    } else if (/Invalid PDF|structure/i.test(msg)) {
      error.value = '该文件不是有效的PDF文档，无法在线预览，请点击"下载合同"查看'
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
  
  // 使用项目的getToken函数获取token（支持Cookies和localStorage）
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

  // 如果已启用备用渲染，跳过canvas渲染
  if (fallbackRendering.value) {
    console.log('已启用备用渲染，跳过canvas渲染')
    return
  }

  try {
    console.log(`开始渲染第${pageNum}页...`)
    
    // 尝试获取页面，处理可能的私有字段访问错误
    let page
    try {
      page = await pdfDoc.value.getPage(pageNum)
      console.log(`第${pageNum}页获取成功`)
    } catch (getPageError: any) {
      console.error(`获取页面${pageNum}失败:`, getPageError)
      
      // 如果是私有字段访问错误，启用备用渲染
      if (getPageError.message.includes('private field') || getPageError.message.includes('Cannot read from private field')) {
        console.log('检测到私有字段访问错误，启用备用iframe渲染')
        fallbackRendering.value = true
        return // 跳过canvas渲染，让模板显示iframe
      } else {
        throw getPageError
      }
    }
    
    // 设置渲染比例
    const viewport = page.getViewport({ scale: 1.5 })
    console.log(`页面尺寸: ${viewport.width}x${viewport.height}`)
    
    const canvas = canvasRefs.value[pageNum]
    
    if (!canvas) {
      console.log(`没有找到页面${pageNum}的canvas，创建新的...`)
      // 如果没有canvas，添加到渲染列表
      renderedPages.value = renderedPages.value.filter(p => p.pageNum !== pageNum)
      renderedPages.value.push({
        pageNum,
        width: viewport.width,
        height: viewport.height
      })
      
      // 等待DOM更新
      await nextTick()
      
      // 获取实际的canvas元素
      const actualCanvas = canvasRefs.value[pageNum]
      if (!actualCanvas) {
        console.error(`页面${pageNum}的canvas元素未找到`)
        return
      }
      
      console.log(`渲染到新canvas...`)
      await renderToCanvas(page, actualCanvas, viewport)
    } else {
      console.log(`使用现有canvas渲染...`)
      await renderToCanvas(page, canvas, viewport)
    }
    
    console.log(`第${pageNum}页渲染完成`)
  } catch (err: any) {
    console.error(`渲染第${pageNum}页失败:`, err)
    console.error('错误详情:', err.message)
    console.error('错误堆栈:', err.stack)
    error.value = `渲染页面失败: ${err.message}`
  }
}

// 渲染到canvas
const renderToCanvas = async (page: any, canvas: HTMLCanvasElement, viewport: any) => {
  const context = canvas.getContext('2d')
  if (!context) {
    console.error('无法获取canvas 2d上下文')
    return
  }

  // 设置canvas尺寸
  canvas.width = viewport.width
  canvas.height = viewport.height

  console.log(`开始渲染canvas，尺寸: ${canvas.width}x${canvas.height}`)
  
  try {
    // PDF.js 3.x版本渲染方法
    // 方法1：尝试使用标准renderContext
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }
    
    console.log('使用标准renderContext渲染...')
    const renderTask = page.render(renderContext)
    
    // 等待渲染完成
    await renderTask
    console.log('Canvas渲染完成')
    
  } catch (err: any) {
    console.error('PDF渲染失败，尝试备用方法:', err)
    
    try {
      // 方法2：尝试使用更简单的参数
      console.log('尝试备用渲染方法...')
      await page.render({
        canvasContext: context,
        viewport: viewport,
        intent: 'display'
      })
      console.log('备用渲染方法成功')
    } catch (err2: any) {
      console.error('所有渲染方法都失败:', err2)
      throw new Error(`PDF渲染失败: ${err2.message || '未知错误'}`)
    }
  }
}

// 设置canvas引用
const setCanvasRef = (el: any, pageNum: number) => {
  if (el) {
    canvasRefs.value[pageNum] = el
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
}

// 缩小
const zoomOut = () => {
  zoom.value = Math.max(0.5, zoom.value - 0.1)
}

// 切换适应宽度模式
const toggleFitWidth = () => {
  if (fitMode.value === 'width') {
    fitMode.value = 'none'
  } else {
    fitMode.value = 'width'
    // 自动调整缩放以适应宽度
    if (renderedPages.value.length > 0 && pdfViewer.value) {
      const page = renderedPages.value[0]
      const viewerWidth = pdfViewer.value.clientWidth - 40
      if (viewerWidth > 0 && page.width > 0) {
        const targetZoom = viewerWidth / page.width
        zoom.value = Math.min(Math.max(targetZoom, 0.5), 3)
      }
    }
  }
}

// 全屏切换
const toggleFullscreen = () => {
  if (!pdfContainer.value) return
  
  if (!document.fullscreenElement) {
    pdfContainer.value.requestFullscreen?.()
  } else {
    document.exitFullscreen?.()
  }
}

// 监听容器大小变化
const updateContainerSize = () => {
  if (pdfViewer.value) {
    containerWidth.value = pdfViewer.value.clientWidth
    // 如果启用适应宽度模式，重新计算缩放
    if (fitMode.value === 'width' && renderedPages.value.length > 0) {
      const page = renderedPages.value[0]
      const viewerWidth = pdfViewer.value.clientWidth - 40
      if (viewerWidth > 0 && page.width > 0) {
        const targetZoom = viewerWidth / page.width
        zoom.value = Math.min(Math.max(targetZoom, 0.5), 3)
      }
    }
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
  
  // 监听窗口大小变化
  window.addEventListener('resize', updateContainerSize)
  
  // 监听全屏变化
  document.addEventListener('fullscreenchange', updateContainerSize)
  
  // 初始更新容器大小
  setTimeout(updateContainerSize, 100)
})

onUnmounted(() => {
  // 清理资源
  if (pdfDoc.value) {
    pdfDoc.value.destroy()
  }

  // 清理blob URL
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
  }
  
  // 移除事件监听器
  window.removeEventListener('resize', updateContainerSize)
  document.removeEventListener('fullscreenchange', updateContainerSize)
})

// 暴露方法给父组件
defineExpose({
  loadPdf,
  prevPage,
  nextPage,
  goToPage,
  zoomIn,
  zoomOut,
  toggleFullscreen,
  toggleFitWidth,
  updateContainerSize
})
</script>

<style scoped lang="scss">
.pdf-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 800px; /* 进一步增加最小高度 */
  
  .pdf-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: #f5f7fa;
    border-bottom: 1px solid #e4e7ed;
    flex-shrink: 0;
    
    .controls-left {
      display: flex;
      align-items: center;
      gap: 15px;
      
      .fit-button {
        &.active-fit {
          color: #409EFF;
          background-color: #ecf5ff;
        }
      }
    }
    
    .page-info {
      margin: 0 15px;
      font-size: 14px;
      color: #606266;
      font-weight: 500;
    }
    
    .controls-right {
      display: flex;
      align-items: center;
      gap: 10px;
      
      .zoom-controls {
        display: flex;
        align-items: center;
        gap: 5px;
        
        .zoom-percentage {
          font-size: 14px;
          color: #606266;
          min-width: 45px;
          text-align: center;
        }
      }
    }
  }
  
  .pdf-container {
    flex: 1 1 auto;
    overflow: auto;
    position: relative;
    min-height: 700px; /* 显著增加容器最小高度 */
    
    .pdf-loading, .pdf-error {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      height: 100%;
      min-height: 700px;
      color: #909399;
      
      .loading-icon {
        animation: rotate 2s linear infinite;
        margin-bottom: 15px;
      }
      
      .error-icon {
        color: #f56c6c;
        margin-bottom: 15px;
      }
      
      .loading-tip, .error-tip {
        font-size: 12px;
        color: #c0c4cc;
        margin-top: 10px;
      }
    }
    
    .pdf-viewer {
      padding: 25px;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 700px;
      
      .pdf-page {
        display: block;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
        background: white;
        border-radius: 4px;
        max-width: 100%;
        
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        
        &:hover {
          box-shadow: 0 8px 30px 0 rgba(0, 0, 0, 0.25);
          transform: translateY(-2px);
        }
      }
    }
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .pdf-preview {
    .pdf-controls {
      flex-wrap: wrap;
      gap: 10px;
      
      .controls-left, .controls-right {
        width: 100%;
        justify-content: space-between;
      }
    }
  }
}

@media (max-width: 768px) {
  .pdf-preview {
    min-height: 700px;
    
    .pdf-controls {
      flex-direction: column;
      align-items: stretch;
      gap: 10px;
      padding: 10px;
      
      .controls-left {
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
        
        .page-info {
          margin: 0;
          text-align: center;
        }
      }
      
      .controls-right {
        flex-direction: column;
        gap: 8px;
        
        .zoom-controls {
          justify-content: center;
        }
      }
    }
    
    .pdf-container {
      min-height: 600px;
      
      .pdf-viewer {
        padding: 15px;
        
        .pdf-page {
          box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
        }
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