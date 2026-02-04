<!-- src/views/HomeView.vue -->
<template>
  <div>
    <h1>Trail System - 天地图底图 + POI</h1>
    <button @click="manualLocation">定位到我的位置</button>
    <button @click="loadPois">加载 POI</button>
    <!-- 新增的导航链接 -->
    <a
      href="/about"
      target="_blank"
      rel="noopener noreferrer"
      style="margin-left: 10px; text-decoration: underline; color: #007bff; cursor: pointer;"
    >
      在新页面打开“关于我们”
    </a>
    <div id="map" style="width: 100%; height: 900px; margin-top: 10px"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import axios from 'axios'
import type { Poi } from '@/types/poi'

// 引入 OpenLayers 相关依赖
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import XYZ from 'ol/source/XYZ'
import VectorSource from 'ol/source/Vector'
import VectorLayer from 'ol/layer/Vector'
import Point from 'ol/geom/Point'
import Feature from 'ol/Feature'
import { Style, Circle, Fill, Stroke } from 'ol/style'
import { fromLonLat } from 'ol/proj'

// === 替换为你自己的天地图 Key ===
const TDT_KEY = '83ed38f63fae8ac967cf2e62de6f77a0' // ←←← 这里填你的 Key！

// 地图实例引用
let map: Map | null = null

// POI 矢量数据源（用于存储和渲染POI点）
const vectorSource = new VectorSource()

// POI 矢量图层（配置POI显示样式）
const vectorLayer = new VectorLayer({
  source: vectorSource,
  style: new Style({
    image: new Circle({
      radius: 8,
      fill: new Fill({ color: '#ff6f61' }), // POI填充色：珊瑚红
      stroke: new Stroke({ color: '#fff', width: 2 }), // 白色边框
    }),
  }),
})

// 用户当前位置（经纬度：[经度, 纬度]）
const userLocation = ref<[number, number] | null>(null)

// 组件挂载时初始化
onMounted(async () => {
  // 初始化地图，默认以北京（116.4074, 39.9042）为中心
  initializeMap([116.4074, 39.9042])
  // 自动尝试获取用户当前位置
  await getCurrentLocation()
})

// 组件卸载时清理地图资源（防止内存泄漏）
onBeforeUnmount(() => {
  if (map) {
    map.setTarget(undefined) // 解除地图与DOM的绑定
    map = null // 释放地图实例引用
  }
})

/**
 * 初始化地图实例
 * @param center - 地图中心点经纬度（WGS84坐标系）
 */
const initializeMap = (center: [number, number]) => {
  // 1. 天地图矢量底图（无注记）
  const vecLayer = new TileLayer({
    source: new XYZ({
      url: `http://t0.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TDT_KEY}`,
      attributions: '© <a href="https://www.tianditu.gov.cn/" target="_blank">天地图</a>',
    }),
  })

  // 2. 天地图注记层（文字标签，如街道名、地名）
  const cvaLayer = new TileLayer({
    source: new XYZ({
      url: `http://t0.tianditu.gov.cn/cia_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cia&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TDT_KEY}`,
      attributions: '© <a href="https://www.tianditu.gov.cn/" target="_blank">天地图</a>',
    }),
  })

  // 3. 创建地图实例
  map = new Map({
    target: 'map', // 绑定DOM元素ID（对应模板中的<div id="map">）
    layers: [vecLayer, cvaLayer, vectorLayer], // 图层顺序：底图→注记→POI
    view: new View({
      center: fromLonLat(center), // 转换WGS84经纬度到EPSG:3857墨卡托坐标
      zoom: 18, // 初始缩放级别（1-20，越大越详细）
      projection: 'EPSG:3857', // 地图投影坐标系（Web墨卡托）
    }),
  })
}

/**
 * 获取用户当前位置（调用浏览器地理定位API）
 * @returns Promise<void> - 定位完成后resolve
 */
const getCurrentLocation = (): Promise<void> => {
  return new Promise((resolve) => {
    // 检查浏览器是否支持地理定位
    if (!navigator.geolocation) {
      console.warn('浏览器不支持地理定位功能')
      resolve()
      return
    }

    // 调用浏览器地理定位API
    navigator.geolocation.getCurrentPosition(
      // 定位成功回调
      (position) => {
        const { longitude, latitude } = position.coords // 获取经纬度
        userLocation.value = [longitude, latitude] // 存储用户位置

        // 地图平滑移动到用户位置
        if (map) {
          map.getView().animate({
            center: fromLonLat([longitude, latitude]), // 转换坐标
            zoom: 18.3, // 定位后缩放级别（比初始略大）
            duration: 1000, // 动画时长：1秒
          })
        }

        console.log('获取到用户位置:', userLocation.value)
        resolve()
      },
      // 定位失败回调
      (error) => {
        console.error('获取位置失败:', error.message)
        resolve() // 无论成功失败都resolve，避免阻塞
      },
      // 定位配置项
      {
        enableHighAccuracy: true, // 启用高精度定位（GPS）
        timeout: 10000, // 超时时间：10秒
        maximumAge: 300000, // 位置缓存有效期：5分钟（300秒）
      },
    )
  })
}

/**
 * 手动触发定位（点击按钮调用）
 */
const manualLocation = async () => {
  await getCurrentLocation()
  // 定位失败时给出用户提示
  if (!userLocation.value) {
    alert('无法获取您的位置，请确保已允许浏览器位置访问权限')
  }
}

/**
 * 从后端加载POI数据并渲染到地图
 */
const loadPois = async () => {
  try {
    // 调用后端API获取POI列表（后端地址：http://localhost:8000/pois）
    const response = await axios.get<Poi[]>('http://localhost:8000/pois')
    const pois = response.data

    // 清空现有POI数据（避免重复渲染）
    vectorSource.clear()

    // 遍历POI数据，转换坐标并添加到地图
    pois.forEach((poi) => {
      // 将WGS84经纬度（lng, lat）转换为EPSG:3857墨卡托坐标
      const point = fromLonLat([poi.lng, poi.lat])
      // 创建OpenLayers要素（包含几何形状和属性）
      const feature = new Feature({
        geometry: new Point(point), // 几何形状：点
      })
      feature.set('name', poi.name) // 存储POI名称（可用于弹窗显示）
      vectorSource.addFeature(feature) // 添加要素到数据源
    })

    // 若有POI数据，地图自动适配所有POI范围
    if (pois.length > 0) {
      const extent = vectorSource.getExtent() // 获取所有POI的包围盒
      map?.getView().fit(extent, {
        padding: [50, 50, 50, 50], // 地图边缘内边距：50px（避免POI贴边）
        maxZoom: 18, // 最大缩放级别限制
        duration: 1000, // 适配动画时长：1秒
      })
    }
  } catch (error) {
    console.error('加载POI失败:', error)
    alert('加载失败，请检查后端服务是否已启动（http://localhost:8000）')
  }
}
</script>

<style scoped>
/* 地图容器样式 */
#map {
  border: 1px solid #ccc;
  border-radius: 4px; /* 可选：添加圆角 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* 可选：添加轻微阴影 */
}

/* 按钮样式 */
button {
  margin-right: 10px;
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease; /*  hover过渡效果 */
}

/* 按钮 hover 状态 */
button:hover {
  background-color: #0056b3; /* 深色系 hover 效果 */
}

/* 导航链接样式优化（保持原功能，增强可读性） */
a {
  font-size: 14px;
  transition: color 0.3s ease;
}

a:hover {
  color: #0056b3; /* 链接 hover 深色效果 */
  text-decoration: none;
}
</style>