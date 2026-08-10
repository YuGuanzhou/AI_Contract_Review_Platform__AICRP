<template>
  <div class="profile">
    <div class="header">
      <h1>个人中心</h1>
      <p>管理个人信息和账户设置</p>
    </div>

    <div class="profile-content">
      <el-row :gutter="24">
        <el-col :span="7">
          <el-card class="profile-card">
            <template #header>
              <div class="card-header">
                <span>个人信息</span>
                <el-button type="primary" text @click="editProfile">编辑</el-button>
              </div>
            </template>
            <div class="user-info">
              <div class="avatar">
                <el-avatar :size="100" :src="user.avatar" />
                <div class="avatar-upload">
                  <el-button size="small" text @click="changeAvatar">更换头像</el-button>
                </div>
              </div>
              <div class="user-details">
                <h2>{{ user.name }}</h2>
                <p><el-icon><User /></el-icon> {{ user.role }}</p>
                <p><el-icon><Message /></el-icon> {{ user.email }}</p>
                <p><el-icon><Phone /></el-icon> {{ user.phone || '未设置' }}</p>
                <p><el-icon><Calendar /></el-icon> 注册时间: {{ user.registerDate }}</p>
              </div>
            </div>
          </el-card>

        </el-col>

        <el-col :span="17">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="基本信息" name="basic">
              <el-form :model="profileForm" label-width="100px">
                <el-form-item label="用户名">
                  <el-input v-model="profileForm.username" />
                </el-form-item>
                <el-form-item label="真实姓名">
                  <el-input v-model="profileForm.realName" />
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="profileForm.email" />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="profileForm.phone" />
                </el-form-item>
                <el-form-item label="部门">
                  <el-input v-model="profileForm.department" />
                </el-form-item>
                <el-form-item label="职位">
                  <el-input v-model="profileForm.position" />
                </el-form-item>
                
                <!-- 用户角色 -->
                <el-form-item label="用户角色">
                  <div v-if="isAdmin">
                    <el-select
                      v-model="profileForm.role"
                      placeholder="选择用户角色"
                      style="width: 100%"
                    >
                      <el-option label="普通用户" value="user" />
                      <el-option label="审核员" value="reviewer" />
                      <el-option label="管理员" value="admin" />
                    </el-select>
                    <el-text type="info" size="small">只有管理员可以修改用户角色</el-text>
                  </div>
                  <div v-else>
                    <el-input
                      v-model="profileForm.roleDisplay"
                      readonly
                      placeholder="用户角色"
                      style="width: 100%"
                    >
                      <template #append>
                        <el-icon><Lock /></el-icon>
                      </template>
                    </el-input>
                    <el-text type="info" size="small">您的角色不可修改，请联系管理员</el-text>
                  </div>
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" @click="saveProfile">保存修改</el-button>
                  <el-button @click="resetProfile">重置</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="安全设置" name="security">
              <h3>修改密码</h3>
              <el-form :model="passwordForm" label-width="100px" :rules="passwordRules">
                <el-form-item label="当前密码" prop="currentPassword">
                  <el-input v-model="passwordForm.currentPassword" type="password" show-password />
                </el-form-item>
                <el-form-item label="新密码" prop="newPassword">
                  <el-input v-model="passwordForm.newPassword" type="password" show-password />
                </el-form-item>
                <el-form-item label="确认密码" prop="confirmPassword">
                  <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="changePassword">修改密码</el-button>
                </el-form-item>
              </el-form>

            </el-tab-pane>

            <el-tab-pane label="通知偏好" name="notification">
              <el-form label-width="120px">
                <el-form-item label="邮件通知">
                  <el-switch v-model="notificationPrefs.email" />
                  <el-text type="info" style="margin-left: 10px">接收系统邮件通知</el-text>
                </el-form-item>
                <el-form-item label="合同审核提醒">
                  <el-switch v-model="notificationPrefs.contractReview" />
                </el-form-item>
                <el-form-item label="系统公告">
                  <el-switch v-model="notificationPrefs.announcement" />
                </el-form-item>
                <el-form-item label="每周报告">
                  <el-switch v-model="notificationPrefs.weeklyReport" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveNotificationPrefs">保存偏好</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Message, Phone, Calendar, Briefcase, OfficeBuilding, Document, Check, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import dashboardApi from '@/api/dashboard'
