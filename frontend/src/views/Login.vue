<template>
  <div class="page-login" style="width: 400px; margin: 50px auto; padding: 30px; border: 1px solid #eee; border-radius: 8px;">
    <h2 style="text-align: center; margin-bottom: 20px;">系统登录</h2>
    <!-- 后续可添加账号密码输入框、登录按钮 -->
    <div style="margin-top: 20px; text-align: center;">
      <button style="padding: 8px 32px; cursor: pointer;" @click="handleLogin">
        测试登录（临时）
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
const router = useRouter();
const route = useRoute();
// 临时登录方法（后续替换为真实接口请求）
const handleLogin = () => {
  // 模拟登录：存储token到localStorage
  localStorage.setItem('token', 'test_token_123456');
  ElMessage.success('登录成功');
  // 跳转回原目标页面（若无则跳转到后台首页）
  const redirect = route.query.redirect as string || '/admin';
  router.push(redirect);
};
</script>

<style scoped>
.page-login {
  margin-top: 100px;
}
</style>