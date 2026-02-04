<template>
  <el-container style="height: 100vh;">
    <!-- 侧边栏 -->
    <el-aside width="200px" style="background: #2e3b4e; color: #fff;">
      <div class="admin-logo" style="padding: 20px; text-align: center; font-size: 18px; border-bottom: 1px solid #44546a;">
        系统管理中心
      </div>
      <el-menu
        default-active="/admin/dashboard"
        class="el-menu-vertical-demo"
        background-color="#2e3b4e"
        text-color="#fff"
        active-text-color="#ffd04b"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/admin/poi-manage">
          <el-icon><LocationFilled /></el-icon>
          <span>POI管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/road-network">
          <el-icon><MapLocation /></el-icon>
          <span>路网管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/system-config">
          <el-icon><Setting /></el-icon>
          <span>系统配置</span>
        </el-menu-item>
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/login">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <!-- 主内容区 -->
    <el-container>
      <el-header style="text-align: right; font-size: 12px; border-bottom: 1px solid #eee;">
        <span>当前用户：管理员</span>
      </el-header>
      <el-main style="padding: 20px;">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
// 修复：替换为低版本Element Plus Icons 通用兼容图标（无Road/LogOut时）
import { LocationFilled, MapLocation, Setting, DataBoard, SwitchButton } from '@element-plus/icons-vue';

const router = useRouter();

// 统一菜单选择逻辑：包含路由跳转+退出登录，无重复声明
const handleMenuSelect = (index: string) => {
  // 退出登录逻辑
  if (index === '/login') {
    localStorage.removeItem('token');
    ElMessage.success('退出成功');
    router.push('/login');
    return;
  }
  // 普通菜单路由跳转
  router.push(index);
};
</script>

<style scoped>
.el-header {
  line-height: 60px;
}
/* 优化菜单样式，消除默认边距 */
:deep(.el-menu-vertical-demo) {
  border-right: none;
  height: calc(100vh - 62px);
  padding-top: 10px;
}
:deep(.el-menu-item) {
  margin: 0;
  color: #e5eaf3 !important;
}
:deep(.el-menu-item.is-active) {
  background-color: #1f2d3d !important;
  color: #ffd04b !important;
}
:deep(.el-icon) {
  margin-right: 8px;
}
</style>