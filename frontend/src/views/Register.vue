<template>
  <div class="register-container">
    <div class="register-wrapper">
      <div class="register-left">
        <div class="register-header">
          <h1 class="register-title">智能合同审查平台</h1>
          <p class="register-subtitle">AI驱动的中小企业合同智能审核系统</p>
        </div>
        
        <div class="register-features">
          <div class="feature-item">
            <el-icon class="feature-icon"><User /></el-icon>
            <div class="feature-content">
              <h3>快速注册</h3>
              <p>只需填写基本信息，立即开始使用智能合同审查服务</p>
            </div>
          </div>
          
          <div class="feature-item">
            <el-icon class="feature-icon"><Lock /></el-icon>
            <div class="feature-content">
              <h3>安全可靠</h3>
              <p>采用银行级加密技术，保障您的账户和数据安全</p>
            </div>
          </div>
          
          <div class="feature-item">
            <el-icon class="feature-icon"><Document /></el-icon>
            <div class="feature-content">
              <h3>免费使用</h3>
              <p>目前开放给全部用户使用，开放所有功能</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="register-right">
        <div class="register-card">
          <div class="register-card-header">
            <h2>用户注册</h2>
            <p>创建您的账户，开始智能合同审查之旅</p>
          </div>
          
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            class="register-form"
            @submit.prevent="handleRegister"
          >
            <el-form-item prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请输入用户名（3-20个字符）"
                size="large"
                :prefix-icon="User"
                @blur="checkUsernameAvailability"
              />
              <div v-if="usernameChecking" class="checking-text">
                <el-icon class="loading-icon"><Loading /></el-icon>
                检查用户名可用性...
              </div>
              <div v-else-if="usernameAvailable !== null" class="availability-text" :class="usernameAvailable ? 'available' : 'unavailable'">
                <el-icon><CircleCheck v-if="usernameAvailable" /><CircleClose v-else /></el-icon>
                {{ usernameAvailable ? '用户名可用' : '用户名已被占用' }}
              </div>
            </el-form-item>
            
            <el-form-item prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="请输入邮箱地址"
                size="large"
                :prefix-icon="Message"
                @blur="checkEmailAvailability"
              />
              <div v-if="emailChecking" class="checking-text">
                <el-icon class="loading-icon"><Loading /></el-icon>
                检查邮箱可用性...
              </div>
              <div v-else-if="emailAvailable !== null" class="availability-text" :class="emailAvailable ? 'available' : 'unavailable'">
                <el-icon><CircleCheck v-if="emailAvailable" /><CircleClose v-else /></el-icon>
                {{ emailAvailable ? '邮箱可用' : '邮箱已被注册' }}
              </div>
            </el-form-item>
            
            <el-form-item prop="fullName">
              <el-input
                v-model="registerForm.fullName"
                placeholder="请输入真实姓名（可选）"
                size="large"
                :prefix-icon="UserFilled"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码（至少6位）"
                size="large"
                :prefix-icon="Lock"
                show-password
                @input="checkPasswordStrength"
              />
              <div class="password-strength">
                <div class="strength-bar" :class="passwordStrengthClass"></div>
                <div class="strength-text">{{ passwordStrengthText }}</div>
              </div>
            </el-form-item>
            
            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请确认密码"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
              <div v-if="registerForm.password && registerForm.confirmPassword" class="password-match" :class="passwordsMatch ? 'match' : 'mismatch'">
                <el-icon><CircleCheck v-if="passwordsMatch" /><CircleClose v-else /></el-icon>
                {{ passwordsMatch ? '密码匹配' : '密码不匹配' }}
              </div>
            </el-form-item>
            
            <el-form-item prop="agreement">
              <el-checkbox v-model="registerForm.agreement">
                我已阅读并同意
                <el-link type="primary" :underline="false" @click="showTermsDialog">《用户协议》</el-link>
                和
                <el-link type="primary" :underline="false" @click="showPrivacyDialog">《隐私政策》</el-link>
              </el-checkbox>
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="register-btn"
                :loading="loading"
                :disabled="!canSubmit"
                @click="handleRegister"
              >
                立即注册
              </el-button>
            </el-form-item>
            
            <div class="register-footer">
              <p>
                已有账户？
                <el-link type="primary" :underline="false" @click="goToLogin">
                  立即登录
                </el-link>
              </p>
            </div>
          </el-form>
        </div>
      </div>
    </div>
    
    <!-- 用户协议对话框 -->
    <el-dialog
      v-model="termsDialogVisible"
      title="用户协议"
      width="600px"
      append-to-body
    >
      <div class="terms-content">
        <h3>智能合同审查平台用户协议</h3>
        <p>欢迎使用智能合同审查平台！请仔细阅读以下条款...</p>
        <!-- 这里可以添加完整的用户协议内容 -->
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="termsDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="acceptTerms">同意并继续</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 隐私政策对话框 -->
    <el-dialog
      v-model="privacyDialogVisible"
      title="隐私政策"
      width="600px"
      append-to-body
    >
      <div class="privacy-content">
        <h3>隐私政策</h3>
        <p>我们非常重视您的隐私保护...</p>
        <!-- 这里可以添加完整的隐私政策内容 -->
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="privacyDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  User,
  Lock,
  Message,
  UserFilled,
  OfficeBuilding,
  Loading,
  CircleCheck,
  CircleClose,
  Document,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const registerFormRef = ref<FormInstance>()

