<template>
  <el-container class="front-layout" style="height: 100vh;">
    <el-header class="front-header">
      <div class="header-logo">徒步路线规划系统</div>
      <el-menu class="front-menu" mode="horizontal" router :default-active="$route.fullPath">
        <el-menu-item :index="'/front/path-planning'">
          <el-icon><MapLocation /></el-icon>路径规划
        </el-menu-item>
        <el-menu-item :index="'/front/feature-routes'">
          <el-icon><Guide /></el-icon>特色路线
        </el-menu-item>
        <el-menu-item :index="'/admin'" v-if="isLogin">
          <el-icon><Setting /></el-icon>管理中心
        </el-menu-item>
      </el-menu>
      <div class="header-opt">
        <el-button type="text" @click="toLogin" v-if="!isLogin">登录</el-button>
        <el-button type="text" @click="handleLogout" v-else>退出</el-button>
      </div>
    </el-header>
    <el-main class="front-main"><router-view /></el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { MapLocation, Guide, Setting } from '@element-plus/icons-vue';

// 路由实例（TS类型）
const router = useRouter();

// 登录状态（TS类型：ComputedRef<boolean>）
const isLogin = computed<boolean>(() => !!localStorage.getItem('token'));

// 跳转到登录页（TS类型：() => void）
const toLogin = (): void => {
  router.push('/login');
};

// 退出登录（TS类型：() => void）
const handleLogout = (): void => {
  localStorage.removeItem('token');
  ElMessage.success('退出成功');
  router.push('/front/path-planning');
};
</script>

<style scoped>
/* 样式与JS版一致，无修改 */
.front-layout { --el-color-primary: #1890ff; overflow: hidden; }
.front-header { height: 60px; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 0 40px; display: flex; align-items: center; justify-content: space-between; }
.header-logo { font-size: 20px; font-weight: 600; color: var(--el-color-primary); cursor: pointer; }
.front-menu { flex: 1; text-align: center; }
.header-opt { width: 100px; text-align: right; }
.front-main { padding: 0; margin: 0; height: calc(100vh - 60px); background: #f5f7fa; overflow: hidden; }
</style>