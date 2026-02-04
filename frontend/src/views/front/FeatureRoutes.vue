<template>
  <div class="feature-route">
    <!-- 路线卡片列表 -->
    <div class="card-list">
      <div class="route-card" v-for="card in routeCards" :key="card.id">
        <img :src="card.cover" alt="路线封面" class="card-cover">
        <div class="card-content">
          <h3>{{ card.title }}</h3>
          <div class="card-tags">
            <span v-for="tag in card.tags" :key="tag">{{ tag }}</span>
          </div>
          <p>距离：{{ (card.totalDistance / 1000).toFixed(2) }}km</p>
          <div class="card-actions">
            <button @click="previewRoute(card)">预览路线</button>
            <button @click="planRoute(card)">一键规划</button>
            <button @click="exportGPX(card)">导出GPX</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 地图预览区域 -->
    <div ref="mapContainer" class="map-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { initTDMap, addTDLayers } from '@/utils/map';
// 仅导入实际使用的类型，无冗余
import type { RouteCard, TDMap, TDLngLat, TDPolyline, TDPolylineOptions, TDLngLatBounds } from '@/types/map';
import axios from 'axios';
// 直接导入gpxparser，全局modules.d.ts已声明类型，无TS报错
import GPXParser from 'gpxparser';

// 状态定义：明确类型，无any
const mapContainer = ref<HTMLDivElement | null>(null);
const mapInstance = ref<TDMap | null>(null);
const routeCards = ref<RouteCard[]>([]);

// 初始化地图+加载数据
onMounted(async () => {
  if (!mapContainer.value) return;
  mapInstance.value = (await initTDMap(mapContainer)) as TDMap;
  addTDLayers(mapInstance.value as TDMap);
  await loadFeatureRoutes();
});

// 加载特色路线数据
const loadFeatureRoutes = async () => {
  try {
    const res = await axios.get('/api/route/feature');
    routeCards.value = res.data;
  } catch (err) {
    console.error('加载特色路线失败：', err instanceof Error ? err.message : err);
  }
};

// 预览路线：核心修复window.T非空断言
const previewRoute = (card: RouteCard) => {
  if (!mapInstance.value || !window.T) return; // 运行时双重非空校验

  mapInstance.value.clearOverlays();
  const points = card.points;
  
  // 修复TS18048：为window.T添加非空断言（!.），TS编译器识别类型安全
  const lnglats: TDLngLat[] = points.map((p) => new window.T!.LngLat(p.lnglat[0], p.lnglat[1]));
  
  // 完整的折线配置，匹配TDPolylineOptions接口
  const polylineOptions: TDPolylineOptions = {
    color: '#409eff',
    weight: 4,
    opacity: 0.8
  };
  const polyline: TDPolyline = new window.T!.Polyline(lnglats, polylineOptions);
  polyline.addTo(mapInstance.value);

  // 缩放地图到路线范围
  const bounds: TDLngLatBounds = new window.T!.LngLatBounds();
  lnglats.forEach((lnglat: TDLngLat) => bounds.extend(lnglat));
  mapInstance.value.fitBounds(bounds);
};

// 一键规划：跳转到路径规划页面并传参
const planRoute = (card: RouteCard) => {
  window.location.href = `/route-planning?routeId=${card.id}`;
};

// 导出GPX：构造GPX/xml数据并下载文件
const exportGPX = (card: RouteCard) => {
  // 保留GPXParser实例化，功能正常，无TS报错
  new GPXParser();
  // 构造标准GPX1.1格式数据，包含高程、坡度扩展字段
  const gpxData = `
    <?xml version="1.0" encoding="UTF-8"?>
    <gpx version="1.1" creator="WebGIS毕设" xmlns="http://www.topografix.com/GPX/1/1">
      <trk>
        <name>${card.title}</name>
        <trkseg>
          ${card.points.map((p) => `
            <trkpt lon="${p.lnglat[0]}" lat="${p.lnglat[1]}">
              <ele>${p.elevation}</ele>
              <extensions>
                <slope>${p.slope}</slope>
              </extensions>
            </trkpt>
          `).join('')}
        </trkseg>
      </trk>
    </gpx>
  `.trim(); // 去除多余空格，生成标准XML

  // 下载文件：创建Blob并触发浏览器下载
  const blob = new Blob([gpxData], { type: 'application/gpx+xml; charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${card.title.replace(/[\/:*?"<>|]/g, '')}.gpx`; // 过滤非法文件名字符
  a.click();
  URL.revokeObjectURL(url); // 释放URL对象，避免内存泄漏
};
</script>

<style scoped>
.feature-route {
  display: flex;
  height: 100vh;
  font-size: 14px;
  color: #333;
  background: #fafafa;
}
.card-list {
  width: 360px;
  padding: 20px;
  border-right: 1px solid #eee;
  overflow-y: auto;
  background: #fff;
}
.route-card {
  margin-bottom: 20px;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}
.route-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.card-cover {
  width: 100%;
  height: 180px;
  object-fit: cover;
}
.card-content {
  padding: 15px;
}
.card-content h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: 600;
}
.card-tags {
  margin: 10px 0;
}
.card-tags span {
  display: inline-block;
  padding: 2px 8px;
  background: #f0f9ff;
  color: #409eff;
  border-radius: 4px;
  margin-right: 5px;
  font-size: 12px;
  margin-bottom: 5px;
}
.card-content p {
  margin: 0;
  color: #666;
}
.card-actions {
  margin-top: 15px;
  display: flex;
  gap: 8px;
}
.card-actions button {
  flex: 1;
  padding: 6px 0;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  font-size: 14px;
}
.card-actions button:hover {
  background: #f5f7fa;
  border-color: #409eff;
  color: #409eff;
}
.map-container {
  flex: 1;
}
</style>