<template>
  <div class="path-planning-page">
    <div class="page-toolbar">
      <el-select v-model="strategy" placeholder="选择规划策略" style="width: 180px; margin-right: 16px;">
        <el-option label="最短距离" value="shortest" />
        <el-option label="坡度最平缓" value="gentlest" />
      </el-select>
      <el-button type="primary" @click="handlePathPlanning">开始规划</el-button>
      <el-button type="success" @click="handleDownloadGpx" icon="Download" :disabled="!hasPath">下载GPX</el-button>
      <el-button type="default" @click="handleClear" icon="Clear" :disabled="!hasPath">清空路径</el-button>
    </div>
    <div class="page-content">
      <div class="content-map">
        <MapContainer 
          ref="mapRef"
          :center="mapCenter"
          :zoom="mapZoom"
          @map-init="onMapInit"
          @map-click="onMapClick"
        />
      </div>
      <div class="content-chart">
        <ElevationProfile 
          :data="samplingResult"
          title="当前路径高程/坡度剖面图"
          height="100%"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed} from 'vue';
import { ElMessage } from 'element-plus';
import MapContainer from '@/components/map/MapContainer.vue';
import ElevationProfile from '@/components/chart/ElevationProfile.vue';
import { Map } from 'ol';
import type{ LngLat, MapClickEvent } from '@/types/map';
import type{ PathSamplingPoint, PathStrategy } from '@/types';
// 接口请求（后续实现TS版Axios泛型请求）
// import { pathPlanningApi, downloadGpxApi } from '@/api/front';

// 地图实例Ref（TS类型：DefineRef<MapContainer | null>）
const mapRef = ref<InstanceType<typeof MapContainer> | null>(null);

// 响应式数据（全TS类型约束）
const strategy = ref<PathStrategy>('shortest');
const mapCenter = ref<LngLat>({ lng: 116.40, lat: 39.90 });
const mapZoom = ref<number>(14);
const startNode = ref<{ id: number; lng: number; lat: number } | null>(null);
const endNode = ref<{ id: number; lng: number; lat: number } | null>(null);
const samplingResult = ref<PathSamplingPoint[]>([]);

// 计算属性（TS类型：ComputedRef<boolean>）
const hasPath = computed<boolean>(() => samplingResult.value.length > 0);


  
// 地图初始化完成（TS类型：(mapInstance: Map) => void）
const onMapInit = (mapInstance: Map): void => {
  console.log('地图初始化完成', mapInstance);
};

// 地图点击事件（TS类型：(event: MapClickEvent) => void）
const onMapClick = (event: MapClickEvent): void => {
  console.log('地图点击', event);
  // 后续实现：点击选择起点/终点
};

// 开始路径规划（TS类型：() => Promise<void>）
const handlePathPlanning = async (): Promise<void> => {
  if (!startNode.value || !endNode.value) {
    ElMessage.warning('请先选择起点和终点');
    return;
  }
  try {
    // 后续对接TS版接口请求
    // const res = await pathPlanningApi({
    //   start_node_id: startNode.value.id,
    //   end_node_id: endNode.value.id,
    //   strategy: strategy.value
    // });
    // if (res.code === 200) {
    //   samplingResult.value = res.data.sampling_result;
    //   ElMessage.success('路径规划成功');
    // }
  } catch (error) {
    ElMessage.error(`路径规划失败：${(error as Error).message}`);
  }
};

// 下载GPX（TS类型：() => Promise<void>）
const handleDownloadGpx = async (): Promise<void> => {
  if (!startNode.value || !endNode.value) {
    ElMessage.warning('请先完成路径规划');
    return;
  }
  try {
    // 后续对接TS版GPX下载接口
    // await downloadGpxApi({
    //   start_node_id: startNode.value.id,
    //   end_node_id: endNode.value.id,
    //   strategy: strategy.value
    // });
  } catch (error) {
    ElMessage.error(`GPX下载失败：${(error as Error).message}`);
  }
};

// 清空路径（TS类型：() => void）
const handleClear = (): void => {
  samplingResult.value = [];
  startNode.value = null;
  endNode.value = null;
  ElMessage.success('已清空路径');
};
</script>

<style scoped>
.path-planning-page { width: 100%; height: 100%; display: flex; flex-direction: column; }
.page-toolbar { padding: 16px; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; align-items: center; }
.page-content { flex: 1; display: flex; width: 100%; height: calc(100% - 72px); }
.content-map { flex: 7; height: 100%; border-right: 1px solid #e5e7eb; }
.content-chart { flex: 3; height: 100%; padding: 16px; }
</style>
