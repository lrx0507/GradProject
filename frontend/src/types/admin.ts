// src/types/admin.ts
import type { LngLat } from './map';

// POI完整信息（扩展原有PoiMarkerProps）
export interface PoiInfo extends LngLat {
  id: number;
  name: string;
  type: 'entrance' | 'view' | 'rest' | 'exit';
  desc: string; // 描述
  status: boolean; // 启用/禁用
  createTime: string; // 创建时间
}

// 路网边（折线）信息
export interface RoadEdge {
  id: number;
  points: LngLat[]; // 折线点集合
  length: number; // 长度（米）
  createTime: string;
}

// 拓扑节点信息
export interface TopoNode {
  id: number;
  lng: number;
  lat: number;
  connectEdges: number[]; // 关联路网边ID
}

// 系统配置参数
export interface SystemConfig {
  slopeWeight: number; // 坡度权重α（0-1）
  featureRoutes: FeatureRoute[]; // 特色路线配置
}

// 特色路线信息
export interface FeatureRoute {
  id: number;
  name: string;
  cover: string; // 封面图地址
  poiIds: number[]; // 关联POI ID（拖拽排序后）
  desc: string; // 路线描述
}

// 操作日志
export interface OperationLog {
  id: number;
  operator: string; // 操作人
  type: 'add' | 'edit' | 'delete' | 'config'; // 操作类型
  content: string; // 操作内容
  time: string; // 操作时间
}

// 统计数据
export interface StatData {
  poiCount: { [key in 'entrance' | 'view' | 'rest' | 'exit']: number }; // POI类型分布
  roadTotalLength: number; // 路网总长度（米）
  poiTotal: number; // POI总数
  roadTotal: number; // 路网边总数
  recentLogs: OperationLog[]; // 最近操作日志
}