import { authApi } from '@/api/auth'

const userStore = useUserStore()
const activeTab = ref('basic')
const isAdmin = computed(() => userStore.isAdmin)

// 基于实际用户数据的响应式对象
const user = computed(() => {
  const userInfo = userStore.userInfo
  if (!userInfo) {
    return {
      name: '用户',
      role: '未登录',
      email: '',
      phone: '',
      avatar: '',
      registerDate: ''
    }
  }
  
  // 根据角色显示不同的身份信息
  const roleDisplay = getRoleDisplay(userInfo.role)
  
  return {
    name: userInfo.full_name || userInfo.username,
    role: roleDisplay,
    email: userInfo.email,
    phone: '',
    avatar: userInfo.avatar || '',
    registerDate: formatDate(userInfo.created_at)
  }
})

// 根据角色获取显示文本
const getRoleDisplay = (role: string) => {
  const roleMap: Record<string, string> = {
    'admin': '系统管理员',
    'reviewer': '审核员',
    'user': '普通用户',
    'contract_manager': '合同管理员',
    'finance': '财务人员',
    'legal': '法务人员'
  }
  return roleMap[role] || role
}


const profileForm = reactive({
  username: '',
  realName: '',
  email: '',
  phone: '',
  department: '',
  position: '',
  role: '',
  roleDisplay: ''
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' }
  ]
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 初始化用户数据
const initUserData = () => {
  const userInfo = userStore.userInfo
  if (userInfo) {
    profileForm.username = userInfo.username
    profileForm.realName = userInfo.full_name || userInfo.username
    profileForm.email = userInfo.email
    profileForm.phone = ''
    profileForm.department = ''
    profileForm.position = getRoleDisplay(userInfo.role)
    profileForm.role = userInfo.role
    profileForm.roleDisplay = getRoleDisplay(userInfo.role)
  }
}


// 组件挂载时初始化
onMounted(() => {
  initUserData()
})

const notificationPrefs = reactive({
  email: true,
  contractReview: true,
  announcement: false,
  weeklyReport: true
})


const editProfile = () => {
  ElMessage.info('进入编辑模式')
}

const changeAvatar = () => {
  ElMessage.info('更换头像功能开发中')
}

const saveProfile = async () => {
  try {
    // 更新基本信息
    await userStore.updateUserInfo({
      full_name: profileForm.realName,
      phone: profileForm.phone,
      company: profileForm.department
    })
    
    // 如果是管理员并且修改了角色，更新角色
    if (isAdmin.value && profileForm.role && profileForm.role !== userStore.userInfo?.role) {
      try {
        await authApi.updateUserRole(userStore.userInfo!.id, {
          role: profileForm.role
        })
        ElMessage.success('个人信息和用户角色已保存')
        // 刷新用户信息
        await userStore.fetchUserInfo()
      } catch (roleError) {
        ElMessage.error('角色更新失败，但基本信息已保存')
      }
    } else {
      ElMessage.success('个人信息已保存')
    }
  } catch (error) {
    ElMessage.error('保存失败，请重试')
  }
}

const resetProfile = () => {
  initUserData()
  ElMessage.info('已重置为原始信息')
}

const changePassword = async () => {
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
  try {
    await userStore.changePassword({
      old_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword,
      confirm_password: passwordForm.confirmPassword
    })
    ElMessage.success('密码修改成功')
    // 清空表单
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (error) {
    ElMessage.error('密码修改失败')
  }
}

const saveNotificationPrefs = () => {
  ElMessage.success('通知偏好已保存')
}
</script>

<style scoped>
.profile {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 30px;
}

.header h1 {
  margin-bottom: 10px;
  color: #303133;
}

.header p {
  color: #909399;
}

.profile-content {
  margin-top: 20px;
}

.profile-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.avatar {
  position: relative;
  margin-bottom: 20px;
}

.avatar-upload {
  margin-top: 10px;
}

.user-details h2 {
  margin: 10px 0 5px 0;
}

.user-details p {
  margin: 5px 0;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-details .el-icon {
  margin-right: 5px;
}


.stats-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #606266;
}

.stat-value {
  font-weight: bold;
  color: #409EFF;
}

h3 {
  margin: 20px 0 15px 0;
  color: #303133;
}
</style>