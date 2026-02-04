<template>
  <div class="route-planning">
    <div class="control-panel">
      <h3>路径规划</h3>
      <!-- 起点选择 -->
      <div class="form-item">
        <label>起点：</label>
        <button @click="useCurrentLocation">定位当前位置</button>
        <span v-if="startPoint">
          {{ startPoint[0].toFixed(6) }}, {{ startPoint[1].toFixed(6) }}
        </span>
        <p>或点击地图选择起点</p>
      </div>
      <!-- 终点选择 -->
      <div class="form-item">
        <label>终点：</label>
        <select v-model="selectedEndPOI" @change="handleEndChange">
          <option value="">请选择终点POI</option>
          <option 
            v-for="poi in endPOIList" 
            :key="poi.id"
            :value="JSON.stringify(poi)"
          >
            {{ poi.name }} ({{ poi.type }})
          </option>
        </select>
      </div>
      <!-- 策略切换 -->
      <div class="form-item">
        <label>规划策略：</label>
        <button 
          v-for="strategy in strategyList" 
          :key="strategy.value"
          :class="{ active: activeStrategy === strategy.value }"
          @click="activeStrategy = strategy.value"
        >
          {{ strategy.label }}
        </button>
      </div>
      <button class="plan-btn" @click="handleRoutePlan" :disabled="!startPoint || !endPoint">
        生成路线
      </button>
    </div>
    <div class="map-section">
      <div ref="mapContainer" class="map-container"></div>
      <div class="elevation-chart" v-if="routeInfo">
        <h4>高程剖面</h4>
        <div ref="chartContainer" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
// 工具方法与类型分离导入（符合项目规范）
import { initTDMap, addTDLayers } from '@/utils/map';
import type { TDMap, TDLngLat, TDMarker, TDPolyline, TDIcon } from '@/types/map';
import type { POI, RoutePlanParams, RouteInfo } from '@/types/map';
import axios from 'axios';
import * as echarts from 'echarts';

// 状态定义
const mapContainer = ref<HTMLDivElement | null>(null);
const chartContainer = ref<HTMLDivElement | null>(null);
const mapInstance = ref<TDMap | null>(null);
const startPoint = ref<[number, number] | null>(null);
const endPoint = ref<[number, number] | null>(null);
const selectedEndPOI = ref<string>('');
const endPOIList = ref<POI[]>([]);
// 策略类型约束
type StrategyType = 'leastTime' | 'leastDistance' | 'leastSlope';
const activeStrategy = ref<StrategyType>('leastTime');
const routeInfo = ref<RouteInfo | null>(null);
const elevationChart = ref<echarts.ECharts | null>(null);

// 策略列表（类型约束）
const strategyList: { label: string; value: StrategyType }[] = [
  { label: '最短时间', value: 'leastTime' },
  { label: '最短距离', value: 'leastDistance' },
  { label: '最小坡度', value: 'leastSlope' },
];

// 初始化地图（initTDMap保证window.T已加载）
onMounted(async () => {
  if (!mapContainer.value) return;
  try {
    mapInstance.value = await initTDMap(mapContainer);
    addTDLayers(mapInstance.value);

    // 地图点击选择起点 - 修复：window.T添加!断言
    mapInstance.value.addEventListener('click', (e: { lnglat: TDLngLat }) => {
      const lng = e.lnglat.getLng();
      const lat = e.lnglat.getLat();
      startPoint.value = [lng, lat];
      // 显式声明变量类型，解决链式调用推导问题
      const lngLat = new window.T!.LngLat(lng, lat);
      const marker: TDMarker = new window.T!.Marker(lngLat);
      marker.addTo(mapInstance.value!);
    });

    await loadEndPOIList();
  } catch (err) {
    console.error('地图初始化失败：', err instanceof Error ? err.message : err);
    alert(`初始化失败：${err instanceof Error ? err.message : '未知错误'}`);
  }
});

// 组件卸载：清理资源
onUnmounted(() => {
  if (elevationChart.value) {
    elevationChart.value.dispose();
    elevationChart.value = null;
  }
  window.removeEventListener('resize', handleChartResize);
});

// 加载终点POI列表
const loadEndPOIList = async () => {
  try {
    const res = await axios.get<POI[]>('/api/poi/list');
    endPOIList.value = res.data;
  } catch (err) {
    console.error('加载POI失败：', err instanceof Error ? err.message : err);
  }
};

// 选择终点POI解析
const handleEndChange = () => {
  if (!selectedEndPOI.value) {
    endPoint.value = null;
    return;
  }
  try {
    const poi = JSON.parse(selectedEndPOI.value) as POI;
    endPoint.value = poi.lnglat;
  } catch (err) {
    console.error('解析POI失败：', err);
    selectedEndPOI.value = '';
    endPoint.value = null;
  }
};

// 定位当前位置 - 修复：所有window.T添加!断言
const useCurrentLocation = () => {
  if (!mapInstance.value) {
    alert('地图未初始化，无法定位');
    return;
  }
  // window.T添加!断言
  const geolocation = new window.T!.Geolocation();
  geolocation.getCurrentPosition((res: { success: boolean; lnglat: TDLngLat }) => {
    if (res.success) {
      const lng = res.lnglat.getLng();
      const lat = res.lnglat.getLat();
      startPoint.value = [lng, lat];
      mapInstance.value!.panTo(new window.T!.LngLat(lng, lat));
      // 显式声明变量类型
      const lngLat = new window.T!.LngLat(lng, lat);
      const marker: TDMarker = new window.T!.Marker(lngLat);
      marker.addTo(mapInstance.value!);
    }
  });
};

