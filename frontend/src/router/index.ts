// 严格区分：值导入 + 类型仅导入（适配verbatimModuleSyntax）
import { createRouter, createWebHistory } from 'vue-router';
import type { RouteRecordRaw, RouteMeta } from 'vue-router';
import frontRoutes from './front';
import adminRoutes from './admin';
import FrontLayout from '@/layout/FrontLayout.vue';
import AdminLayout from '@/layout/AdminLayout.vue';
import { ElMessage } from 'element-plus';

// 终极修复：直接扩展Vue Router原生RouteMeta，声明自定义属性
// 无需导入外部CustomRouteMeta，避免多层继承的递归引用问题
declare module 'vue-router' {
  interface RouteMeta {
    // 页面标题（用于动态设置document.title）
    title?: string;
    // 是否需要登录验证（受保护路由）
    requiresAuth?: boolean;
    // 可扩展其他自定义属性（如缓存、权限等）
    // keepAlive?: boolean;
    // permission?: string[];
  }
}

// 路由规则数组（严格RouteRecordRaw类型约束）
const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/front/path-planning' },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/404.vue') },
  // 前台路由
  {
    path: '/front',
    name: 'Front',
    component: FrontLayout,
    children: frontRoutes
  },
  // 后台路由（需要登录验证）
  {
    path: '/admin',
    name: 'Admin',
    component: AdminLayout,
    meta: { requiresAuth: true, title: '管理中心' },
    children: adminRoutes
  },
  // 登录页
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '系统登录' }
  }
];

// 创建路由实例，配置历史模式+滚动行为
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }) // 路由跳转后回到页面顶部
});

// 全局前置路由守卫 - 登录验证 + 页面标题设置
router.beforeEach((to, from, next) => {
  // 动态设置页面标题（结合路由meta）
  if (to.meta.title) {
    document.title = `${to.meta.title} - 徒步路线规划系统`;
  }

  // 受保护路由（需要登录）验证
  if (to.meta.requiresAuth) {
    const hasToken = !!localStorage.getItem('token');
    if (hasToken) {
      next(); // 已登录，正常放行
    } else {
      ElMessage.warning('请先登录后台管理系统');
      // 重定向到登录页，并携带原跳转路径（登录后可返回）
      next({ path: '/login', query: { redirect: to.fullPath } });
    }
  } else {
    next(); // 无需登录，直接放行
  }
});

export default router;