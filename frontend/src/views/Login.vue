<template>
  <div class="login-container">
    <div class="login-wrapper">
      <div class="login-left">
        <div class="login-header">
          <h1 class="login-title">智能合同审查平台</h1>
          <p class="login-subtitle">AI驱动的中小企业合同智能审核系统</p>
        </div>
        
        <div class="login-features">
          <div class="feature-item">
            <el-icon class="feature-icon"><Document /></el-icon>
            <div class="feature-content">
              <h3>智能合同解析</h3>
              <p>支持PDF、Word等多种格式，自动提取关键信息</p>
            </div>
          </div>
          
          <div class="feature-item">
            <el-icon class="feature-icon"><Checked /></el-icon>
            <div class="feature-content">
              <h3>AI风险识别</h3>
              <p>基于法律大模型，自动识别合同风险点</p>
            </div>
          </div>
          
          <div class="feature-item">
            <el-icon class="feature-icon"><Edit /></el-icon>
            <div class="feature-content">
              <h3>智能修订建议</h3>
              <p>提供专业的合同修改建议和条款优化</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="login-right">
        <div class="login-card">
          <div class="login-card-header">
            <h2>用户登录</h2>
            <p>欢迎回来，请登录您的账户</p>
          </div>
          
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            
            <el-form-item>
              <div class="login-options">
                <el-checkbox v-model="rememberMe">记住我</el-checkbox>
                <el-link type="primary" :underline="false">忘记密码？</el-link>
              </div>
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-btn"
                :loading="loading"
                @click="handleLogin"
              >
                登录
              </el-button>
            </el-form-item>
            
            <div class="login-footer">
              <p>
                还没有账户？
                <el-link type="primary" :underline="false" @click="goToRegister">
                  立即注册
                </el-link>
              </p>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Document, Checked, Edit } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 表单数据
const loginForm = reactive({
  username: '',
  password: '',
})

// 表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
  ],
}

// 状态
const loading = ref(false)
const rememberMe = ref(false)

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    loading.value = true
    
    await userStore.login(loginForm.username, loginForm.password)
    
    ElMessage.success('登录成功')
    
    // 跳转到首页或重定向页面
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/dashboard')
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}

// 跳转到注册页面
const goToRegister = () => {
  router.push('/register')
}

// 页面加载时检查记住我
onMounted(() => {
  const savedUsername = localStorage.getItem('remembered_username')
  if (savedUsername) {
    loginForm.username = savedUsername
    rememberMe.value = true
  }
})
</script>

<style lang="scss" scoped>
.login-container {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-wrapper {
  width: 100%;
  max-width: 1200px;
  height: 700px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  overflow: hidden;
}

.login-left {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
}

.login-header {
  margin-bottom: 60px;
}

.login-title {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 10px;
  line-height: 1.2;
}

.login-subtitle {
  font-size: 16px;
  opacity: 0.9;
}

.login-features {
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

.login-right {
  flex: 1;
  padding: 60px 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 400px;
}

.login-card-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-card-header h2 {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
}

.login-card-header p {
  font-size: 14px;
  color: #666;
}

.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }
  
  :deep(.el-input__wrapper) {
    border-radius: 8px;
    padding: 0 15px;
  }
  
  :deep(.el-input__prefix) {
    margin-right: 10px;
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
}

.login-footer {
  text-align: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  
  p {
    color: #666;
    font-size: 14px;
  }
}

// 响应式设计
@media (max-width: 992px) {
  .login-wrapper {
    flex-direction: column;
    height: auto;
    max-height: 90vh;
    overflow-y: auto;
  }
  
  .login-left {
    padding: 40px 20px;
  }
  
  .login-right {
    padding: 40px 20px;
  }
  
  .login-features {
    gap: 30px;
  }
  
  .feature-item {
    gap: 15px;
  }
}

@media (max-width: 576px) {
  .login-container {
    padding: 10px;
  }
  
  .login-wrapper {
    border-radius: 10px;
  }
  
  .login-title {
    font-size: 28px;
  }
  
  .login-card-header h2 {
    font-size: 24px;
  }
}
</style>