// 表单数据
const registerForm = reactive({
  username: '',
  email: '',
  fullName: '',
  password: '',
  confirmPassword: '',
  agreement: false,
})

// 状态
const loading = ref(false)
const usernameChecking = ref(false)
const usernameAvailable = ref<boolean | null>(null)
const emailChecking = ref(false)
const emailAvailable = ref<boolean | null>(null)
const passwordStrength = ref(0) // 0-4
const termsDialogVisible = ref(false)
const privacyDialogVisible = ref(false)

// 计算属性
const passwordsMatch = computed(() => {
  return registerForm.password === registerForm.confirmPassword
})

const passwordStrengthClass = computed(() => {
  if (passwordStrength.value === 0) return 'strength-0'
  if (passwordStrength.value === 1) return 'strength-1'
  if (passwordStrength.value === 2) return 'strength-2'
  if (passwordStrength.value === 3) return 'strength-3'
  return 'strength-4'
})

const passwordStrengthText = computed(() => {
  if (passwordStrength.value === 0) return '密码强度：弱'
  if (passwordStrength.value === 1) return '密码强度：较弱'
  if (passwordStrength.value === 2) return '密码强度：中等'
  if (passwordStrength.value === 3) return '密码强度：强'
  return '密码强度：非常强'
})

const canSubmit = computed(() => {
  return (
    registerForm.username &&
    registerForm.email &&
    registerForm.password &&
    registerForm.confirmPassword &&
    passwordsMatch.value &&
    registerForm.agreement &&
    usernameAvailable.value === true &&
    emailAvailable.value === true
  )
})

// 表单验证规则
const validateUsername = (rule: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error('请输入用户名'))
  } else if (value.length < 3 || value.length > 20) {
    callback(new Error('用户名长度在 3 到 20 个字符'))
  } else if (!/^[a-zA-Z0-9_]+$/.test(value)) {
    callback(new Error('用户名只能包含字母、数字和下划线'))
  } else {
    callback()
  }
}

const validateEmail = (rule: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error('请输入邮箱地址'))
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    callback(new Error('请输入有效的邮箱地址'))
  } else {
    callback()
  }
}

