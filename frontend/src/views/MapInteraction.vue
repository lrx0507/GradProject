<template>
  <div class="map-interaction">
    <!-- 左侧抽屉面板 -->
    <div class="drawer">
      <h3>POI分类筛选</h3>
      <div class="type-filter">
        <button 
          v-for="type in poiTypes" 
          :key="type.value"
          :class="{ active: activeType === type.value }"
          @click="handleTypeChange(type.value)"
        >
          {{ type.label }}
        </button>
      </div>
      <!-- 悬停POI信息 -->
      <div class="hover-poi" v-if="hoveredPOI">
        <h4>{{ hoveredPOI.name }}</h4>
        <p>类型：{{ hoveredPOI.type }}</p>
        <p>地址：{{ hoveredPOI.address }}</p>
      </div>
    </div>

    <!-- 地图容器 -->
    <div ref="mapContainer" class="map-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';
// 修复1：类型与工具方法分离导入（核心规范）
// 1. 工具方法：从@/utils/map导入（仅函数，无类型）
import { initTDMap, addTDLayers } from '@/utils/map';
// 2. 天地图类型：从@/types/map导入（仅类型，无函数），删除未使用的TDLngLat
import type { TDMap, TDGeolocation, TDGeolocationResult, TDMarker, TDInfoWindow } from '@/types/map';

// 1. 本地声明POI业务类型（与后端数据格式一致，解决POI导入失败问题）
/** POI基础类型（前后端统一，关联PostGIS空间数据） */
interface POI {
  id: string; // 唯一标识
  name: string; // POI名称
  type: 'rest' | 'food' | 'spot'; // 严格限定类型，避免无效值
  lnglat: [number, number]; // 经纬度元组 [经度, 纬度]
  address: string; // 详细地址
  distance?: number; // 可选：距离当前位置的距离（米，后端计算）
  geom?: string; // 可选：PostGIS的WKT几何字段
}

// 状态定义（全量使用具体类型，无any，天地图类型从全局导入）
const mapContainer = ref<HTMLDivElement | null>(null);
const mapInstance = ref<TDMap | null>(null); // 地图实例：TDMap | null
const activeType = ref<string>('all'); // 选中的POI分类
const hoveredPOI = ref<POI | null>(null); // 悬停的POI信息
const poiList = ref<POI[]>([]); // 所有POI列表

// POI分类选项（与POI.type严格匹配，保证类型一致性）
const poiTypes = [
  { label: '全部', value: 'all' },
  { label: '休息区', value: 'rest' },
  { label: '餐饮', value: 'food' },
  { label: '景点', value: 'spot' },
];

// 初始化地图 + 定位 + 加载POI
onMounted(async () => {
  // 兜底：地图容器未挂载则终止执行，避免空值报错
  if (!mapContainer.value) {
    console.warn('地图容器未挂载，初始化失败');
    return;
  }

  // 1. 初始化天地图（严格TDMap类型，无any）
  mapInstance.value = (await initTDMap(mapContainer)) as TDMap;
  addTDLayers(mapInstance.value);

  // 修复2：window.T非空前置校验，确保后续调用安全
  if (!window.T) {
    console.error('天地图脚本加载失败，window.T未定义');
    return;
  }

  // 2. 浏览器定位（使用全局导入的TDGeolocation/TDGeolocationResult类型）
  // 修复3：添加window.T!非空断言，消除TS18048
  const geolocation: TDGeolocation = new window.T!.Geolocation();
  geolocation.getCurrentPosition((res: TDGeolocationResult) => {
    // 定位成功 + 地图实例已初始化
    if (res.success && mapInstance.value) {
      const lng = res.lnglat.getLng();
      const lat = res.lnglat.getLat();
      // 构造目标经纬度（直接传数值，解决扩展运算符类型错误）
      const targetLngLat = new window.T!.LngLat(lng, lat);
      // 平移地图到当前定位位置
      mapInstance.value.panTo(targetLngLat);
      // 添加定位标记点（使用全局导入的TDMarker类型）
      const locationMarker: TDMarker = new window.T!.Marker(targetLngLat);
      locationMarker.addTo(mapInstance.value);
    }
  });

  // 3. 从后端FastAPI接口加载POI数据（PostGIS空间查询）
  await loadPOIData();
});

