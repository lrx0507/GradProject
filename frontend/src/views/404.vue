<template>
  <div class="page-404" style="text-align: center; padding: 50px; font-size: 20px;">
    <h1>404 页面未找到</h1>
    <p>你访问的路径不存在，请返回首页</p>
    <button style="margin-top: 20px; padding: 8px 16px; cursor: pointer;" @click="goHome">
      返回首页
    </button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
const router = useRouter();
// 跳转首页方法
const goHome = () => {
  router.push('/');
};
</script>

<style scoped>
.page-404 {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>