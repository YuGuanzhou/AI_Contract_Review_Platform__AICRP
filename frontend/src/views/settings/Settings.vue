<template>
  <div class="settings">
    <div class="header">
      <h1>系统设置</h1>
      <p>管理系统配置和个性化选项</p>
    </div>

    <el-card class="settings-card">
      <el-tabs v-model="activeTab" tab-position="left" style="min-height: 400px">
        <el-tab-pane label="基本设置" name="general">
          <template #label>
            <span><el-icon><Setting /></el-icon> 基本设置</span>
          </template>
          <div class="tab-content">
            <h2>基本设置</h2>
            <el-form :model="generalForm" label-width="120px">
              <el-form-item label="系统名称">
                <el-input v-model="generalForm.systemName" placeholder="请输入系统名称" />
              </el-form-item>
              <el-form-item label="系统语言">
                <el-select v-model="generalForm.language" placeholder="请选择语言">
                  <el-option label="简体中文" value="zh-CN" />
                  <el-option label="English" value="en" />
                </el-select>
              </el-form-item>
              <el-form-item label="时区">
                <el-select v-model="generalForm.timezone" placeholder="请选择时区">
                  <el-option label="Asia/Shanghai (UTC+8)" value="Asia/Shanghai" />
                  <el-option label="UTC" value="UTC" />
                  <el-option label="America/New_York" value="America/New_York" />
                </el-select>
              </el-form-item>
              <el-form-item label="页面大小">
                <el-select v-model="generalForm.pageSize" placeholder="请选择每页显示数量">
                  <el-option label="10条/页" value="10" />
                  <el-option label="20条/页" value="20" />
                  <el-option label="50条/页" value="50" />
                  <el-option label="100条/页" value="100" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveGeneralSettings">保存设置</el-button>
                <el-button @click="resetGeneralSettings">重置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane label="通知设置" name="notification">
          <template #label>
            <span><el-icon><Bell /></el-icon> 通知设置</span>
          </template>
          <div class="tab-content">
            <h2>通知设置</h2>
            <el-form label-width="120px">
              <el-form-item label="邮件通知">
                <el-switch v-model="notificationForm.emailEnabled" />
                <el-text type="info" style="margin-left: 10px">开启后，系统重要通知将通过邮件发送</el-text>
              </el-form-item>
              <el-form-item label="合同审核通知">
                <el-switch v-model="notificationForm.contractReviewEnabled" />
              </el-form-item>
              <el-form-item label="系统公告">
                <el-switch v-model="notificationForm.systemAnnouncementEnabled" />
              </el-form-item>
              <el-form-item label="每日摘要">
                <el-switch v-model="notificationForm.dailySummaryEnabled" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveNotificationSettings">保存设置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane label="API设置" name="api">
          <template #label>
            <span><el-icon><Connection /></el-icon> API设置</span>
          </template>
          <div class="tab-content">
            <h2>API集成设置</h2>
            <el-form :model="apiForm" label-width="120px">
              <el-form-item label="OpenAI API密钥">
                <el-input
                  v-model="apiForm.openaiApiKey"
                  type="password"
                  placeholder="请输入OpenAI API密钥"
                  show-password
                />
              </el-form-item>
              <el-form-item label="AI模型">
                <el-select v-model="apiForm.aiModel" placeholder="请选择AI模型">
                  <el-option label="GPT-4" value="gpt-4" />
                  <el-option label="GPT-3.5-Turbo" value="gpt-3.5-turbo" />
                  <el-option label="Claude 3" value="claude-3" />
                </el-select>
              </el-form-item>
              <el-form-item label="API请求超时">
                <el-input-number v-model="apiForm.timeout" :min="10" :max="120" />
                <el-text type="info" style="margin-left: 10px">秒</el-text>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveApiSettings">保存设置</el-button>
                <el-button @click="testApiConnection">测试连接</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane label="关于" name="about">
          <template #label>
            <span><el-icon><InfoFilled /></el-icon> 关于</span>
          </template>
          <div class="tab-content">
            <h2>关于系统</h2>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="系统名称">智能合同审查平台</el-descriptions-item>
              <el-descriptions-item label="版本">v1.0.0</el-descriptions-item>
              <el-descriptions-item label="发布日期">2023-12-01</el-descriptions-item>
              <el-descriptions-item label="开发者">技术团队</el-descriptions-item>
              <el-descriptions-item label="技术支持">support@contract-ai.com</el-descriptions-item>
            </el-descriptions>
            <div style="margin-top: 30px">
              <h3>系统说明</h3>
              <p>智能合同审查平台是一款基于AI技术的合同分析工具，能够自动识别合同中的风险条款、提供修改建议，并生成审查报告。</p>
              <p>系统支持多种合同类型，包括采购合同、劳动合同、保密协议等。</p>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Bell, Connection, InfoFilled } from '@element-plus/icons-vue'

const activeTab = ref('general')

const generalForm = reactive({
  systemName: '智能合同审查平台',
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  pageSize: '20'
})

const notificationForm = reactive({
  emailEnabled: true,
  contractReviewEnabled: true,
  systemAnnouncementEnabled: false,
  dailySummaryEnabled: false
})

const apiForm = reactive({
  openaiApiKey: '',
  aiModel: 'gpt-3.5-turbo',
  timeout: 30
})

const saveGeneralSettings = () => {
  ElMessage.success('基本设置已保存')
  // 实际应用中这里应该调用API保存设置
}

const resetGeneralSettings = () => {
  generalForm.systemName = '智能合同审查平台'
  generalForm.language = 'zh-CN'
  generalForm.timezone = 'Asia/Shanghai'
  generalForm.pageSize = '20'
  ElMessage.info('已重置为默认设置')
}

const saveNotificationSettings = () => {
  ElMessage.success('通知设置已保存')
}

const saveApiSettings = () => {
  ElMessage.success('API设置已保存')
}

const testApiConnection = () => {
  ElMessage.info('正在测试API连接...')
  // 模拟API测试
  setTimeout(() => {
    ElMessage.success('API连接测试成功')
  }, 1000)
}
</script>

<style scoped>
.settings {
  padding: 20px;
  max-width: 1200px;
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

.settings-card {
  min-height: 500px;
}

.tab-content {
  padding: 20px;
}

.tab-content h2 {
  margin-bottom: 20px;
  color: #303133;
}

.tab-content h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #606266;
}

.tab-content p {
  color: #606266;
  line-height: 1.6;
}
</style>