// 加载POI数据（明确axios响应类型为POI[]，TS自动校验返回格式）
const loadPOIData = async () => {
  try {
    const res = await axios.get<POI[]>('/api/poi/list');
    poiList.value = res.data;
    // 加载完成后渲染POI标记
    renderPOIMarkers();
  } catch (err) {
    // 友好的错误处理，区分Error对象和普通值
    console.error('POI数据加载失败：', err instanceof Error ? err.message : err);
  }
};

// 渲染POI标记（带鼠标悬停/移出事件，全量具体类型，无隐式any）
const renderPOIMarkers = () => {
  // 兜底：地图实例未初始化/天地图未加载则终止执行
  if (!mapInstance.value || !window.T) return;

  // 清空地图上现有所有覆盖物（标记/信息窗体等）
  // 修复4：修正方法名拼写（L小写，与类型声明一致）
  mapInstance.value.clearOverlays();

  // 按选中的分类筛选POI（显式声明filteredPOI类型为POI[]）
  const filteredPOI: POI[] = activeType.value === 'all'
    ? [...poiList.value] // 全部：浅拷贝原数组
    : poiList.value.filter(poi => poi.type === activeType.value); // 筛选：匹配类型

  // 遍历渲染每个POI标记（显式声明poi类型为POI，解决隐式any）
  filteredPOI.forEach((poi: POI) => {
    // 构造POI经纬度（直接取元组值，避免扩展运算符类型错误）
    const poiLngLat = new window.T!.LngLat(poi.lnglat[0], poi.lnglat[1]);
    // 创建标记点（使用全局导入的TDMarker类型）
    const poiMarker: TDMarker = new window.T!.Marker(poiLngLat);
    // 将标记添加到地图（非空断言：已做地图实例兜底，可安全使用!）
    poiMarker.addTo(mapInstance.value!);

    // 鼠标悬停事件：显示信息窗体 + 左侧抽屉同步POI信息
    poiMarker.addEventListener('mouseover', () => {
      hoveredPOI.value = poi;
      // 构造信息窗体内容（自定义样式，提升美观度）
      const infoWindowContent = `
        <div style="padding: 8px; min-width: 200px;">
          <h3 style="margin: 0 0 4px 0; font-size: 16px; color: #333;">${poi.name}</h3>
          <p style="margin: 2px 0; font-size: 14px; color: #666;">类型：${
            poi.type === 'rest' ? '休息区' : poi.type === 'food' ? '餐饮' : '景点'
          }</p>
          <p style="margin: 2px 0; font-size: 14px; color: #666;">地址：${poi.address}</p>
        </div>
      `;
      // 创建信息窗体（使用全局导入的TDInfoWindow类型）
      const infoWindow: TDInfoWindow = new window.T!.InfoWindow(infoWindowContent);
      // 打开信息窗体（绑定到当前POI经纬度）
      infoWindow.open(mapInstance.value!, poiLngLat);
    });

    // 鼠标移出事件：清空左侧POI信息 + 关闭信息窗体
    poiMarker.addEventListener('mouseout', () => {
      hoveredPOI.value = null;
      mapInstance.value!.closeInfoWindow();
    });
  });
};

// 切换POI分类（显式声明参数类型为string）
const handleTypeChange = (type: string) => {
  activeType.value = type;
  // 分类变化后重新渲染标记
  renderPOIMarkers();
};

// 监听POI列表变化，重新渲染标记（深度监听，确保数组内元素变化也能触发）
watch(poiList, renderPOIMarkers, { deep: true });
</script>

<style scoped>
/* 页面整体布局：左侧抽屉 + 右侧地图 */
.map-interaction {
  display: flex;
  height: 100vh;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 左侧筛选抽屉 */
.drawer {
  width: 280px;
  padding: 20px;
  border-right: 1px solid #eee;
  background: #fff;
  overflow-y: auto;
}

.drawer h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
}

/* POI分类筛选按钮 */
.type-filter {
  margin: 0 0 30px 0;
}

.type-filter button {
  margin: 0 10px 10px 0;
  padding: 6px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fff;
}

.type-filter button:hover {
  border-color: #409eff;
  color: #409eff;
}

.type-filter button.active {
  background: #409eff;
  color: #fff;
  border-color: #409eff;
}

/* 悬停POI信息展示 */
.hover-poi {
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
}

.hover-poi h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #333;
}

.hover-poi p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
}

/* 右侧地图容器 */
.map-container {
  flex: 1;
  height: 100vh;
}

/* 样式穿透：修复天地图信息窗体默认样式（提升UI美观度） */
:deep(.t-info-window) {
  padding: 0 !important;
  border-radius: 8px !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1) !important;
  border: none !important;
}
</style>