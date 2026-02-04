// src/types/map.d.ts
/** POI基础类型（关联PostGIS空间字段） */
export interface POI {
  id: string;
  name: string;
  type: string; // 休息区/餐饮/景点等
  lnglat: [number, number]; // 经纬度 [lng, lat]
  address: string;
  geom?: string; // PostGIS的WKT格式几何字段
  distance?: number; // 距离当前点的距离（米）
}

/** 路径规划参数 */
export interface RoutePlanParams {
  start: [number, number]; // 起点经纬度
  end: [number, number]; // 终点经纬度
  strategy: 'leastTime' | 'leastDistance' | 'leastSlope'; // 规划策略
}

/** 路线节点（含坡度/高程） */
export interface RoutePoint {
  lnglat: [number, number];
  slope: number; // 坡度（%）
  elevation: number; // 高程（米）
  distance: number; // 累计距离（米）
}

/** 路线信息 */
export interface RouteInfo {
  id: string;
  name: string;
  desc: string;
  points: RoutePoint[]; // 路线节点
  totalDistance: number; // 总距离（米）
  totalDuration: number; // 总时长（秒）
  elevationProfile: { x: number; y: number }[]; // 高程剖面（x:距离，y:高程）
}

/** 特色路线卡片 */
export interface RouteCard {
  id: string;
  title: string;
  cover: string; // 预览图URL
  tags: string[]; // 标签（低坡度/风景好）
  routeInfo: RouteInfo;
}