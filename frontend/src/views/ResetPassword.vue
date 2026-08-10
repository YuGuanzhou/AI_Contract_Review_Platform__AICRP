<template>
  <div class="reset-container">
    <div class="reset-card">
      <div class="reset-header">
        <h1 class="reset-title">智能合同审查平台</h1>
        <h2 class="reset-subtitle">重置密码</h2>

        <!-- 令牌校验中 -->
        <p v-if="checking">正在验证重置链接...</p>

        <!-- 令牌有效 -->
        <template v-else-if="tokenValid">
          <p>请为账户「{{ email }}」设置新密码</p>
        </template>

        <!-- 令牌无效 -->
        <template v-else>
          <p class="invalid-text">重置链接无效或已过期</p>
        </template>
      </div>

      <!-- 有效时显示重置表单 -->
      <el-form
        v-if="tokenValid"
        ref="formRef"
        :model="form"
        :rules="rules"
        class="reset-form"
        @submit.prevent="handleSubmit"
      >
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入新密码（至少6位）"
            size="large"
            :prefix-icon="Lock"
            show-password
            @input="checkPasswordStrength"
          />
          <div class="password-strength">
            <div class="strength-bar" :class="strengthClass"></div>
            <span class="strength-text">{{ strengthText }}</span>
          </div>
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请确认新密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="reset-btn"
            :loading="loading"
            @click="handleSubmit"
          >
            确认重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 无效时提供重新申请入口 -->
      <template v-if="!tokenValid && !checking">
        <el-button type="primary" size="large" class="reset-btn" @click="goToForgot">
          重新申请重置链接
        </el-button>
      </template>

      <div class="reset-footer">
        <el-link type="primary" :underline="false" @click="goToLogin">
          返回登录
        </el-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()

const formRef = ref<FormInstance>()
const loading = ref(false)
const checking = ref(true)
const tokenValid = ref(false)
const email = ref('')
const passwordStrength = ref(0)

const token = computed(() => (route.query.token as string) || '')

const form = reactive({
  password: '',
  confirmPassword: '',
})

const rules: FormRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const strengthClass = computed(() => {
  const levels = ['strength-0', 'strength-1', 'strength-2', 'strength-3', 'strength-4']
  return levels[passwordStrength.value]
})

const strengthText = computed(() => {
  const texts = ['密码强度：弱', '密码强度：较弱', '密码强度：中等', '密码强度：强', '密码强度：非常强']
  return texts[passwordStrength.value]
})

const checkPasswordStrength = () => {
  const pwd = form.password
  if (!pwd) {
    passwordStrength.value = 0
    return
  }
  let strength = 0
  if (pwd.length >= 6) strength += 1
  if (pwd.length >= 8) strength += 1
  if (/[a-z]/.test(pwd)) strength += 1
  if (/[A-Z]/.test(pwd)) strength += 1
  if (/[0-9]/.test(pwd)) strength += 1
  if (/[^a-zA-Z0-9]/.test(pwd)) strength += 1
  passwordStrength.value = Math.min(strength, 4)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    loading.value = true

    await authApi.resetPassword(token.value, form.password, form.confirmPassword)
    ElMessage.success('密码重置成功，请使用新密码登录')

    // 清除 URL 中的 token，避免留在地址栏
    router.replace('/login')
  } catch (error: any) {
    console.error('重置密码失败:', error)
    const detail = error?.response?.data?.detail
    if (detail) {
      ElMessage.error(detail)
    } else {
      ElMessage.error('重置失败，请重试')
    }
  } finally {
    loading.value = false
  }
}

const goToForgot = () => {
  router.push('/forgot-password')
}

const goToLogin = () => {
  router.push('/login')
}

onMounted(async () => {
  if (!token.value) {
    tokenValid.value = false
    checking.value = false
    return
  }
  try {
    const result = await authApi.verifyResetToken(token.value)
    tokenValid.value = result.valid
    email.value = result.email || ''
  } catch (error) {
    console.error('校验重置令牌失败:', error)
    tokenValid.value = false
  } finally {
    checking.value = false
  }
})
</script>

<style lang="scss" scoped>
.reset-container {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.reset-card {
  width: 100%;
  max-width: 440px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 50px 44px;
}

.reset-header {
  text-align: center;
  margin-bottom: 32px;

  .reset-title {
    font-size: 20px;
    font-weight: bold;
    color: #333;
    margin-bottom: 20px;
  }

  .reset-subtitle {
    font-size: 26px;
    font-weight: bold;
    color: #333;
    margin-bottom: 10px;
  }

  p {
    font-size: 14px;
    color: #666;
  }

  .invalid-text {
    color: #f56c6c;
  }
}

.reset-btn {
  width: 100%;
  height: 46px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
}

.reset-footer {
  text-align: center;
  margin-top: 14px;
}

.password-strength {
  margin-top: 8px;

  .strength-bar {
    height: 4px;
    border-radius: 2px;
    margin-bottom: 4px;
    transition: all 0.3s;
  }

  .strength-text {
    font-size: 12px;
    color: #666;
  }

  .strength-0,
  .strength-1 {
    width: 25%;
    background-color: #f56c6c;
  }

  .strength-2 {
    width: 50%;
    background-color: #e6a23c;
  }

  .strength-3 {
    width: 75%;
    background-color: #e6a23c;
  }

  .strength-4 {
    width: 100%;
    background-color: #67c23a;
  }
}
</style>