// 路径规划接口请求
const handleRoutePlan = async () => {
  if (!startPoint.value || !endPoint.value || !mapInstance.value) return;
  try {
    const params: RoutePlanParams = {
      start: startPoint.value,
      end: endPoint.value,
      strategy: activeStrategy.value,
    };
    const res = await axios.post<RouteInfo>('/api/route/plan', params);
    routeInfo.value = res.data;
    renderRouteWithSlope();
    renderElevationChart();
  } catch (err) {
    console.error('路径规划失败：', err instanceof Error ? err.message : err);
  }
};

// 渲染坡度路线 - 修复：所有window.T添加!断言+显式类型声明
const renderRouteWithSlope = () => {
  if (!routeInfo.value || !mapInstance.value || routeInfo.value.points.length < 2) return;
  mapInstance.value.clearOverlays();

  const points = routeInfo.value.points;
  // 坡度颜色映射
  const getSlopeColor = (slope: number) => {
    return slope > 10 ? '#ff4444' : slope > 5 ? '#ff8888' : '#44ff44';
  };

  // 绘制分段路线折线 - 修复：window.T添加!断言
  points.forEach((_, i) => {
    if (i >= points.length - 1) return;
    const p1 = points[i]!;
    const p2 = points[i + 1]!;
    // 所有window.T添加!断言
    const polyline: TDPolyline = new window.T!.Polyline(
      [
        new window.T!.LngLat(p1.lnglat[0], p1.lnglat[1]),
        new window.T!.LngLat(p2.lnglat[0], p2.lnglat[1])
      ],
      { color: getSlopeColor((p1.slope + p2.slope) / 2), weight: 6, opacity: 0.8 }
    );
    polyline.addTo(mapInstance.value!);
  });

  // 绘制起点标记 - 修复：window.T!+拆分为临时变量+显式类型
  const startLngLat = new window.T!.LngLat(startPoint.value![0], startPoint.value![1]);
  const startMarker: TDMarker = new window.T!.Marker(startLngLat);
  const startIcon: TDIcon = new window.T!.Icon({ iconUrl: '@/assets/start.png', iconSize: [30, 30] });
  startMarker.setIcon(startIcon);
  startMarker.addTo(mapInstance.value!);

  // 绘制终点标记 - 修复：window.T!+拆分为临时变量+显式类型
  const endLngLat = new window.T!.LngLat(endPoint.value![0], endPoint.value![1]);
  const endMarker: TDMarker = new window.T!.Marker(endLngLat);
  const endIcon: TDIcon = new window.T!.Icon({ iconUrl: '@/assets/end.png', iconSize: [30, 30] });
  endMarker.setIcon(endIcon);
  endMarker.addTo(mapInstance.value!);

  // 缩放至路线范围 - 修复：window.T添加!断言
  const bounds = new window.T!.LngLatBounds();
  points.forEach(p => bounds.extend(new window.T!.LngLat(p.lnglat[0], p.lnglat[1])));
  mapInstance.value!.fitBounds(bounds);
};

// 渲染高程剖面图表
const renderElevationChart = () => {
  if (!routeInfo.value || !chartContainer.value || !routeInfo.value.elevationProfile.length) return;
  elevationChart.value = echarts.init(chartContainer.value);
  elevationChart.value.setOption({
    xAxis: { type: 'value', name: '距离 (米)', nameTextStyle: { fontSize: 12 } },
    yAxis: { type: 'value', name: '高程 (米)', nameTextStyle: { fontSize: 12 } },
    series: [{ type: 'line', data: routeInfo.value.elevationProfile.map(i => [i.x, i.y]), smooth: true, lineStyle: { color: '#409eff' } }],
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '3%', bottom: '3%', containLabel: true }
  });
  window.addEventListener('resize', handleChartResize);
  handleChartResize();
};

// ECharts窗口自适应
const handleChartResize = () => elevationChart.value && elevationChart.value.resize();
</script>

<style scoped>
.route-planning { display: flex; height: 100vh; margin: 0; padding: 0; box-sizing: border-box; }
.control-panel { width: 320px; padding: 20px; border-right: 1px solid #eee; background: #fff; }
.form-item { margin: 15px 0; }
.form-item label { display: inline-block; width: 60px; font-weight: 500; margin-bottom: 8px; }
.form-item button { margin-right: 8px; padding: 6px 12px; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; transition: all 0.2s; }
.form-item button:hover { border-color: #409eff; }
.form-item button.active { background: #409eff; color: #fff; border-color: #409eff; }
.form-item select { padding: 6px 12px; border: 1px solid #ccc; border-radius: 4px; min-width: 200px; }
.form-item p { margin: 8px 0 0; font-size: 12px; color: #666; }
.plan-btn { padding: 8px 20px; background: #409eff; color: #fff; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; font-size: 14px; }
.plan-btn:disabled { background: #ccc; cursor: not-allowed; }
.map-section { flex: 1; display: flex; flex-direction: column; }
.map-container { flex: 1; }
.elevation-chart { height: 200px; padding: 10px; border-top: 1px solid #eee; }
.elevation-chart h4 { margin: 0 0 8px; font-size: 14px; color: #333; }
.chart { width: 100%; height: 160px; }
</style>