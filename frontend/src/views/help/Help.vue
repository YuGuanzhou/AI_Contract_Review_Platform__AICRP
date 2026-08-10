<template>
  <div class="help">
    <div class="header">
      <h1>帮助中心</h1>
      <p>常见问题解答和使用指南</p>
    </div>

    <div class="help-content">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="sidebar">
            <el-menu
              :default-active="activeMenu"
              class="help-menu"
              @select="handleMenuSelect"
            >
              <el-menu-item index="quick-start">
                <el-icon><Star /></el-icon>
                <span>快速开始</span>
              </el-menu-item>
              <el-menu-item index="contract-upload">
                <el-icon><Upload /></el-icon>
                <span>合同上传</span>
              </el-menu-item>
              <el-menu-item index="review-process">
                <el-icon><Checked /></el-icon>
                <span>审核流程</span>
              </el-menu-item>
              <el-menu-item index="faq">
                <el-icon><QuestionFilled /></el-icon>
                <span>常见问题</span>
              </el-menu-item>
              <el-menu-item index="contact">
                <el-icon><Phone /></el-icon>
                <span>联系我们</span>
              </el-menu-item>
            </el-menu>
          </el-card>
        </el-col>

        <el-col :span="18">
          <el-card class="content-card">
            <div v-if="activeMenu === 'quick-start'">
              <h2>快速开始指南</h2>
              <el-steps :active="3" align-center style="margin: 30px 0">
                <el-step title="注册登录" description="创建账户并登录系统" />
                <el-step title="上传合同" description="上传需要审核的合同文件" />
                <el-step title="AI审核" description="系统自动分析合同风险" />
                <el-step title="查看报告" description="获取详细的审核报告" />
              </el-steps>

              <div class="guide-section">
                <h3>第一步：注册与登录</h3>
                <p>1. 点击右上角"注册"按钮创建账户</p>
                <p>2. 使用邮箱和密码登录系统</p>
                <p>3. 首次登录后可以完善个人信息</p>
              </div>

              <div class="guide-section">
                <h3>第二步：上传合同</h3>
                <p>1. 在导航栏点击"合同管理" -> "上传合同"</p>
                <p>2. 拖拽合同文件到上传区域，或点击选择文件</p>
                <p>3. 支持PDF、DOC、DOCX、TXT格式，最大50MB</p>
              </div>

              <div class="guide-section">
                <h3>第三步：查看审核结果</h3>
                <p>1. 上传完成后，系统会自动开始AI审核</p>
                <p>2. 审核完成后，可以在"审核记录"中查看结果</p>
                <p>3. 点击合同详情查看完整的风险分析和修改建议</p>
              </div>
            </div>

            <div v-else-if="activeMenu === 'contract-upload'">
              <h2>合同上传指南</h2>
              <div class="guide-section">
                <h3>支持的文件格式</h3>
                <el-tag type="success">PDF</el-tag>
                <el-tag type="success">DOC</el-tag>
                <el-tag type="success">DOCX</el-tag>
                <el-tag type="success">TXT</el-tag>
                <p style="margin-top: 10px">文件大小限制：最大50MB</p>
              </div>

              <div class="guide-section">
                <h3>上传步骤</h3>
                <p>1. 进入"合同管理" -> "上传合同"页面</p>
                <p>2. 将文件拖拽到上传区域，或点击选择文件</p>
                <p>3. 填写合同相关信息（名称、类型、描述）</p>
                <p>4. 点击"提交审核"按钮开始AI分析</p>
              </div>

              <div class="guide-section">
                <h3>常见问题</h3>
                <el-collapse>
                  <el-collapse-item title="文件上传失败怎么办？">
                    <p>• 检查文件格式是否支持</p>
                    <p>• 确认文件大小不超过50MB</p>
                    <p>• 检查网络连接是否正常</p>
                  </el-collapse-item>
                  <el-collapse-item title="上传后没有反应？">
                    <p>• 检查是否点击了"提交审核"按钮</p>
                    <p>• 查看浏览器控制台是否有错误信息</p>
                    <p>• 刷新页面重新尝试</p>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>


            <div v-else-if="activeMenu === 'faq'">
              <h2>常见问题解答</h2>
              <el-collapse>
                <el-collapse-item title="AI审核的准确性如何？">
                  <p>我们的AI模型经过大量合同数据训练，能够识别常见风险条款，准确率超过90%。但对于复杂的法律条款，建议仍需人工复核。</p>
                </el-collapse-item>
                <el-collapse-item title="合同数据是否安全？">
                  <p>所有上传的合同文件都会进行加密存储，仅用于AI分析处理。我们严格遵守数据隐私政策，不会泄露您的任何合同内容。</p>
                </el-collapse-item>
                <el-collapse-item title="如何导出审核报告？">
                  <p>在合同详情页面，点击"导出报告"按钮，可以选择PDF或Word格式导出完整的审核报告。</p>
                </el-collapse-item>
                <el-collapse-item title="支持哪些合同类型？">
                  <p>目前支持：采购合同、劳动合同、服务合同、保密协议、销售合同、租赁合同、技术合同等常见类型。</p>
                </el-collapse-item>
                <el-collapse-item title="是否需要付费？">
                  <p>目前完全免费，功能完全开放</p>
                </el-collapse-item>
              </el-collapse>
            </div>

            <div v-else-if="activeMenu === 'contact'">
              <h2>联系我们</h2>
              <div class="contact-info">
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="客服邮箱">support@contract-ai.com</el-descriptions-item>
                  <el-descriptions-item label="客服电话">400-123-4567</el-descriptions-item>
                  <el-descriptions-item label="工作时间">工作日 9:00-18:00</el-descriptions-item>
                  <el-descriptions-item label="公司地址">湖南省长沙市岳麓区**地</el-descriptions-item>
                </el-descriptions>

                <div class="contact-form" style="margin-top: 30px">
                  <h3>问题反馈</h3>
                  <el-form :model="feedbackForm" label-width="80px">
                    <el-form-item label="问题类型">
                      <el-select v-model="feedbackForm.type" placeholder="请选择问题类型">
                        <el-option label="功能建议" value="suggestion" />
                        <el-option label="BUG反馈" value="bug" />
                        <el-option label="使用咨询" value="consult" />
                        <el-option label="其他" value="other" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="联系方式">
                      <el-input v-model="feedbackForm.contact" placeholder="请输入邮箱或手机号" />
                    </el-form-item>
                    <el-form-item label="问题描述">
                      <el-input
                        v-model="feedbackForm.description"
                        type="textarea"
                        :rows="4"
                        placeholder="请详细描述您的问题或建议"
                      />
                    </el-form-item>
                    <el-form-item>
                      <el-button type="primary" @click="submitFeedback">提交反馈</el-button>
                    </el-form-item>
                  </el-form>
                </div>
              </div>
            </div>

            <div v-else>
              <!-- 默认内容：审核流程 -->
              <h2>审核流程说明</h2>
              <div class="guide-section">
                <h3>AI审核流程</h3>
                <ol>
                  <li><strong>文件解析</strong>：系统解析合同文本，提取关键信息</li>
                  <li><strong>条款识别</strong>：识别合同中的各类条款（付款、责任、保密等）</li>
                  <li><strong>风险评估</strong>：分析条款的风险等级，标记高风险内容</li>
                  <li><strong>建议生成</strong>：提供修改建议和标准条款参考</li>
                  <li><strong>报告生成</strong>：生成详细的审核报告</li>
                </ol>
              </div>

              <div class="guide-section">
                <h3>审核标准</h3>
                <el-table :data="reviewStandards" style="width: 100%">
                  <el-table-column prop="level" label="风险等级" width="120">
                    <template #default="{ row }">
                      <el-tag :type="row.tagType">{{ row.level }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" />
                  <el-table-column prop="action" label="建议操作" />
                </el-table>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Star, Upload, Files, Checked, QuestionFilled, Phone } from '@element-plus/icons-vue'

