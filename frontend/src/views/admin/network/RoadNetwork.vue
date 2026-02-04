<template>
  <div class="road-network" style="display: flex; gap: 20px; height: calc(100vh - 40px);">
    <!-- 左侧地图绘制区域 -->
    <div style="flex: 2; border: 1px solid #eee; border-radius: 8px; position: relative; overflow: hidden;">
      <!-- 绘制控制按钮：修复图标绑定为 EditPen + Close 组件 -->
      <div style="position: absolute; top: 20px; left: 20px; z-index: 999; display: flex; gap: 10px;">
        <el-button type="primary" @click="toggleDraw" :icon="drawStatus ? Close : EditPen">
          {{ drawStatus ? '停止绘制' : '开始绘制路网' }}
        </el-button>
        <el-button type="success" @click="handleGenerateTopo" :disabled="!store.roadEdges.length">
          生成拓扑节点
        </el-button>
        <el-button type="info" @click="handleHighlightIsolated">
          高亮孤立POI
        </el-button>
      </div>
      <!-- 地图容器 -->
      <MapContainer :height="'100%'" ref="mapRef" />
      <!-- 孤立POI提示 -->
      <div v-if="isolatedPoiTip" style="position: absolute; bottom: 20px; left: 20px; background: rgba(255,77,77,0.9); color: #fff; padding: 8px 16px; border-radius: 4px;">
        发现{{ store.isolatedPoi.length }}个孤立POI（未关联路网），已在地图高亮
      </div>
    </div>
    <!-- 右侧路网信息区域 -->
    <div style="flex: 1; display: flex; flex-direction: column; gap: 20px;">
      <!-- 路网统计 -->
      <el-card shadow="hover">
        <div style="display: flex; justify-content: space-around; text-align: center;">
          <div>
            <div style="font-size: 24px; font-weight: bold; color: #1890ff;">{{ store.roadEdges.length }}</div>
            <div style="font-size: 14px; color: #666;">路网边总数</div>
          </div>
          <div>
            <div style="font-size: 24px; font-weight: bold; color: #f56c6c;">{{ (store.statData.roadTotalLength / 1000).toFixed(2) }}</div>
            <div style="font-size: 14px; color: #666;">路网总长度(km)</div>
          </div>
          <div>
            <div style="font-size: 24px; font-weight: bold; color: #67c23a;">{{ store.topoNodes.length }}</div>
            <div style="font-size: 14px; color: #666;">拓扑节点数</div>
          </div>
          <div>
            <div style="font-size: 24px; font-weight: bold; color: #909399;">{{ store.isolatedPoi.length }}</div>
            <div style="font-size: 14px; color: #666;">孤立POI数</div>
          </div>
        </div>
      </el-card>
      <!-- 路网边列表 -->
      <el-card shadow="hover" title="路网边列表" style="flex: 1; overflow: auto;">
        <el-table :data="store.roadEdges" border stripe style="width: 100%;">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column label="起点坐标" width="200">
            <template #default="scope">
              {{ scope.row.points[0]?.lng.toFixed(6) }}, {{ scope.row.points[0]?.lat.toFixed(6) }}
            </template>
          </el-table-column>
          <el-table-column label="终点坐标" width="200">
            <template #default="scope">
              {{ scope.row.points[scope.row.points.length-1]?.lng.toFixed(6) }}, {{ scope.row.points[scope.row.points.length-1]?.lat.toFixed(6) }}
            </template>
          </el-table-column>
          <el-table-column prop="length" label="长度(米)" width="120">
            <template #default="scope">{{ scope.row.length.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="createTime" label="创建时间" width="180" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
// 核心修复：删除不存在的PenIcon，替换为全版本通用的EditPen（+保留Close）
import { Close, EditPen } from '@element-plus/icons-vue';
import MapContainer from '@/components/map/MapContainer.vue';
import { useAdminStore } from '@/store';
import type { LngLat } from '@/types/map';
import type { Map } from 'ol';
import { Draw } from 'ol/interaction';
import VectorLayer from 'ol/layer/Vector';
import { LineString } from 'ol/geom';
import { Vector as VectorSource } from 'ol/source';
import { Style, Stroke } from 'ol/style';

const store = useAdminStore();
const drawStatus = ref(false);
const isolatedPoiTip = ref(false);
const mapRef = ref<{ mapInstance: Map | null }>({ mapInstance: null });
let draw: Draw | null = null;
let vectorLayer: VectorLayer<VectorSource> | null = null;

// 切换绘制状态（原有逻辑完全不变）
const toggleDraw = () => {
  drawStatus.value = !drawStatus.value;
  const map = mapRef.value.mapInstance;
  if (!map) return ElMessage.warning('地图实例未加载');

  if (drawStatus.value) {
    const vectorSource = new VectorSource();
    vectorLayer = new VectorLayer({
      source: vectorSource,
      style: new Style({
        stroke: new Stroke({ color: '#ff4500', width: 4 })
      })
    });
    map.addLayer(vectorLayer);

    draw = new Draw({
      source: vectorSource,
      type: 'LineString' as const,
      style: new Style({
        stroke: new Stroke({ color: '#ff4500', width: 4 })
      })
    });
    map.addInteraction(draw);

    draw.on('drawend', (e) => {
      const line = e.feature.getGeometry() as LineString;
      const coordinates = line.getCoordinates();
      const points = coordinates.map(coord => ({ lng: coord[0], lat: coord[1] })) as LngLat[];
      if (points.length < 2) return ElMessage.warning('路网边至少需要2个点');
      store.addRoadEdge({ points });
      vectorSource.clear();
    });

    ElMessage.success('开始绘制路网边，点击地图添加点，双击结束绘制');
  } else {
    if (draw) mapRef.value.mapInstance?.removeInteraction(draw);
    if (vectorLayer) mapRef.value.mapInstance?.removeLayer(vectorLayer);
    draw = null;
    vectorLayer = null;
    ElMessage.success('已停止路网绘制');
  }
};

// 生成拓扑节点
const handleGenerateTopo = () => {
  store.generateTopoNodes();
};

// 高亮孤立POI
const handleHighlightIsolated = () => {
  isolatedPoiTip.value = true;
  if (store.isolatedPoi.length === 0) {
    ElMessage.info('暂无孤立POI，所有POI均已关联路网');
    isolatedPoiTip.value = false;
    return;
  }
  ElMessage.info(`已高亮${store.isolatedPoi.length}个孤立POI`);
  setTimeout(() => isolatedPoiTip.value = false, 3000);
};

// 地图实例加载监听
onMounted(() => {
  const timer = setInterval(() => {
    if (mapRef.value.mapInstance) {
      clearInterval(timer);
      console.log('路网管理：地图实例加载完成');
    }
  }, 100);
});

// 页面卸载清理资源
onUnmounted(() => {
  const map = mapRef.value.mapInstance;
  if (map && draw) map.removeInteraction(draw);
  if (map && vectorLayer) map.removeLayer(vectorLayer);
  drawStatus.value = false;
});
</script>

<style scoped>
.road-network {
  flex: 1;
}
</style>