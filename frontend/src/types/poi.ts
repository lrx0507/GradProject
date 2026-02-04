// src/types/poi.ts
/**
 * POI类型（与后端pois表type字段同步）
 */
export type PoiType = 'entrance' | 'view' | 'rest' | 'exit';

/**
 * 类型对应的中文标签（用于UI显示）
 */
export const POI_TYPE_LABELS: Record<PoiType, string> = {
  entrance: '入口',
  view: '观景点',
  rest: '休息区',
  exit: '出口'
};

/**
 * POI类型对应的图标（用于地图渲染，补充缺失的导出）
 */
export const POI_TYPE_ICONS: Record<PoiType, string> = {
  entrance: '🚪',
  view: '👁️',
  rest: '🪑',
  exit: '🏁'
};

/**
 * 完整POI数据结构（新增is_active属性，与组件/后端一致）
 */
export interface Poi {
  id?: number;
  name: string;
  type: PoiType;
  description: string;
  lat: number;
  lng: number;
  is_active?: boolean; // 新增：匹配组件中的启用/禁用字段
  create_time?: string;
}