// 修复1：纯类型 RouteRecordRaw 改用 import type 导入（解决 TS1484）
import type { RouteRecordRaw } from 'vue-router';

// 前台路由规则（TS类型：RouteRecordRaw[]）
const frontRoutes: RouteRecordRaw[] = [
  {
    path: 'path-planning',
    name: 'FrontPathPlanning',
    component: () => import('@/views/front/PathPlanning.vue'),
    meta: { title: '路径规划', icon: 'MapLocation' }
  },
  {
    path: 'feature-routes',
    name: 'FrontFeatureRoutes',
    component: () => import('@/views/front/FeatureRoutes.vue'), // 修复2：确认该文件真实存在（路径/文件名完全匹配）
    meta: { title: '特色路线', icon: 'Route' }
  }
];

export default frontRoutes;