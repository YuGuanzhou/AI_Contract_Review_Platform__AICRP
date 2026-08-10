import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false,
    },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: {
      title: '注册',
      requiresAuth: false,
    },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: {
      title: '忘记密码',
      requiresAuth: false,
    },
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPassword.vue'),
    meta: {
      title: '重置密码',
      requiresAuth: false,
    },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          title: '仪表板',
          icon: 'Odometer',
        },
      },
      {
        path: 'review/workstation',
        name: 'ReviewWorkstation',
        component: () => import('@/views/review/ReviewWorkstation.vue'),
        meta: {
          title: '审核工作站',
          icon: 'Document',
          roles: ['reviewer', 'admin'],
        },
      },
      {
        path: 'contracts/upload',
        name: 'ContractUpload',
        component: () => import('@/views/contract/ContractUpload.vue'),
        meta: {
          title: '上传合同',
          hideInMenu: true,
          roles: ['user', 'admin'],
        },
      },
      {
        path: 'user/contracts',
        name: 'UserContracts',
        component: () => import('@/views/user/UserContracts.vue'),
        meta: {
          title: '我的合同',
          icon: 'Document',
          roles: ['user', 'admin'],
        },
      },
      {
        path: 'contracts/:id',
        name: 'ContractDetail',
        component: () => import('@/views/contract/ContractDetail.vue'),
        meta: {
          title: '合同详情',
          hideInMenu: true,
        },
      },
      {
        path: 'contracts/:id/review',
        name: 'ContractReview',
        component: () => import('@/views/contract/ContractReview.vue'),
        meta: {
          title: '合同审核',
          hideInMenu: true,
          roles: ['reviewer', 'admin'],
        },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: {
          title: '系统设置',
          icon: 'Setting',
        },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Profile.vue'),
        meta: {
          title: '个人中心',
          icon: 'User',
        },
      },
      {
        path: 'help',
        name: 'Help',
        component: () => import('@/views/help/Help.vue'),
        meta: {
          title: '帮助中心',
          icon: 'QuestionFilled',
        },
      },
      {
        path: 'admin/users',
        name: 'admin/users',
        component: () => import('@/views/admin/UserManagement.vue'),
        meta: {
          title: '用户管理',
          icon: 'User',
          roles: ['admin'],
        },
      },
      {
        path: 'admin/contracts',
        name: 'admin/contracts',
        component: () => import('@/views/admin/ContractManagement.vue'),
        meta: {
          title: '合同管理',
          icon: 'Document',
          roles: ['admin'],
        },
      },
    ],
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: {
      title: '页面不存在',
      requiresAuth: false,
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智能合同审查平台`
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (userStore.isAuthenticated) {
      // 检查角色权限
      if (to.meta.roles) {
        const userRole = userStore.userRole
        const allowedRoles = to.meta.roles as string[]
        
        if (allowedRoles.includes(userRole)) {
          next()
        } else {
          // 角色权限不足，重定向到无权限页面或首页
          next('/dashboard')
        }
      } else {
        next()
      }
    } else {
      // 尝试从本地存储恢复登录状态
      await userStore.checkAuth()
      if (userStore.isAuthenticated) {
        // 再次检查角色权限
        if (to.meta.roles) {
          const userRole = userStore.userRole
          const allowedRoles = to.meta.roles as string[]
          
          if (allowedRoles.includes(userRole)) {
            next()
          } else {
            next('/dashboard')
          }
        } else {
          next()
        }
      } else {
        next({
          path: '/login',
          query: { redirect: to.fullPath },
        })
      }
    }
  } else {
    // 如果已经登录，访问登录页则重定向到首页
    if ((to.path === '/login' || to.path === '/register') && userStore.isAuthenticated) {
      next('/dashboard')
    } else {
      next()
    }
  }
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
})

export default router