// src/types/map.ts - 完整类型定义（天地图核心类型 + 原有业务类型，全量导出）
declare global {
  interface Window {
    T?: {
      // 天地图所有核心构造器，与实际API一致
      Map: new (container: HTMLElement) => TDMap;
      LngLat: new (lng: number, lat: number) => TDLngLat;
      LngLatBounds: new () => TDLngLatBounds;
      TileLayer: new (url: string, options: TDTileLayerOptions) => TDTileLayer;
      Marker: new (lnglat: TDLngLat, options?: TDMarkerOptions) => TDMarker;
      Icon: new (options: TDIconOptions) => TDIcon;
      Polyline: new (lnglats: TDLngLat[], options: TDPolylineOptions) => TDPolyline;
      InfoWindow: new (content: string, options?: TDInfoWindowOptions) => TDInfoWindow;
      Geolocation: new () => TDGeolocation;
    };
  }
}

// -------------------------- 天地图核心类型（全量导出，匹配页面导入） --------------------------
/**
 * 天地图经纬度类型（命名TDLngLat，匹配页面导入，解决TS2724）
 */
export interface TDLngLat {
  new (lng: number, lat: number): TDLngLat;
  getLng(): number;
  getLat(): number;
}
/** 天地图标记点事件类型（新增：补充mouseover/mouseout） */
export type TDMarkerEvent = "click" | "mouseover" | "mouseout";

/**
 * 天地图经纬度范围类型
 */
export interface TDLngLatBounds {
  extend: (lnglat: TDLngLat) => void;
}

/**
 * 天地图瓦片图层配置类型
 */
export interface TDTileLayerOptions {
  layer: string;
  style: string;
  tileMatrixSet: string;
  format: string;
}
export type TDTileLayer = object;

/**
 * 天地图图标配置类型
 */
export interface TDIconOptions {
  iconUrl: string;
  iconSize: [number, number];
  iconAnchor?: [number, number];
}
/**
 * 天地图图标实例类型（导出，匹配页面导入）
 */
export type TDIcon = object;

/**
 * 天地图标记点配置类型
 */
export interface TDMarkerOptions {
  icon?: TDIcon;
}

/**
 * 天地图标记点实例类型（导出，包含事件方法，匹配页面使用）
 */
/** 天地图标记点类型（修改：事件类型改为TDMarkerEvent） */
export interface TDMarker {
  new (lnglat: TDLngLat): TDMarker;
  addTo(map: TDMap): void;
  addEventListener(
    event: TDMarkerEvent, // 替换为包含鼠标事件的类型
    callback: (e: { lnglat: TDLngLat }) => void
  ): void;
}

/** 天地图信息窗体类型（新增：声明open方法） */
export interface TDInfoWindow {
  new (content: string): TDInfoWindow;
  // 声明open方法：参数为地图实例+经纬度，无返回值
  open(map: TDMap, lnglat: TDLngLat): void;
}

/**
 * 天地图折线配置类型（必填opacity，与实际使用一致）
 */
export interface TDPolylineOptions {
  color: string;
  weight: number;
  opacity: number;
}

/**
 * 天地图折线实例类型（导出，匹配页面导入）
 */
export interface TDPolyline {
  addTo: (map: TDMap) => void;
}

/**
 * 天地图信息窗口配置类型
 */
export interface TDInfoWindowOptions {
  width?: number;
  height?: number;
}


/**
 * 天地图定位结果类型
 */
export interface TDGeolocationResult {
  success: boolean;
  lnglat: TDLngLat;
}

/**
 * 天地图定位实例类型
 */
export interface TDGeolocation {
  getCurrentPosition: (callback: (res: TDGeolocationResult) => void) => void;
}

/**
 * 天地图核心实例类型（导出，包含所有页面用到的方法，解决TS2305）
 */
export interface TDMap {
  centerAndZoom: (lnglat: TDLngLat, zoom: number) => void;
  enableScrollWheelZoom: (enable: boolean) => void;
  addLayer: (layer: TDTileLayer) => void;
  clearOverlays: () => void;
  panTo: (lnglat: TDLngLat) => void;
  addOverlay: (overlay: TDMarker | TDPolyline) => void;
  addEventListener: (event: 'click', callback: (e: { lnglat: TDLngLat }) => void) => void;
  fitBounds: (bounds: TDLngLatBounds) => void;
  openInfoWindow: (infoWindow: TDInfoWindow, lnglat: TDLngLat) => void;
  closeInfoWindow(): void;
}

// -------------------------- 原有业务类型（完全保留，无任何修改） --------------------------
// 基础经纬度坐标类型（保留原有定义，作为核心基础类型）
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

// 地图点击事件参数类型（保留原有定义，完善事件参数规范）
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

/**
 * 业务POI基础类型（前后端统一，关联PostGIS空间数据，扩展原有PoiMarkerProps的业务属性）
 */
export interface POI {
  id: string | number;  // 兼容数字/字符串ID，适配不同接口返回
  name: string;
  type: 'entrance' | 'view' | 'rest' | 'exit' | 'food' | 'spot'; // 扩展类型，兼容原有POI类型
  lnglat: [number, number]; // 经纬度元组 [经度, 纬度]，与地图API适配
  address?: string;     // 详细地址（可选）
  distance?: number;    // 可选：距离当前位置的距离（米），用于周边POI排序
  geom?: string;        // 可选：PostGIS WKT几何字段，用于空间分析
}

/**
 * 路径规划参数类型（传给后端的请求参数，适配路径规划功能）
 */
export interface RoutePlanParams {
  start: [number, number]; // 起点经纬度元组，与地图点击/定位结果适配
  end: [number, number];   // 终点经纬度元组，支持POI选择/手动点击
  strategy: 'leastTime' | 'leastDistance' | 'leastSlope'; // 规划策略：最短时间/最短距离/最小坡度
}

/**
 * 路径点类型（包含坡度/高程信息，路径规划核心节点）
 */
export interface RoutePoint {
  lnglat: [number, number]; // 经纬度元组
  slope: number;            // 坡度（°），用于坡度着色渲染
  elevation: number;        // 高程（米），用于高程剖面图表
  distance: number;         // 累计距离（米），用于高程剖面X轴
}

/**
 * 高程剖面数据类型（适配ECharts图表渲染）
 */
export interface ElevationProfileItem {
  x: number; // 距离起点的水平距离（米）
  y: number; // 对应位置的高程（米）
}

/**
 * 路径规划结果类型（后端PostGIS空间分析后返回，包含完整路线信息）
 */
export interface RouteInfo {
  points: RoutePoint[];          // 路线节点集合，用于绘制分段折线
  totalDistance: number;         // 路线总距离（米）
  totalTime: number;             // 预估总时间（分钟），按策略计算
  elevationProfile: ElevationProfileItem[]; // 高程剖面数据，用于图表渲染
}

/**
 * 特色路线卡片类型（适配FeatureRoutes.vue特色路线展示/选择功能）
 */
export interface RouteCard {
  id: string | number;
  name: string;
  desc: string;
  totalDistance: number;
  difficulty: 'easy' | 'medium' | 'hard';
  points: {
    lnglat: [number, number];
    slope: number;
    elevation: number;
    distance: number;
  }[];
  cover?: string;
  type?: 'leisure' | 'adventure' | 'fitness';
  // 新增：补充缺失的属性（解决TS2339）
  title: string; // 对应模板中route.title
  tags: string[]; // 对应模板中route.tags
  routeInfo: { // 对应模板中route.routeInfo
    distance: string;
    time: string;
    elevation: string;
  };
}

// 导出空对象，确保全局声明生效
export {};