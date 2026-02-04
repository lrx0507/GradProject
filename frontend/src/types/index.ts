// 路由元信息类型（匹配router中meta字段）
//export interface CustomRouteMeta  {
  //title: string;        // 菜单/页面标题
  //  title?: string;
  //icon?: string;        // Element Plus图标名称
  //requiresAuth?: boolean; // 是否需要登录
//}

// POI基础类型（含所有属性，与后端POI表对齐）
export interface POI {
  id: number;
  name: string;
  type: 'entrance' | 'view' | 'rest' | 'exit'; // POI类型枚举
  lng: number;          // 经度（WGS84）
  lat: number;          // 纬度（WGS84）
  description?: string; // 描述（可选）
  is_active: boolean;   // 启用状态
  create_time: string;  // 创建时间（字符串格式，如2026-02-04 15:30:00）
}

// 路径规划采样点类型（与后端sampling_result返回值对齐）
export interface PathSamplingPoint {
  lng: number;
  lat: number;
  distance_m: number;   // 距起点累计距离（米）
  elevation_m: number;  // 高程（米）
  slope_deg: number;    // 坡度（度）
}

// 路径规划统计信息类型
export interface PathStatistics {
  total_length_m: number;
  avg_slope_deg: number;
  node_count: number;
  edge_count: number;
  sampling_count: number;
}

// 路径规划策略类型
export type PathStrategy = 'shortest' | 'gentlest';