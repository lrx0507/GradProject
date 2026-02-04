// src/router/admin.ts
import type { RouteRecordRaw } from 'vue-router';

const adminRoutes: RouteRecordRaw[] = [
  {
    path: 'poi-manage',
    name: 'AdminPoiManage',
    component: () => import('@/views/admin/poi/PoiManage.vue'),
    meta: { title: 'POI管理', icon: 'LocationFilled' }
  },
  {
    path: 'road-network',
    name: 'AdminRoadNetwork',
    component: () => import('@/views/admin//network/RoadNetwork.vue'),
    meta: { title: '路网管理', icon: 'Route' }
  },
  {
    path: 'system-config',
    name: 'AdminSystemConfig',
    component: () => import('@/views/admin/SystemConfig.vue'),
    meta: { title: '系统配置', icon: 'Setting' }
  },
  {
    path: 'dashboard',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/Dashboard.vue'),
    meta: { title: '仪表盘', icon: 'DataBoard' }
  }
];

export default adminRoutes;