<template>
  <div class="contract-upload">
    <div class="header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">仪表板</el-breadcrumb-item>
        <el-breadcrumb-item>上传合同</el-breadcrumb-item>
      </el-breadcrumb>
      <h1>上传合同</h1>
      <p class="subtitle">上传合同文件进行AI智能审核</p>
    </div>

    <el-card class="upload-card">
      <template #header>
        <h3>合同信息</h3>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        :disabled="uploading"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="合同标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入合同标题，例如：XX公司采购合同"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="合同描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入合同描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="合同类型" prop="contract_type">
          <el-select
            v-model="form.contract_type"
            placeholder="请选择合同类型"
            style="width: 100%"
          >
            <el-option label="采购合同" value="purchase" />
            <el-option label="销售合同" value="sales" />
            <el-option label="服务合同" value="service" />
            <el-option label="劳动合同" value="employment" />
            <el-option label="租赁合同" value="lease" />
            <el-option label="合作协议" value="partnership" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="合同文件" prop="file">
          <el-upload
            class="upload-demo"
            drag
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
            :auto-upload="false"
            :file-list="fileList"
            :limit="1"
            :on-exceed="handleExceed"
            accept=".pdf,.doc,.docx,.txt"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、Word、TXT 等格式，单个文件大小不超过 50MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="uploading"
            @click="handleSubmit"
          >
            提交上传
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { uploadContract } from '@/api/contract'

const router = useRouter()

// 表单数据
const form = reactive({
  title: '',
  description: '',
  contract_type: 'other',
})

// 文件列表
const fileList = ref<any[]>([])

// 上传状态
const uploading = ref(false)

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入合同标题', trigger: 'blur' },
    { min: 2, max: 200, message: '标题长度在 2 到 200 个字符之间', trigger: 'blur' }
  ],
  contract_type: [
    { required: true, message: '请选择合同类型', trigger: 'change' }
  ],
  file: [
    { required: true, message: '请上传合同文件', trigger: 'change' }
  ]
}

// 文件选择变化
const handleFileChange = (file: any, uploadFiles: any[]) => {
  console.log('file changed', file, uploadFiles)
  // 更新文件列表到响应式ref，确保handleSubmit能检测到文件
  fileList.value = uploadFiles
  // 限制只保留一个文件
  if (fileList.value.length > 1) {
    fileList.value.splice(0, fileList.value.length - 1)
  }
}

// 上传前的验证
const beforeUpload = (file: any) => {
  const allowedTypes = ['pdf', 'doc', 'docx', 'txt']
  const extension = file.name.split('.').pop().toLowerCase()
  const isValidType = allowedTypes.includes(extension)
  if (!isValidType) {
    ElMessage.error(`不支持的文件类型：${extension}，请上传 PDF、Word、TXT 文件`)
    return false
  }
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }
  return true
}

// 处理超出限制
const handleExceed = () => {
  ElMessage.warning('最多只能上传一个文件')
}


// 提交表单
const handleSubmit = async () => {
  // 验证文件是否已选择
  if (fileList.value.length === 0) {
    ElMessage.error('请选择要上传的合同文件')
    return
  }

  const file = fileList.value[0].raw
  if (!file) {
    ElMessage.error('文件无效')
    return
  }

  // 验证文件类型和大小
  if (!beforeUpload(file)) {
    return
  }

  uploading.value = true

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', form.title)
    formData.append('description', form.description || '')
    formData.append('contract_type', form.contract_type)

    const response = await uploadContract(formData)
    ElMessage.success(response.message || '合同上传成功，正在启动AI审核...')

    // 跳转到合同详情页
    router.push(`/contracts/${response.contract.id}`)
  } catch (error: any) {
    console.error('上传失败:', error)
    ElMessage.error(error.response?.data?.detail || error.message || '合同上传失败')
  } finally {
    uploading.value = false
  }
}

// 重置表单
const resetForm = () => {
  form.title = ''
  form.description = ''
  form.contract_type = 'other'
  fileList.value = []
}
</script>

<style scoped lang="scss">
.contract-upload {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;

  .header {
    margin-bottom: 24px;

    h1 {
      margin: 12px 0 8px;
      font-size: 28px;
      font-weight: 600;
    }

    .subtitle {
      color: var(--el-text-color-secondary);
      font-size: 16px;
    }
  }

  .upload-card {
    :deep(.el-card__header) {
      padding-bottom: 0;

      h3 {
        margin: 0;
        font-size: 20px;
      }
    }

    :deep(.el-form) {
      margin-top: 20px;
    }

    .el-upload {
      width: 100%;
    }

    .el-upload-dragger {
      width: 100%;
      height: 200px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }
  }
}
</style>