<template>
  <div class="nearby-poi">
    <div class="search-bar">
      <input v-model="searchKey" placeholder="搜索周边POI..." @keyup.enter="searchPOI" />
      <button @click="searchPOI">搜索</button>
    </div>
    <div class="poi-container">
      <div ref="mapContainer" class="poi-map"></div>
      <div class="poi-list">
        <div v-for="poi in poiList" :key="poi.id" class="poi-item" @click="focusPOI(poi)">
          <h4>{{ poi.name }}</h4>
          <p>{{ poi.address }}</p>
          <span class="poi-type">{{ poi.type }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
// 核心修复：1. 移除未使用的TDLngLat导入 2. 统一从types/map导入所有类型
import { initTDMap, addTDLayers } from '@/utils/map'; // 仅导入工具方法，不导入类型
import type { TDMap, POI } from '@/types/map'; // 从types/map导入需要的类型（TDMap/POI）
import axios from 'axios';

// 状态定义（完全不变）
const mapContainer = ref<HTMLDivElement | null>(null);
const mapInstance = ref<TDMap | null>(null);
const searchKey = ref<string>('');
const poiList = ref<POI[]>([]);
const currentCenter = ref<[number, number]>([116.397428, 39.90923]);

// 初始化地图：优先定位，再加载POI（完全不变）
onMounted(async () => {
  if (!mapContainer.value) return;
  try {
    mapInstance.value = await initTDMap(mapContainer);
    addTDLayers(mapInstance.value);
    await getCurrentLocation();
    await loadNearbyPOI();
  } catch (err) {
    console.error('初始化失败：', err instanceof Error ? err.message : err);
    alert(`初始化失败：${err instanceof Error ? err.message : '未知错误'}`);
  }
});

// 卸载清理（完全不变）
onUnmounted(() => {
  mapInstance.value = null;
});

// 获取当前位置 - 加!断言消除window.T未定义报错（完全不变）
const getCurrentLocation = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (!mapInstance.value) return reject(new Error('地图未初始化'));
    // 核心：添加window.T!非空断言
    const geolocation = new window.T!.Geolocation();
    geolocation.getCurrentPosition((res: { success: boolean; lnglat: { getLng: () => number; getLat: () => number } }) => {
      if (res.success) {
        const lng = res.lnglat.getLng();
        const lat = res.lnglat.getLat();
        currentCenter.value = [lng, lat];
        mapInstance.value!.panTo(new window.T!.LngLat(lng, lat));
        resolve();
      } else {
        reject(new Error('定位失败，请开启定位权限'));
      }
    });
  });
};

// 加载周边POI（完全不变）
const loadNearbyPOI = async () => {
  try {
    const res = await axios.get<POI[]>(`/api/poi/nearby`, {
      params: { lng: currentCenter.value[0], lat: currentCenter.value[1], radius: 2000 }
    });
    poiList.value = res.data;
    renderPOIMarkers(res.data);
  } catch (err) {
    console.error('加载POI失败：', err instanceof Error ? err.message : err);
  }
};

// 搜索POI（完全不变）
const searchPOI = async () => {
  if (!searchKey.value.trim() || !mapInstance.value) return;
  try {
    const res = await axios.get<POI[]>(`/api/poi/search`, {
      params: { key: searchKey.value, lng: currentCenter.value[0], lat: currentCenter.value[1] }
    });
    poiList.value = res.data;
    renderPOIMarkers(res.data);
  } catch (err) {
    console.error('搜索失败：', err instanceof Error ? err.message : err);
  }
};

// 渲染POI标记 - 所有window.T添加!断言，类型已补全（完全不变）
const renderPOIMarkers = (pois: POI[]) => {
  if (!mapInstance.value) return;
  mapInstance.value.clearOverlays();
  
  pois.forEach(poi => {
    // 经纬度+标记点：加!断言
    const lnglat = new window.T!.LngLat(poi.lnglat[0], poi.lnglat[1]);
    const marker = new window.T!.Marker(lnglat);
    // 信息窗口：加!断言（类型已补全，无缺失）
    const infoWindow = new window.T!.InfoWindow(`<h3>${poi.name}</h3><p>${poi.address}</p>`);
    // 标记点点击事件：类型已补全，无报错
    marker.addEventListener('click', () => {
      mapInstance.value!.openInfoWindow(infoWindow, lnglat);
    });
    marker.addTo(mapInstance.value!);
  });

  // 中心点标记：加!断言
  const centerMarker = new window.T!.Marker(new window.T!.LngLat(currentCenter.value[0], currentCenter.value[1]));
  centerMarker.setIcon(new window.T!.Icon({ iconUrl: '@/assets/center.png', iconSize: [24, 24] }));
  centerMarker.addTo(mapInstance.value!);
};

// 聚焦指定POI - 加!断言，类型已补全（完全不变）
const focusPOI = (poi: POI) => {
  if (!mapInstance.value) return;
  const lnglat = new window.T!.LngLat(poi.lnglat[0], poi.lnglat[1]);
  mapInstance.value.panTo(lnglat);
  // 信息窗口：加!断言
  const infoWindow = new window.T!.InfoWindow(`<h3>${poi.name}</h3><p>${poi.address}</p>`);
  mapInstance.value.openInfoWindow(infoWindow, lnglat);
};
</script>

<style scoped>
.nearby-poi { height: 100vh; display: flex; flex-direction: column; box-sizing: border-box; margin: 0; padding: 0; }
.search-bar { padding: 10px 20px; background: #fff; border-bottom: 1px solid #eee; display: flex; gap: 10px; }
.search-bar input { flex: 1; padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; outline: none; }
.search-bar input:focus { border-color: #409eff; }
.search-bar button { padding: 8px 20px; background: #409eff; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.poi-container { flex: 1; display: flex; }
.poi-map { flex: 2; height: 100%; }
.poi-list { flex: 1; height: 100%; overflow-y: auto; border-left: 1px solid #eee; background: #fff; }
.poi-item { padding: 15px; border-bottom: 1px solid #f5f5f5; cursor: pointer; transition: background 0.2s; }
.poi-item:hover { background: #f5f5f5; }
.poi-item h4 { margin: 0 0 5px; font-size: 16px; color: #333; }
.poi-item p { margin: 0 0 5px; font-size: 12px; color: #666; }
.poi-type { font-size: 12px; padding: 2px 6px; background: #e6f7ff; color: #409eff; border-radius: 2px; }
</style>