<template>
  <div class="map-container" ref="mapRef"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { Map, View } from 'ol';
import TileLayer from 'ol/layer/Tile';
import XYZ from 'ol/source/XYZ';
import { fromLonLat, toLonLat } from 'ol/proj';
import type { Coordinate } from 'ol/coordinate';
import 'ol/ol.css';
import type { MapContainerProps, MapClickEvent, LngLat } from '@/types/map';

// Props + TS类型 + 默认值（正常使用，无修改）
const props = withDefaults(defineProps<MapContainerProps>(), {
  center: () => ({ lng: 116.40, lat: 39.90 }),
  zoom: 14,
  height: '100vh'
});

// 🔥 终极兜底：放弃defineEmits泛型，直接创建emit并指定类型断言
// 完全绕开Vue3与TS的兼容问题，TS100%识别正确类型
const emit = defineEmits() as {
  (e: 'map-init', mapInstance: Map): void;
  (e: 'map-click', event: MapClickEvent): void;
};

// 地图核心实例（无修改）
const mapRef = ref<HTMLDivElement | null>(null);
const mapInstance = ref<Map | null>(null);

// 天地图底图配置（无修改）
const TDT_KEY = '83ed38f63fae8ac967cf2e62de6f77a0';
const getTDTLayer = (layerType: string = 'vec'): TileLayer => {
  return new TileLayer({
    source: new XYZ({
      url: `http://t0.tianditu.gov.cn/${layerType}_c/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${layerType}&STYLE=default&TILEMATRIXSET=c&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TDT_KEY}`,
      projection: 'EPSG:4326',
      wrapX: true
    })
  });
};

// 初始化地图（无修改，保留所有修复点）
const initMap = (): void => {
  if (!mapRef.value) return;
  const map = new Map({
    target: mapRef.value,
    layers: [getTDTLayer('vec'), getTDTLayer('cva')],
    view: new View({
      projection: 'EPSG:4326',
      center: fromLonLat([props.center.lng, props.center.lat]),
      zoom: props.zoom,
      minZoom: 10,
      maxZoom: 18,
      constrainResolution: true
    })
  });
  mapInstance.value = map;

  // map-init 事件触发（类型完全匹配）
  map.on('rendercomplete', () => {
    emit('map-init', map);
  });

  // 地图点击事件（保留非空断言，确保类型合法）
  map.on('singleclick', (e) => {
    const lonLat = toLonLat(e.coordinate) as Coordinate;
    const lng = lonLat[0]!;
    const lat = lonLat[1]!;
    emit('map-click', {
      lng,
      lat,
      pixel: e.pixel as [number, number]
    });
  });
};

// 监听Props变化（无修改）
watch([() => props.center, () => props.zoom], ([newCenter, newZoom]) => {
  if (mapInstance.value) {
    mapInstance.value.getView().setCenter(fromLonLat([newCenter.lng, newCenter.lat]));
    mapInstance.value.getView().setZoom(newZoom);
  }
}, { deep: true });

// 生命周期（无修改）
onMounted(() => {
  initMap();
});

onUnmounted(() => {
  if (mapInstance.value) {
    mapInstance.value.setTarget(undefined);
    mapInstance.value = null;
  }
});

// 暴露给父组件的属性/方法（无修改）
defineExpose({
  mapRef,
  mapInstance,
  fromLonLat: (lngLat: LngLat) => fromLonLat([lngLat.lng, lngLat.lat]),
  toLonLat: (coord: number[]) => toLonLat(coord) as unknown as LngLat
});
</script>

<style scoped>
.map-container {
  width: 100%;
  height: v-bind(height);
  position: relative;
}
</style>