// @/types/map.ts
// 经纬度坐标类型
export interface LngLat {
  lng: number;
  lat: number;
}

// 地图容器Props类型 - 核心优化：center/zoom改为可选（与组件withDefaults默认值匹配）
export interface MapContainerProps {
  center?: LngLat;       // 优化：改为可选，组件已通过withDefaults设置默认值
  zoom?: number;         // 优化：改为可选，组件已通过withDefaults设置默认值
  height?: string;       // 容器高度（可选，默认100vh）
}

// 地图点击事件参数类型
export interface MapClickEvent {
  lng: number;
  lat: number;
  pixel: [number, number]; // 地图像素坐标，严格元组类型
}

// POI渲染组件Props类型 - 补充：给可选属性设置合理默认值注释，提升开发体验
export interface PoiMarkerProps {
  id: number;
  name: string;
  type: 'entrance' | 'view' | 'rest' | 'exit'; // 联合类型限定POI类型
  lng: number;
  lat: number;
  size?: number;        // 图标大小（可选，默认40）
  showName?: boolean;   // 是否显示名称（可选，默认true）
  iconColor?: string;   // 自定义图标颜色（可选，默认随type变化）
}