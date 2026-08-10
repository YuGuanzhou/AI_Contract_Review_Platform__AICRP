# 智能合同审查平台 - 页面说明

## 已完成页面

### 1. 审核员页面
- **ReviewerDashboard.vue** - 审核员工作台
  - 显示待审核合同统计
  - 今日审核量统计
  - 审核准确率分析
  - 高风险合同提醒
  - 待审核合同列表
  - 快速操作面板
  - 系统通知

- **ReviewerPendingList.vue** - 待审核合同管理
  - 合同筛选和搜索功能
  - 批量操作（通过、标记需修改、拒绝、分配）
  - 合同详细信息展示
  - 分页功能
  - 导出数据功能

### 2. 用户页面
- **UserContractList.vue** - 我的合同
  - 用户合同统计卡片
  - 合同列表展示
  - 审核状态跟踪
  - 风险评分显示
  - 合同操作（查看详情、下载、重新上传、删除）
  - 筛选和搜索功能

### 3. 管理员页面
- **AdminDashboard.vue** - 系统管理控制台
  - 系统概览统计
  - 用户、合同、审核数据统计
  - 系统服务状态监控
  - 实时系统监控（CPU、内存、磁盘使用率）
  - 最近活动记录
  - 系统告警显示
  - 快速操作入口

## 路由配置
已更新路由配置，支持基于角色的访问控制：

### 角色权限
- **普通用户 (user)**: 可以访问用户功能菜单
- **审核员 (reviewer)**: 可以访问用户功能和审核功能菜单
- **管理员 (admin)**: 可以访问所有菜单

### 新增路由
- `/reviewer/dashboard` - 审核员工作台
- `/reviewer/pending` - 待审核合同管理
- `/user/contracts` - 我的合同
- `/admin/dashboard` - 系统管理控制台

## 类型定义
创建了完整的TypeScript类型定义：

### 审核员类型 (`@/types/reviewer.ts`)
- `ReviewerStats` - 审核员统计信息
- `PendingContract` - 待审核合同
- `ReviewRecord` - 审核记录
- `ReviewDetail` - 审核详情

### 管理员类型 (`@/types/admin.ts`)
- `AdminOverview` - 系统概览
- `MonitorData` - 监控数据
- `SystemSettings` - 系统设置
- `ManagedUser` - 用户管理

### 合同类型 (`@/types/contract.ts`)
- `UserContract` - 用户合同
- `ContractStats` - 合同统计
- `ContractDetail` - 合同详情
- `ContractSearchParams` - 搜索参数

## API接口
创建了相应的API接口文件：

### 审核员API (`@/api/reviewer.ts`)
- `getReviewerStats()` - 获取审核员统计
- `getPendingContracts()` - 获取待审核合同
- `assignContracts()` - 分配合同
- `submitReview()` - 提交审核结果

### 管理员API (`@/api/admin.ts`)
- `getOverview()` - 获取系统概览
- `getMonitorData()` - 获取监控数据
- `getUsers()` - 获取用户列表
- `updateSystemSettings()` - 更新系统设置

### 用户合同API (`@/api/userContract.ts`)
- `getUserStats()` - 获取用户合同统计
- `getUserContracts()` - 获取用户合同列表
- `getContractDetail()` - 获取合同详情
- `deleteUserContract()` - 删除用户合同

## 布局更新
更新了主布局 (`MainLayout.vue`)，支持：

### 动态菜单
- 根据用户角色显示不同的菜单项
- 用户角色徽章显示
- 响应式设计

### 菜单结构
1. **通用菜单**: 仪表板、个人中心、帮助中心
2. **用户菜单**: 我的合同、上传合同、我的模板
3. **审核员菜单**: 审核工作台、待审核合同、审核记录、审核统计
4. **管理员菜单**: 管理控制台、用户管理、审核员管理、合同管理、系统设置

## AI审核流程实现

### 用户端流程
1. 用户上传合同 → 自动触发AI审核
2. AI分析合同内容，识别风险点和问题
3. 生成风险评分和审核报告
4. 合同进入待审核队列

### 审核员端流程
1. 查看待审核合同列表
2. 查看AI审核结果和建议
3. 进行人工核对和确认
4. 提交审核结果（通过/需修改/拒绝）
5. 系统通知用户审核结果

### 管理员端流程
1. 监控整个系统运行状态
2. 管理用户和审核员账户
3. 查看所有合同和审核记录
4. 配置系统参数和AI模型
5. 处理系统告警和异常

## 技术特点

### 前端技术栈
- Vue 3 + Composition API
- TypeScript
- Element Plus UI组件库
- Pinia状态管理
- Vue Router路由管理
- SCSS样式预处理器

### 代码规范
- 完整的TypeScript类型定义
- 模块化的组件设计
- 响应式布局设计
- 基于角色的权限控制
- 统一的API接口规范

## 下一步开发建议

### 后端接口开发
需要实现以下后端API接口：
1. 审核员相关的统计和操作接口
2. 管理员系统管理接口
3. 用户合同管理接口
4. AI审核服务接口

### 功能完善
1. 合同详情页面优化
2. 审核流程可视化
3. 实时通知系统
4. 数据导出和报表功能
5. 移动端适配优化

### 测试和部署
1. 单元测试和集成测试
2. 性能优化
3. 安全加固
4. 生产环境部署配置