const validatePassword = (rule: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error('请输入密码'))
  } else if (value.length < 6) {
    callback(new Error('密码长度至少为6位'))
  } else {
    callback()
  }
}

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error('请确认密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validateAgreement = (rule: any, value: boolean, callback: any) => {
  if (!value) {
    callback(new Error('请阅读并同意用户协议和隐私政策'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  username: [
    { validator: validateUsername, trigger: 'blur' },
  ],
  email: [
    { validator: validateEmail, trigger: 'blur' },
  ],
  password: [
    { validator: validatePassword, trigger: 'blur' },
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
  agreement: [
    { validator: validateAgreement, trigger: 'change' },
  ],
}

// 检查用户名可用性
const checkUsernameAvailability = async () => {
  if (!registerForm.username || registerForm.username.length < 3) {
    usernameAvailable.value = null
    return
  }
  
  usernameChecking.value = true
  try {
    const response = await authApi.checkUsernameAvailability(registerForm.username)
    usernameAvailable.value = response.available
  } catch (error) {
    console.error('检查用户名失败:', error)
    usernameAvailable.value = null
  } finally {
    usernameChecking.value = false
  }
}

// 检查邮箱可用性
const checkEmailAvailability = async () => {
  if (!registerForm.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)) {
    emailAvailable.value = null
    return
  }
  
  emailChecking.value = true
  try {
    const response = await authApi.checkEmailAvailability(registerForm.email)
    emailAvailable.value = response.available
  } catch (error) {
    console.error('检查邮箱失败:', error)
    emailAvailable.value = null
  } finally {
    emailChecking.value = false
  }
}

// 检查密码强度
const checkPasswordStrength = () => {
  const password = registerForm.password
  if (!password) {
    passwordStrength.value = 0
    return
  }
  
  let strength = 0
  
  // 长度评分
  if (password.length >= 6) strength += 1
  if (password.length >= 8) strength += 1
  
  // 复杂度评分
  if (/[a-z]/.test(password)) strength += 1
  if (/[A-Z]/.test(password)) strength += 1
  if (/[0-9]/.test(password)) strength += 1
  if (/[^a-zA-Z0-9]/.test(password)) strength += 1
  
  // 限制最大强度为4
  passwordStrength.value = Math.min(strength, 4)
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  try {
    await registerFormRef.value.validate()
    
    if (!canSubmit.value) {
      ElMessage.warning('请完成所有必填项并确保信息正确')
      return
    }
    
    loading.value = true
    
    // 调用注册API
    const response = await authApi.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      full_name: registerForm.fullName || undefined,
    })
    
    ElMessage.success('注册成功！')
    
    // 注册成功后自动登录
    try {
      await userStore.login(registerForm.username, registerForm.password)
      ElMessage.success('自动登录成功')
      
      // 跳转到首页
      router.push('/dashboard')
    } catch (loginError) {
      console.error('自动登录失败:', loginError)
      // 如果自动登录失败，跳转到登录页面
      router.push('/login')
    }
  } catch (error: any) {
    console.error('注册失败:', error)
    
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error.message) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('注册失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// 跳转到登录页面
const goToLogin = () => {
  router.push('/login')
}

// 显示用户协议对话框
const showTermsDialog = () => {
  termsDialogVisible.value = true
}

// 显示隐私政策对话框
const showPrivacyDialog = () => {
  privacyDialogVisible.value = true
}

// 同意用户协议
const acceptTerms = () => {
  registerForm.agreement = true
  termsDialogVisible.value = false
  ElMessage.success('已同意用户协议')
}

// 监听表单变化
watch(() => registerForm.username, () => {
  usernameAvailable.value = null
})

watch(() => registerForm.email, () => {
  emailAvailable.value = null
})
</script>

<style lang="scss" scoped>
.register-container {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.register-wrapper {
  width: 100%;
  max-width: 1200px;
  height: 700px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  overflow: hidden;
}

.register-left {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
}

.register-header {
  margin-bottom: 60px;
}

.register-title {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 10px;
  line-height: 1.2;
}

.register-subtitle {
  font-size: 16px;
  opacity: 0.9;
}
.register-features {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.feature-icon {
  font-size: 32px;
  margin-top: 5px;
  flex-shrink: 0;
}

.feature-content h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.feature-content p {
  font-size: 14px;
  opacity: 0.8;
  line-height: 1.5;
}

.register-right {
  flex: 1;
  padding: 60px 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
}

.register-card {
  width: 100%;
  max-width: 400px;
}

.register-card-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-card-header h2 {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
}

.register-card-header p {
  font-size: 14px;
  color: #666;
}

.register-form {
  .el-form-item {
    margin-bottom: 20px;
  }
  
  :deep(.el-input__wrapper) {
    border-radius: 8px;
    padding: 0 15px;
  }
  
  :deep(.el-input__prefix) {
    margin-right: 10px;
  }
}

.checking-text {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.availability-text {
  font-size: 12px;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  
  &.available {
    color: #67c23a;
  }
  
  &.unavailable {
    color: #f56c6c;
  }
}

.password-strength {
  margin-top: 8px;
}

.strength-bar {
  height: 4px;
  border-radius: 2px;
  margin-bottom: 4px;
  transition: all 0.3s;
  
  &.strength-0 {
    width: 25%;
    background-color: #f56c6c;
  }
  
  &.strength-1 {
    width: 50%;
    background-color: #e6a23c;
  }
  
  &.strength-2 {
    width: 75%;
    background-color: #e6a23c;
  }
  
  &.strength-3 {
    width: 100%;
    background-color: #67c23a;
  }
  
  &.strength-4 {
    width: 100%;
    background-color: #67c23a;
  }
}

.strength-text {
  font-size: 12px;
  color: #666;
}

.password-match {
  font-size: 12px;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  
  &.match {
    color: #67c23a;
  }
  
  &.mismatch {
    color: #f56c6c;
  }
}

.register-btn {
  width: 100%;
  height: 48px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.register-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  
  p {
    color: #666;
    font-size: 14px;
  }
}

.terms-content,
.privacy-content {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 10px;
  
  h3 {
    margin-bottom: 15px;
    color: #333;
  }
  
  p {
    margin-bottom: 10px;
    line-height: 1.6;
    color: #666;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

// 响应式设计
@media (max-width: 992px) {
  .register-wrapper {
    flex-direction: column;
    height: auto;
    max-height: 90vh;
    overflow-y: auto;
  }
  
  .register-left {
    padding: 40px 20px;
  }
  
  .register-right {
    padding: 40px 20px;
  }
  
  .register-features {
    gap: 30px;
  }
  
  .feature-item {
    gap: 15px;
  }
}

@media (max-width: 576px) {
  .register-container {
    padding: 10px;
  }
  
  .register-wrapper {
    border-radius: 10px;
  }
  
  .register-title {
    font-size: 28px;
  }
  
  .register-card-header h2 {
    font-size: 24px;
  }
}
</style>

