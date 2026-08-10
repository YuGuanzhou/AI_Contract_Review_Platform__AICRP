<template>
  <div class="main-layout">
    <header class="header">
      <div class="logo">
        <h1>智能合同审查平台</h1>
        <span class="role-badge" :class="userRoleClass">{{ userRoleText }}</span>
      </div>
      <nav class="nav">
        <router-link to="/dashboard">仪表板</router-link>
        <router-link to="/settings" v-if="showSettingsMenu">系统设置</router-link>
      </nav>
      <div class="user-info">
        <div class="user-details">
          <span class="user-name">欢迎回来，{{ userStore.userName || '用户' }}</span>
          <span class="user-role">{{ userRoleText }}</span>
        </div>
        <el-dropdown @command="handleUserCommand">
          <span class="user-avatar">
            <el-avatar :size="32" :src="userAvatar" />
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                个人中心
              </el-dropdown-item>
              <el-dropdown-item command="settings">
                <el-icon><Setting /></el-icon>
                个人设置
              </el-dropdown-item>
              <el-dropdown-item divided command="help">
                <el-icon><QuestionFilled /></el-icon>
                帮助中心
              </el-dropdown-item>
              <el-dropdown-item command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>
    <div class="content-wrapper">
      <aside class="sidebar">
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          @select="handleMenuSelect"
        >
          <!-- 通用菜单 -->
          <el-menu-item index="Dashboard">
            <el-icon><Odometer /></el-icon>
            <span>仪表板</span>
          </el-menu-item>
          
          <el-menu-item index="ContractUpload" v-if="showUploadMenu">
            <el-icon><Upload /></el-icon>
            <span>上传合同</span>
          </el-menu-item>
          
          <el-menu-item index="UserContracts" v-if="showMyContractsMenu">
            <el-icon><Document /></el-icon>
            <span>我的合同</span>
          </el-menu-item>
          
          <el-menu-item index="ReviewWorkstation" v-if="showReviewerMenu">
            <el-icon><Document /></el-icon>
            <span>审核工作站</span>
          </el-menu-item>
          
          <!-- 管理员菜单 -->
          <el-sub-menu index="admin" v-if="showAdminMenu">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="admin/users">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="admin/contracts">
              <el-icon><Document /></el-icon>
              <span>合同管理</span>
            </el-menu-item>
            <el-menu-item index="Settings">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 通用功能 -->
          <el-menu-item index="Profile">
            <el-icon><User /></el-icon>
            <span>个人中心</span>
          </el-menu-item>
          
          <el-menu-item index="Help">
            <el-icon><QuestionFilled /></el-icon>
            <span>帮助中心</span>
          </el-menu-item>
        </el-menu>
      </aside>
      <main class="main-content">
        <div class="breadcrumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRouteName }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="content-area">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Odometer,
  Document,
  Checked,
  Files,
  Setting,
  User,
  QuestionFilled,
  Upload,
  Clock,
  Histogram,
  TrendCharts,
  Monitor,
  SwitchButton
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 计算属性
const currentRouteName = computed(() => {
  return route.meta?.title || route.name?.toString() || ''
})

const activeMenu = computed(() => {
  return route.name?.toString().toLowerCase() || 'dashboard'
})

const userRole = computed(() => userStore.userRole || 'user')

const userRoleText = computed(() => {
  const roleMap: Record<string, string> = {
    'user': '普通用户',
    'reviewer': '审核员',
    'admin': '管理员'
  }
  return roleMap[userRole.value] || '用户'
})

const userRoleClass = computed(() => {
  return `role-${userRole.value}`
})

const userAvatar = computed(() => {
  // 这里可以根据用户信息返回头像URL
  return ''
})

// 菜单显示控制
const showUserMenu = computed(() => {
  return ['user', 'reviewer', 'admin'].includes(userRole.value)
})


const showReviewerMenu = computed(() => {
  return ['reviewer', 'admin'].includes(userRole.value)
})

const showReviewMenu = computed(() => {
  return ['reviewer', 'admin'].includes(userRole.value)
})

const showAdminMenu = computed(() => {
  return userRole.value === 'admin'
})


const showSettingsMenu = computed(() => {
  return userRole.value === 'admin'
})

const showUploadMenu = computed(() => {
  return userRole.value !== 'reviewer'
})

const showMyContractsMenu = computed(() => {
  return userRole.value !== 'reviewer'
})

// 方法
const handleMenuSelect = (index: string) => {
  router.push({ name: index })
}

const handleUserCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push({ name: 'Profile' })
      break
    case 'settings':
      router.push({ name: 'Settings' })
      break
    case 'help':
      router.push({ name: 'Help' })
      break
    case 'logout':
      handleLogout()
      break
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    // 用户取消退出
    if (error !== 'cancel') {
      ElMessage.error('退出登录失败')
    }
  }
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
    
    h1 {
      font-size: 20px;
      font-weight: 600;
      color: #409eff;
      margin: 0;
    }
    
    .role-badge {
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 500;
      
      &.role-user {
        background-color: #e8f4ff;
        color: #409eff;
      }
      
      &.role-reviewer {
        background-color: #f0f9eb;
        color: #67c23a;
      }
      
      &.role-admin {
        background-color: #fef0f0;
        color: #f56c6c;
      }
    }
  }
  
  .nav {
    display: flex;
    gap: 24px;
    
    a {
      color: #606266;
      text-decoration: none;
      font-size: 14px;
      padding: 4px 8px;
      border-radius: 4px;
      transition: all 0.3s;
      
      &:hover {
        color: #409eff;
        background-color: #f5f7fa;
      }
      
      &.router-link-active {
        color: #409eff;
        font-weight: 500;
        background-color: #ecf5ff;
      }
    }
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .user-details {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      
      .user-name {
        font-size: 14px;
        font-weight: 500;
        color: #303133;
      }
      
      .user-role {
        font-size: 12px;
        color: #909399;
      }
    }
    
    .user-avatar {
      cursor: pointer;
    }
  }
}

.content-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
  
  .sidebar {
    width: 240px;
    background-color: #fff;
    border-right: 1px solid #dcdfe6;
    overflow-y: auto;
    
    .sidebar-menu {
      border-right: none;
      height: 100%;
      
      :deep(.el-menu-item) {
        height: 48px;
        line-height: 48px;
        
        &.is-active {
          background-color: #ecf5ff;
          color: #409eff;
          
          .el-icon {
            color: #409eff;
          }
        }
      }
      
      :deep(.el-sub-menu__title) {
        height: 48px;
        line-height: 48px;
      }
    }
  }
  
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    
    .breadcrumb {
      padding: 16px 24px;
      background-color: #fff;
      border-bottom: 1px solid #dcdfe6;
      
      :deep(.el-breadcrumb) {
        font-size: 14px;
      }
    }
    
    .content-area {
      flex: 1;
      padding: 24px;
      overflow-y: auto;
      background-color: #f5f7fa;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .header {
    .nav {
      display: none;
    }
    
    .user-info {
      .user-details {
        display: none;
      }
    }
  }
  
  .content-wrapper {
    .sidebar {
      width: 200px;
    }
  }
}
</style>