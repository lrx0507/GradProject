// src/global.d.ts - 新增InfoWindow构造器声明
import type { TDLngLat, TDMarker, TDPolyline, TDIcon, TDLngLatBounds, TDGeolocation, TDInfoWindow } from '@/types/map'; // 新增TDInfoWindow导入

export interface TDTGlobal {
    // 新增：地图核心构造器
  Map: new (container: HTMLElement) => TDMap;
  // 新增：瓦片图层构造器
  TileLayer: new (url: string, options: TDTileLayerOptions) => TDTileLayer;
  LngLat: new (lng: number, lat: number) => TDLngLat;
  Marker: new (lnglat: TDLngLat) => TDMarker;
  Polyline: new (lnglats: TDLngLat[], options: { color: string; weight: number; opacity: number }) => TDPolyline;
  Icon: new (options: { iconUrl: string; iconSize: [number, number] }) => TDIcon;
  LngLatBounds: new () => TDLngLatBounds;
  Geolocation: new () => TDGeolocation;
  InfoWindow: new (content: string) => TDInfoWindow; // 新增：信息窗口构造器
}

declare global {
  interface Window {
    T: TDTGlobal;
  }
}

export {};