const activeMenu = ref('quick-start')

const feedbackForm = reactive({
  type: '',
  contact: '',
  description: ''
})

const reviewStandards = [
  { level: '高风险', tagType: 'danger', description: '条款存在重大法律风险，可能造成重大损失', action: '必须修改' },
  { level: '中风险', tagType: 'warning', description: '条款存在一定风险，建议优化', action: '建议修改' },
  { level: '低风险', tagType: 'info', description: '条款基本合规，可选择性优化', action: '可选修改' },
  { level: '安全', tagType: 'success', description: '条款符合标准，无需修改', action: '无需修改' }
]

const handleMenuSelect = (index: string) => {
  activeMenu.value = index
}

const submitFeedback = () => {
  if (!feedbackForm.type || !feedbackForm.description) {
    ElMessage.warning('请填写完整的信息')
    return
  }
  ElMessage.success('感谢您的反馈，我们会尽快处理')
  feedbackForm.type = ''
  feedbackForm.contact = ''
  feedbackForm.description = ''
}
</script>

<style scoped>
.help {
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

.help-content {
  margin-top: 20px;
}

.sidebar {
  height: 100%;
}

.help-menu {
  border-right: none;
}

.content-card {
  min-height: 600px;
}

.content-card h2 {
  margin-bottom: 20px;
  color: #303133;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 10px;
}

.guide-section {
  margin: 25px 0;
}

.guide-section h3 {
  margin: 15px 0 10px 0;
  color: #606266;
}

.guide-section p {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

.guide-section ol {
  margin-left: 20px;
  color: #606266;
  line-height: 1.6;
}

.guide-section li {
  margin: 8px 0;
}

.contact-info {
  margin-top: 20px;
}
</style>