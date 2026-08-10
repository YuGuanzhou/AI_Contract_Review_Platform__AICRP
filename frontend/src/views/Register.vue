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
      width="700px"
      append-to-body
    >
      <div class="terms-content">
        <h3>智能合同审查平台用户协议</h3>
        <p class="doc-meta">更新日期：2026年8月10日 ｜ 生效日期：2026年8月10日</p>
        <p>欢迎使用智能合同审查平台（以下简称"本平台"）。本平台为中小企业及个人用户提供合同上传、AI 风险识别、人工复核、风险统计分析等合同管理服务。</p>
        <p>请您在使用本平台前，仔细阅读并充分理解本协议的全部内容。当您注册账号、勾选"我已阅读并同意《用户协议》"或开始使用本平台服务时，即表示您已充分理解并同意接受本协议的全部条款。</p>

        <h4>一、协议范围</h4>
        <p>1.1 本协议是您与本平台之间就使用平台服务所订立的具有法律约束力的协议。</p>
        <p>1.2 本平台同时发布的隐私政策、平台规则、帮助文档等，均为本协议的组成部分，与正文具有同等法律效力。</p>
        <p>1.3 如您不同意本协议的任何条款，请立即停止注册或使用本平台服务。</p>

        <h4>二、定义</h4>
        <p>2.1 用户：指注册并使用本平台服务的自然人、法人及其他组织。</p>
        <p>2.2 合同文档：指用户通过本平台上传播放、Word、TXT 等格式的合同文件。</p>
        <p>2.3 审查结果：指平台利用 AI 技术对合同文档进行分析后生成的风险评分、风险点识别、修改建议等输出内容。</p>
        <p>2.4 账户：指用户在本平台注册并获得授权使用的唯一身份标识。</p>

        <h4>三、服务内容</h4>
        <p>3.1 本平台向用户提供以下服务：</p>
        <p>（1）合同文档的上传、存储与解析；</p>
        <p>（2）基于 AI 大模型的合同风险识别、风险评分与修改建议；</p>
        <p>（3）审核员人工复核及审核记录管理；</p>
        <p>（4）合同数据统计分析与可视化展示；</p>
        <p>（5）平台不时推出的其他功能与服务。</p>
        <p>3.2 本平台有权根据业务发展需要，对服务内容进行调整、升级、暂停或终止，并通过平台公告等方式通知用户。</p>

        <h4>四、账号注册与管理</h4>
        <p>4.1 您应按照平台要求提供真实、准确、完整的注册信息，包括用户名、邮箱及密码等。因提供虚假信息或未及时更新信息所导致的一切后果由您自行承担。</p>
        <p>4.2 您应对账户下的全部行为负责，包括但不限于通过该账户上传的合同文档、提交的审核意见及进行的各项操作。</p>
        <p>4.3 请妥善保管您的账户名和密码。任何使用您账户进行的操作均视为您本人的行为。如发现账户被他人盗用或存在安全隐患，请立即通知平台方。</p>
        <p>4.4 您的密码应设置为足够强度的字符组合，并定期更换，避免使用与个人信息明显关联的弱密码。</p>
        <p>4.5 用户不得出借、转让、出售或以其他方式允许他人使用您的账户。如确有需要，请联系平台方办理相关手续。</p>

        <h4>五、用户行为规范</h4>
        <p>5.1 您承诺在使用本平台过程中遵守国家法律法规、公序良俗及本协议约定，不得利用本平台从事任何违法违规活动，包括但不限于：</p>
        <p>（1）上传含有违法、淫秽、暴力、诽谤、侮辱他人等内容的合同文档；</p>
        <p>（2）利用平台从事侵犯他人知识产权、商业秘密或其他合法权益的行为；</p>
        <p>（3）通过任何技术手段攻击、破坏、干扰平台的正常运行，或试图获取未经授权的数据；</p>
        <p>（4）批量注册、恶意刷量、发布虚假信息等扰乱平台秩序的行为。</p>
        <p>5.2 如您违反上述规范，平台方有权视情节采取警告、限制功能、暂停或终止服务等措施，并保留追究法律责任的权利。</p>

        <h4>六、合同文档的上传与使用</h4>
        <p>6.1 您上传合同文档，即表示您保证对该文档享有合法权利（包括但不限于所有权、处分权或合法授权），且文档内容不违反任何法律法规及第三方权益。</p>
        <p>6.2 平台对合同文档的使用严格限定于为您提供审查服务所必需的范围内，包括文档解析、AI 分析与人工复核。除本协议另有约定或法律另有规定外，平台不会将您的合同文档用于其他商业用途。</p>
        <p>6.3 如合同文档涉及第三方商业秘密或个人隐私，请您在评估合规风险后再行上传，并对上传内容承担全部责任。</p>

        <h4>七、AI 审查服务说明与特别提示</h4>
        <p>7.1 本平台基于 AI 大模型为您提供合同审查服务。审查结果由算法自动生成，仅供您参考，不构成任何形式的法律意见或专业建议。</p>
        <p>7.2 AI 审查可能存在识别不准确、分析不全面等局限。涉及重大利益事项，请您务必咨询具有资质的专业法律人士。</p>
        <p>7.3 您理解并同意，因依赖 AI 审查结果而作出的任何决策，其风险与后果由您自行承担，平台方在法律允许的范围内不承担责任。</p>

        <h4>八、知识产权</h4>
        <p>8.1 本平台提供的软件、界面设计、文字、图标、数据统计口径及相关技术成果，其知识产权归平台方或相关权利人所有。未经许可，您不得擅自复制、修改、传播或用于商业用途。</p>
        <p>8.2 您上传的合同文档及相关数据，其知识产权归您或原权利人所有。本平台不主张对该等文档的知识产权。</p>

        <h4>九、服务中断与责任限制</h4>
        <p>9.1 平台方将尽合理努力保障服务的稳定与可用，但不对服务的绝对不间断性作出保证。因不可抗力、系统维护、网络故障、第三方服务（包括 AI 服务提供商、云服务商）等原因造成的服务中断，平台方不承担违约责任。</p>
        <p>9.2 在法律允许的最大范围内，平台方对因使用或无法使用本服务所导致的间接损失、附带损失或惩罚性损失不承担责任。</p>

        <h4>十、协议的变更与终止</h4>
        <p>10.1 平台方有权根据业务需要修改本协议。修改后的协议将在平台公示并更新生效日期，自公示之日起，如您继续使用本平台服务，即视为接受修改后的协议。</p>
        <p>10.2 您可随时停止使用本平台服务，并可按平台指引注销账户。注销后，您的账户信息及合同文档将依隐私政策及法律规定予以处理。</p>
        <p>10.3 如您违反本协议，平台方有权终止向您提供服务，并保留追究法律责任的权利。</p>

        <h4>十一、争议解决</h4>
        <p>11.1 本协议的订立、履行与解释均适用中华人民共和国法律。</p>
        <p>11.2 因本协议引起的争议，双方应首先友好协商解决；协商不成的，任何一方均可向平台运营方所在地有管辖权的人民法院提起诉讼。</p>

        <h4>十二、联系我们</h4>
        <p>12.1 如您对本协议有任何疑问、意见或建议，欢迎通过以下方式与我们联系：</p>
        <p>（1）平台站内客服；</p>
        <p>（2）反馈邮箱：support@contract-review.com。</p>
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
      width="700px"
      append-to-body
    >
      <div class="privacy-content">
        <h3>隐私政策</h3>
        <p class="doc-meta">更新日期：2026年8月10日 ｜ 生效日期：2026年8月10日</p>
        <p>我们非常重视您的隐私和个人信息保护。本隐私政策旨在说明智能合同审查平台（以下简称"本平台"）如何收集、使用、存储、共享和保护您的个人信息，以及您享有的相关权利。请您在使用本平台前仔细阅读本政策。</p>

        <h4>一、我们收集的信息</h4>
        <p>1.1 账号信息：您注册时提供的用户名、邮箱地址、密码（加密存储）以及您自愿填写的姓名、所属公司等信息。</p>
        <p>1.2 合同文档信息：您上传的合同文件及其解析、审核结果，包括合同文本内容、风险评分、风险点、修改建议等。</p>
        <p>1.3 使用信息：您的登录时间、操作日志、IP 地址、设备信息及浏览器类型等，用于安全审计与问题排查。</p>
        <p>1.4 联系我们时提供的信息：当您通过站内客服或邮件与我们联系时，您提供的联系方式及沟通内容。</p>

        <h4>二、信息的使用目的</h4>
        <p>我们仅在以下目的范围内使用您的个人信息：</p>
        <p>2.1 创建和管理您的账户，验证您的身份；</p>
        <p>2.2 为您提供合同解析、AI 审查、人工复核、统计分析等核心服务；</p>
        <p>2.3 保障平台安全，识别和防范欺诈、滥用等风险行为；</p>
        <p>2.4 改进和优化平台功能与服务质量；</p>
        <p>2.5 在法律法规要求或平台合法利益需要时履行相应义务。</p>

        <h4>三、信息的存储</h4>
        <p>3.1 存储位置：您的个人信息及合同文档存储于中华人民共和国境内的服务器。</p>
        <p>3.2 存储期限：我们仅在实现本政策所述目的所必需的期限内保留您的信息，法律法规另有规定的除外。账户注销后，我们将按照法律规定对您的信息进行删除或匿名化处理。</p>
        <p>3.3 加密保护：您的密码使用 bcrypt 加盐哈希算法加密存储；合同文档在传输过程中使用 HTTPS 加密，存储过程中采用相应的加密与访问控制措施。</p>

        <h4>四、信息共享与对外提供</h4>
        <p>4.1 我们不会向任何无关第三方出售或出租您的个人信息。</p>
        <p>4.2 为向您提供 AI 审查服务，合同文档内容将发送至我们选用的第三方 AI 服务提供商（如 DeepSeek）进行处理。该等处理仅为实现审查服务之目的，我们将通过协议约束第三方履行保密与安全义务。</p>
        <p>4.3 以下情形除外：</p>
        <p>（1）征得您明确同意；</p>
        <p>（2）依据法律法规、司法机关或行政机关的要求；</p>
        <p>（3）为保护平台方、用户或社会公众的合法权益所必需。</p>

        <h4>五、数据安全措施</h4>
        <p>5.1 我们采用符合行业标准的安全防护措施，包括但不限于访问控制、加密传输与存储、操作审计日志、数据备份等，防止您的信息遭到未经授权的访问、披露、篡改或丢失。</p>
        <p>5.2 我们已建立信息安全管理制度，并对相关人员进行安全培训。</p>
        <p>5.3 如发生个人信息安全事件，我们将按照法律法规的要求及时采取补救措施，并履行通知义务。</p>

        <h4>六、您的权利</h4>
        <p>6.1 访问与更正：您可以在"个人中心"查看并更正您的个人信息。</p>
        <p>6.2 删除：您可以申请删除您上传的合同文档及相关数据。</p>
        <p>6.3 注销账户：您可以通过联系平台方申请注销账户。注销后，我们将依法删除或匿名化处理您的信息。</p>
        <p>6.4 撤回同意：您有权随时撤回对个人信息使用的同意，撤回不影响撤回前已进行的处理。</p>

        <h4>七、未成年人保护</h4>
        <p>本平台面向具有完全民事行为能力的成年用户。如您是未满十八周岁的未成年人，请在监护人指导下使用本平台，并在征得监护人同意后进行注册。</p>

        <h4>八、Cookie 与本地存储</h4>
        <p>8.1 为提供登录状态保持等基础功能，本平台会在您的设备上使用 Cookie 或浏览器本地存储（localStorage）。</p>
        <p>8.2 您可以清除相关本地数据，但可能导致需要重新登录或部分功能无法正常使用。</p>

        <h4>九、政策变更</h4>
        <p>我们可能适时修订本政策。修订后的政策将随版本更新在平台公示并更新生效日期。如涉及对您权益有重大影响的变更，我们将通过显著方式通知您。继续使用本平台即视为您接受修订后的政策。</p>

        <h4>十、联系我们</h4>
        <p>如您对本政策或个人信息保护有任何疑问、意见或投诉，请通过以下方式与我们联系：</p>
        <p>（1）平台站内客服；</p>
        <p>（2）反馈邮箱：support@contract-review.com。</p>
        <p>我们将在收到您反馈后的十五个工作日内予以答复。</p>
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

  h4 {
    margin: 18px 0 8px;
    color: #333;
    font-size: 15px;
  }

  p {
    margin-bottom: 8px;
    line-height: 1.7;
    color: #666;
    font-size: 14px;
  }

  .doc-meta {
    color: #999;
    font-size: 12px;
    margin-bottom: 12px;
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

