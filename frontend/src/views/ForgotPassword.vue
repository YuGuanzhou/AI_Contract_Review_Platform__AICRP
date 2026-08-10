<template>
  <div class="forgot-container">
    <div class="forgot-card">
      <div class="forgot-header">
        <h1 class="forgot-title">智能合同审查平台</h1>
        <h2 class="forgot-subtitle">找回密码</h2>
        <p>请输入注册邮箱，我们将发送密码重置链接给您</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="forgot-form"
        @submit.prevent="handleSubmit"
      >
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="请输入注册邮箱"
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="forgot-btn"
            :loading="loading"
            @click="handleSubmit"
          >
            发送重置链接
          </el-button>
        </el-form-item>

        <div class="forgot-footer">
          <el-link type="primary" :underline="false" @click="goToLogin">
            返回登录
          </el-link>
        </div>
      </el-form>

      <!-- 提交成功提示 / 开发模式重置链接 -->
      <el-alert
        v-if="submitted"
        type="success"
        :closable="false"
        show-icon
        class="result-alert"
      >
        <template #title>
          {{ resultMessage }}
        </template>
        <div v-if="devResetLink" class="dev-link">
          <p class="dev-tip">当前未配置邮件服务，请使用以下开发模式链接（有效期内可直接访问）：</p>
          <a :href="devResetLink" class="link-text">{{ devResetLink }}</a>
          <el-button size="small" class="copy-btn" @click="copyLink">复制链接</el-button>
        </div>
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Message } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'

const router = useRouter()

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitted = ref(false)
const resultMessage = ref('')
const devResetLink = ref('')

const form = reactive({
  email: '',
})

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    loading.value = true

    const response = await authApi.forgotPassword(form.email)

    // 无论邮箱是否存在，后端都返回统一成功提示（防止枚举）
    resultMessage.value = response.message || '如果该邮箱已注册，重置链接已发送，请查收'

    // 开发模式：SMTP 未配置时后端返回重置链接
    const resp = response as any
    if (resp?.dev_mode && resp?.reset_link) {
      devResetLink.value = resp.reset_link
    } else {
      devResetLink.value = ''
    }

    submitted.value = true
  } catch (error) {
    console.error('发送重置链接失败:', error)
    ElMessage.error('发送失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(devResetLink.value)
    ElMessage.success('已复制重置链接')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.forgot-container {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.forgot-card {
  width: 100%;
  max-width: 460px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 50px 44px;
}

.forgot-header {
  text-align: center;
  margin-bottom: 32px;

  .forgot-title {
    font-size: 20px;
    font-weight: bold;
    color: #333;
    margin-bottom: 20px;
  }

  .forgot-subtitle {
    font-size: 26px;
    font-weight: bold;
    color: #333;
    margin-bottom: 10px;
  }

  p {
    font-size: 14px;
    color: #666;
  }
}

.forgot-btn {
  width: 100%;
  height: 46px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
}

.forgot-footer {
  text-align: center;
  margin-top: 10px;
}

.result-alert {
  margin-top: 20px;
}

.dev-link {
  margin-top: 12px;

  .dev-tip {
    font-size: 12px;
    color: #999;
    margin-bottom: 8px;
  }

  .link-text {
    font-size: 12px;
    color: #409eff;
    word-break: break-all;
    display: inline-block;
    margin-bottom: 8px;
  }

  .copy-btn {
    margin-left: 8px;
  }
}
</style>
