<template>
  <div class="not-found">
    <div class="container">
      <div class="error-code">
        404
      </div>
      <div class="error-title">
        页面未找到
      </div>
      <div class="error-description">
        抱歉，您访问的页面不存在或已被移除
      </div>
      <div class="action-buttons">
        <el-button type="primary" @click="goHome">返回首页</el-button>
        <el-button @click="goBack">返回上一页</el-button>
      </div>
      <div class="tips">
        <p>可能的原因：</p>
        <ul>
          <li>链接地址输入错误</li>
          <li>页面已被删除或移动</li>
          <li>您没有访问权限</li>
        </ul>
        <p>如果您认为这是一个错误，请联系管理员</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.not-found {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
  padding: 40px 20px;
  background-color: #f5f7fa;
}

.container {
  text-align: center;
  max-width: 600px;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  color: #409EFF;
  line-height: 1;
  margin-bottom: 20px;
}

.error-title {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 20px;
}

.error-description {
  font-size: 18px;
  color: #606266;
  margin-bottom: 40px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 40px;
}

.tips {
  text-align: left;
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.tips p {
  margin: 10px 0;
  color: #606266;
}

.tips ul {
  margin: 10px 0 10px 20px;
  color: #606266;
}

.tips li {
  margin: 5px 0;
}
</style>